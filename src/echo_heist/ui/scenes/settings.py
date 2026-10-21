"""Real persisted audio/display options; no gameplay rules live on this screen."""

from dataclasses import replace

import pygame

from echo_heist.infrastructure.persistence.settings import Settings
from echo_heist.ui.render import theme
from echo_heist.ui.render.hud import panel
from echo_heist.ui.render.surfaces.cinematic import draw_scene
from echo_heist.ui.render.theme import Fonts

OPTION_RECTS = (
    pygame.Rect(64, 232, 480, 68),
    pygame.Rect(64, 310, 480, 68),
    pygame.Rect(64, 438, 480, 62),
    pygame.Rect(64, 510, 480, 62),
    pygame.Rect(44, 650, 130, 42),
)


def adjust(settings: Settings, index: int, direction: int) -> Settings:
    if index in (0, 1):
        name = "music_volume" if index == 0 else "sfx_volume"
        value = round(max(0.0, min(1.0, getattr(settings, name) + direction * 0.05)), 2)
        return replace(settings, **{name: value})
    if index == 2:
        return replace(settings, reduced_flashing=not settings.reduced_flashing)
    if index == 3:
        return replace(settings, fullscreen=not settings.fullscreen)
    return settings


def click(settings: Settings, index: int, point: tuple[int, int]) -> Settings:
    if index in (0, 1):
        rect = OPTION_RECTS[index]
        value = round(max(0.0, min(1.0, (point[0] - rect.x - 24) / (rect.w - 48))), 2)
        return (
            replace(settings, music_volume=value)
            if index == 0
            else replace(settings, sfx_volume=value)
        )
    return adjust(settings, index, 1)


def draw_settings(
    canvas: pygame.Surface,
    fonts: Fonts,
    backdrop: pygame.Surface,
    settings: Settings,
    selected: int,
    clock_ms: int,
) -> None:
    draw_scene(canvas, backdrop, clock_ms, reduced_motion=settings.reduced_flashing)
    canvas.blit(fonts.micro.render("ECHO HEIST / PREFERENCES", True, theme.ACCENT), (44, 35))
    canvas.blit(fonts.title.render("SETTINGS", True, theme.TEXT), (40, 69))
    canvas.blit(
        fonts.small.render("Find your balance of sound and display.", True, theme.MUTED), (44, 138)
    )
    panel(canvas, pygame.Rect(44, 184, 520, 440), fill=(5, 18, 28, 227), border=theme.BORDER)
    canvas.blit(fonts.micro.render("AUDIO", True, theme.ACCENT), (64, 201))
    canvas.blit(fonts.micro.render("DISPLAY", True, theme.ACCENT), (64, 405))
    for index, (label, rect) in enumerate(
        zip(
            ("MUSIC", "SOUND EFFECTS", "REDUCED FLASHING", "FULLSCREEN", "BACK"),
            OPTION_RECTS,
            strict=True,
        )
    ):
        color = theme.ACCENT if selected == index else theme.MUTED
        panel(canvas, rect, fill=(5, 25, 35, 185 if selected == index else 110), border=color)
        canvas.blit(fonts.small.render(label, True, theme.TEXT), (rect.x + 20, rect.y + 13))
        if index in (0, 1):
            volume = settings.music_volume if index == 0 else settings.sfx_volume
            text = fonts.small.render(f"{round(volume * 100)}%", True, color)
            canvas.blit(text, (rect.right - text.get_width() - 20, rect.y + 13))
            track = pygame.Rect(rect.x + 24, rect.y + 49, rect.w - 48, 5)
            pygame.draw.rect(canvas, theme.BORDER, track, border_radius=3)
            pygame.draw.rect(
                canvas, color, (track.x, track.y, round(track.w * volume), 5), border_radius=3
            )
            pygame.draw.circle(canvas, color, (track.x + round(track.w * volume), track.centery), 6)
        elif index in (2, 3):
            enabled = settings.reduced_flashing if index == 2 else settings.fullscreen
            text = fonts.small.render("ON" if enabled else "OFF", True, color)
            canvas.blit(text, (rect.right - text.get_width() - 20, rect.y + 13))
            note = "Steady lights and less menu motion." if index == 2 else "Use the full display."
            canvas.blit(fonts.micro.render(note, True, theme.MUTED), (rect.x + 20, rect.y + 38))
    canvas.blit(
        fonts.micro.render("ARROWS Adjust / Select    ENTER Toggle    ESC Back", True, theme.MUTED),
        (64, 598),
    )
