"""Foot contact and soft silhouette projection from a consistent upper-left key light."""

from dataclasses import dataclass
from functools import lru_cache

import pygame


@dataclass(frozen=True, slots=True)
class GroundShadow:
    surface: pygame.Surface
    pivot: tuple[int, int]


@lru_cache(maxsize=192)
def cast_shadow(sprite: pygame.Surface) -> GroundShadow:
    silhouette = pygame.mask.from_surface(sprite, 50).to_surface(
        setcolor=(0, 3, 7, 85), unsetcolor=(0, 0, 0, 0)
    )
    # Shear height onto the floor while preserving horizontal ground width.
    # Rotating the complete flattened picture turns a broad desk sideways and
    # produces an implausibly long diagonal shadow.
    width, height = sprite.get_size()
    # Ceiling light is high: keep the cast short and attached to the feet/base.
    # The former long projection separated the broad top of equipment from its
    # narrow legs, making cabinets and chairs appear to hover above the floor.
    depth, sideways = max(5, height // 11), max(4, height // 13)
    padded = pygame.Surface((width + sideways + 12, depth + 12), pygame.SRCALPHA)
    for row in range(height):
        distance = (height - 1 - row) / max(1, height - 1)
        strip = silhouette.subsurface((0, row, width, 1))
        padded.blit(
            strip,
            (6 + round(sideways * distance), 6 + round(depth * distance)),
            special_flags=pygame.BLEND_RGBA_MAX,
        )
    contact = pygame.mask.from_surface(sprite, 60).to_surface(
        setcolor=(0, 2, 4, 110), unsetcolor=(0, 0, 0, 0)
    )
    base = contact.subsurface((0, height * 3 // 4, width, height - height * 3 // 4))
    padded.blit(pygame.transform.smoothscale(base, (width, 6)), (6, 3))
    pivot = (width // 2 + 6, 6)
    return GroundShadow(pygame.transform.gaussian_blur(padded, 2), pivot)


@lru_cache(maxsize=8)
def foot_contact(width: int) -> pygame.Surface:
    contact = pygame.Surface((width + 8, 20), pygame.SRCALPHA)
    pygame.draw.ellipse(contact, (0, 2, 5, 160), (4, 6, width, 8))
    return pygame.transform.gaussian_blur(contact, 2)


def draw_shadow(
    canvas: pygame.Surface, sprite: pygame.Surface, feet: tuple[int, int], *, width: int = 25
) -> None:
    shadow = cast_shadow(sprite)
    canvas.blit(shadow.surface, (feet[0] - shadow.pivot[0], feet[1] - shadow.pivot[1]))
    contact = foot_contact(width)
    canvas.blit(contact, contact.get_rect(center=feet))
