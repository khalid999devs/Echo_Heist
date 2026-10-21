"""Unweighted four-neighbor BFS with an actual path and expansion count."""

from collections import deque
from dataclasses import dataclass

from echo_heist.core.contracts.world import StaticMap, Tile


@dataclass(frozen=True, slots=True)
class PathResult:
    path: tuple[Tile, ...]
    expanded: int


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
            return PathResult(tuple(reversed(reverse)), expanded)
        for tile in world_map.connections(current):
            if world_map.can_walk(tile) and tile not in parent:
                parent[tile] = current
                pending.append(tile)
    return PathResult((), expanded)
