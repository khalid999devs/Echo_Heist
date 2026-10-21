"""Cached architectural light and restrained equipment motion; no gameplay effects."""

import pygame

from echo_heist.level.model import Deck, LevelData
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.motifs import light_pool


def bake_lighting(surface: pygame.Surface, level: LevelData) -> None:
    size = level.static_map.tile_size_px
    light = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    mask = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for tile in level.floor_tiles:
        pygame.draw.rect(mask, (255, 255, 255, 255), (*[axis * size for axis in tile], size, size))
    for room in level.rooms:
        rect = pygame.Rect(room.left * size, room.top * size, room.width * size, room.height * size)
        light.set_clip(rect)
        clinical = room.style in ("laboratory", "office", "reception")
        color = (188, 218, 211) if clinical else (220, 187, 130)
        radius = max(95, min(rect.width, rect.height))
        light_pool(light, rect.center, color, radius)
        if clinical:
            light_pool(light, (rect.centerx, rect.top + size), (199, 231, 223), radius)
        # Wall-mounted linear luminaires, with a reflected wash rather than a neon grid.
        for x in (rect.left - 6, rect.right + 2):
            fixture = pygame.Rect(x, rect.top + size // 3, 4, size // 2)
            tile = (fixture.centerx // size, fixture.centery // size)
            if tile in level.floor_tiles or not level.static_map.contains(tile):
                continue
            pygame.draw.rect(surface, (13, 30, 38), fixture.inflate(6, 6), border_radius=3)
            pygame.draw.rect(
                surface, (170, 214, 206) if clinical else (218, 179, 108), fixture, border_radius=2
            )
            light_pool(light, fixture.center, color, size * 2)
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
    light.set_clip(None)
    light.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(light, (0, 0))


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
