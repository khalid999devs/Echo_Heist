"""Readable industrial palette shared by scenes and renderers."""

import pygame

type Color = tuple[int, int, int]

BACKGROUND: Color = (4, 11, 18)
WALL: Color = (29, 43, 54)
WALL_EDGE: Color = (77, 100, 111)
GLASS: Color = (78, 194, 219)
COVER: Color = (107, 88, 59)
TEXT: Color = (236, 247, 249)
MUTED: Color = (154, 185, 199)
ACCENT: Color = (37, 226, 235)
ACCENT_DIM: Color = (27, 110, 128)
WARNING: Color = (251, 190, 82)
DANGER: Color = (255, 87, 84)
OPERATIVE: Color = (52, 216, 241)
DISABLED: Color = (104, 135, 145)
BORDER: Color = (53, 94, 109)
PANEL: tuple[int, int, int, int] = (5, 15, 25, 225)
ZONE_FLOORS: dict[str, Color] = {
    "entry": (33, 49, 56),
    "service-wing": (31, 44, 53),
    "security-control": (39, 47, 56),
    "research-floor": (35, 55, 60),
    "core-chamber": (39, 56, 65),
}
CORRIDOR_FLOOR: Color = (31, 45, 54)


class Fonts:
    """Created after pygame.font.init(); default font ships with pygame."""

    def __init__(self) -> None:
        self.logo = pygame.font.Font(None, 81)
        self.title = pygame.font.Font(None, 65)
        self.heading = pygame.font.Font(None, 39)
        self.body = pygame.font.Font(None, 26)
        self.small = pygame.font.Font(None, 20)
        self.micro = pygame.font.Font(None, 17)
        self.stat = pygame.font.Font(None, 57)
