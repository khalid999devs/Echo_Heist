"""Unweighted four-neighbor BFS with an actual path and expansion count, plus lane steering."""

from collections import deque
from dataclasses import dataclass

from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import Position, StaticMap, Tile


@dataclass(frozen=True, slots=True)
class PathResult:
    path: tuple[Tile, ...]
    expanded: int
    cost: int = 0


def neighbors(tile: Tile) -> tuple[Tile, ...]:
    x, y = tile
    return (x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)


def bfs(world_map: StaticMap, start: Tile, goal: Tile) -> PathResult:
    if not world_map.can_walk(start) or not world_map.can_walk(goal):
        return PathResult((), 0)
    pending = deque([start])
    parent: dict[Tile, Tile | None] = {start: None}
    expanded = 0
    while pending:
        current = pending.popleft()
        expanded += 1
        if current == goal:
            reverse = [goal]
            previous = parent[goal]
            while previous is not None:
                reverse.append(previous)
                previous = parent[previous]
            return PathResult(tuple(reversed(reverse)), expanded, len(reverse) - 1)
        for tile in world_map.connections(current):
            if world_map.can_walk(tile) and tile not in parent:
                parent[tile] = current
                pending.append(tile)
    return PathResult((), expanded)


def distances_from(
    world_map: StaticMap, start: Tile, *, max_steps: int | None = None
) -> dict[Tile, int]:
    """Legal-graph step counts from ``start``, optionally within a step budget."""
    if not world_map.can_walk(start):
        return {}
    found = {start: 0}
    pending = deque([start])
    while pending:
        current = pending.popleft()
        if max_steps is not None and found[current] >= max_steps:
            continue
        for tile in world_map.connections(current):
            if tile not in found and world_map.can_walk(tile):
                found[tile] = found[current] + 1
                pending.append(tile)
    return found


def unsnag(world_map: StaticMap, position: Position, direction: Tile, delta: Tile) -> Tile:
    """Centre on the waypoint's lane before a shoulder clips a wall corner.

    Steering is axis-first, so a body arriving off-centre could press its body
    into the corner of the next tile on every tick and never move again (P08
    stuck guard). When the step leans toward solid ground just ahead, slide
    across toward the lane first; open floor keeps the direct step.
    """
    if direction == (0, 0):
        return direction
    axis = 0 if direction[0] else 1
    other = 1 - axis
    if abs(delta[other]) <= UNIT // 10:
        return direction
    corner = [0, 0]
    corner[axis] = position[axis] + direction[axis] * UNIT // 2
    corner[other] = position[other] - sign(delta[other]) * UNIT // 2
    if not world_map.point_blocked((corner[0], corner[1])):
        return direction
    slide = [0, 0]
    slide[other] = sign(delta[other])
    return slide[0], slide[1]


def sign(value: int) -> int:
    return (value > 0) - (value < 0)
