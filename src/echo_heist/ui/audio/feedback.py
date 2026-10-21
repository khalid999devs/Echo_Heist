"""Explicit pointer-entry and activation feedback, independent of selection changes."""

from collections.abc import Sequence

import pygame


class UiFeedback:
    def __init__(self) -> None:
        self.serial = 0
        self.cue = "hover"
        self.hovered: tuple[str, int] | None = None

    def feed(
        self, events: Sequence[pygame.event.Event], scene: str, rects: tuple[pygame.Rect, ...]
    ) -> None:
        if not rects:
            self.hovered = None
            return
        pending: str | None = None
        for event in events:
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                index = next(
                    (i for i, rect in enumerate(rects) if rect.collidepoint(event.pos)), None
                )
                target = (scene, index) if index is not None else None
                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and target is not None
                ):
                    pending = "confirm"
                elif (
                    event.type == pygame.MOUSEMOTION
                    and target is not None
                    and target != self.hovered
                    and pending is None
                ):
                    pending = "hover"
                self.hovered = target
            elif event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    pending = "confirm"
                elif event.key == pygame.K_ESCAPE:
                    pending = "back"
                elif event.key in (
                    pygame.K_UP,
                    pygame.K_DOWN,
                    pygame.K_LEFT,
                    pygame.K_RIGHT,
                    pygame.K_TAB,
                ):
                    pending = pending or "hover"
            elif event.type == pygame.WINDOWFOCUSLOST:
                self.hovered = None
        if pending is not None:
            self.cue = pending
            self.serial += 1
