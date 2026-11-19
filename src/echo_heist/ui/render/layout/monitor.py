"""Shared layout for the live Companion and security monitors."""

import pygame

from echo_heist.ui.render import theme
from echo_heist.ui.render.layout.text import fit, lines, render
from echo_heist.ui.render.surfaces.glass import panel
from echo_heist.ui.render.theme import Fonts

FRAME = pygame.Rect(20, 142, 462, 536)
LEFT, RIGHT = 36, 466
CARD_FILL = (12, 29, 41, 248)


def tabs(count: int) -> tuple[pygame.Rect, ...]:
    width = (RIGHT - LEFT) // count
    return tuple(pygame.Rect(LEFT + i * width, 190, width - 4, 32) for i in range(count))


class Monitor:
    def __init__(self, canvas: pygame.Surface, fonts: Fonts, title: str, shortcut: str) -> None:
        self.canvas, self.fonts = canvas, fonts
        panel(canvas, FRAME, fill=(5, 17, 27, 249), border=theme.ACCENT_DIM)
        self.text(title, 151, theme.TEXT, font=fonts.body, width=280)
        self.text(shortcut, 157, theme.MUTED, right=RIGHT)

    def text(
        self,
        value: str,
        y: int,
        color: theme.Color = theme.TEXT,
        x: int = LEFT,
        *,
        font: pygame.font.Font | None = None,
        width: int | None = None,
        right: int | None = None,
    ) -> None:
        font = font or self.fonts.micro
        label = render(font, fit(font, value, width or RIGHT - x), color)
        anchor = (right - label.get_width(), y) if right is not None else (x, y)
        self.canvas.blit(label, anchor)

    def paragraph(
        self,
        value: str,
        y: int,
        color: theme.Color = theme.MUTED,
        *,
        x: int = LEFT,
        limit: int = 2,
    ) -> None:
        for i, line in enumerate(lines(self.fonts.micro, value, RIGHT - x, limit)):
            self.text(line, y + i * 18, color, x)

    def select(
        self,
        rect: pygame.Rect,
        label: str,
        active: bool,
    ) -> None:
        panel(self.canvas, rect, fill=CARD_FILL, border=theme.ACCENT if active else theme.BORDER)
        color = theme.ACCENT if active else theme.MUTED
        text = render(self.fonts.micro, fit(self.fonts.micro, label, rect.width - 12), color)
        self.canvas.blit(text, text.get_rect(center=rect.center))

    def card(self, y: int, height: int) -> None:
        panel(self.canvas, pygame.Rect(LEFT, y, RIGHT - LEFT, height), fill=CARD_FILL)

    def rule(self, y: int) -> None:
        pygame.draw.line(self.canvas, theme.BORDER, (LEFT, y), (RIGHT, y))

    def bar(self, bounds: tuple[int, int, int, int], fraction: float, color: theme.Color) -> None:
        x, y, width, height = bounds
        pygame.draw.rect(self.canvas, theme.BORDER, bounds, border_radius=2)
        amount = round(width * min(1.0, max(0.0, fraction)))
        if amount:
            pygame.draw.rect(self.canvas, color, (x, y, amount, height), border_radius=2)


def age(tick: int, at: int, hz: int) -> str:
    return f"{max(0, tick - at) / hz:.1f}s ago"


def identifier(value: str) -> str:
    return value.removeprefix("guard-").replace("-", " ").replace("_", " ").capitalize()
