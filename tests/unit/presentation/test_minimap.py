"""Navigation cannot display stale walkability after real geometry replacement."""

from dataclasses import replace

from echo_heist.core.contracts.world import StaticMap
from echo_heist.ui.render.layout.minimap import MinimapLayer


def test_cached_floor_is_reused_but_invalidated_when_actual_map_changes() -> None:
    layer = MinimapLayer()
    world_map = StaticMap("fixture", 4, 4)
    bounds = (0, 0, 4, 4)
    original = layer.base(world_map, bounds)
    assert layer.base(world_map, bounds) is original
    assert original.get_at((1, 1)).a > 0
    changed = replace(world_map, blocked_tiles=frozenset({(0, 0)}))
    refreshed = layer.base(changed, bounds)
    assert refreshed is not original and refreshed.get_at((1, 1)).a == 0
    assert len(layer.layers) == 1
