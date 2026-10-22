"""Shared guard helpers: reading one filtered Observation and steering legally.

Extracted from the original Sentinel so the Tracker follows identical physical,
stair and identification rules. Nothing here reads Simulation state.
"""

from collections.abc import Callable
from dataclasses import dataclass, replace

from echo_heist.ai.guards.fuzzy import investigate_urgency
from echo_heist.ai.navigation.grid import PathResult, neighbors
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.observations import EntityView, Observation
from echo_heist.core.contracts.security.model import (
    GuardDecision,
    GuardMemory,
    GuardState,
    SensorRules,
)
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import (
    ActorKind,
    MissionPhase,
    Position,
    StaticMap,
    Tile,
    tile_center,
)

type Planner = Callable[[StaticMap, Tile, Tile], PathResult]

INTRUDERS = (ActorKind.OPERATIVE, ActorKind.COMPANION)
SALIENCE = {"CROUCH": 0.15, "FOOTSTEP": 0.25, "SPRINT": 0.75, "EMP": 1.0, "MELEE": 1.0}
MOTION = "UNIDENTIFIED_MOTION"
HIDE_ENTRY = "HIDE_ENTRY"


def distance(first: Tile, second: Tile) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def sign(value: int) -> int:
    return (value > 0) - (value < 0)


def arrived(position: Position, tile: Tile | None) -> bool:
    return (
        tile is not None
        and max(abs(a - b) for a, b in zip(position, tile_center(tile), strict=True)) <= UNIT // 10
    )


