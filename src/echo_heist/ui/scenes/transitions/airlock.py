"""Preloaded pressure-door leaves reveal the real mission and its committed result."""

import pygame

from echo_heist.ui.render.environment.art import image


class AirlockTransition:
    def __init__(self) -> None:
        self.source = image("assets/scenes/airlock.png")
        self.leaves: tuple[pygame.Surface, pygame.Surface] | None = None
        self.size = (0, 0)
        self.kind = ""
        self.elapsed_ms = 0
        self.serial = 0
        self.cue = "stair-start"

    @property
    def active(self) -> bool:
        return bool(self.kind)

    @property
    def showing_mission(self) -> bool:
        return self.kind == "EXIT" and self.elapsed_ms < 900

    def start(self, kind: str) -> None:
        self.kind, self.elapsed_ms = kind, 0
        self.cue = "stair-start" if kind == "ENTRY" else "stair-arrive"
        self.serial += 1

    def skip(self) -> None:
        self.kind = ""

    def advance(self, elapsed_ms: int) -> None:
        before = self.elapsed_ms
        self.elapsed_ms += max(0, elapsed_ms)
        if self.kind == "EXIT" and before < 1000 <= self.elapsed_ms:
            self.cue = "stair-start"
            self.serial += 1
        if self.elapsed_ms >= (1250 if self.kind == "ENTRY" else 1950):
            self.skip()

    def draw(self, canvas: pygame.Surface, *, reduced_motion: bool) -> None:
        if not self.active:
            return
        size = canvas.get_size()
        if self.leaves is None or self.size != size:
            self.size = size
            scale = max(size[0] / self.source.get_width(), size[1] / self.source.get_height())
            fitted = pygame.transform.smoothscale(
                self.source, tuple(round(value * scale) for value in self.source.get_size())
            )
            region = fitted.get_rect(center=canvas.get_rect().center)
            picture = pygame.Surface(size)
            picture.blit(fitted, region)
            split = size[0] // 2
            self.leaves = (
                picture.subsurface((0, 0, split, size[1])).copy(),
                picture.subsurface((split, 0, size[0] - split, size[1])).copy(),
            )
        if self.kind == "ENTRY":
            aperture = (self.elapsed_ms - 180) / 1000
        elif self.elapsed_ms < 650:
            aperture = 1 - self.elapsed_ms / 650
        else:
            aperture = (self.elapsed_ms - 1000) / 900
        aperture = min(1.0, max(0.0, aperture))
        aperture = aperture * aperture * (3 - 2 * aperture)
        if reduced_motion:
            # A short opacity reveal replaces lateral travel, retaining context.
            alpha = round(255 * (1 - aperture))
            for leaf in self.leaves:
                leaf.set_alpha(alpha)
            offset = 0
        else:
            for leaf in self.leaves:
                leaf.set_alpha(None)
            offset = round((size[0] / 2 + 2) * aperture)
        canvas.blit(self.leaves[0], (-offset, 0))
        canvas.blit(self.leaves[1], (size[0] // 2 + offset, 0))
