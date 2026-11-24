"""Shared guard helpers: reading one filtered Observation and steering legally.

Extracted from the original Sentinel so the Tracker follows identical physical,
stair and identification rules. Nothing here reads Simulation state.
"""

from collections.abc import Callable
from dataclasses import dataclass, replace
from math import isqrt

from echo_heist.ai.guards.fuzzy import investigate_urgency
from echo_heist.ai.navigation.grid import PathResult, neighbors, unsnag
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.events import SecurityReport
from echo_heist.core.contracts.observations import EntityView, Observation
from echo_heist.core.contracts.security.model import (
    FuzzyTrace,
    GuardDecision,
    GuardMemory,
    GuardState,
    SensorRules,
    VisualCue,
)
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import (
    ActorKind,
    MissionPhase,
    Position,
    StaticMap,
    Tile,
    position_tile,
    tile_center,
)

type Planner = Callable[[StaticMap, Tile, Tile], PathResult]

INTRUDERS = (ActorKind.OPERATIVE, ActorKind.COMPANION)
GLANCE_TICKS = 30  # keep looking toward a shape lost from sight for one second
SPOT_GRACE_TICKS = 10  # keep staring at a half-seen shape before going to check
SALIENCE = {
    "CROUCH": 0.15,
    "FOOTSTEP": 0.25,
    "DOOR": 0.4,
    "SPRINT": 0.75,
    "METAL": 0.85,
    "EMP": 1.0,
    "MELEE": 1.0,
    "GLASS": 1.0,
}
MOTION = "UNIDENTIFIED_MOTION"
HIDE_ENTRY = "HIDE_ENTRY"
DISPATCH = "DISPATCH"
VERIFY_ECHO_TILES = 4
SHOULDER_UNITS = UNIT // 5  # half a body's width, as the motion rules size it
PAUSE_SPREAD = 2


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
    """Lockdown shortens patrol pauses; searches and sensing are unchanged, so a
    guard that loses the thief after the alarm gives up as soon as it would before."""
    if observation.phase != MissionPhase.LOCKDOWN:
        return rules
    return replace(rules, patrol_pause_ticks=max(1, rules.patrol_pause_ticks // 2))


def patrol_pause(rules: SensorRules, memory: GuardMemory, tick: int) -> int:
    """How long a guard lingers at the patrol corner it just reached.

    Each guard has its own rhythm drawn from the mission seed, so different
    seeds walk the same routes at different times while one seed always
    replays identically. A pause lasts one to three times the configured one.
    """
    base = rules.patrol_pause_ticks
    if not memory.cadence:
        return base
    mixed = (memory.cadence * 0x9E3779B1 + tick * 0x85EBCA77 + memory.patrol_index) & 0xFFFFFFFF
    mixed ^= mixed >> 15
    return base + mixed % (base * PAUSE_SPREAD + 1)


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
        evidence_tile=intruder.tile,
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


def strongest_cue(observation: Observation, verify_within: int | None = None) -> Cue | None:
    """Newest heard origin, else unidentified motion.

    Under NEXUS VERIFY_ECHO a guard only walks to motion it can verify nearby
    (``verify_within`` tiles); heard sounds and real sightings are unaffected.
    """
    if observation.heard_events:
        heard = max(observation.heard_events, key=lambda cue: (cue.tick, cue.event_id))
        return Cue(
            heard.tile, SALIENCE.get(heard.kind, 0.5), 0.0, "NOISE", heard.event_id, heard.tick
        )
    motion = [
        cue
        for cue in observation.visual_cues
        if cue.kind == MOTION
        and (
            verify_within is None
            or distance(observation.own_status.tile, cue.tile) <= verify_within
        )
    ]
    if motion:
        seen = motion[-1]
        return Cue(seen.tile, 0.0, 0.5, "MOTION", seen.cue_id, seen.tick)
    return None


def investigate(
    observation: Observation,
    rules: SensorRules,
    memory: GuardMemory,
    verify_within: int | None = None,
) -> GuardMemory:
    """Turn the strongest cue into a fuzzy-graded investigation with provenance."""
    cue = strongest_cue(observation, verify_within)
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
        evidence_tile=cue.tile,
        fuzzy_trace=FuzzyTrace(
            observation.tick,
            cue.tick,
            cue.tile,
            distance(observation.own_status.tile, cue.tile),
            cue.salience,
            cue.visibility,
            fuzzy.memberships,
            fuzzy.activations,
            fuzzy.outputs,
            fuzzy.urgency,
        ),
    )


def dispatch_for(observation: Observation, memory: GuardMemory) -> SecurityReport | None:
    """Newest live NEXUS DISPATCH addressed to this guard, newer than its evidence.

    A dispatch keeps the original evidence tick of what another guard sensed
    (or the public Core alarm); it is a place to go, never an identity.
    """
    orders = [
        report
        for report in observation.shared_reports
        if report.report_kind == DISPATCH
        and report.recipient == observation.agent_id
        and observation.tick <= report.expires_at_tick
        and (report.tick, report.event_id) > (memory.evidence_tick, memory.evidence_id)
        and report.tick >= memory.last_seen_tick
    ]
    return max(orders, key=lambda report: (report.tick, report.event_id)) if orders else None


def follow_dispatch(observation: Observation, memory: GuardMemory) -> GuardMemory:
    order = dispatch_for(observation, memory)
    if order is None:
        return memory
    return replace(
        memory,
        state=GuardState.INVESTIGATE,
        target=order.tile,
        urgency=order.confidence,
        search_tiles=(),
        evidence_kind="REPORT",
        evidence_id=order.event_id,
        evidence_tick=order.tick,
        evidence_tile=order.tile,
    )


def witnessed_hide(observation: Observation, memory: GuardMemory) -> VisualCue | None:
    """Cover this guard saw the intruder enter after its latest direct sighting."""
    cues = [
        cue
        for cue in observation.visual_cues
        if cue.kind == HIDE_ENTRY and cue.tick >= memory.last_seen_tick
    ]
    return max(cues, key=lambda cue: (cue.tick, cue.cue_id)) if cues else None


def glancing(observation: Observation, memory: GuardMemory) -> bool:
    """Was the quarry seen within the last moment?"""
    return memory.last_seen_tick >= 0 and observation.tick - memory.last_seen_tick <= GLANCE_TICKS


def spot_lapsed(observation: Observation, memory: GuardMemory) -> bool:
    """Has a half-seen shape been out of sight long enough to go and check it?

    Dropping to a check on the first unseen tick made a guard at the edge of its
    range flick between identifying and checking on every tick."""
    return (
        memory.state == GuardState.SPOTTED
        and observation.tick - memory.last_seen_tick > SPOT_GRACE_TICKS
    )


def evidence_expired(observation: Observation, rules: SensorRules, memory: GuardMemory) -> bool:
    return (
        memory.evidence_tick >= 0 and observation.tick - memory.evidence_tick > rules.memory_ticks
    )


def open_line(world_map: StaticMap, start: Position, end: Position) -> bool:
    """Is the straight walk from ``start`` to ``end`` clear of walls and furniture?

    Both shoulders must pass, not just the centre line. A line that only the
    centre clears made a chaser beside a desk corner alternate every tick
    between running at its quarry and stepping back onto its path.
    """
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = max(1, isqrt(dx * dx + dy * dy))
    side = (-dy * SHOULDER_UNITS // length, dx * SHOULDER_UNITS // length)
    steps = max(1, max(abs(dx), abs(dy)) * 8 // UNIT)
    for offset in ((0, 0), side, (-side[0], -side[1])):
        for index in range(steps + 1):
            point = (
                start[0] + offset[0] + dx * index // steps,
                start[1] + offset[1] + dy * index // steps,
            )
            if world_map.point_blocked(point) or not world_map.can_walk(position_tile(point)):
                return False
    return True


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
    cover = {item.tile for item in world_map.objects if item.kind == "HideSpot"}
    if target is not None and (not world_map.can_walk(target) or target in cover):
        # A cue or last sighting can lie beneath a desk or inside a locker.
        # Investigate a reachable edge of that cover; never push into it.
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
    # Running a quarry down directly can leave the plan behind: a path that no
    # longer starts beside the guard would pull it back to where it came from.
    drifted = (
        bool(path)
        and distance(own.tile, path[0]) > 1
        and not any(
            link.tile == own.tile and link.destination == path[0] for link in world_map.stairs
        )
    )
    if (
        stale
        or drifted
        or target != memory.path_goal
        or (not path and not arrived(position, target))
    ):
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
    direction = unsnag(world_map, position, direction, (dx, dy))
    quarry = intruder.position if intruder is not None else None
    if quarry is None and memory.last_seen_tile is not None and glancing(observation, memory):
        quarry = tile_center(memory.last_seen_tile)  # flickering sight keeps one course
    if (
        memory.state == GuardState.CHASE
        and quarry is not None
        and quarry != position
        and open_line(world_map, position, quarry)
    ):
        # A seen quarry in the open is run down directly. Re-centring on tile
        # paths made a chaser shadow a thief moving across its line, or step back
        # each time a thief hopped between two rows, instead of closing in.
        dx, dy = quarry[0] - position[0], quarry[1] - position[1]
        direction = (sign(dx), 0) if abs(dx) >= abs(dy) else (0, sign(dy))
        direction = unsnag(world_map, position, direction, (dx, dy))
    facing = direction if direction != (0, 0) else own.facing
    if memory.state in (GuardState.SPOTTED, GuardState.CHASE) and intruder is not None:
        # Keep a seen quarry in the cone; an axis-aligned step used to turn a
        # chaser away from a diagonal target, so it lost and re-spotted it.
        look = intruder.position or tile_center(intruder.tile)
        facing = (sign(look[0] - position[0]), sign(look[1] - position[1]))
        facing = facing if facing != (0, 0) else own.facing
    elif memory.last_seen_tile is not None and glancing(observation, memory):
        # A shape that just slipped out of sight is still watched. Snapping back
        # to the walking direction made a guard at the edge of its range flick
        # its view between the shape and the path on every tick.
        look = tile_center(memory.last_seen_tile)
        glance = (sign(look[0] - position[0]), sign(look[1] - position[1]))
        facing = glance if glance != (0, 0) else facing
    if (
        observation.tick < memory.wait_until
        or memory.state == GuardState.SPOTTED
        or arrived(position, target)
    ):
        return GuardDecision(wait, memory, facing)
    return GuardDecision(
        Action(observation.agent_id, ActionKind.MOVE, observation.tick, direction), memory, facing
    )
