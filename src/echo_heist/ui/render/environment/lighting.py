"""Cached architectural light and restrained equipment motion; no gameplay effects."""

import pygame

from echo_heist.level.model import Deck, LevelData
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.environment.illumination.model import room_lights
from echo_heist.ui.render.motifs import light_pool


def bake_lighting(surface: pygame.Surface, level: LevelData) -> None:
    size = level.static_map.tile_size_px
    for room in level.rooms:
        rect = pygame.Rect(room.left * size, room.top * size, room.width * size, room.height * size)
        # Room-local buffers avoid two full-facility alpha allocations/blits.
        # This also bounds each C operation while the opening is animating.
        light = pygame.Surface(rect.size, pygame.SRCALPHA)
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        for x in range(room.left, room.left + room.width):
            for y in range(room.top, room.top + room.height):
                if (x, y) in level.floor_tiles:
                    pygame.draw.rect(
                        mask,
                        (255, 255, 255, 255),
                        ((x - room.left) * size, (y - room.top) * size, size, size),
                    )
        for lamp in room_lights(room, size):
            x, y = lamp.position
            light_pool(light, (x - rect.x, y - rect.y), lamp.color, lamp.radius)
            if not lamp.ceiling:
                # Visible fixtures and shadow sources share exactly the same positions.
                horizontal = min(abs(y - rect.top), abs(y - rect.bottom)) < size // 2
                fixture = pygame.Rect(
                    0, 0, size // 2 if horizontal else 5, 5 if horizontal else size // 2
                )
                fixture.center = lamp.position
                pygame.draw.rect(surface, (15, 26, 30), fixture.inflate(6, 6), border_radius=3)
                pygame.draw.rect(surface, lamp.color, fixture, border_radius=2)
        if room.style == "laboratory":
            # Pale wall caps and a second clean edge give the laboratory a physical depth.
            pygame.draw.line(
                surface,
                (151, 176, 175),
                (rect.left + 4, rect.top + 3),
                (rect.right - 4, rect.top + 3),
                4,
            )
            pygame.draw.line(
                surface,
                (60, 87, 92),
                (rect.left + 4, rect.top + 7),
                (rect.right - 4, rect.top + 7),
                2,
            )
        # Light affects floors, not adjacent sealed roof space or another storey.
        light.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(light, rect.topleft)


def draw_equipment(
    canvas: pygame.Surface, level: LevelData, camera: Camera, clock_ms: int, deck: Deck | None
) -> None:
    size = level.static_map.tile_size_px
    for obj in level.static_map.objects:
        if obj.kind == "Stair" and (deck is None or deck.contains(obj.tile)):
            x, y = camera.to_screen(((obj.tile[0] + 0.5) * size, (obj.tile[1] + 0.5) * size))
            up = str(dict(obj.properties).get("destination", "")).endswith("down")
            color = (109, 223, 212)
            for offset in (-6, 3):
                pygame.draw.lines(
                    canvas,
                    color,
                    False,
                    (
                        (x - 7, y + offset + (4 if up else -4)),
                        (x, y + offset),
                        (x + 7, y + offset + (4 if up else -4)),
                    ),
                    2,
                )
