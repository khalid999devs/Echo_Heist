"""Foot contact and soft silhouette projection from a consistent upper-left key light."""

from dataclasses import dataclass
from functools import lru_cache
from math import cos, radians, sin

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
    # Project the upright silhouette onto the ground, away from the key light.
    ground = pygame.transform.smoothscale(
        silhouette, (sprite.get_width(), max(10, sprite.get_height() // 3))
    )
    # The sprite's feet are at bottom-centre. Flip the flattened silhouette so
    # that its feet are at top-centre before turning it away from the key light.
    angle = 55
    projected = pygame.transform.rotate(pygame.transform.flip(ground, False, True), angle)
    padded = pygame.Surface(
        (projected.get_width() + 12, projected.get_height() + 12), pygame.SRCALPHA
    )
    padded.blit(projected, (6, 6))
    pivot = (
        round(projected.get_width() / 2 - ground.get_height() / 2 * sin(radians(angle))) + 6,
        round(projected.get_height() / 2 - ground.get_height() / 2 * cos(radians(angle))) + 6,
    )
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
