"""Working session controls/accessibility; optional persistence is supplied by SR3."""

from dataclasses import replace

import pygame

from echo_heist.core.contracts.experience.model import DesktopPreferences
from echo_heist.core.contracts.experience.ports import ExperienceGateway, ExperienceUnavailable
from echo_heist.infrastructure.persistence.settings import Settings
from echo_heist.ui.input.configuration import ACTIONS, assign, bindings_for, key_label
from echo_heist.ui.render import theme
from echo_heist.ui.render.hud import panel
from echo_heist.ui.render.layout.text import fit
from echo_heist.ui.render.theme import Fonts
from echo_heist.ui.scenes.navigation.controls import button, hit
from echo_heist.ui.scenes.settings import OPTION_RECTS, adjust, click, draw_settings

EXTRA_SETTINGS = (pygame.Rect(640, 260, 548, 58), pygame.Rect(640, 344, 548, 58))
KEY_ROWS = tuple(pygame.Rect(64 + i // 5 * 584, 190 + i % 5 * 74, 552, 62) for i in range(10))
KEY_FOOTER = (pygame.Rect(64, 596, 552, 48), pygame.Rect(648, 596, 552, 48))
ACCESS_ROWS = (
    pygame.Rect(64, 210, 1136, 78),
    pygame.Rect(64, 312, 1136, 78),
    pygame.Rect(64, 430, 1136, 58),
    pygame.Rect(64, 610, 1136, 48),
)


class PreferencesPanel:
    def __init__(self, gateway: ExperienceGateway | None) -> None:
        self.gateway = gateway
        self.preferences = DesktopPreferences()
        self.page = "GENERAL"
        self.selected = 0
        self.capturing: str | None = None
        self.dragging: int | None = None
        self.notice = ""
        if gateway:
            try:
                preferences = gateway.preferences()
                bindings_for(preferences)
                self.preferences = preferences
            except (ExperienceUnavailable, ValueError) as error:
                self.notice = "Using default controls. " + str(error)

    def controls(self) -> tuple[pygame.Rect, ...]:
        if self.page == "GENERAL":
            return (*OPTION_RECTS, *EXTRA_SETTINGS)
        return (*KEY_ROWS, *KEY_FOOTER) if self.page == "CONTROLS" else ACCESS_ROWS

    def reset_page(self) -> None:
        self.page, self.selected, self.capturing, self.dragging = "GENERAL", 0, None, None

    def handle(self, events: list[pygame.event.Event], settings: Settings) -> tuple[Settings, bool]:
        for event in events:
            if event.type == pygame.WINDOWFOCUSLOST:
                self.capturing, self.dragging = None, None
            if event.type == pygame.QUIT:
                continue
            if self.capturing:
                if event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
                    if event.key == pygame.K_ESCAPE:
                        self.capturing = None
                    else:
                        try:
                            self.preferences = assign(self.preferences, self.capturing, event.key)
                            self.capturing, self.notice = None, "Applied for this session."
                        except ValueError as error:
                            self.notice = str(error)
                continue
            activate = None
            rects = self.controls()
            if event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
                if event.key == pygame.K_ESCAPE:
                    if self.page == "GENERAL":
                        return settings, True
                    self.reset_page()
                    continue
                if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_TAB):
                    direction = (
                        -1
                        if event.key == pygame.K_UP
                        or (
                            event.key == pygame.K_TAB
                            and getattr(event, "mod", 0) & pygame.KMOD_SHIFT
                        )
                        else 1
                    )
                    self.selected = (self.selected + direction) % len(rects)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    activate = self.selected
                elif self.page == "GENERAL" and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    settings = adjust(
                        settings, self.selected, -1 if event.key == pygame.K_LEFT else 1
                    )
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = None
            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                if self.page == "GENERAL" and self.dragging is not None:
                    settings = click(settings, self.dragging, event.pos)
                    continue
                index = hit(rects, event.pos)
                if index is not None:
                    self.selected = index
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        activate = index
            if activate is None:
                continue
            if self.page == "GENERAL":
                if activate == 4:
                    return settings, True
                if activate >= 5:
                    self.page, self.selected = ("CONTROLS" if activate == 5 else "ACCESSIBILITY"), 0
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    settings = click(settings, activate, event.pos)
                    self.dragging = activate if activate < 2 else None
                elif activate in (2, 3):
                    settings = adjust(settings, activate, 1)
            elif self.page == "CONTROLS":
                if activate < 10:
                    self.capturing, self.notice = ACTIONS[activate], "Press a key. Escape cancels."
                elif activate == 10:
                    self.preferences = replace(self.preferences, controls=())
                    self.notice = "Default controls restored for this session."
                else:
                    self.reset_page()
            elif activate < 2:
                name = "subtitles" if activate == 0 else "high_contrast"
                self.preferences = (
                    replace(self.preferences, subtitles=not self.preferences.subtitles)
                    if name == "subtitles"
                    else replace(self.preferences, high_contrast=not self.preferences.high_contrast)
                )
                self.notice = "Applied for this session."
            elif activate == 2:
                try:
                    if self.gateway is None:
                        raise ExperienceUnavailable(
                            "Applied for this session. Saving is unavailable in this build."
                        )
                    self.gateway.save_preferences(self.preferences)
                    self.notice = "Preferences saved."
                except (ExperienceUnavailable, ValueError) as error:
                    self.notice = str(error)
            else:
                self.reset_page()
        return settings, False

    def draw(
        self,
        canvas: pygame.Surface,
        fonts: Fonts,
        backdrop: pygame.Surface,
        settings: Settings,
        clock_ms: int,
    ) -> None:
        if self.page == "GENERAL":
            draw_settings(
                canvas, fonts, backdrop, settings, self.selected, clock_ms, paint_background=False
            )
            panel(canvas, pygame.Rect(620, 184, 596, 440), fill=(5, 18, 28, 227))
            canvas.blit(fonts.heading.render("MAKE IT YOURS", True, theme.TEXT), (640, 207))
            for i, name in enumerate(("CONTROLS", "ACCESSIBILITY")):
                button(canvas, EXTRA_SETTINGS[i], name, fonts, self.selected == i + 5)
            canvas.blit(
                fonts.micro.render(
                    "Controls and accessibility apply immediately.", True, theme.MUTED
                ),
                (640, 444),
            )
        else:
            canvas.blit(fonts.title.render(self.page, True, theme.TEXT), (44, 68))
            if self.page == "CONTROLS":
                bindings = bindings_for(self.preferences)
                for i, action in enumerate(ACTIONS):
                    text = f"{action.replace('_', ' ').upper()}    {key_label(bindings, action)}"
                    button(canvas, KEY_ROWS[i], text, fonts, self.selected == i)
                for i, name in enumerate(("RESTORE DEFAULTS", "BACK")):
                    button(canvas, KEY_FOOTER[i], name, fonts, self.selected == i + 10)
            else:
                descriptions = (
                    (
                        "SOUND CAPTIONS",
                        "Relevant tool, nearby-noise and alarm cues.",
                        self.preferences.subtitles,
                    ),
                    (
                        "HIGH-CONTRAST HUD",
                        "Solid backplates behind critical mission information.",
                        self.preferences.high_contrast,
                    ),
                )
                for i, (name, note, enabled) in enumerate(descriptions):
                    rect = ACCESS_ROWS[i]
                    panel(canvas, rect, border=theme.ACCENT if self.selected == i else theme.BORDER)
                    canvas.blit(
                        fonts.body.render(
                            name + ("   ON" if enabled else "   OFF"), True, theme.TEXT
                        ),
                        (rect.x + 18, rect.y + 12),
                    )
                    canvas.blit(
                        fonts.micro.render(note, True, theme.MUTED), (rect.x + 18, rect.y + 49)
                    )
                button(
                    canvas,
                    ACCESS_ROWS[2],
                    "SAVE PREFERENCES",
                    fonts,
                    self.selected == 2,
                    enabled=self.gateway is not None,
                )
                button(canvas, ACCESS_ROWS[3], "BACK", fonts, self.selected == 3)
        if self.notice:
            position = (
                (640, 510)
                if self.page == "GENERAL"
                else (64, 560 if self.page == "ACCESSIBILITY" else 670)
            )
            canvas.blit(
                fonts.micro.render(
                    fit(fonts.micro, self.notice, 548 if self.page == "GENERAL" else 1080),
                    True,
                    theme.WARNING,
                ),
                position,
            )
        if self.capturing:
            panel(
                canvas, pygame.Rect(264, 270, 752, 160), fill=(3, 12, 20, 252), border=theme.ACCENT
            )
            canvas.blit(fonts.heading.render("PRESS A KEY", True, theme.TEXT), (290, 296))
            canvas.blit(
                fonts.small.render(fit(fonts.small, self.notice, 700), True, theme.WARNING),
                (290, 365),
            )
