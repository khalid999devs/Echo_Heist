"""Body obstacles and the lanes recently seen guards occupy or are walking along.

Built only from the Companion's own observations and belief sightings.
"""

from collections.abc import Iterable
from dataclasses import replace

from echo_heist.ai.companion import tactics
from echo_heist.ai.companion.belief import Beliefs
from echo_heist.ai.companion.utility import active_guards
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.security.director import RouteGraph
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import Position, StaticMap, Tile, tile_center
from echo_heist.core.perception.sensors import line_of_sight

KEEP_TILES = 4  # trailing distance behind a seen patrol
PREDICT_TICKS = 90  # how long a lost guard's walking lane stays predicted
GATE_TILES = 3  # a guard this close to the next junction is holding it
CLOSE_TILES = 3  # a guard this near must not be approached while fleeing
REVERSAL_TICKS = 4  # consecutive requests before a full about-turn is taken
RECENT_TICKS = 45  # a guard seen this recently nearby is still treated as there


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)


def bodies(observation: Observation, actor_id: str) -> set[Tile]:
    """Tiles of seen bodies that block motion; a stunned or disabled guard can be stepped past."""
    return {
        entity.tile
        for entity in observation.visible_entities
        if entity.actor_id != actor_id and not (entity.disabled or entity.stunned)
    }


