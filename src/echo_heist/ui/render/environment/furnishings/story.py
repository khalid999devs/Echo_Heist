"""Authored aftermath and connected utility runs; cosmetic marks never change collision."""

from random import Random

import pygame

from echo_heist.level.model import LevelData


def paint_room_story(surface: pygame.Surface, level: LevelData) -> None:
    size = level.static_map.tile_size_px
    for detail in level.floor_details:
        rect = pygame.Rect(
            detail.left * size, detail.top * size, detail.width * size, detail.height * size
        )
        if detail.style == "utility":
            vertical = rect.height > rect.width
            start = (rect.left + 12, rect.top + 8)
            end = (start[0], rect.bottom - 8) if vertical else (rect.right - 8, start[1])
            pygame.draw.line(surface, (12, 22, 27), start, end, 10)
            pygame.draw.line(surface, (80, 104, 109), start, end, 5)
            pygame.draw.line(
                surface, (134, 151, 148), (start[0] - 1, start[1]), (end[0] - 1, end[1]), 1
            )
            length = rect.height if vertical else rect.width
            for offset in range(24, length - 20, size):
                x, y = (start[0], start[1] + offset) if vertical else (start[0] + offset, start[1])
                pygame.draw.rect(surface, (35, 54, 60), (x - 6, y - 3, 12, 6))
                if vertical:
                    pygame.draw.lines(
                        surface,
                        (82, 106, 112),
                        False,
                        ((x + 3, y), (x + 21, y), (x + 21, y + 17)),
                        3,
                    )
            continue
        if detail.style != "aftermath":
            continue
        rng = Random(sum(ord(char) * (i + 1) for i, char in enumerate(detail.detail_id)))
        marks = pygame.Surface(rect.size, pygame.SRCALPHA)
        # Keep small clusters rather than uniform debris across every aisle.
        for i in range(5):
            x, y = rng.randrange(15, rect.w - 15), rng.randrange(15, rect.h - 15)
            tile = detail.left + x // size, detail.top + y // size
            if tile not in level.floor_tiles:
                continue
            if i < 2:
                paper = pygame.Rect(x, y, 16, 20)
                pygame.draw.polygon(
                    marks,
                    (162, 168, 153, 175),
                    ((x, y + 2), (x + 15, y), (x + 18, y + 19), (x + 2, y + 21)),
                )
                for line in range(3):
                    pygame.draw.line(
                        marks,
                        (58, 78, 80, 170),
                        (paper.x + 4, paper.y + 5 + line * 4),
                        (paper.x + 12, paper.y + 4 + line * 4),
                        1,
                    )
            else:
                pygame.draw.ellipse(marks, (43, 34, 24, 65), (x - 13, y - 7, 31, 16))
                pygame.draw.arc(marks, (98, 80, 54, 75), (x - 8, y - 5, 18, 11), 0.3, 5.3, 2)
        for i in range(5):
            x, y = round(rect.w * 0.35 + i * 14), round(rect.h * 0.65 - i * 9)
            pygame.draw.ellipse(marks, (13, 20, 23, 72), (x, y, 7, 15))
            pygame.draw.ellipse(marks, (13, 20, 23, 65), (x + 10, y + 8, 7, 15))
        pygame.draw.line(
            marks,
            (180, 177, 151, 48),
            (rect.w // 3, rect.h // 2),
            (rect.w * 2 // 3, rect.h // 2 + 18),
            2,
        )
        surface.blit(marks, rect.topleft)
    for marker in level.markers:
        if marker.kind != "HideSpot":
            continue
        x, y = marker.tile[0] * size, marker.tile[1] * size
        recess = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(recess, (4, 13, 18, 80), (8, 8, size - 16, size - 16), border_radius=6)
        pygame.draw.rect(recess, (64, 103, 107, 140), (12, 12, size - 24, size - 24), 1, 4)
        pygame.draw.line(
            recess, (84, 153, 151, 150), (size // 2 - 12, size - 15), (size // 2 + 12, size - 15), 2
        )
        surface.blit(recess, (x, y))
