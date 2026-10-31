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


def test_vision_culls_only_cones_whose_entire_extent_is_outside_the_view(monkeypatch) -> None:
    import pygame

    from echo_heist.core.contracts.security.model import GuardView
    from echo_heist.ui.render.camera import Camera
    from echo_heist.ui.render.surfaces import vision
    from echo_heist.ui.scenes.flow import GameFlow

    pygame.font.init()
    flow = GameFlow((1280, 720))
    flow._start_run()
    snapshot = flow.session.simulation.presentation_snapshot()
    canvas = pygame.Surface((1280, 720), pygame.SRCALPHA)
    calls = []

    def fan(world_map, start, facing, radius, half_angle):
        calls.append(start)
        return (start, (start[0] + 1, start[1] + 1), (start[0] + 2, start[1]))

    monkeypatch.setattr(vision, "_fan", fan)
    camera = Camera(1280, 720, 1000000, 1000000, 900000, 900000)
    vision.draw_vision(canvas, snapshot.world_map, snapshot, camera)
    assert not calls
    # The ordinary guard registry determines which actor to inspect.
    selected: GuardView = snapshot.guards[0]
    guard = next(a for a in snapshot.actors if a.actor_id == selected.actor_id)
    assert guard.position
    camera.x = guard.position[0] * snapshot.world_map.tile_size_px / 30000 - 640
    camera.y = guard.position[1] * snapshot.world_map.tile_size_px / 30000 - 360
    vision.draw_vision(canvas, snapshot.world_map, snapshot, camera)
    assert guard.position in calls
