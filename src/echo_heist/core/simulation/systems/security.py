"""Simulation-owned application of observation-driven Sentinel decisions and sensors."""

from dataclasses import replace

from echo_heist.ai.guards.sentinel import decide
from echo_heist.core.contracts.events import EventKind, GameEvent, HeardCue, SecurityReport
from echo_heist.core.contracts.observations import EntityView, Observation
from echo_heist.core.contracts.security.model import (
    GuardDecision,
    GuardState,
    SecuritySpec,
    VisualCue,
)
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import ActorKind, StaticMap
from echo_heist.core.perception.sensors import can_see, line_of_sight, sound_reaches
from echo_heist.core.simulation.world import Emit, WorldState

INTRUDERS = frozenset({ActorKind.OPERATIVE, ActorKind.COMPANION})


def decisions(
    spec: SecuritySpec, observations: tuple[Observation, ...], world: WorldState
) -> tuple[tuple[Observation, GuardDecision], ...]:
    by_id = {observation.agent_id: observation for observation in observations}
    return tuple(
        (
            by_id[patrol.actor_id],
            decide(
                by_id[patrol.actor_id], patrol, spec.rules, world.guard_memories[patrol.actor_id]
            ),
        )
        for patrol in spec.patrols
    )


def apply_decisions(
    world: WorldState,
    spec: SecuritySpec,
    choices: tuple[tuple[Observation, GuardDecision], ...],
    emit: Emit,
) -> None:
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
        world.actors[actor_id].facing = decision.facing
        if memory.state != previous.state or memory.path_goal != previous.path_goal:
            emit(
                EventKind.POLICY_DECISION,
                actor_id,
                (
                    ("state", memory.state.value),
                    ("algorithm", "BFS"),
                    ("expanded_nodes", memory.expanded_nodes),
                    ("fuzzy_urgency", memory.urgency),
                ),
            )
        if (
            memory.state == GuardState.CHASE
            and memory.last_seen_tile is not None
            and (
                previous.state != GuardState.CHASE
                or memory.last_seen_tick - previous.last_report_tick >= 15
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


def refresh(
    world: WorldState, world_map: StaticMap, spec: SecuritySpec, events: tuple[GameEvent, ...]
) -> None:
    rules = spec.rules
    active = {patrol.actor_id for patrol in spec.patrols}
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
            if other.actor_id == actor_id:
                continue
            sight = (
                can_see(
                    world_map,
                    actor.position,
                    other.position,
                    actor.facing,
                    rules.sight_range_tiles,
                    rules.half_angle_degrees,
                )
                if actor_id in active
                else (
                    (actor.position[0] - other.position[0]) ** 2
                    + (actor.position[1] - other.position[1]) ** 2
                    <= (rules.sight_range_tiles * UNIT) ** 2
                    and line_of_sight(world_map, actor.position, other.position)
                )
            )
            if sight:
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
        world.visual_cues[actor_id] = tuple(
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
        )


def capture_eligible(world: WorldState) -> frozenset[str]:
    # Unconnected P02 posts retain their contact behavior. Active guards must
    # actually identify and currently see an intruder before starting a grab.
    return frozenset(
        actor_id
        for actor_id in world.actors
        if actor_id not in world.guard_memories
        or (
            world.guard_memories[actor_id].state == GuardState.CHASE
            and any(entity.kind in INTRUDERS for entity in world.visible_entities.get(actor_id, ()))
        )
    )
