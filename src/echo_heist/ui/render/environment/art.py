"""Decode production atlases once; preserve proportions and transparent margins."""

from io import BytesIO

import pygame

from echo_heist.infrastructure.resources import resource_bytes


def image(path: str) -> pygame.Surface:
    return pygame.image.load(BytesIO(resource_bytes(path)), path)


def sprite_grid(
    path: str, columns: int, rows: int, size: tuple[int, int]
) -> tuple[pygame.Surface, ...]:
    sheet = image(path)
    frames = []
    for row in range(rows):
        for col in range(columns):
            left, right = (
                col * sheet.get_width() // columns,
                (col + 1) * sheet.get_width() // columns,
            )
            top, bottom = row * sheet.get_height() // rows, (row + 1) * sheet.get_height() // rows
            cell = sheet.subsurface((left, top, right - left, bottom - top))
            crop = cell.subsurface(cell.get_bounding_rect(min_alpha=24))
            frame = pygame.Surface(size, pygame.SRCALPHA)
            fitted = pygame.transform.smoothscale(
                crop, crop.get_rect().fit(pygame.Rect((0, 0), size)).size
            )
            frame.blit(fitted, fitted.get_rect(midbottom=(size[0] // 2, size[1])))
            frames.append(frame)
    return tuple(frames)


def laboratory_props() -> tuple[pygame.Surface, ...]:
    sheet = image("assets/tiles/laboratory-props.png")
    regions = (
        (0, 0, 615, 515),
        (630, 0, 285, 515),
        (940, 0, 596, 515),
        (50, 515, 430, 509),
        (540, 515, 450, 509),
        (1000, 515, 536, 509),
    )
    cells = (sheet.subsurface(rect) for rect in regions)
    return tuple(cell.subsurface(cell.get_bounding_rect(min_alpha=24)) for cell in cells)
