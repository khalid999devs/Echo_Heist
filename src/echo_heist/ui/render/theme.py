"""Readable industrial palette and bundled interface type shared by scenes."""

from io import BytesIO

import pygame

from echo_heist.infrastructure.resources import resource_bytes

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
PANEL: tuple[int, int, int, int] = (5, 15, 25, 192)
ZONE_FLOORS: dict[str, Color] = {
    "entry": (33, 49, 56),
    "service-wing": (31, 44, 53),
    "security-control": (39, 47, 56),
    "research-floor": (35, 55, 60),
    "core-chamber": (39, 56, 65),
}
CORRIDOR_FLOOR: Color = (31, 45, 54)


class Fonts:
    """Load the same legible futuristic faces in source and frozen builds."""

    def __init__(self) -> None:
        def face(weight: str, size: int) -> pygame.font.Font:
            data = resource_bytes(f"assets/fonts/Oxanium-{weight}.ttf")
            return pygame.font.Font(BytesIO(data), size)

        self.logo = face("Bold", 74)
        self.title = face("Bold", 59)
        self.heading = face("Bold", 35)
        self.body = face("SemiBold", 23)
        self.small = face("Regular", 19)
        self.micro = face("SemiBold", 15)
        self.stat = face("Bold", 55)
