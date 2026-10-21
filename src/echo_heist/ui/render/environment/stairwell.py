"""Animated architectural transition driven by committed stair travel progress."""

from math import sin

import pygame

from echo_heist.core.contracts.results import StairView
from echo_heist.ui.render.environment.art import image
from echo_heist.ui.render.hud import panel
from echo_heist.ui.render.theme import ACCENT, MUTED, TEXT, Fonts


class Stairwell:
    def __init__(self) -> None:
        source = image("assets/scenes/stairwell.png")
        self.scene = pygame.transform.smoothscale(source, (684, 385))
        self.active: StairView | None = None
        self.finished_at = -1000

    def draw(
        self,
        canvas: pygame.Surface,
        travel: StairView | None,
        frames: tuple[pygame.Surface, ...],
        fonts: Fonts,
        clock_ms: int,
        *,
        reduced_motion: bool,
    ) -> None:
        if travel is not None:
            self.active, self.finished_at = travel, clock_ms
        elif self.active is None or clock_ms - self.finished_at > 220:
            self.active = None
            return
        current = travel or self.active
        assert current is not None
        progress = 1 - current.remaining_ticks / current.total_ticks if travel else 1.0
        rect = pygame.Rect(298, 118, 684, 385)
        shade = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
        shade.fill((2, 9, 15, 145))
        canvas.blit(shade, (0, 0))
        panel(canvas, rect.inflate(4, 4), border=ACCENT)
        canvas.blit(self.scene, rect)
        ascending = current.destination[0] > current.source[0]
        p = progress if ascending else 1 - progress
        point = (
            rect.x + round(rect.w * (0.35 + 0.30 * p)),
            rect.y + round(rect.h * (0.76 - 0.47 * p)),
        )
        index = 1 + (clock_ms // 140) % 2 if not reduced_motion else 0
        frame = frames[index if ascending else 8 + index]
        bob = round(2 * abs(sin(clock_ms / 100))) if not reduced_motion else 0
        canvas.blit(frame, frame.get_rect(midbottom=(point[0], point[1] - bob)))
        panel(canvas, pygame.Rect(298, 515, 684, 50), fill=(4, 17, 25, 240))
        label = "ASCENDING / RESEARCH" if ascending else "DESCENDING / SERVICE"
        canvas.blit(fonts.small.render(label, True, TEXT), (318, 524))
        canvas.blit(fonts.micro.render("Move to cancel", True, MUTED), (826, 526))
        pygame.draw.rect(canvas, ACCENT, (318, 554, round(644 * progress), 3))
