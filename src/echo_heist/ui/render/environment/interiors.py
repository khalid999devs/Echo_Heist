"""Purposeful room floors, gangways, services and small environmental details."""

import pygame

from echo_heist.level.model import LevelData
from echo_heist.ui.render import theme
from echo_heist.ui.render.environment.architecture.materials import room_floors as room_floors
from echo_heist.ui.render.theme import Fonts


def draw_details(surface: pygame.Surface, level: LevelData, stair: pygame.Surface | None) -> None:
    size = level.static_map.tile_size_px
    for detail in level.floor_details:
        rect = pygame.Rect(
            detail.left * size, detail.top * size, detail.width * size, detail.height * size
        )
        if detail.style == "stairs":
            if stair is not None:
                sprite = pygame.transform.rotate(stair, detail.rotation)
                surface.blit(pygame.transform.smoothscale(sprite, rect.size), rect)
            else:
                pygame.draw.rect(surface, (37, 49, 55), rect)
                for offset in range(0, rect.width, 12):
                    pygame.draw.line(
                        surface,
                        (133, 153, 158),
                        (rect.x + offset, rect.top),
                        (rect.x + offset, rect.bottom),
                        2,
                    )
        elif detail.style == "grate":
            pygame.draw.rect(surface, (17, 28, 35), rect.inflate(-8, -4), border_radius=3)
            for y in range(rect.top + 7, rect.bottom - 4, 5):
                pygame.draw.line(surface, (57, 73, 79), (rect.left + 7, y), (rect.right - 7, y), 1)
        elif detail.style == "cables":
            for offset in (0, 4, 8):
                points = [
                    (rect.left, rect.centery + offset),
                    (rect.left + 9, rect.centery + offset - 5),
                    (rect.right - 12, rect.centery + offset - 5),
                    (rect.right, rect.centery + offset),
                ]
                pygame.draw.lines(surface, (8, 18, 23), False, points, 4)
                pygame.draw.lines(surface, (61, 78, 84), False, points, 1)
        elif detail.style == "threshold":
            pygame.draw.rect(surface, theme.WARNING, rect, 2)


def draw_room_trim(surface: pygame.Surface, level: LevelData, fonts: Fonts) -> None:
    size = level.static_map.tile_size_px
    for room in level.rooms:
        rect = pygame.Rect(room.left * size, room.top * size, room.width * size, room.height * size)
        # A restrained seam defines each room without drawing a second tile grid.
        edge = (49, 104, 116) if room.style in ("laboratory", "reactor", "server") else (89, 90, 76)
        pygame.draw.rect(surface, edge, rect.inflate(-4, -4), 1)
        if room.style == "laboratory":
            pygame.draw.line(
                surface,
                (166, 196, 193),
                (rect.left + 6, rect.top + 6),
                (rect.right - 6, rect.top + 6),
                2,
            )
        title = fonts.micro.render(room.label.upper(), True, (143, 168, 176))
        if title.get_width() > rect.width - 8:
            title = pygame.transform.smoothscale(title, (rect.width - 8, title.get_height()))
        label_rect = title.get_rect(midbottom=(rect.centerx, rect.top - 5))
        pygame.draw.rect(surface, (4, 14, 21), label_rect.inflate(10, 5), border_radius=2)
        surface.blit(title, label_rect)
        if room.style in ("laboratory", "office", "server"):
            # Small inset light fixtures sit on the wall; geometry stays map-owned.
            for x in (rect.left + 11, rect.right - 13):
                pygame.draw.rect(surface, (10, 29, 36), (x - 3, rect.top - 5, 12, 4))
                pygame.draw.line(
                    surface, theme.ACCENT_DIM, (x, rect.top - 3), (x + 6, rect.top - 3), 2
                )
