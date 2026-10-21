"""Authoritative fixed-step gameplay; pure values in, committed events out."""

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict
from hashlib import sha256

from echo_heist.ai.navigation.grid import bfs
from echo_heist.core.abilities.tools import advance_echoes, tool_reason, use_tool
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind, GameEvent
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.results import (
    MissionSpec,
    PresentationSnapshot,
    RunOutcome,
    StepResult,
)
from echo_heist.core.contracts.security.model import GuardMemory, SecuritySpec
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, Scalar, StaticMap, tile_center
from echo_heist.core.simulation import views
from echo_heist.core.simulation.systems import security as guard_security
from echo_heist.core.simulation.systems.capture import update_captures
from echo_heist.core.simulation.systems.mission import (
    check_extraction,
    end_mission,
    interaction_reason,
    mission_object,
    update_theft,
)
from echo_heist.core.simulation.systems.motion import body_fits, move_actor, remember_paths
from echo_heist.core.simulation.systems.traversal import stair_hints, update_sprint, use_stair
from echo_heist.core.simulation.world import GUARD_KINDS, ActorState, WorldState

TOOL_ACTIONS = frozenset({ActionKind.ECHO, ActionKind.EMP, ActionKind.MELEE})


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
    ) -> None:
        if not spawns:
            raise ValueError("At least one actor is required")
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
        if mission is not None:
            actor = self._world.actors.get(mission.operative_id)
            if actor is None or actor.kind not in (ActorKind.OPERATIVE, ActorKind.COMPANION):
                raise ValueError("Mission operative must identify an intruder actor")
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
                if guard is None or guard.kind != ActorKind.SENTINEL:
                    raise ValueError("The active Sentinel slice requires a Sentinel actor")
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
            guard_security.refresh(self._world, world_map, security, ())

    @property
    def tick(self) -> int:
        return self._world.tick

    @property
    def ticks_per_second(self) -> int:
        return self._rules.simulation_hz

    def observe(self, actor_id: str) -> Observation:
        return views.observe(self._world, self._map, self._rules, self._mission, actor_id)

    def presentation_snapshot(self) -> PresentationSnapshot:
        return views.presentation(self._world, self._map, self._rules, self._security)

    def step(self, actions: Iterable[Action] = (), *, abort: bool = False) -> StepResult:
        if self._world.mission_end is not None:
            return self._result(())
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

        if abort:
            operative = (
                self._mission.operative_id if self._mission else next(iter(self._world.actors))
            )
            end_mission(self._world, operative, RunOutcome.ABORTED, emit)
            return self._result(tuple(events))
        for actor in self._world.actors.values():
            actor.traversed_tiles = (actor.tile,)
        if self._security is not None:
            guard_security.apply_decisions(self._world, self._security, choices, emit)
        advance_echoes(self._world)
        update_sprint(
            self._world,
            self._rules,
            frozenset(
                action.actor_id
                for action in accepted
                if action.kind == ActionKind.MOVE and action.sprint
            ),
        )
        for action, reason in rejected:
            emit(EventKind.ACTION_REJECTED, action.actor_id, (("reason", reason),))
        for action in accepted:
            if action.kind == ActionKind.MOVE:
                move_actor(self._world, self._map, self._rules, action, emit)
            elif action.kind == ActionKind.WAIT:
                emit(EventKind.ACTION_ACCEPTED, action.actor_id)
        # Revalidate interaction/tool reach after ALL movements, before effects.
        # Thus actor-ID ordering cannot make a distant melee hit after a guard moved.
        interactions: list[Action] = []
        for action in accepted:
            if action.kind == ActionKind.INTERACT:
                reason = interaction_reason(
                    self._world, self._map, self._rules, self._mission, action
                )
                if reason is None:
                    stairs = stair_hints(self._world, self._map, action.actor_id)
                    if stairs and (
                        action.target_id is None or action.target_id == stairs[0].target_id
                    ):
                        use_stair(
                            self._world,
                            self._map,
                            self._rules,
                            action.actor_id,
                            stairs[0].target_id,
                            emit,
                        )
                    else:
                        interactions.append(action)
                else:
                    emit(EventKind.ACTION_REJECTED, action.actor_id, (("reason", reason),))
            elif action.kind in TOOL_ACTIONS:
                reason = tool_reason(self._world, self._map, self._rules, action)
                if reason is None:
                    use_tool(self._world, self._map, self._rules, action, emit)
                else:
                    emit(EventKind.ACTION_REJECTED, action.actor_id, (("reason", reason),))
        update_theft(self._world, self._rules, self._mission, tuple(interactions), emit)
        if self._security is not None:
            guard_security.refresh(self._world, self._map, self._security, tuple(events))
        # Tools precede capture; completed contact capture precedes extraction.
        update_captures(
            self._world,
            self._map,
            self._rules,
            self._mission,
            emit,
            guard_security.capture_eligible(self._world) if self._security else None,
        )
        check_extraction(self._world, self._map, self._mission, emit)
        remember_paths(self._world, self._rules)
        return self._result(tuple(events))

    def _result(self, events: tuple[GameEvent, ...]) -> StepResult:
        return StepResult(
            self.tick,
            events,
            tuple(self.observe(actor_id) for actor_id in self._world.actors),
            mission_end=self._world.mission_end,
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
            action.kind not in (ActionKind.INTERACT, ActionKind.MELEE)
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
        if action.kind == ActionKind.HIDE:
            return "environment_system_not_connected"
        if action.kind == ActionKind.INTERACT:
            return interaction_reason(self._world, self._map, self._rules, self._mission, action)
        return tool_reason(self._world, self._map, self._rules, action)

    def fingerprint(self) -> str:
        """Privileged hash includes timers, decoy history, rules and mission spec."""
        payload = {
            "schema_version": 4,
            "seed": self._seed,
            "rules": asdict(self._rules),
            "mission": asdict(self._mission) if self._mission else None,
            "security": {
                "patrols": [asdict(patrol) for patrol in self._security.patrols],
                "rules": asdict(self._security.rules),
                "sound_blocking_tiles": sorted(self._security.sound_blocking_tiles),
            }
            if self._security
            else None,
            "world": asdict(self._world),
            "map": {
                "id": self._map.map_id,
                "width": self._map.width,
                "height": self._map.height,
                "tile_size_px": self._map.tile_size_px,
                "blocked": sorted(self._map.blocked_tiles),
                "opaque": sorted(self._map.opaque_tiles),
                "objects": [asdict(obj) for obj in self._map.objects],
                "stairs": [asdict(link) for link in self._map.stairs],
            },
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        return sha256(canonical.encode()).hexdigest()
