"""Simulation-owned application of observation-driven guard decisions and sensors."""

from collections.abc import Mapping
from dataclasses import replace

from echo_heist.ai.guards import sentinel, tracker
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.events import EventKind, GameEvent, HeardCue, SecurityReport
from echo_heist.core.contracts.observations import EntityView, Observation
from echo_heist.core.contracts.security.model import (
    ROLE_ALGORITHMS,
    GuardDecision,
    GuardMemory,
    GuardPatrol,
    GuardRole,
    GuardState,
    SecuritySpec,
    VisualCue,
)
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import ActorKind, StaticMap
from echo_heist.core.perception.concealment import (
    inspection_reveals,
    is_concealed,
    witnessed_entry,
)
from echo_heist.core.perception.sensors import can_see, line_of_sight, sound_reaches
from echo_heist.core.simulation.world import Emit, WorldState

INTRUDERS = frozenset({ActorKind.OPERATIVE, ActorKind.COMPANION})
CONTROLLED = frozenset({GuardRole.SENTINEL, GuardRole.TRACKER})
REPORT_INTERVAL_TICKS = 15


def _decide(
    patrol: GuardPatrol, observation: Observation, spec: SecuritySpec, memory: GuardMemory
) -> GuardDecision:
    if patrol.role == GuardRole.SENTINEL:
        return sentinel.decide(observation, patrol, spec.rules, memory)
    if patrol.role == GuardRole.TRACKER:
        return tracker.decide(observation, patrol, spec.rules, memory)
    # A POST senses for capture fairness but has no strategy until P04.
    wait = Action(observation.agent_id, ActionKind.WAIT, observation.tick)
    return GuardDecision(wait, memory, observation.own_status.facing)


def decisions(
    spec: SecuritySpec, observations: tuple[Observation, ...], world: WorldState
) -> tuple[tuple[Observation, GuardDecision], ...]:
    by_id = {observation.agent_id: observation for observation in observations}
    return tuple(
        (
            by_id[patrol.actor_id],
            _decide(patrol, by_id[patrol.actor_id], spec, world.guard_memories[patrol.actor_id]),
        )
        for patrol in spec.patrols
    )


def _evidence_observed(observation: Observation, memory: GuardMemory) -> bool:
    """New goal evidence must be something this guard's own Observation contained."""
    kind, key, tick = memory.evidence_kind, memory.evidence_id, memory.evidence_tick
    if kind == "SIGHT":
        return tick == observation.tick and key == f"sight:{observation.agent_id}:{tick}"
    if kind == "NOISE":
        return any(c.event_id == key and c.tick == tick for c in observation.heard_events)
    if kind in ("MOTION", "HIDE_ENTRY"):
        return any(c.cue_id == key and c.tick == tick for c in observation.visual_cues)
    if kind == "REPORT":
        return any(
            r.event_id == key and r.tick == tick and r.source_guard != observation.agent_id
            for r in observation.shared_reports
        )
    return False


def apply_decisions(
    world: WorldState,
    spec: SecuritySpec,
    choices: tuple[tuple[Observation, GuardDecision], ...],
    emit: Emit,
) -> None:
    roles = {patrol.actor_id: patrol.role for patrol in spec.patrols}
    for observation, decision in choices:
        actor_id = observation.agent_id
        previous = world.guard_memories[actor_id]
        memory = decision.memory
        if memory.last_seen_tick > previous.last_seen_tick and (
            memory.last_seen_tick != observation.tick
            or not any(
                entity.kind in INTRUDERS and entity.tile == memory.last_seen_tile
                for entity in observation.visible_entities
            )
        ):
            raise ValueError("A guard may remember only an actually observed intruder location")
        if (
            memory.evidence_id,
            memory.evidence_tick,
        ) != (previous.evidence_id, previous.evidence_tick) and not _evidence_observed(
            observation, memory
        ):
            raise ValueError("Guard evidence must come from its own filtered observation")
        world.actors[actor_id].facing = decision.facing
        if memory.state != previous.state or memory.path_goal != previous.path_goal:
            emit(
                EventKind.POLICY_DECISION,
                actor_id,
                (
                    ("state", memory.state.value),
                    ("algorithm", ROLE_ALGORITHMS[roles[actor_id]]),
                    ("expanded_nodes", memory.expanded_nodes),
                    ("path_cost", memory.path_cost),
                    ("fuzzy_urgency", memory.urgency),
                    ("evidence_kind", memory.evidence_kind),
                    ("evidence_tick", memory.evidence_tick),
                ),
            )
        if (
            memory.state == GuardState.CHASE
            and memory.last_seen_tile is not None
            and (
                previous.state != GuardState.CHASE
                or memory.last_seen_tick - previous.last_report_tick >= REPORT_INTERVAL_TICKS
            )
        ):
            report_id = f"sight:{actor_id}:{memory.last_seen_tick}"
            report = SecurityReport(
                actor_id,
                "SIGHTING",
                memory.last_seen_tile,
                memory.last_seen_tick,
                1.0,
                report_id,
                memory.last_seen_tick + spec.rules.report_ttl_ticks,
            )
            world.security_reports = (
                *(value for value in world.security_reports if value.source_guard != actor_id),
                report,
            )
            memory = replace(memory, last_report_tick=memory.last_seen_tick)
            if previous.state != GuardState.CHASE:
                emit(
                    EventKind.SIGHTING_CONFIRMED,
                    actor_id,
                    (("x", report.tile[0]), ("y", report.tile[1]), ("observed_tick", report.tick)),
                )
            emit(
                EventKind.REPORT_SENT,
                actor_id,
                (
                    ("report_id", report_id),
                    ("observed_tick", report.tick),
                    ("expires_at_tick", report.expires_at_tick),
                ),
            )
        world.guard_memories[actor_id] = memory


