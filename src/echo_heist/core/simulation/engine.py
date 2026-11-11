"""Authoritative fixed-step gameplay; pure values in, committed events out."""

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict
from hashlib import sha256

from echo_heist.ai.director.nexus import initial_memory
from echo_heist.ai.navigation.grid import bfs
from echo_heist.core.abilities.tools import advance_echoes, tool_reason, use_tool
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.config.scenario import IntruderStart
from echo_heist.core.contracts.config.scoring import ScoringRules
from echo_heist.core.contracts.environment.model import EnvironmentSpec
from echo_heist.core.contracts.events import EventKind, GameEvent
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.results import (
    MissionSpec,
    PresentationSnapshot,
    RunOutcome,
    RunResult,
    StepResult,
)
from echo_heist.core.contracts.security.director import NexusStatus
from echo_heist.core.contracts.security.model import (
    GuardMemory,
    GuardRole,
    GuardState,
    InterceptPlan,
    SecuritySpec,
)
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import (
    ActorKind,
    ActorSpawn,
    MissionPhase,
    Position,
    Scalar,
    StaticMap,
    tile_center,
)
from echo_heist.core.environment import lifecycle as props
from echo_heist.core.perception.sensors import line_of_sight
from echo_heist.core.scoring import encounters
from echo_heist.core.scoring.score import score_run
from echo_heist.core.simulation import views
from echo_heist.core.simulation.systems import security as guard_security
from echo_heist.core.simulation.systems.capture import update_captures
from echo_heist.core.simulation.systems.mission import (
    check_extraction,
    end_mission,
    interaction_reason,
    interaction_target,
    mission_object,
    update_theft,
)
from echo_heist.core.simulation.systems.motion import body_fits, move_actor, remember_paths
from echo_heist.core.simulation.systems.traversal import (
    advance_stairs,
    cancel_stair,
    stair_hints,
    update_sprint,
    use_stair,
)
from echo_heist.core.simulation.world import GUARD_KINDS, ActorState, WorldState

TOOL_ACTIONS = frozenset({ActionKind.ECHO, ActionKind.EMP, ActionKind.MELEE})
DECISIVE = frozenset(
    {
        EventKind.CORE_TAKEN,
        EventKind.LOCKDOWN_STARTED,
        EventKind.CAPTURE_COMPLETED,
        EventKind.MISSION_ENDED,
    }
)
ROLE_KINDS = {
    GuardRole.SENTINEL: frozenset({ActorKind.SENTINEL}),
    GuardRole.TRACKER: frozenset({ActorKind.TRACKER}),
    GuardRole.POST: GUARD_KINDS,
    GuardRole.INTERCEPTOR: frozenset({ActorKind.INTERCEPTOR}),
}


def _map_payload(world_map: StaticMap) -> dict[str, object]:
    return {
        "id": world_map.map_id,
        "width": world_map.width,
        "height": world_map.height,
        "tile_size_px": world_map.tile_size_px,
        "blocked": sorted(world_map.blocked_tiles),
        "opaque": sorted(world_map.opaque_tiles),
        "crouch_tiles": sorted(world_map.crouch_tiles),
        "obstacles": [
            (
                obj.object_id,
                obj.left,
                obj.top,
                obj.right,
                obj.bottom,
                sorted(obj.reserved_tiles),
                obj.opaque,
            )
            for obj in world_map.obstacles
        ],
        "objects": [asdict(obj) for obj in world_map.objects],
        "stairs": [asdict(link) for link in world_map.stairs],
        "door_tiles": sorted(world_map.door_tiles),
    }


