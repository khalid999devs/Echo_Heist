"""Soft glass surfaces with consistent edges across menus and gameplay."""

from functools import lru_cache

import pygame

from echo_heist.ui.render import theme


@lru_cache(maxsize=64)
def _glass(
    size: tuple[int, int], fill: tuple[int, int, int, int], border: theme.Color
) -> pygame.Surface:
    width, height = size
    surface = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(height):
        lift = round(9 * (1 - y / max(1, height - 1)))
        color = tuple(min(255, channel + lift) for channel in fill[:3])
        pygame.draw.line(surface, (*color, fill[3]), (0, y), (width, y))
    mask = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=8)
    surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    pygame.draw.rect(surface, (*border, 115), surface.get_rect(), 1, border_radius=8)
    pygame.draw.line(surface, (*border, 175), (10, 0), (min(width - 10, 56), 0), 1)
    pygame.draw.line(surface, (174, 219, 231, 22), (10, 2), (width - 10, 2), 1)
    return surface


def panel(
    canvas: pygame.Surface,
    rect: pygame.Rect,
    *,
    fill: tuple[int, int, int, int] = theme.PANEL,
    border: theme.Color = theme.BORDER,
) -> None:
    canvas.blit(_glass(rect.size, fill, border), rect.topleft)


@lru_cache(maxsize=12)
def edge_veil(size: tuple[int, int], side: str, strength: int = 240) -> pygame.Surface:
    """A continuous scene-to-type transition without a visible panel boundary."""
    width, height = size
    surface = pygame.Surface(size, pygame.SRCALPHA)
    for x in range(width):
        position = x / max(1, width - 1)
        distance = position if side == "left" else 1 - position
        blend = max(0.0, min(1.0, (0.78 - distance) / 0.52))
        alpha = round(strength * blend**1.6)
        pygame.draw.line(surface, (2, 9, 16, alpha), (x, 0), (x, height))
    vertical = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(height):
        amount = abs(2 * y / max(1, height - 1) - 1)
        alpha = round(75 * amount**3)
        pygame.draw.line(vertical, (1, 6, 11, alpha), (0, y), (width, y))
    surface.blit(vertical, (0, 0))
    return surface


@lru_cache(maxsize=4)
def alert_frame(size: tuple[int, int]) -> pygame.Surface:
    surface = pygame.Surface(size, pygame.SRCALPHA)
    for inset in range(22):
        alpha = round(72 * (1 - inset / 22) ** 2)
        pygame.draw.rect(
            surface, (*theme.DANGER, alpha), surface.get_rect().inflate(-2 * inset, -2 * inset), 1
        )
    return surface
