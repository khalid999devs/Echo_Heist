"""Restrained concrete, epoxy and steel surfaces; generated once at map load."""

from functools import lru_cache
from io import BytesIO

import pygame

from echo_heist.infrastructure.resources import resource_bytes

PALETTES = {
    "corridor": (72, 73, 68),
    "reception": (82, 82, 74),
    "storage": (66, 65, 59),
    "maintenance": (58, 62, 60),
    "server": (53, 63, 66),
    "office": (78, 80, 74),
    "laboratory": (84, 93, 88),
    "reactor": (64, 75, 74),
}


@lru_cache(maxsize=8)
def material_floor(style: str, size: tuple[int, int] = (768, 768)) -> pygame.Surface:
    base = PALETTES[style]
    source = pygame.image.load(BytesIO(resource_bytes("assets/tiles/materials/mineral-floor.png")))
    surface = pygame.transform.smoothscale(source, size)
    average = pygame.transform.average_color(surface)
    surface.fill((128, 128, 128), special_flags=pygame.BLEND_RGB_MULT)
    surface.fill(tuple(channel // 2 for channel in average[:3]), special_flags=pygame.BLEND_RGB_ADD)
    # Material-only bitmap: no baked cast shadows or perspective. Room grading
    # and architectural seams are shared with the map, rather than painted props.
    surface.fill(
        tuple(
            min(255, round(channel * 255 / max(1, mean)))
            for channel, mean in zip(base, average[:3], strict=True)
        ),
        special_flags=pygame.BLEND_RGB_MULT,
    )
    steel = style in ("server", "maintenance")
    panel_w, panel_h = (96, 192) if steel else (192, 96)
    dark = tuple(max(0, channel - 11) for channel in base)
    light = tuple(channel + 5 for channel in base)
    for y in range(0, size[1], panel_h):
        for x in range(0, size[0], panel_w):
            pygame.draw.line(surface, dark, (x, y), (x + panel_w - 1, y))
            pygame.draw.line(surface, dark, (x, y), (x, y + panel_h - 1))
            pygame.draw.line(surface, light, (x + 1, y + 1), (x + panel_w - 2, y + 1))
            if steel:
                for px, py in ((x + 6, y + 6), (x + panel_w - 7, y + panel_h - 7)):
                    pygame.draw.circle(surface, dark, (px, py), 2)
                    pygame.draw.line(surface, light, (px, py), (px + 1, py))
    return surface


def room_floors(_texture: pygame.Surface) -> dict[str, pygame.Surface]:
    return {style: material_floor(style) for style in PALETTES if style != "corridor"}


def room_grade(style: str, condition: str) -> tuple[int, int, int]:
    # The same cool research / warm service balance affects both props and floor.
    base = (221, 225, 213) if style in ("laboratory", "office", "reception") else (195, 206, 202)
    reduction = {"kept": 0, "used": 9, "dusty": 24, "interrupted": 16}[condition]
    return tuple(channel - reduction for channel in base)  # type: ignore[return-value]