class Simulation:
    def __init__(
        self,
        world_map: StaticMap,
        spawns: tuple[ActorSpawn, ...],
        *,
        rules: GameRules,
        mission: MissionSpec | None = None,
        seed: int = 1042,
        security: SecuritySpec | None = None,
        environment: EnvironmentSpec | None = None,
        scoring: ScoringRules | None = None,
        intruder_start: IntruderStart | None = None,
    ) -> None:
        if not spawns:
            raise ValueError("At least one actor is required")
        self._base_map, self._environment = world_map, environment
        self._scoring = scoring or ScoringRules()
        self._start = intruder_start
        prop_state = props.initial_state(environment) if environment is not None else None
        if environment is not None and prop_state is not None:
            stair_tiles = {link.tile for link in world_map.stairs}
            for prop in environment.props:
                if any(
                    not world_map.can_walk(tile)
                    or tile in stair_tiles
                    or tile in world_map.crouch_tiles
                    for tile in prop.tiles
                ):
                    raise ValueError(f"Prop {prop.object_id!r} must stand on open, non-stair floor")
            world_map = props.effective_map(world_map, prop_state)
        if len({spawn.actor_id for spawn in spawns}) != len(spawns) or len(
            {spawn.tile for spawn in spawns}
        ) != len(spawns):
            raise ValueError("Actor IDs and starting tiles must be unique")
        if any(
            not body_fits(world_map, tile_center(spawn.tile), rules.actor_radius_units)
            for spawn in spawns
        ):
            raise ValueError("Actor spawn must fit on a walkable map tile")
        self._map, self._rules, self._mission, self._seed = world_map, rules, mission, seed
        self._security = security
        self._pending_geometry: tuple[StaticMap, str] | None = None
        self._world = WorldState(
            actors={
                spawn.actor_id: ActorState(
                    spawn.actor_id,
                    spawn.kind,
                    tile_center(spawn.tile),
                    path=[tile_center(spawn.tile)],
                    sprint_ticks_remaining=rules.sprint_duration_ticks,
                )
                for spawn in sorted(spawns, key=lambda value: value.actor_id)
            }
        )
        if prop_state is not None:
            self._world.environment = prop_state
        if mission is not None and environment is not None:
            anchors = {
                mission_object(world_map, object_id).tile
                for object_id in (mission.core_object_id, mission.exit_object_id)
            }
            if any(tile in anchors for prop in environment.props for tile in prop.tiles):
                raise ValueError("A prop may not cover the Core or Exit anchor")
        if mission is not None:
            actor = self._world.actors.get(mission.operative_id)
            if actor is None or actor.kind not in (ActorKind.OPERATIVE, ActorKind.COMPANION):
                raise ValueError("Mission operative must identify an intruder actor")
            if intruder_start is not None:
                # Experiment start (P07): reduced stock or an already-stolen Core.
                actor.inventory = intruder_start.inventory()
                if intruder_start.core_held:
                    self._world.core_owner = actor.actor_id
                    self._world.phase = MissionPhase.LOCKDOWN
            if mission.mode not in ("HUMAN", "COMPANION"):
                raise ValueError("Unsupported mission mode")
            core = mission_object(world_map, mission.core_object_id)
            exit_object = mission_object(world_map, mission.exit_object_id)
            if (
                core.kind.lower() != "core"
                or exit_object.kind.lower() != "exit"
                or core.tile == exit_object.tile
            ):
                raise ValueError("Mission needs distinct Core and Exit anchors")
            if not world_map.can_walk(exit_object.tile):
                raise ValueError("Extraction marker must be walkable")
        if security is not None:
            for patrol in security.patrols:
                guard = self._world.actors.get(patrol.actor_id)
                if guard is None or guard.kind not in ROLE_KINDS[patrol.role]:
                    raise ValueError(f"Guard {patrol.actor_id!r} cannot take role {patrol.role}")
                if any(
                    not body_fits(world_map, tile_center(tile), rules.actor_radius_units)
                    for tile in patrol.points
                ):
                    raise ValueError("Every patrol waypoint must fit on a walkable tile")
                if any(
                    not bfs(world_map, first, second).path
                    for first, second in zip(
                        patrol.points, (*patrol.points[1:], patrol.points[0]), strict=True
                    )
                ):
                    raise ValueError("Patrol waypoints must be connected")
                next_point = next(
                    (tile for tile in patrol.points if tile != guard.tile), patrol.points[0]
                )
                guard.facing = (
                    1
                    if next_point[0] > guard.tile[0]
                    else -1
                    if next_point[0] < guard.tile[0]
                    else 0,
                    1
                    if next_point[1] > guard.tile[1]
                    else -1
                    if next_point[1] < guard.tile[1]
                    else 0,
                )
                self._world.guard_memories[patrol.actor_id] = GuardMemory()
            if security.director is not None:
                self._world.nexus = initial_memory(security.director)
            guard_security.refresh(self._world, world_map, security, ())

    @property
    def tick(self) -> int:
        return self._world.tick

    @property
    def ticks_per_second(self) -> int:
        return self._rules.simulation_hz

    def observe(self, actor_id: str) -> Observation:
        return views.observe(self._world, self._map, self._rules, self._mission, actor_id)

    @property
    def geometry_revision(self) -> int:
        return self._world.geometry_revision

    def request_geometry_revision(self, world_map: StaticMap, reason: str) -> None:
        """Queue a validated static-geometry change for the start of the next tick.

        This is the adapter later door/glass lifecycles use. It keeps stairs and
        map identity, never moves an actor and refuses a map in which any actor's
        current physical body would no longer fit.
        """
        current = self._base_map
        if (
            world_map.map_id != current.map_id
            or (world_map.width, world_map.height) != (current.width, current.height)
            or world_map.stairs != current.stairs
            or not reason
        ):
            raise ValueError("A geometry revision must keep map identity, size and stairs")
        physical = props.effective_map(world_map, self._world.environment)
        if any(
            not body_fits(
                physical, actor.position, self._rules.actor_radius_units, crouched=actor.crouched
            )
            for actor in self._world.actors.values()
        ):
            raise ValueError("A geometry revision cannot enclose an actor's body")
        self._base_map = world_map
        self._pending_geometry = (physical, reason)

    def nexus_status(self) -> NexusStatus | None:
        """Privileged NEXUS display/persistence data; never given to a controller."""
        if self._security is None or self._security.director is None:
            return None
        memory = self._world.nexus
        return NexusStatus(
            memory.evaluated_tick,
            memory.dispatches,
            memory.announcement,
            memory.announcement_tick,
            memory.evidence,
            self._security.director.protocol,
        )

    def intercept_plans(self) -> tuple[tuple[str, InterceptPlan], ...]:
        """Each Interceptor's last actual search (privileged display/QA data)."""
        return tuple(
            (guard_id, memory.intercept)
            for guard_id, memory in sorted(self._world.guard_memories.items())
            if memory.intercept is not None
        )

    def presentation_snapshot(self) -> PresentationSnapshot:
        return views.presentation(self._world, self._map, self._rules, self._security)

    def _cue_visible(self, position: Position, actor_id: str) -> bool:
        """Whether the mission intruder actually saw a prop cue (own cues always)."""
        observer_id = self._mission.operative_id if self._mission else None
        if observer_id is None or actor_id == observer_id:
            return True
        observer = self._world.actors[observer_id]
        reach = (self._security.rules.sight_range_tiles if self._security else 8) * UNIT
        return (observer.position[0] - position[0]) ** 2 + (
            observer.position[1] - position[1]
        ) ** 2 <= reach**2 and line_of_sight(self._map, observer.position, position)

    def step(self, actions: Iterable[Action] = (), *, abort: bool = False) -> StepResult:
        if self._world.mission_end is not None:
            return self._result(())
        geometry_reason: str | None = None
        if not abort and self._pending_geometry is not None:
            self._map, geometry_reason = self._pending_geometry
            self._pending_geometry = None
            self._world.geometry_revision += 1
            if self._security is not None:
                # Decisions must see the new map and its current visibility.
                # Already-heard sounds retain their original provenance.
                guard_security.refresh(self._world, self._map, self._security, None)
        if self._security is not None:
            guard_security.direct(self._world, self._map, self._security)
        choices = (
            guard_security.decisions(
                self._security,
                tuple(self.observe(patrol.actor_id) for patrol in self._security.patrols),
                self._world,
            )
            if self._security is not None
            else ()
        )
        supplied = tuple(actions)
        controlled = self._world.guard_memories
        queued = tuple(
            sorted(
                (
                    *[action for action in supplied if action.actor_id not in controlled],
                    *(decision.action for _, decision in choices),
                ),
                key=lambda action: (action.actor_id, action.kind.value, repr(action)),
            )
        )
        counts = Counter(action.actor_id for action in queued)
        rejected: list[tuple[Action, str]] = [
            (action, "simulation_controlled_actor")
            for action in supplied
            if action.actor_id in controlled
        ]
        accepted: list[Action] = []
        for action in queued:
            reason = self._rejection_reason(action, counts[action.actor_id])
            if reason is not None:
                rejected.append((action, reason))
            else:
                accepted.append(action)
        self._world.tick += 1
        events: list[GameEvent] = []

        def emit(
            kind: EventKind, actor_id: str, details: tuple[tuple[str, Scalar], ...] = ()
        ) -> None:
            events.append(
                GameEvent(
                    f"{self.tick}:{self._world.next_event_id}", self.tick, kind, actor_id, details
                )
            )
            self._world.next_event_id += 1

        t = props.Tick(self._world, self._map, self._rules, emit, self._cue_visible)
        if abort:
            operative = (
                self._mission.operative_id if self._mission else next(iter(self._world.actors))
            )
            end_mission(self._world, operative, RunOutcome.ABORTED, emit)
            self._world.decisive_events.extend(events[-1:])
            return self._result(tuple(events))
        if geometry_reason is not None:
            emit(
                EventKind.GEOMETRY_REVISED,
                "facility",
                (("revision", self._world.geometry_revision), ("reason", geometry_reason)),
            )
        for actor in self._world.actors.values():
            actor.traversed_tiles = (actor.tile,)
        confirmed: list[int] = []
        if self._security is not None:
            guard_security.apply_decisions(self._world, self._security, choices, emit)
            observed_tick = self._world.tick - 1
            confirmed = [
                memory.last_seen_tick
                for memory in self._world.guard_memories.values()
                if memory.state == GuardState.CHASE and memory.last_seen_tick == observed_tick
            ]
        advance_echoes(self._world)
        update_sprint(
            self._world,
            self._rules,
            frozenset(
                action.actor_id
                for action in accepted
                if action.kind == ActionKind.MOVE
                and action.sprint
                and not self._world.actors[action.actor_id].crouched
            ),
        )
        for action, reason in rejected:
            emit(EventKind.ACTION_REJECTED, action.actor_id, (("reason", reason),))
        for action in accepted:
            if action.kind == ActionKind.MOVE:
                cancel_stair(self._world, action.actor_id, emit)
                actor = self._world.actors[action.actor_id]
                if actor.hidden_in is not None:
                    props.leave_locker(t, action.actor_id)  # "exit by E or move"
                sprint = (
                    action.sprint
                    and not actor.crouched
                    and actor.sprint_ready_at == 0
                    and actor.sprint_ticks_remaining > 0
                )
                props.push(t, action.actor_id, action.direction, sprint)
                move_actor(self._world, self._map, self._rules, action, emit)
            elif action.kind == ActionKind.WAIT:
                emit(EventKind.ACTION_ACCEPTED, action.actor_id)
            elif action.kind == ActionKind.CROUCH:
                cancel_stair(self._world, action.actor_id, emit)
                actor = self._world.actors[action.actor_id]
                actor.crouched = not actor.crouched
                emit(
                    EventKind.ACTION_ACCEPTED,
                    action.actor_id,
                    (("posture", "crouched" if actor.crouched else "standing"),),
                )
        # Revalidate interaction/tool reach after ALL movements, before effects.
        # Thus actor-ID ordering cannot make a distant melee hit after a guard moved.
        interactions: list[Action] = []
        for action in accepted:
            if action.kind == ActionKind.INTERACT:
                reason = interaction_reason(
                    self._world, self._map, self._rules, self._mission, action
                )
                if reason is None:
                    hint = interaction_target(
                        self._world, self._map, self._rules, self._mission, action
                    )
                    if hint.kind == "Stair":
                        use_stair(
                            self._world,
                            self._map,
                            self._rules,
                            action.actor_id,
                            hint.target_id,
                            emit,
                        )
                    elif hint.kind == "Core":
                        interactions.append(action)
                    else:
                        reason = props.interact(t, action.actor_id, hint.target_id)
                if reason is not None:
                    emit(EventKind.ACTION_REJECTED, action.actor_id, (("reason", reason),))
            elif action.kind == ActionKind.HIDE:
                spot = self._hide_spot(action)
                reason = (
                    "no_hide_spot"
                    if spot is None
                    else props.enter_locker(
                        t, action.actor_id, self._world.environment.lockers[spot]
                    )
                )
                if reason is not None:
                    emit(EventKind.ACTION_REJECTED, action.actor_id, (("reason", reason),))
            elif action.kind in TOOL_ACTIONS:
                reason = tool_reason(self._world, self._map, self._rules, action)
                if reason is None:
                    cancel_stair(self._world, action.actor_id, emit)
                    use_tool(self._world, self._map, self._rules, action, emit)
                else:
                    emit(EventKind.ACTION_REJECTED, action.actor_id, (("reason", reason),))
        for action in accepted:
            if action.kind == ActionKind.MOVE:
                props.bump(t, action.actor_id)
        props.advance(t)
        if self._world.environment.geometry_reasons:
            reasons = ";".join(self._world.environment.geometry_reasons)
            self._world.environment.geometry_reasons.clear()
            # Applied at the start of the next tick, like every geometry change.
            self._pending_geometry = (
                props.effective_map(self._base_map, self._world.environment),
                reasons,
            )
        update_theft(self._world, self._rules, self._mission, tuple(interactions), emit)
        advance_stairs(self._world, self._map, self._rules, emit)
        if self._security is not None:
            guard_security.refresh(self._world, self._map, self._security, tuple(events), emit)
        # Tools precede capture; completed contact capture precedes extraction.
        update_captures(
            self._world,
            self._map,
            self._rules,
            self._mission,
            emit,
            guard_security.capture_targets(self._world, self._security) if self._security else None,
        )
        check_extraction(self._world, self._map, self._mission, emit)
        self._score_encounters(events, confirmed)
        remember_paths(self._world, self._rules)
        return self._result(tuple(events))

    def _score_encounters(self, events: list[GameEvent], confirmed: list[int]) -> None:
        """Team detection encounters from actual confirmations and grabs (SCORING.md)."""
        world = self._world
        if self._security is not None:
            grabs = [world.tick for e in events if e.kind == EventKind.CAPTURE_STARTED]
            started = encounters.update(
                world.encounters,
                world.tick,
                [*confirmed, *grabs],
                grab_active=bool(world.captures),
                ttl_ticks=self._security.rules.memory_ticks,
            )
            if started:
                first = next(
                    (
                        e
                        for e in events
                        if e.kind in (EventKind.SIGHTING_CONFIRMED, EventKind.CAPTURE_STARTED)
                    ),
                    None,
                )
                if first is not None:
                    world.decisive_events.append(first)
        world.decisive_events.extend(e for e in events if e.kind in DECISIVE)
        del world.decisive_events[:-24]

    def _result(self, events: tuple[GameEvent, ...]) -> StepResult:
        return StepResult(
            self.tick,
            events,
            tuple(self.observe(actor_id) for actor_id in self._world.actors),
            terminal=self.terminal_result(),
            mission_end=self._world.mission_end,
        )

    def terminal_result(self) -> RunResult | None:
        """The authoritative approved score once the mission has ended."""
        end, mission = self._world.mission_end, self._mission
        if end is None or mission is None:
            return None
        return score_run(
            mode=mission.mode,
            seed=self._seed,
            outcome=end.outcome,
            elapsed_ticks=end.elapsed_ticks,
            detection_encounters=self._world.encounters.count,
            rules=self._scoring,
            decisive_events=tuple(self._world.decisive_events),
        )

    def _rejection_reason(self, action: Action, count: int) -> str | None:
        if action.actor_id not in self._world.actors:
            return "unknown_actor"
        if count != 1:
            return "multiple_intents"
        if action.tick_issued != self.tick:
            return "stale_or_future_tick"
        actor = self._world.actors[action.actor_id]
        if actor.incapacitated(self.tick + 1):
            return "actor_incapacitated"
        if action.target_tile is not None:
            return "unsupported_target_tile"
        if (
            action.kind not in (ActionKind.INTERACT, ActionKind.MELEE, ActionKind.HIDE)
            and action.target_id is not None
        ):
            return "unexpected_target_id"
        if action.kind == ActionKind.MOVE:
            if any(value not in (-1, 0, 1) for value in action.direction) or action.direction == (
                0,
                0,
            ):
                return "invalid_direction"
            if actor.kind in GUARD_KINDS and action.sprint:
                return "guard_cannot_sprint"
            return None
        if action.direction != (0, 0) or action.sprint:
            return "unexpected_movement_payload"
        if action.kind == ActionKind.WAIT:
            return None
        if actor.kind in GUARD_KINDS and (
            action.kind != ActionKind.INTERACT
            or not stair_hints(self._world, self._map, action.actor_id)
        ):
            return "intruder_only_action"
        if action.kind == ActionKind.CROUCH:
            if actor.hidden_in is not None:
                return "hidden"
            if actor.crouched and not body_fits(
                self._map, actor.position, self._rules.actor_radius_units
            ):
                return "low_headroom"
            return None
        if action.kind == ActionKind.HIDE:
            if actor.hidden_in is not None:
                return "already_hidden"
            return None if self._hide_spot(action) is not None else "no_hide_spot"
        if action.kind == ActionKind.INTERACT:
            return interaction_reason(self._world, self._map, self._rules, self._mission, action)
        return tool_reason(self._world, self._map, self._rules, action, at_tick=self.tick + 1)

    def _hide_spot(self, action: Action) -> str | None:
        """The locker a HIDE action enters: the named one or the closest offered."""
        hints = props.hints(self._world, self._map, self._rules, action.actor_id)
        return next(
            (
                hint.target_id
                for _, hint in hints
                if hint.kind == "HideSpot" and action.target_id in (None, hint.target_id)
            ),
            None,
        )

    def fingerprint(self) -> str:
        """Privileged hash includes timers, decoy history, rules and mission spec."""
        payload = {
            "schema_version": 13,
            "seed": self._seed,
            "rules": asdict(self._rules),
            "pending_geometry": {
                "map": _map_payload(self._pending_geometry[0]),
                "reason": self._pending_geometry[1],
            }
            if self._pending_geometry
            else None,
            "mission": asdict(self._mission) if self._mission else None,
            "security": {
                "patrols": [asdict(patrol) for patrol in self._security.patrols],
                "rules": asdict(self._security.rules),
                "sound_blocking_tiles": sorted(self._security.sound_blocking_tiles),
                "graph": asdict(self._security.graph) if self._security.graph else None,
                "director": asdict(self._security.director) if self._security.director else None,
            }
            if self._security
            else None,
            "world": asdict(self._world),
            "map": _map_payload(self._map),
            "base_map": _map_payload(self._base_map),
            "environment": asdict(self._environment) if self._environment else None,
            "scoring": asdict(self._scoring),
            "intruder_start": asdict(self._start) if self._start else None,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        return sha256(canonical.encode()).hexdigest()
