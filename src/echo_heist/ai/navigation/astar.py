"""Heuristic A* over the same legal four-neighbor/stair graph as BFS.

The plain Manhattan heuristic is admissible on one floor, but a stair link joins
two landings that are several atlas tiles apart for a step cost of one. The
heuristic therefore uses the exact distance in a relaxed graph: free Manhattan
moves plus every stair link at its true cost. That relaxation never exceeds the
real path cost and changes by at most one per legal step, so it is consistent
and A* returns a minimum-cost path.
"""

from collections.abc import Callable
from heapq import heappop, heappush

from echo_heist.ai.navigation.grid import PathResult
from echo_heist.core.contracts.world import StaticMap, Tile

type StepPenalty = Callable[[Tile], int]


def manhattan(first: Tile, second: Tile) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def portal_heuristic(world_map: StaticMap, goal: Tile) -> Callable[[Tile], int]:
    """Admissible, consistent lower bound to ``goal`` that respects stair links."""
    portals = tuple(sorted({link.tile for link in world_map.stairs}))
    links = {link.tile: link.destination for link in world_map.stairs}
    # Dijkstra over the tiny portal graph: distance from each landing to goal.
    best = {portal: manhattan(portal, goal) for portal in portals}
    changed = True
    while changed:
        changed = False
        for portal in portals:
            through = 1 + best[links[portal]]
            via = min(
                (manhattan(portal, other) + best[other] for other in portals if other != portal),
                default=best[portal],
            )
            value = min(best[portal], through, via)
            if value < best[portal]:
                best[portal] = value
                changed = True

    def estimate(tile: Tile) -> int:
        direct = manhattan(tile, goal)
        return min((direct, *(manhattan(tile, portal) + best[portal] for portal in portals)))

    return estimate


def astar(
    world_map: StaticMap,
    start: Tile,
    goal: Tile,
    *,
    penalty: StepPenalty | None = None,
) -> PathResult:
    """Minimum-cost path; each step costs one plus a nonnegative entry penalty."""
    if not world_map.can_walk(start) or not world_map.can_walk(goal):
        return PathResult((), 0)
    heuristic = portal_heuristic(world_map, goal)
    cost: dict[Tile, int] = {start: 0}
    parent: dict[Tile, Tile | None] = {start: None}
    closed: set[Tile] = set()
    # (f, h, insertion order, tile): deterministic ties prefer the goal-nearest node,
    # then the earliest discovered one, independent of hashing.
    pending: list[tuple[int, int, int, Tile]] = [(heuristic(start), heuristic(start), 0, start)]
    order = 1
    expanded = 0
    while pending:
        _, _, _, current = heappop(pending)
        if current in closed:
            continue
        closed.add(current)
        expanded += 1
        if current == goal:
            reverse = [goal]
            previous = parent[goal]
            while previous is not None:
                reverse.append(previous)
                previous = parent[previous]
            return PathResult(tuple(reversed(reverse)), expanded, cost[goal])
        for tile in world_map.connections(current):
            if tile in closed or not world_map.can_walk(tile):
                continue
            extra = penalty(tile) if penalty is not None else 0
            if extra < 0:
                raise ValueError("A* step penalties must be nonnegative")
            candidate = cost[current] + 1 + extra
            if candidate < cost.get(tile, candidate + 1):
                cost[tile] = candidate
                parent[tile] = current
                estimate = heuristic(tile)
                heappush(pending, (candidate + estimate, estimate, order, tile))
                order += 1
    return PathResult((), expanded)
