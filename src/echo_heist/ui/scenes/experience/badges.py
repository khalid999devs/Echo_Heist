"""Result medals reflect the achievements already committed by the game."""

import pygame

from echo_heist.core.contracts.experience.model import Achievement
from echo_heist.ui.render import theme
from echo_heist.ui.render.layout.text import fit
from echo_heist.ui.render.surfaces.glass import panel
from echo_heist.ui.render.theme import Fonts

BADGES = (
    (Achievement.GHOST, "GHOST", "Zero detections"),
    (Achievement.AI_MASTER, "AI MASTER", "Companion victory"),
    (Achievement.SPEEDRUNNER, "SPEEDRUNNER", "Fast extraction"),
)


def _emblem(canvas: pygame.Surface, kind: Achievement, x: int, y: int, color: theme.Color) -> None:
    pygame.draw.polygon(
        canvas,
        color,
        (
            (x, y - 14),
            (x + 12, y - 7),
            (x + 12, y + 7),
            (x, y + 14),
            (x - 12, y + 7),
            (x - 12, y - 7),
        ),
        1,
    )
    if kind == Achievement.GHOST:
        pygame.draw.ellipse(canvas, color, (x - 8, y - 4, 16, 8), 1)
        pygame.draw.line(canvas, color, (x - 7, y + 7), (x + 7, y - 7), 2)
    elif kind == Achievement.AI_MASTER:
        pygame.draw.rect(canvas, color, (x - 7, y - 5, 14, 10), 1, 3)
        pygame.draw.circle(canvas, color, (x - 3, y), 1)
        pygame.draw.circle(canvas, color, (x + 3, y), 1)
    else:
        pygame.draw.circle(canvas, color, (x, y), 7, 1)
        pygame.draw.lines(canvas, color, False, ((x, y - 4), (x, y), (x + 4, y + 1)), 2)


def draw_badges(canvas: pygame.Surface, fonts: Fonts, earned: tuple[Achievement, ...]) -> None:
    for index, (achievement, name, condition) in enumerate(BADGES):
        unlocked = achievement in earned
        color = theme.WARNING if unlocked else theme.DISABLED
        card = pygame.Rect(660 + 186 * index, 411, 180, 53)
        panel(canvas, card, fill=(10, 25, 34, 242), border=color if unlocked else theme.BORDER)
        _emblem(canvas, achievement, card.x + 20, card.centery, color)
        title = fonts.micro.render(name, True, color)
        subtitle = fonts.micro.render(fit(fonts.micro, condition, 138), True, theme.MUTED)
        canvas.blit(title, (card.x + 38, card.y + 7))
        canvas.blit(subtitle, (card.x + 38, card.y + 29))
