"""Lay out Khalid's ObjectiveView values and scene panels; text only, no rules."""

import pygame

from echo_heist.ui.presenters.objective import ObjectiveView
from echo_heist.ui.render import theme
from echo_heist.ui.render.theme import Color, Fonts

CONTROLS = (
    "WASD/arrows move  Shift sprint  Hold E core  Q Echo  F EMP  Space melee  "
    "Tab objective  Esc pause"
)


def panel(canvas: pygame.Surface, rect: pygame.Rect) -> None:
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    layer.fill(theme.PANEL)
    canvas.blit(layer, rect.topleft)
    pygame.draw.rect(canvas, theme.WALL_EDGE, rect, 1, border_radius=6)


def draw_hud(canvas: pygame.Surface, view: ObjectiveView, zone_label: str, fonts: Fonts) -> None:
    width = canvas.get_width()
    panel(canvas, pygame.Rect(12, 12, 560, 104))
    canvas.blit(fonts.body.render(f"OBJECTIVE  {view.objective}", True, theme.TEXT), (24, 22))
    status = fonts.small.render(f"{view.elapsed}   {view.inventory}", True, theme.MUTED)
    canvas.blit(status, (24, 52))
    if view.interaction:
        canvas.blit(fonts.body.render(view.interaction, True, theme.WARNING), (24, 78))
    elif view.warning:
        canvas.blit(fonts.body.render(view.warning, True, theme.DANGER), (24, 78))
    panel(canvas, pygame.Rect(width - 372, 12, 360, 72))
    canvas.blit(fonts.body.render(zone_label, True, theme.TEXT), (width - 360, 22))
    canvas.blit(
        fonts.small.render("Guards: stationary posts (patrol AI in P03)", True, theme.MUTED),
        (width - 360, 54),
    )
    if view.warning and view.interaction:
        canvas.blit(fonts.body.render(view.warning, True, theme.DANGER), (24, 124))
    footer = fonts.small.render(CONTROLS, True, theme.MUTED)
    panel(canvas, pygame.Rect(12, canvas.get_height() - 40, footer.get_width() + 24, 30))
    canvas.blit(footer, (24, canvas.get_height() - 33))


def draw_dialog(
    canvas: pygame.Surface,
    title: str,
    lines: tuple[tuple[str, Color], ...],
    fonts: Fonts,
    *,
    title_color: Color = theme.TEXT,
) -> None:
    height = 96 + 34 * len(lines)
    rect = pygame.Rect(0, 0, 640, height)
    rect.center = canvas.get_rect().center
    shade = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 120))
    canvas.blit(shade, (0, 0))
    panel(canvas, rect)
    heading = fonts.heading.render(title, True, title_color)
    canvas.blit(heading, (rect.centerx - heading.get_width() // 2, rect.top + 24))
    for index, (text, color) in enumerate(lines):
        line = fonts.body.render(text, True, color)
        canvas.blit(line, (rect.centerx - line.get_width() // 2, rect.top + 80 + index * 34))
