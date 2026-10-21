"""Fill the display while keeping authored controls in a centred, undistorted safe area."""

from collections.abc import Sequence
from math import ceil

import pygame

from echo_heist.infrastructure.persistence.settings import MAX_WINDOW_SIZE

DESIGN_SIZE = (1280, 720)


def logical_size_for(window_size: tuple[int, int]) -> tuple[int, int]:
    width, height = (max(1, axis) for axis in window_size)
    scale = min(width / DESIGN_SIZE[0], height / DESIGN_SIZE[1])
    return (
        min(MAX_WINDOW_SIZE[0], max(DESIGN_SIZE[0], ceil(width / scale))),
        min(MAX_WINDOW_SIZE[1], max(DESIGN_SIZE[1], ceil(height / scale))),
    )


def interface_origin(view_size: tuple[int, int]) -> tuple[int, int]:
    return ((view_size[0] - DESIGN_SIZE[0]) // 2, (view_size[1] - DESIGN_SIZE[1]) // 2)


def interface_canvas(canvas: pygame.Surface) -> pygame.Surface:
    return canvas.subsurface(pygame.Rect(interface_origin(canvas.get_size()), DESIGN_SIZE))


def interface_events(
    events: Sequence[pygame.event.Event], view_size: tuple[int, int]
) -> list[pygame.event.Event]:
    origin = interface_origin(view_size)
    result = []
    for event in events:
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            point = event.pos[0] - origin[0], event.pos[1] - origin[1]
            event = pygame.event.Event(event.type, {**event.dict, "pos": point})
        result.append(event)
    return result
