from echo_heist.ai.navigation.grid import bfs
from echo_heist.core.contracts.world import StaticMap


def test_bfs_shortest_valid_detour_and_unreachable_goal() -> None:
    blocked = frozenset((2, y) for y in range(4))
    world = StaticMap("detour", 5, 5, blocked, blocked)
    result = bfs(world, (0, 0), (4, 0))
    assert len(result.path) == 13 and result.expanded > 0
    assert result.path[0] == (0, 0) and result.path[-1] == (4, 0)
    assert all(world.can_walk(tile) for tile in result.path)
    assert all(
        abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
        for a, b in zip(result.path, result.path[1:], strict=False)
    )
    assert not bfs(world, (0, 0), (2, 1)).path
