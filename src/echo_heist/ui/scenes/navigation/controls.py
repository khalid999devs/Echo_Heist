"""Shared control geometry keeps drawing and mouse activation identical."""

import pygame

from echo_heist.ui.render import theme
from echo_heist.ui.render.hud import panel
from echo_heist.ui.render.theme import Fonts

PAUSE_BUTTONS = tuple(pygame.Rect(460, 310 + index * 58, 360, 46) for index in range(4))
ABORT_BUTTONS = (pygame.Rect(452, 412, 182, 48), pygame.Rect(650, 412, 182, 48))
MAP_CLOSE = pygame.Rect(1108, 28, 134, 40)


def button(
    canvas: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    fonts: Fonts,
    selected: bool = False,
    *,
    enabled: bool = True,
) -> None:
    color = theme.ACCENT if selected and enabled else theme.BORDER
    panel(canvas, rect, fill=(7, 39, 50, 235) if selected else (5, 20, 30, 220), border=color)
    text = fonts.small.render(label, True, theme.TEXT if enabled else theme.DISABLED)
    canvas.blit(text, text.get_rect(center=rect.center))


def hit(rects: tuple[pygame.Rect, ...], point: tuple[int, int]) -> int | None:
    return next((i for i, rect in enumerate(rects) if rect.collidepoint(point)), None)
