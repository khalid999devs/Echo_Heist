"""A* optimality against a reference Dijkstra, including stair links and penalties."""

import heapq
import random

import pytest

from echo_heist.ai.navigation.astar import astar, portal_heuristic
from echo_heist.ai.navigation.grid import bfs
from echo_heist.core.contracts.world import StairLink, StaticMap, Tile


def dijkstra(world: StaticMap, start: Tile, penalty: dict[Tile, int]) -> dict[Tile, int]:
    best = {start: 0}
    pending = [(0, start)]
    while pending:
        cost, tile = heapq.heappop(pending)
        if cost > best[tile]:
            continue
        for step in world.connections(tile):
            if world.can_walk(step):
                value = cost + 1 + penalty.get(step, 0)
                if value < best.get(step, value + 1):
                    best[step] = value
                    heapq.heappush(pending, (value, step))
    return best


def two_deck_map(seed: int) -> StaticMap:
    """Two disjoint 'floors' separated by a solid gap, joined only by stairs."""
    rng = random.Random(seed)
    gap = frozenset((x, y) for x in range(8, 12) for y in range(10))
    walls = frozenset(
        (x, y) for x in range(20) for y in range(10) if (x, y) not in gap and rng.random() < 0.18
    )
    stairs = (
        StairLink("a", (7, 2), "b", (12, 2)),
        StairLink("b", (12, 2), "a", (7, 2)),
        StairLink("c", (7, 8), "d", (12, 8)),
        StairLink("d", (12, 8), "c", (7, 8)),
    )
    landings = {(7, 2), (12, 2), (7, 8), (12, 8)}
    blocked = (gap | walls) - landings
    return StaticMap("decks", 20, 10, blocked, blocked, stairs=stairs)


@pytest.mark.parametrize("seed", range(12))
def test_astar_cost_matches_reference_on_two_decks_with_penalties(seed: int) -> None:
    world = two_deck_map(seed)
    rng = random.Random(100 + seed)
    floor = sorted(
        tile for tile in ((x, y) for x in range(20) for y in range(10)) if world.can_walk(tile)
    )
    penalty = {tile: rng.choice((0, 0, 0, 2, 5)) for tile in floor}
    for _ in range(6):
        start, goal = rng.choice(floor), rng.choice(floor)
        reference = dijkstra(world, start, penalty)
        result = astar(world, start, goal, penalty=lambda tile: penalty.get(tile, 0))
        if goal not in reference:
            assert result.path == ()
            continue
        assert result.cost == reference[goal]
        assert result.path[0] == start and result.path[-1] == goal
        # Every step is a legal four-neighbor move or a real stair link.
        assert all(
            b in world.connections(a) for a, b in zip(result.path, result.path[1:], strict=False)
        )
        assert result.cost == sum(1 + penalty.get(tile, 0) for tile in result.path[1:])


@pytest.mark.parametrize("seed", range(6))
def test_stair_heuristic_is_admissible_and_consistent(seed: int) -> None:
    world = two_deck_map(seed)
    floor = [
        tile for tile in ((x, y) for x in range(20) for y in range(10)) if world.can_walk(tile)
    ]
    goal = floor[len(floor) // 2]
    exact = dijkstra(world, goal, {})  # unit graph is symmetric
    estimate = portal_heuristic(world, goal)
    for tile in floor:
        if tile in exact:
            assert estimate(tile) <= exact[tile]
        for step in world.connections(tile):
            if world.can_walk(step):
                assert estimate(tile) <= 1 + estimate(step)


def test_unit_astar_agrees_with_bfs_and_expands_no_more_on_open_floor() -> None:
    world = StaticMap("open", 30, 30)
    for goal in ((29, 29), (15, 2), (0, 28)):
        reference = bfs(world, (0, 0), goal)
        result = astar(world, (0, 0), goal)
        assert result.cost == reference.cost == len(reference.path) - 1
        assert result.expanded <= reference.expanded


def test_no_path_and_negative_penalty_are_rejected() -> None:
    wall = frozenset((5, y) for y in range(10))
    world = StaticMap("split", 10, 10, wall, wall)
    assert astar(world, (1, 1), (8, 8)).path == ()
    with pytest.raises(ValueError):
        astar(StaticMap("open", 5, 5), (0, 0), (4, 4), penalty=lambda tile: -1)
