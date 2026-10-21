"""Visible cones clipped by the same opaque geometry as Simulation's sight test."""

from functools import lru_cache
from math import atan2, cos, radians, sin

import pygame

from echo_heist.core.contracts.results import PresentationSnapshot
from echo_heist.core.contracts.security.model import GuardState
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import Position, StaticMap, Tile
from echo_heist.core.perception.sensors import sight_ray
from echo_heist.ui.render import theme
from echo_heist.ui.render.actors.model import DEFENDER_SIZE
from echo_heist.ui.render.camera import Camera


@lru_cache(maxsize=64)
def _fan(
    world_map: StaticMap, start: Position, facing: Tile, radius: int, half_angle: int
) -> tuple[Position, ...]:
    heading = atan2(facing[1], facing[0])
    points = [start]
    for ray in range(41):
        angle = heading + radians(-half_angle + 2 * half_angle * ray / 40)
        dx, dy = cos(angle), sin(angle)
        end = round(start[0] + dx * radius * UNIT), round(start[1] + dy * radius * UNIT)
        points.append(sight_ray(world_map, start, end)[1])
    return tuple(points)


def draw_vision(
    canvas: pygame.Surface, world_map: StaticMap, snapshot: PresentationSnapshot, camera: Camera
) -> None:
    actors = {actor.actor_id: actor for actor in snapshot.actors}
    layer = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
    size = world_map.tile_size_px
    for view in snapshot.guards:
        actor = actors[view.actor_id]
        if actor.position is None or actor.disabled or actor.stunned:
            continue
        color = theme.DANGER if view.state == GuardState.CHASE else theme.WARNING
        points = [
            camera.to_screen((p[0] * size / UNIT, p[1] * size / UNIT))
            for p in _fan(
                world_map,
                actor.position,
                view.facing,
                view.sight_range_tiles,
                view.half_angle_degrees,
            )
        ]
        pygame.draw.polygon(layer, (*color, 28), points)
        pygame.draw.lines(layer, (*color, 60), False, points[1:], 1)
        for edge in (points[1], points[-1]):
            pygame.draw.line(layer, (*color, 100), points[0], edge, 1)
        if view.identification_ticks:
            x, y = points[0]
            top = y - DEFENDER_SIZE[1] - 8
            pygame.draw.rect(layer, (5, 13, 20, 230), (x - 21, top, 42, 6), border_radius=2)
            width = round(
                40 * min(1, view.identification_ticks / view.identification_required_ticks)
            )
            pygame.draw.rect(layer, (*color, 255), (x - 20, top + 1, width, 4), border_radius=2)
    canvas.blit(layer, (0, 0))
