"""Subtle light and dust animation over the rendered three-dimensional title scene."""

from functools import lru_cache
from math import sin

import pygame

from echo_heist.ui.render.surfaces.glass import edge_veil

BACKDROP_PAD = 16


@lru_cache(maxsize=4)
def _bloom(radius: int) -> pygame.Surface:
    surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for distance in range(radius, 0, -4):
        alpha = round(5 * (1 - distance / radius) ** 2)
        pygame.draw.circle(surface, (45, 206, 228, alpha), (radius, radius), distance)
    return surface


@lru_cache(maxsize=2)
def _mirrored(backdrop: pygame.Surface) -> pygame.Surface:
    return pygame.transform.flip(backdrop, True, False)


def draw_scene(
    canvas: pygame.Surface,
    backdrop: pygame.Surface,
    clock_ms: int,
    *,
    text_side: str = "left",
) -> None:
    drift_x = round(5 * sin(clock_ms / 7500))
    drift_y = round(3 * sin(clock_ms / 9400))
    scene = backdrop if text_side == "left" else _mirrored(backdrop)
    canvas.blit(scene, (-BACKDROP_PAD + drift_x, -BACKDROP_PAD + drift_y))
    width, height = canvas.get_size()
    reactor_x = round(width * (0.69 if text_side == "left" else 0.31))
    bloom = _bloom(160)
    bloom.set_alpha(150 + round(25 * sin(clock_ms / 2100)))
    canvas.blit(bloom, (reactor_x - 160, round(height * 0.36) - 160))
    dust = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
    for index in range(22):
        x = (index * 83 + 97 + clock_ms / (190 + index * 13)) % width
        y = (index * 71 + 51 - clock_ms / (100 + index * 19)) % height
        alpha = round(26 + 16 * sin(clock_ms / 1800 + index))
        pygame.draw.circle(dust, (148, 217, 230, alpha), (round(x), round(y)), 1)
    canvas.blit(dust, (0, 0))
    canvas.blit(edge_veil(canvas.get_size(), text_side), (0, 0))
