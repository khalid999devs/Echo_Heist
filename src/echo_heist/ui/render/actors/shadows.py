"""Short source-directed silhouettes and soft grounded contact; no global sun."""

from dataclasses import dataclass
from functools import lru_cache

import pygame


@dataclass(frozen=True, slots=True)
class ShadowStyle:
    dx: int = 0
    dy: int = 4
    alpha: int = 32


DEFAULT_SHADOW = ShadowStyle()


@dataclass(frozen=True, slots=True)
class GroundShadow:
    surface: pygame.Surface
    pivot: tuple[int, int]


@lru_cache(maxsize=384)
def cast_shadow(sprite: pygame.Surface, style: ShadowStyle = DEFAULT_SHADOW) -> GroundShadow:
    silhouette = pygame.mask.from_surface(sprite, 50).to_surface(
        setcolor=(1, 4, 6, style.alpha), unsetcolor=(0, 0, 0, 0)
    )
    width, height = sprite.get_size()
    pad = 8
    pivot = (width // 2 + max(0, -style.dx) + pad, max(0, -style.dy) + pad)
    projected = pygame.Surface(
        (width + abs(style.dx) + pad * 2, abs(style.dy) + pad * 2 + 8), pygame.SRCALPHA
    )
    for row in range(height):
        elevation = (height - 1 - row) / max(1, height - 1)
        projected.blit(
            silhouette.subsurface((0, row, width, 1)),
            (
                pivot[0] - width // 2 + round(style.dx * elevation),
                pivot[1] + round(style.dy * elevation),
            ),
            special_flags=pygame.BLEND_RGBA_MAX,
        )
    # The contact comes from the asset's actual low silhouette, not a generic oval.
    contact = pygame.mask.from_surface(sprite, 60).to_surface(
        setcolor=(0, 2, 4, 70), unsetcolor=(0, 0, 0, 0)
    )
    base = contact.subsurface((0, height * 4 // 5, width, height - height * 4 // 5))
    projected.blit(
        pygame.transform.smoothscale(base, (width, 5)), (pivot[0] - width // 2, pivot[1] - 2)
    )
    return GroundShadow(pygame.transform.gaussian_blur(projected, 2), pivot)


@lru_cache(maxsize=8)
def foot_contact(width: int) -> pygame.Surface:
    contact = pygame.Surface((width + 8, 18), pygame.SRCALPHA)
    pygame.draw.ellipse(contact, (0, 2, 5, 110), (4, 6, width, 6))
    return pygame.transform.gaussian_blur(contact, 2)


def draw_shadow(
    canvas: pygame.Surface,
    sprite: pygame.Surface,
    feet: tuple[int, int],
    *,
    width: int = 25,
    style: ShadowStyle = DEFAULT_SHADOW,
) -> None:
    shadow = cast_shadow(sprite, style)
    canvas.blit(shadow.surface, (feet[0] - shadow.pivot[0], feet[1] - shadow.pivot[1]))
    contact = foot_contact(width)
    canvas.blit(contact, contact.get_rect(center=feet))
