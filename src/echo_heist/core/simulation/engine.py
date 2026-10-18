"""Fixed-tick foundation: diagnostic tile MOVE/WAIT, not final game physics.

P02 adds continuous motion, mission rules and tools; P03 adds sensing. Until
then other actors are deliberately absent from every controller observation.
"""

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict
from hashlib import sha256

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.events import EventKind, GameEvent
from echo_heist.core.contracts.observations import EntityView, Observation, OwnStatus
from echo_heist.core.contracts.results import PresentationSnapshot, StepResult
from echo_heist.core.contracts.world import SIMULATION_HZ, ActorSpawn, StaticMap
from echo_heist.core.simulation.world import ActorState, WorldState


class Simulation:
    def __init__(
        self,
        world_map: StaticMap,
        spawns: tuple[ActorSpawn, ...],
        *,
        seed: int = 1042,
        ticks_per_second: int = SIMULATION_HZ,
    ) -> None:
        if ticks_per_second <= 0 or not spawns:
            raise ValueError("A positive tick rate and at least one actor are required")
        ids = {spawn.actor_id for spawn in spawns}
        tiles = {spawn.tile for spawn in spawns}
        if len(ids) != len(spawns) or len(tiles) != len(spawns):
            raise ValueError("Actor IDs and starting tiles must be unique")
        if any(not world_map.can_walk(spawn.tile) for spawn in spawns):
            raise ValueError("Actor spawn must be on a walkable map tile")
        self._map = world_map
        self._seed = seed
        self._ticks_per_second = ticks_per_second
        self._world = WorldState(
            actors={
                spawn.actor_id: ActorState(spawn.actor_id, spawn.kind, spawn.tile)
                for spawn in sorted(spawns, key=lambda value: value.actor_id)
            }
        )

    @property
    def tick(self) -> int:
        return self._world.tick

    @property
    def ticks_per_second(self) -> int:
        return self._ticks_per_second

    def observe(self, actor_id: str) -> Observation:
        actor = self._world.actors[actor_id]
        return Observation(
            agent_id=actor.actor_id,
            tick=self.tick,
            map_static=self._map,
            phase=self._world.phase,
            own_status=OwnStatus(actor.tile, actor.inventory),
        )

    def presentation_snapshot(self) -> PresentationSnapshot:
        return PresentationSnapshot(
            tick=self.tick,
            world_map=self._map,
            actors=tuple(
                EntityView(actor.actor_id, actor.kind, actor.tile)
                for actor in self._world.actors.values()
            ),
            phase=self._world.phase,
        )

    def step(self, actions: Iterable[Action] = ()) -> StepResult:
        queued = tuple(actions)
        counts = Counter(action.actor_id for action in queued)
        events: list[GameEvent] = []
        for action in sorted(
            queued, key=lambda value: (value.actor_id, value.kind.value, repr(value))
        ):
            reason = self._rejection_reason(action, counts[action.actor_id])
            if reason:
                events.append(self._event(EventKind.ACTION_REJECTED, action, (("reason", reason),)))
                continue
            if action.kind == ActionKind.MOVE:
                actor = self._world.actors[action.actor_id]
                actor.tile = (
                    actor.tile[0] + action.direction[0],
                    actor.tile[1] + action.direction[1],
                )
                events.append(
                    self._event(
                        EventKind.ACTOR_MOVED,
                        action,
                        (("x", actor.tile[0]), ("y", actor.tile[1])),
                    )
                )
            else:
                events.append(self._event(EventKind.ACTION_ACCEPTED, action))
        self._world.tick += 1
        return StepResult(
            tick=self.tick,
            events=tuple(events),
            observations=tuple(self.observe(actor_id) for actor_id in self._world.actors),
        )

    def _rejection_reason(self, action: Action, count: int) -> str | None:
        if action.actor_id not in self._world.actors:
            return "unknown_actor"
        if count != 1:
            return "multiple_intents"
        if action.tick_issued != self.tick:
            return "stale_or_future_tick"
        if action.kind not in (ActionKind.MOVE, ActionKind.WAIT):
            return "not_available_in_foundation"
        if action.target_id is not None or action.target_tile is not None or action.sprint:
            return "unsupported_foundation_payload"
        if action.kind == ActionKind.WAIT:
            return None if action.direction == (0, 0) else "wait_has_direction"
        if action.direction not in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            return "foundation_requires_cardinal_move"
        actor = self._world.actors[action.actor_id]
        target = actor.tile[0] + action.direction[0], actor.tile[1] + action.direction[1]
        occupied = any(other.tile == target for other in self._world.actors.values())
        if not self._map.can_walk(target) or occupied:
            return "blocked"
        return None

    def _event(
        self,
        kind: EventKind,
        action: Action,
        details: tuple[tuple[str, str | int | float | bool | None], ...] = (),
    ) -> GameEvent:
        event = GameEvent(
            event_id=f"{self.tick + 1}:{self._world.next_event_id}",
            tick=self.tick + 1,
            kind=kind,
            actor_id=action.actor_id,
            details=details,
        )
        self._world.next_event_id += 1
        return event

    def fingerprint(self) -> str:
        """Privileged diagnostic hash; this method is not a controller input."""
        payload = {
            "schema_version": 1,
            "seed": self._seed,
            "tick": self.tick,
            "ticks_per_second": self.ticks_per_second,
            "phase": self._world.phase,
            "event_count": self._world.next_event_id,
            "map": {
                "id": self._map.map_id,
                "width": self._map.width,
                "height": self._map.height,
                "tile_size_px": self._map.tile_size_px,
                "blocked": sorted(self._map.blocked_tiles),
                "opaque": sorted(self._map.opaque_tiles),
                "objects": [asdict(obj) for obj in self._map.objects],
            },
            "actors": [asdict(actor) for actor in self._world.actors.values()],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        return sha256(canonical.encode("utf-8")).hexdigest()
