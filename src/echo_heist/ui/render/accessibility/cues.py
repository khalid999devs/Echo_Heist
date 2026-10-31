"""High contrast backplates and concise captions, with no world-state mutation."""

import pygame

from echo_heist.ui.render import theme
from echo_heist.ui.render.theme import Fonts


def backplates(canvas: pygame.Surface) -> None:
    w, h = canvas.get_size()
    for rect in (
        pygame.Rect(18, 18, 430, 82),
        pygame.Rect(w - 238, 18, 220, 82),
        pygame.Rect(w - 374, h - 142, 356, 126),
        pygame.Rect(18, h - 204, 176, 188),
    ):
        pygame.draw.rect(canvas, (2, 8, 13), rect, border_radius=6)
        pygame.draw.rect(canvas, theme.TEXT, rect, 1, border_radius=6)


def caption(canvas: pygame.Surface, fonts: Fonts, message: str) -> None:
    if not message:
        return
    text = fonts.small.render(message, True, theme.TEXT)
    rect = text.get_rect(midbottom=(canvas.get_width() // 2, canvas.get_height() - 212)).inflate(
        28, 14
    )
    pygame.draw.rect(canvas, (2, 8, 13), rect, border_radius=5)
    canvas.blit(text, text.get_rect(center=rect.center))
