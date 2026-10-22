"""A restrained signal-lock logo reveal; all text is baked before loading starts."""

from io import BytesIO
from math import pi, sin

import pygame

from echo_heist.infrastructure.resources import resource_bytes
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.startup.loader import LoadingProgress

INK = (5, 13, 20)
CYAN = (63, 223, 228)
WHITE = (232, 246, 247)
MUTED = (123, 159, 173)


def paint_first_frame(screen: pygame.Surface) -> None:
    """No fonts, bitmaps or audio device required for the first visible pixels."""
    screen.fill(INK)
    draw_mark(screen, screen.get_rect().center, 56)
    pygame.display.flip()


def draw_mark(canvas: pygame.Surface, center: tuple[int, int], radius: int) -> None:
    for scale in (1.0, 0.67, 0.34):
        r = round(radius * scale)
        pygame.draw.arc(
            canvas,
            CYAN,
            (center[0] - r, center[1] - r, 2 * r, 2 * r),
            pi * 0.18,
            pi * 1.82,
            max(2, radius // 20),
        )
    pygame.draw.circle(canvas, WHITE, center, max(3, radius // 12))


class OpeningScreen:
    def __init__(self, *, reduced_motion: bool) -> None:
        self.reduced_motion = reduced_motion
        image = pygame.image.load(BytesIO(resource_bytes("assets/branding/concepts/core.png")))
        self.icon = pygame.transform.smoothscale(image, (132, 132))
        regular = resource_bytes("assets/fonts/Oxanium-Regular.ttf")
        bold = resource_bytes("assets/fonts/Oxanium-Bold.ttf")
        logo = pygame.font.Font(BytesIO(bold), 70)
        subtitle = pygame.font.Font(BytesIO(regular), 19)
        small = pygame.font.Font(BytesIO(regular), 16)
        self.title = logo.render("ECHO HEIST", True, WHITE)
        self.subtitle = subtitle.render("THE CORE REBELLION", True, MUTED)
        labels = ("Preparing the facility", "Connecting audio", "Preparing the main menu", "Ready")
        # No Font.render calls after the resource worker begins, including resize.
        self.labels = {text: small.render(text, True, MUTED) for text in labels}
        self.percent = tuple(small.render(f"{value:02d}%", True, CYAN) for value in range(101))
        self.skip = small.render("PRESS ANY KEY TO SKIP", True, MUTED)
        self.closing = small.render("Closing", True, MUTED)
        self.background: pygame.Surface | None = None
        self._panel = pygame.Surface((720, 460), pygame.SRCALPHA)

    def _background(self, size: tuple[int, int]) -> pygame.Surface:
        if self.background is None or self.background.get_size() != size:
            self.background = opaque_surface(size)
            width, height = size
            for y in range(height):
                strength = max(0.0, 1 - abs(y / max(1, height) - 0.43) * 2.2)
                color = (
                    5 + round(3 * strength),
                    13 + round(12 * strength),
                    20 + round(14 * strength),
                )
                pygame.draw.line(self.background, color, (0, y), (width, y))
            cx, cy = width // 2, height // 2
            for radius in (220, 340, 480):
                pygame.draw.circle(self.background, (13, 33, 43), (cx, cy - 82), radius, 1)
            for x in range(cx % 120, width, 120):
                pygame.draw.line(self.background, (10, 25, 34), (x, 0), (x, height), 1)
        return self.background

    def draw(
        self,
        canvas: pygame.Surface,
        elapsed_ms: float,
        progress: LoadingProgress,
        *,
        ready: bool,
        closing: bool = False,
    ) -> None:
        canvas.blit(self._background(canvas.get_size()), (0, 0))
        center = canvas.get_rect().center
        motion = 0.0 if self.reduced_motion else elapsed_ms
        # A slow sweep and restrained rings establish the signal without flashes.
        pulse = 0.5 + sin(motion / 650) * 0.5
        scan = center[1] - 200 + round((motion / 14) % 400)
        if not self.reduced_motion:
            pygame.draw.line(canvas, (18, 54, 64), (center[0] - 310, scan), (center[0] + 310, scan))
        panel = self._panel
        panel.fill((0, 0, 0, 0))
        mark = (360, 128)
        pygame.draw.circle(panel, (20, 66 + round(pulse * 8), 76, 160), mark, 91, 1)
        panel.blit(self.icon, self.icon.get_rect(center=mark))
        arc_start = motion / 1200
        pygame.draw.arc(
            panel,
            (33, 123, 137),
            (mark[0] - 84, mark[1] - 84, 168, 168),
            arc_start,
            arc_start + pi * 0.35,
            2,
        )
        panel.blit(self.title, self.title.get_rect(midtop=(360, 232)))
        panel.blit(self.subtitle, self.subtitle.get_rect(midtop=(360, 318)))
        track = pygame.Rect(160, 366, 400, 2)
        pygame.draw.rect(panel, (30, 57, 67), track)
        if progress.fraction > 0:
            pygame.draw.rect(panel, CYAN, (track.x, track.y, round(400 * progress.fraction), 2))
        label = self.closing if closing else self.labels[progress.label]
        panel.blit(label, (160, 383))
        number = self.percent[min(100, max(0, int(progress.fraction * 100)))]
        panel.blit(number, number.get_rect(topright=(560, 383)))
        if ready and elapsed_ms > 700 and not closing:
            panel.blit(self.skip, self.skip.get_rect(midtop=(360, 433)))
        # First frame is already visible. Fade in typography, never a black frame.
        panel.set_alpha(255 if self.reduced_motion else min(255, 120 + round(elapsed_ms / 2)))
        canvas.blit(panel, panel.get_rect(center=center))
