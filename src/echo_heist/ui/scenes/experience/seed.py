"""Explicit seed editing; cancel never changes the queued mission."""

import pygame

from echo_heist.ui.render import theme
from echo_heist.ui.render.hud import panel
from echo_heist.ui.render.theme import Fonts
from echo_heist.ui.scenes.navigation.controls import button, hit

SEED_BUTTON = pygame.Rect(650, 103, 250, 42)
SEED_ACTIONS = (pygame.Rect(360, 410, 270, 48), pygame.Rect(650, 410, 270, 48))


class SeedDialog:
    def __init__(self) -> None:
        self.open = False
        self.value = ""
        self.replace_next = True
        self.notice = ""

    def show(self, value: int) -> None:
        self.value, self.open, self.replace_next, self.notice = str(value), True, True, ""
        pygame.key.start_text_input()

    def handle(self, events: list[pygame.event.Event]) -> int | None:
        for event in events:
            action = None
            if event.type == pygame.TEXTINPUT:
                digits = "".join(c for c in event.text if c in "0123456789")
                if digits:
                    self.value = (("" if self.replace_next else self.value) + digits)[:10]
                    self.replace_next = False
            elif event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
                if event.key == pygame.K_ESCAPE:
                    action = 0
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    action = 1
                elif event.key == pygame.K_BACKSPACE:
                    self.value = "" if self.replace_next else self.value[:-1]
                    self.replace_next = False
                elif event.key == pygame.K_a and getattr(event, "mod", 0) & (
                    pygame.KMOD_CTRL | pygame.KMOD_META
                ):
                    self.replace_next = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = hit(SEED_ACTIONS, event.pos)
            if action == 0:
                self.open = False
                pygame.key.stop_text_input()
                return None
            elif action == 1:
                if self.value and 0 <= int(self.value) <= 2**31 - 1:
                    self.open = False
                    pygame.key.stop_text_input()
                    return int(self.value)
                self.notice = "Enter a seed from 0 to 2147483647."
        return None

    def draw(self, canvas: pygame.Surface, fonts: Fonts) -> None:
        panel(canvas, pygame.Rect(300, 190, 680, 330), fill=(3, 13, 21, 252))
        canvas.blit(fonts.heading.render("MISSION SEED", True, theme.TEXT), (360, 228))
        canvas.blit(
            fonts.small.render("Same seed keeps a comparable challenge.", True, theme.MUTED),
            (360, 281),
        )
        panel(canvas, pygame.Rect(360, 324, 560, 60), border=theme.ACCENT)
        canvas.blit(fonts.body.render(self.value or "0", True, theme.TEXT), (380, 341))
        for rect, text in zip(SEED_ACTIONS, ("CANCEL", "APPLY"), strict=True):
            button(canvas, rect, text, fonts, rect == SEED_ACTIONS[1])
        canvas.blit(
            fonts.micro.render(
                self.notice or "TYPE Seed    ENTER Apply    ESC Cancel",
                True,
                theme.WARNING if self.notice else theme.MUTED,
            ),
            (360, 482),
        )