def phase_rules(observation: Observation, rules: SensorRules) -> SensorRules:
    """Lockdown shortens patrol pauses and lengthens searches; sensing is unchanged."""
    if observation.phase != MissionPhase.LOCKDOWN:
        return rules
    return replace(
        rules,
        patrol_pause_ticks=max(1, rules.patrol_pause_ticks // 2),
        search_ticks=rules.search_ticks * 130 // 100,
    )


def visible_intruder(observation: Observation) -> EntityView | None:
    return next(
        (entity for entity in observation.visible_entities if entity.kind in INTRUDERS), None
    )


def identify(
    observation: Observation, rules: SensorRules, memory: GuardMemory, intruder: EntityView
) -> GuardMemory:
    """Advance the visual identification meter from an actual current sighting."""
    own = observation.own_status
    near = distance(own.tile, intruder.tile) <= 1
    threshold = rules.near_identification_ticks if near else rules.identification_ticks
    identity = min(rules.identification_ticks, memory.identity_ticks + 1)
    remembered = (
        memory.state == GuardState.CHASE
        and observation.tick - memory.last_seen_tick <= rules.memory_ticks
    )
    confirmed = remembered or identity >= threshold
    heading = memory.last_seen_heading
    if memory.last_seen_tile is not None and memory.last_seen_tile != intruder.tile:
        heading = (
            sign(intruder.tile[0] - memory.last_seen_tile[0]),
            sign(intruder.tile[1] - memory.last_seen_tile[1]),
        )
    return replace(
        memory,
        state=GuardState.CHASE if confirmed else GuardState.SPOTTED,
        identity_ticks=rules.identification_ticks if confirmed else identity,
        last_seen_tile=intruder.tile,
        last_seen_tick=observation.tick,
        last_seen_heading=heading,
        target=intruder.tile,
        wait_until=0,
        evidence_kind="SIGHT",
        evidence_id=f"sight:{observation.agent_id}:{observation.tick}",
        evidence_tick=observation.tick,
    )


@dataclass(frozen=True, slots=True)
class Cue:
    """A heard origin or unidentified motion: a place to check, never an identity."""

    tile: Tile
    salience: float
    visibility: float
    kind: str
    cue_id: str
    tick: int


def strongest_cue(observation: Observation) -> Cue | None:
    if observation.heard_events:
        heard = max(observation.heard_events, key=lambda cue: (cue.tick, cue.event_id))
        return Cue(
            heard.tile, SALIENCE.get(heard.kind, 0.5), 0.0, "NOISE", heard.event_id, heard.tick
        )
    motion = [cue for cue in observation.visual_cues if cue.kind == MOTION]
    if motion:
        seen = motion[-1]
        return Cue(seen.tile, 0.0, 0.5, "MOTION", seen.cue_id, seen.tick)
    return None


def investigate(observation: Observation, rules: SensorRules, memory: GuardMemory) -> GuardMemory:
    """Turn the strongest cue into a fuzzy-graded investigation with provenance."""
    cue = strongest_cue(observation)
    if cue is None:
        return memory
    fuzzy = investigate_urgency(
        distance(observation.own_status.tile, cue.tile), cue.salience, cue.visibility
    )
    return replace(
        memory,
        state=GuardState.INVESTIGATE,
        target=cue.tile,
        urgency=fuzzy.urgency,
        search_until=observation.tick + rules.search_ticks,
        evidence_kind=cue.kind,
        evidence_id=cue.cue_id,
        evidence_tick=cue.tick,
    )


def witnessed_hide(observation: Observation, memory: GuardMemory) -> Tile | None:
    """Cover this guard saw the intruder enter after its latest direct sighting."""
    cues = [
        cue
        for cue in observation.visual_cues
        if cue.kind == HIDE_ENTRY and cue.tick >= memory.last_seen_tick
    ]
    return max(cues, key=lambda cue: (cue.tick, cue.cue_id)).tile if cues else None


def evidence_expired(observation: Observation, rules: SensorRules, memory: GuardMemory) -> bool:
    return (
        memory.evidence_tick >= 0 and observation.tick - memory.evidence_tick > rules.memory_ticks
    )


def steer(
    observation: Observation,
    memory: GuardMemory,
    target: Tile | None,
    plan: Planner,
    intruder: EntityView | None,
) -> GuardDecision:
    """Plan to ``target`` with ``plan`` and emit one legal MOVE/INTERACT/WAIT."""
    own = observation.own_status
    world_map = observation.map_static
    position = own.position or tile_center(own.tile)
    wait = Action(observation.agent_id, ActionKind.WAIT, observation.tick)
    if target is not None and not world_map.can_walk(target):
        # A cue can originate beneath a desk. Investigate a reachable edge of
        # that physical cover; never walk through it or infer identity.
        approaches = [
            result.path
            for tile in neighbors(target)
            if world_map.can_walk(tile) and (result := plan(world_map, own.tile, tile)).path
        ]
        if approaches:
            target = min(approaches, key=lambda path: (len(path), path[-1]))[-1]
    memory = replace(memory, target=target)
    if target is None:
        return GuardDecision(wait, memory, own.facing)
    path = memory.path
    stale = memory.path_revision != observation.geometry_revision
    if stale or target != memory.path_goal or (not path and not arrived(position, target)):
        result = plan(world_map, own.tile, target)
        path = result.path[1:]
        memory = replace(
            memory,
            expanded_nodes=result.expanded,
            path_goal=target,
            path_cost=result.cost,
            path_revision=observation.geometry_revision,
        )
        if not result.path:
            return GuardDecision(wait, replace(memory, path=()), own.facing)
    while path:
        point = tile_center(path[0])
        if max(abs(point[0] - position[0]), abs(point[1] - position[1])) > UNIT // 10:
            break
        path = path[1:]
    memory = replace(memory, path=path)
    stair = next(
        (
            link
            for link in world_map.stairs
            if link.tile == own.tile and path and link.destination == path[0]
        ),
        None,
    )
    if stair is not None:
        return GuardDecision(
            Action(
                observation.agent_id,
                ActionKind.INTERACT,
                observation.tick,
                target_id=stair.object_id,
            ),
            memory,
            own.facing,
        )
    point = tile_center(path[0] if path else target)
    dx, dy = point[0] - position[0], point[1] - position[1]
    direction = (
        (sign(dx), 0) if abs(dx) > UNIT // 10 else (0, sign(dy)) if abs(dy) > UNIT // 10 else (0, 0)
    )
    facing = direction if direction != (0, 0) else own.facing
    if memory.state == GuardState.SPOTTED and intruder is not None:
        look = intruder.position or tile_center(intruder.tile)
        facing = (sign(look[0] - position[0]), sign(look[1] - position[1]))
        facing = facing if facing != (0, 0) else own.facing
    if (
        observation.tick < memory.wait_until
        or memory.state == GuardState.SPOTTED
        or arrived(position, target)
    ):
        return GuardDecision(wait, memory, facing)
    return GuardDecision(
        Action(observation.agent_id, ActionKind.MOVE, observation.tick, direction), memory, facing
    )
