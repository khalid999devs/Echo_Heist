"""Greybox palette and font sizes shared by scenes and renderers."""

import pygame

type Color = tuple[int, int, int]

BACKGROUND: Color = (11, 19, 31)
WALL: Color = (40, 52, 70)
WALL_EDGE: Color = (62, 78, 101)
GLASS: Color = (120, 190, 230)
COVER: Color = (96, 84, 66)
TEXT: Color = (230, 238, 248)
MUTED: Color = (150, 167, 190)
ACCENT: Color = (91, 222, 166)
WARNING: Color = (255, 207, 100)
DANGER: Color = (242, 109, 131)
OPERATIVE: Color = (75, 214, 246)
DISABLED: Color = (115, 134, 156)
PANEL: tuple[int, int, int, int] = (8, 14, 24, 205)
ZONE_FLOORS: dict[str, Color] = {
    "entry": (26, 46, 52),
    "service-wing": (30, 38, 56),
    "security-control": (36, 34, 58),
    "research-floor": (28, 44, 46),
    "core-chamber": (52, 42, 34),
}
CORRIDOR_FLOOR: Color = (24, 32, 44)


class Fonts:
    """Created after pygame.font.init(); default font ships with pygame."""

    def __init__(self) -> None:
        self.title = pygame.font.Font(None, 82)
        self.heading = pygame.font.Font(None, 40)
        self.body = pygame.font.Font(None, 28)
        self.small = pygame.font.Font(None, 22)
