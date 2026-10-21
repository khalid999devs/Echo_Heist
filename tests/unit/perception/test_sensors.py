from echo_heist.core.contracts.world import StaticMap, tile_center
from echo_heist.core.perception.sensors import can_see, line_of_sight, sound_reaches


def test_cone_range_opaque_wall_and_transparent_partition() -> None:
    glass = StaticMap("glass", 10, 8, frozenset({(4, 3)}))
    start, target = tile_center((3, 3)), tile_center((5, 3))
    assert can_see(glass, start, target, (1, 0), 8, 50)
    assert not can_see(glass, start, target, (-1, 0), 8, 50)
    assert not can_see(glass, start, target, (1, 0), 1, 50)
    solid = StaticMap("wall", 10, 8, glass.blocked_tiles, glass.blocked_tiles)
    assert not line_of_sight(solid, start, target)
    assert not can_see(glass, start, target, (0, 0), 8, 50)


def test_corner_occlusion_and_acoustic_path_budget() -> None:
    blocked = frozenset({(4, 3)})
    world = StaticMap("corner", 10, 8, blocked, blocked)
    assert not line_of_sight(world, tile_center((3, 3)), tile_center((5, 2)))
    assert sound_reaches(world, blocked, (5, 2), (3, 3), 3)
    assert not sound_reaches(world, blocked, (5, 2), (3, 3), 2)