def guard_lanes(observation: Observation, beliefs: Beliefs, hz: int) -> list[Tile]:
    """Where recently seen guards stand or are walking to (own observations only).

    A seen guard's cone may face away, but a patrol turns at every waypoint. A
    guard that just slipped out of view keeps walking the way it faced, so its
    predicted lane counts too. Never reads where unseen guards really are.
    """
    world_map = observation.map_static
    lanes: list[Tile] = []
    for sighting in beliefs.sightings.values():
        age = observation.tick - sighting.tick
        if sighting.incapacitated or age > PREDICT_TICKS:
            continue
        tile = sighting.tile
        lanes.append(tile)
        step = (_sign(sighting.facing[0]), _sign(sighting.facing[1]))
        if sighting.guard_id in beliefs.visible or step == (0, 0):
            continue
        for _ in range(age * 2 // hz + 2):  # patrols walk about two tiles a second
            tile = (tile[0] + step[0], tile[1] + step[1])
            if not world_map.can_walk(tile):
                break
            lanes.append(tile)
    return lanes


def lane_gap(world_map: StaticMap, lanes: list[Tile], tile: Tile) -> int:
    """Closest lane tile with a clear line of sight to ``tile`` (Manhattan tiles)."""
    return min(
        (
            abs(lane[0] - tile[0]) + abs(lane[1] - tile[1])
            for lane in lanes
            if line_of_sight(world_map, tile_center(lane), tile_center(tile))
        ),
        default=KEEP_TILES + 1,
    )


def lane_pressure(
    observation: Observation, beliefs: Beliefs, own: Tile, ahead: Tile, hz: int
) -> tuple[bool, bool]:
    """(the step closes on a guard lane, where it stands is already exposed to one)."""
    world_map = observation.map_static
    lanes = guard_lanes(observation, beliefs, hz)
    here, there = lane_gap(world_map, lanes, own), lane_gap(world_map, lanes, ahead)
    return there <= KEEP_TILES and there < here, here < KEEP_TILES


def gate_guarded(
    observation: Observation, graph: RouteGraph, legs: tuple[tactics.Leg, ...], progress: int
) -> bool:
    """A seen active guard stands on the next junction of the current branch."""
    if not legs or progress >= len(legs[0].route.nodes):
        return False
    gate = graph.node(legs[0].route.nodes[progress]).tile
    return any(
        abs(guard.tile[0] - gate[0]) + abs(guard.tile[1] - gate[1]) <= GATE_TILES
        for guard in active_guards(observation)
    )


def escape_steps(
    observation: Observation, actor_id: str, away: Position, last: Action | None = None
) -> list[Tile]:
    """Open steps that gain distance, least exposed to the seen guards and then farthest first.

    None when cornered: pacing back and forth in a dead end reads as a glitch,
    so the robot stands its ground and the grab reflexes (stun, EMP) answer.
    Among equally exposed steps the current heading is kept: re-ranking by
    distance alone turned a diagonal escape into a right-down flicker every tick.
    """
    keep = last.direction if last is not None and last.kind == ActionKind.MOVE else None
    own = observation.own_status
    # The guard being escaped always counts: when it flickered out of view at a
    # corner, fleeing only the guards still in sight sent the robot round in circles.
    threats = (
        *(guard.position or tile_center(guard.tile) for guard in active_guards(observation)),
        away,
    )
    here = own.position or tile_center(own.tile)
    nearest = min((here[0] - x) ** 2 + (here[1] - y) ** 2 for x, y in threats)
    occupied = bodies(observation, actor_id)
    options = []
    for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        tile = (own.tile[0] + direction[0], own.tile[1] + direction[1])
        if tile in occupied or not observation.map_static.can_walk(tile, crouched=own.crouched):
            continue
        # Judge the step by where it actually leads, not by the next tile's centre:
        # on a tile edge the two centres either side made it flip every tick.
        point = here[0] + direction[0] * UNIT // 2, here[1] + direction[1] * UNIT // 2
        exposed = sum(line_of_sight(observation.map_static, guard, point) for guard in threats)
        distance = min((point[0] - x) ** 2 + (point[1] - y) ** 2 for x, y in threats)
        if distance > nearest:
            options.append((exposed, direction != keep, -distance, direction))
    return [direction for *_, direction in sorted(options)]


def side_lane(observation: Observation, actor_id: str, direction: Tile, turn: int) -> Tile | None:
    """An open parallel lane beside a body the robot is pressed against.

    The preferred side alternates every six blocked ticks."""
    own = observation.own_status
    occupied = bodies(observation, actor_id)
    sides = [(direction[1], direction[0]), (-direction[1], -direction[0])]
    if (turn // 6) % 2:
        sides.reverse()
    for side in sides:
        lane = (own.tile[0] + side[0], own.tile[1] + side[1])
        if observation.map_static.can_walk(lane) and lane not in occupied:
            return side
    return None


def backoff(observation: Observation, actor_id: str, direction: Tile) -> Tile | None:
    """Where to step back to when an active guard stands in the only way on.

    Up to two open tiles straight back the way the robot came; pushing on
    against the guard's body read as walking into a wall."""
    own, occupied = observation.own_status, bodies(observation, actor_id)
    if (own.tile[0] + direction[0], own.tile[1] + direction[1]) not in occupied:
        return None
    back = None
    for step in (1, 2):
        tile = (own.tile[0] - step * direction[0], own.tile[1] - step * direction[1])
        if tile in occupied or not observation.map_static.can_walk(tile, crouched=own.crouched):
            break
        back = tile
    return back


def guard_near(observation: Observation, beliefs: Beliefs, tiles: int = CLOSE_TILES) -> bool:
    """Was an active guard seen within ``tiles`` steps in the last moment?

    Under a desk the robot sees nothing, so judging by this tick's view alone it
    crawled out beside the guard, ducked back and crawled out again."""
    own, tick = observation.own_status.tile, observation.tick
    return any(
        not seen.incapacitated
        and tick - seen.tick <= RECENT_TICKS
        and abs(seen.tile[0] - own[0]) + abs(seen.tile[1] - own[1]) <= tiles
        for seen in beliefs.sightings.values()
    )


def closing_threat(observation: Observation, direction: Tile) -> Position | None:
    """A close seen guard this step would walk toward (fleeing must never close in)."""
    own = observation.own_status.tile
    ahead = (own[0] + direction[0], own[1] + direction[1])
    for guard in active_guards(observation):
        gap = abs(guard.tile[0] - own[0]) + abs(guard.tile[1] - own[1])
        nearer = abs(guard.tile[0] - ahead[0]) + abs(guard.tile[1] - ahead[1]) < gap
        if gap <= CLOSE_TILES and nearer:
            return guard.position or tile_center(guard.tile)
    return None


def safe_crumb(danger: dict[Tile, int], crumbs: Iterable[Tile], *, far: bool) -> Tile | None:
    """A remembered tile some steps back that no observed cone covers."""
    trail = list(crumbs)[: -(14 if far else 6)]
    for tile in reversed(trail):
        if danger.get(tile, 0) == 0:
            return tile
    return trail[0] if trail else None


def away_goal(aim: Tile | None, crumbs: Iterable[Tile], own: Tile, threat: Position) -> Tile | None:
    """A flee goal that does not lie past a close guard.

    A remembered tile beyond the guard sent the robot straight back toward it as
    soon as it slipped out of view, so it paced in front of the guard. The guard
    counts as in the way when it stands within two steps of the straight route."""
    guard = (threat[0] // UNIT, threat[1] // UNIT)

    def gap(a: Tile, b: Tile) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def clear(tile: Tile) -> bool:
        return (
            gap(tile, guard) > gap(own, guard)
            and gap(own, guard) + gap(tile, guard) > gap(own, tile) + 2
        )

    if aim is None or clear(aim):
        return aim
    return next((tile for tile in reversed(list(crumbs)) if clear(tile)), None)


def damp_reversal(
    action: Action, last: Action | None, votes: int, exempt: bool
) -> tuple[Action, int]:
    """Keep the heading unless a full about-turn is requested several ticks running.

    Two competing goals that alternate every tick (flee to a crumb, step away
    from a guard) otherwise read on screen as the robot wiggling in place.
    """
    reversing = (
        last is not None
        and action.kind == last.kind == ActionKind.MOVE
        and action.direction != (0, 0)
        and action.direction == (-last.direction[0], -last.direction[1])
    )
    if not reversing or exempt or votes + 1 >= REVERSAL_TICKS:
        return action, 0
    assert last is not None
    return replace(action, direction=last.direction), votes + 1


def jam_around(jammed: dict[Tile, int], tile: Tile, until: int) -> None:
    """Mark a tile and its four neighbours as costly for path planning until ``until``."""
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        jammed[(tile[0] + dx, tile[1] + dy)] = until
