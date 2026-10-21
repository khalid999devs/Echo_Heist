"""Cached architectural light and restrained equipment motion; no gameplay effects."""

from math import cos, sin

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
        clinical = room.style in ("laboratory", "office", "reception")
        color = (203, 229, 223) if clinical else (122, 179, 207)
        radius = max(95, min(rect.width, rect.height))
        light_pool(light, rect.center, color, radius)
        if clinical:
            light_pool(light, (rect.centerx, rect.top + size), (199, 231, 223), radius)
        # Wall-mounted linear luminaires, with a reflected wash rather than a neon grid.
        for x in (rect.left + 12, rect.right - 16):
            fixture = pygame.Rect(x, rect.top + 10, 4, max(18, min(size, rect.height // 3)))
            pygame.draw.rect(surface, (13, 30, 38), fixture.inflate(6, 6), border_radius=3)
            pygame.draw.rect(
                surface, (181, 222, 220) if clinical else (76, 161, 195), fixture, border_radius=2
            )
            light_pool(light, fixture.center, color, 78)
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
    surface.blit(light, (0, 0))


def draw_equipment(
    canvas: pygame.Surface, level: LevelData, camera: Camera, clock_ms: int, deck: Deck | None
) -> None:
    size = level.static_map.tile_size_px
    for index, obj in enumerate(level.static_map.objects):
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
        if obj.kind != "Furniture" or (deck is not None and not deck.contains(obj.tile)):
            continue
        props = dict(obj.properties)
        width, height = props["width_tiles"], props["height_tiles"]
        assert isinstance(width, int) and isinstance(height, int)
        x, y = camera.to_screen(
            ((obj.tile[0] + width / 2) * size, (obj.tile[1] + height / 2) * size)
        )
        if not canvas.get_rect().inflate(100, 100).collidepoint(x, y):
            continue
        style = props["style"]
        if style in ("console", "labbench", "desk", "rack"):
            brightness = 140 + round(25 * sin(clock_ms / 900 + index))
            pygame.draw.circle(canvas, (53, brightness, min(255, brightness + 24)), (x, y - 6), 2)
            if style == "console":
                length = 5 + round(3 * sin(clock_ms / 680 + index))
                pygame.draw.line(canvas, (78, 190, 205), (x - 8, y - 3), (x - 8 + length, y - 3))
        elif style == "tank":
            for bubble in range(3):
                bubble_offset = (clock_ms / 60 + bubble * 13 + index * 7) % max(
                    12, height * size - 16
                )
                pygame.draw.circle(
                    canvas,
                    (109, 205, 221),
                    (
                        x + round(3 * sin(bubble + clock_ms / 700)),
                        round(y + height * size / 2 - 8 - bubble_offset),
                    ),
                    1,
                )
        elif style == "pump":
            for blade in range(3):
                angle = clock_ms / 330 + blade * 2.094
                pygame.draw.line(
                    canvas,
                    (79, 105, 115),
                    (x, y),
                    (x + round(5 * cos(angle)), y + round(5 * sin(angle))),
                    2,
                )