def _sees(
    world: WorldState, world_map: StaticMap, spec: SecuritySpec, viewer: str, other: str
) -> bool:
    rules = spec.rules
    actor, target = world.actors[viewer], world.actors[other]
    if viewer in world.guard_memories:
        if is_concealed(world_map, target.tile, target.crouched):
            return inspection_reveals(
                actor.tile,
                target.tile,
                world.hide_witnesses.get(viewer, ()),
                world.tick,
                rules.memory_ticks,
            )
        return can_see(
            world_map,
            actor.position,
            target.position,
            actor.facing,
            rules.sight_range_tiles,
            rules.half_angle_degrees,
        )
    return (actor.position[0] - target.position[0]) ** 2 + (
        actor.position[1] - target.position[1]
    ) ** 2 <= (rules.sight_range_tiles * UNIT) ** 2 and line_of_sight(
        world_map, actor.position, target.position
    )


def _witness(
    world: WorldState,
    world_map: StaticMap,
    spec: SecuritySpec,
    previous: Mapping[str, tuple[EntityView, ...]],
    emit: Emit | None,
) -> None:
    """Record cover entries a controlled guard saw happen; expire old ones."""
    ttl = spec.rules.memory_ticks
    for patrol in spec.patrols:
        guard_id = patrol.actor_id
        cues = [
            cue for cue in world.hide_witnesses.get(guard_id, ()) if world.tick - cue.tick <= ttl
        ]
        if patrol.role in CONTROLLED and not world.actors[guard_id].incapacitated(world.tick):
            for entity in previous.get(guard_id, ()):
                actor = world.actors.get(entity.actor_id)
                if (
                    actor is not None
                    and actor.kind in INTRUDERS
                    and not entity.concealed
                    and is_concealed(world_map, actor.tile, actor.crouched)
                ):
                    cue = witnessed_entry(guard_id, actor.tile, world.tick)
                    cues.append(cue)
                    if emit is not None:
                        emit(
                            EventKind.HIDE_WITNESSED,
                            guard_id,
                            (("x", cue.tile[0]), ("y", cue.tile[1]), ("cue_id", cue.cue_id)),
                        )
        if cues:
            world.hide_witnesses[guard_id] = tuple(cues)
        else:
            world.hide_witnesses.pop(guard_id, None)


def refresh(
    world: WorldState,
    world_map: StaticMap,
    spec: SecuritySpec,
    events: tuple[GameEvent, ...],
    emit: Emit | None = None,
) -> None:
    rules = spec.rules
    active = {patrol.actor_id for patrol in spec.patrols}
    previous = dict(world.visible_entities)
    _witness(world, world_map, spec, previous, emit)
    world.visible_entities.clear()
    world.heard_cues.clear()
    world.visual_cues.clear()
    world.security_reports = tuple(
        report for report in world.security_reports if world.tick <= report.expires_at_tick
    )
    for actor_id, actor in world.actors.items():
        if actor.incapacitated(world.tick) or (
            actor_id not in active and actor.kind not in INTRUDERS
        ):
            continue
        visible: list[EntityView] = []
        for other in world.actors.values():
            if other.actor_id == actor_id or not _sees(
                world, world_map, spec, actor_id, other.actor_id
            ):
                continue
            visible.append(
                EntityView(
                    other.actor_id,
                    other.kind,
                    other.tile,
                    other.position,
                    world.tick < other.disabled_until,
                    world.tick < other.stunned_until,
                    other.facing,
                    crouched=other.crouched,
                    concealed=is_concealed(world_map, other.tile, other.crouched),
                )
            )
        world.visible_entities[actor_id] = tuple(visible)
        if actor_id not in active:
            continue
        cues: list[HeardCue] = []
        for event in events:
            if event.kind != EventKind.NOISE_CREATED or event.actor_id == actor_id:
                continue
            details = dict(event.details)
            x, y, radius = details.get("x"), details.get("y"), details.get("radius_tiles")
            if (
                type(x) is int
                and type(y) is int
                and type(radius) is int
                and sound_reaches(world_map, spec.sound_blocking_tiles, (x, y), actor.tile, radius)
            ):
                cues.append(
                    HeardCue(event.event_id, str(details.get("kind", "NOISE")), (x, y), event.tick)
                )
        world.heard_cues[actor_id] = tuple(cues)
        motion: list[VisualCue] = [
            VisualCue(
                echo.echo_id,
                (echo.path[echo.index][0] // UNIT, echo.path[echo.index][1] // UNIT),
                world.tick,
            )
            for echo in world.echoes.values()
            if can_see(
                world_map,
                actor.position,
                echo.path[echo.index],
                actor.facing,
                rules.sight_range_tiles,
                rules.half_angle_degrees,
            )
        ]
        world.visual_cues[actor_id] = (*motion, *world.hide_witnesses.get(actor_id, ()))


def capture_targets(world: WorldState, spec: SecuritySpec) -> Mapping[str, frozenset[str]]:
    """Which intruders each guard may grab: only one it currently, legitimately sees.

    Controlled guards also need confirmed CHASE. A POST needs current sight. A
    guard absent from the registry keeps P02 contact capture of unconcealed
    targets (handled by the capture system's default).
    """
    roles = {patrol.actor_id: patrol.role for patrol in spec.patrols}
    allowed: dict[str, frozenset[str]] = {}
    for guard_id, memory in world.guard_memories.items():
        seen = frozenset(
            entity.actor_id
            for entity in world.visible_entities.get(guard_id, ())
            if entity.kind in INTRUDERS
        )
        if roles[guard_id] == GuardRole.POST or memory.state == GuardState.CHASE:
            allowed[guard_id] = seen
        else:
            allowed[guard_id] = frozenset()
    return allowed
