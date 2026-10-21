"""Cinematic front door and unscored mission outcome presentation."""

from dataclasses import dataclass
from io import BytesIO
from math import sin

import pygame

from echo_heist import __version__
from echo_heist.core.contracts.results import MissionEnd, RunOutcome
from echo_heist.infrastructure.resources import resource_bytes
from echo_heist.ui.render import theme
from echo_heist.ui.render.hud import panel
from echo_heist.ui.render.surfaces.cinematic import BACKDROP_PAD, draw_scene
from echo_heist.ui.render.theme import Fonts


@dataclass(frozen=True, slots=True)
class MenuItem:
    label: str
    enabled: bool = True
    note: str = ""


TITLE_ITEMS = (MenuItem("BEGIN INFILTRATION"), MenuItem("QUIT GAME"))
MODE_ITEMS = (
    MenuItem("HUMAN INFILTRATION", note="Direct control  /  tools and stealth"),
    MenuItem("COMPANION INFILTRATION", enabled=False, note="Available in a later build"),
)
TITLE_BUTTONS = (pygame.Rect(44, 424, 392, 62), pygame.Rect(44, 503, 392, 62))
MODE_BUTTONS = (pygame.Rect(44, 438, 452, 64), pygame.Rect(44, 514, 452, 64))
LAUNCH_BUTTON = pygame.Rect(44, 609, 452, 65)
RESULT_RETRY = pygame.Rect(660, 590, 552, 48)
RESULT_MENU = pygame.Rect(660, 648, 552, 48)


def load_backdrop(size: tuple[int, int]) -> pygame.Surface:
    """Perspective 3D-rendered chamber artwork bundled with the game."""
    art = pygame.image.load(
        BytesIO(resource_bytes("assets/scenes/title-facility.png")), "title.png"
    )
    return pygame.transform.smoothscale(
        art, (size[0] + 2 * BACKDROP_PAD, size[1] + 2 * BACKDROP_PAD)
    )


def move_selection(index: int, items: tuple[MenuItem, ...], key: int) -> int:
    if key in (pygame.K_UP, pygame.K_w):
        return (index - 1) % len(items)
    if key in (pygame.K_DOWN, pygame.K_s):
        return (index + 1) % len(items)
    return index


def menu_hit(scene: str, pos: tuple[int, int]) -> int | None:
    buttons = TITLE_BUTTONS if scene == "TITLE" else MODE_BUTTONS
    return next((index for index, rect in enumerate(buttons) if rect.collidepoint(pos)), None)


def _text(
    canvas: pygame.Surface,
    font: pygame.font.Font,
    message: str,
    color: theme.Color,
    pos: tuple[int, int],
) -> None:
    canvas.blit(font.render(message, True, color), pos)


def _frame(canvas: pygame.Surface, backdrop: pygame.Surface, fonts: Fonts, clock_ms: int) -> None:
    draw_scene(canvas, backdrop, clock_ms)
    pygame.draw.rect(canvas, theme.ACCENT, (44, 38, 6, 6))
    _text(canvas, fonts.micro, "NEXUS RESEARCH  /  FACILITY A1", theme.ACCENT, (62, 33))
    _text(canvas, fonts.logo, "ECHO", theme.TEXT, (39, 83))
    _text(canvas, fonts.logo, "HEIST", theme.TEXT, (39, 149))
    pygame.draw.line(canvas, theme.ACCENT, (44, 229), (150, 229), 3)
    _text(canvas, fonts.small, "THE CORE REBELLION", theme.MUTED, (44, 247))
    pygame.draw.line(canvas, theme.BORDER, (44, 298), (420, 298), 1)
    _text(canvas, fonts.small, "STEAL THE CORE. SURVIVE THE LOCKDOWN.", theme.TEXT, (44, 315))
    _text(canvas, fonts.micro, "ONE SITE  /  TWO ROUTES  /  ONE WAY OUT", theme.MUTED, (44, 345))
    _text(canvas, fonts.micro, f"{__version__}  /  DEVELOPMENT BUILD", theme.MUTED, (993, 692))


def _button(
    canvas: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    fonts: Fonts,
    *,
    selected: bool,
    enabled: bool,
    note: str = "",
    clock_ms: int = 0,
) -> None:
    glow = (1 + sin(clock_ms / 280)) / 2 if selected and enabled else 0
    fill = (
        (7, 39 + round(5 * glow), 53 + round(6 * glow), 185)
        if selected and enabled
        else (5, 18, 29, 96 if enabled else 132)
    )
    border = theme.ACCENT if selected and enabled else theme.DISABLED if selected else theme.BORDER
    panel(canvas, rect, fill=fill, border=border)
    if selected and not enabled:
        pygame.draw.line(
            canvas, theme.DISABLED, (rect.x, rect.y + 12), (rect.x, rect.bottom - 12), 2
        )
    if selected and enabled:
        pygame.draw.line(canvas, theme.ACCENT, (rect.x, rect.y + 12), (rect.x, rect.bottom - 12), 3)
        pygame.draw.line(
            canvas,
            theme.ACCENT,
            (rect.x + 11, rect.bottom - 5),
            (rect.x + 75 + round(10 * glow), rect.bottom - 5),
            2,
        )
    color = theme.TEXT if enabled else theme.DISABLED
    _text(canvas, fonts.body, label, color, (rect.x + 21, rect.y + (11 if note else 19)))
    if note:
        _text(canvas, fonts.micro, note, theme.MUTED, (rect.x + 22, rect.y + 40))
    if enabled:
        x, y = rect.right - 24 + round(2 * glow), rect.centery
        pygame.draw.lines(
            canvas,
            theme.ACCENT if selected else theme.MUTED,
            False,
            ((x - 5, y - 5), (x, y), (x - 5, y + 5)),
            2,
        )


def draw_menu(
    canvas: pygame.Surface,
    fonts: Fonts,
    backdrop: pygame.Surface,
    *,
    scene: str,
    selected: int,
    notice: str,
    clock_ms: int,
) -> None:
    _frame(canvas, backdrop, fonts, clock_ms)
    if scene == "TITLE":
        _text(canvas, fonts.micro, "01  /  ACCESS", theme.ACCENT, (44, 389))
        for index, item in enumerate(TITLE_ITEMS):
            _button(
                canvas,
                TITLE_BUTTONS[index],
                item.label,
                fonts,
                selected=index == selected,
                enabled=item.enabled,
                clock_ms=clock_ms,
            )
        _text(
            canvas,
            fonts.micro,
            "ARROWS  Select    ENTER  Confirm    MOUSE  Navigate",
            theme.MUTED,
            (44, 602),
        )
    else:
        _text(canvas, fonts.micro, "02  /  MISSION BRIEFING", theme.ACCENT, (44, 375))
        _text(canvas, fonts.small, "RESEARCH SITE A1  /  FIVE ZONES", theme.TEXT, (44, 399))
        for index, item in enumerate(MODE_ITEMS):
            _button(
                canvas,
                MODE_BUTTONS[index],
                item.label,
                fonts,
                selected=index == selected,
                enabled=item.enabled,
                note=item.note,
                clock_ms=clock_ms,
            )
        launch_enabled = MODE_ITEMS[selected].enabled
        _button(
            canvas,
            LAUNCH_BUTTON,
            "LAUNCH MISSION",
            fonts,
            selected=launch_enabled,
            enabled=launch_enabled,
            clock_ms=clock_ms,
        )
        if notice:
            _text(canvas, fonts.micro, notice, theme.WARNING, (44, 587))
    _text(
        canvas,
        fonts.micro,
        "ESC  " + ("Quit" if scene == "TITLE" else "Back"),
        theme.MUTED,
        (46, 690),
    )


def draw_results(
    canvas: pygame.Surface,
    end: MissionEnd,
    fonts: Fonts,
    *,
    ticks_per_second: int,
    hovered: str | None = None,
    clock_ms: int = 0,
) -> None:
    """Report only committed mission facts; final score/rank is a P06 rule."""
    seconds = end.elapsed_ticks // max(1, ticks_per_second)
    title, color, detail = {
        RunOutcome.WIN: ("MISSION COMPLETE", theme.ACCENT, "Core secured  /  operative extracted"),
        RunOutcome.CAPTURED: (
            "OPERATIVE CAPTURED",
            theme.DANGER,
            "Security intercepted the operative.",
        ),
        RunOutcome.ABORTED: ("MISSION ABORTED", theme.WARNING, "Operation ended by operative"),
    }[end.outcome]
    if end.outcome == RunOutcome.CAPTURED:
        warning = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
        warning.fill((75, 8, 10, 28))
        canvas.blit(warning, (0, 0))
    _text(canvas, fonts.micro, "NEXUS RESEARCH  /  AFTER ACTION REPORT", color, (660, 55))
    pygame.draw.line(canvas, color, (660, 88), (1212, 88), 2)
    _text(canvas, fonts.logo, "ECHO HEIST", theme.TEXT, (655, 115))
    _text(canvas, fonts.small, "THE CORE REBELLION", theme.MUTED, (660, 187))
    _text(canvas, fonts.heading, title, color, (658, 249))
    _text(canvas, fonts.body, detail, theme.TEXT, (660, 304))
    pygame.draw.line(canvas, theme.BORDER, (660, 359), (1212, 359), 1)
    _text(canvas, fonts.micro, "MISSION TIME", theme.MUTED, (662, 383))
    _text(canvas, fonts.stat, f"{seconds // 60:02d}:{seconds % 60:02d}", theme.TEXT, (658, 410))
    objective = "RECOVERED" if end.outcome == RunOutcome.WIN else "NOT EXTRACTED"
    _text(canvas, fonts.micro, "CORE STATUS", theme.MUTED, (960, 383))
    _text(canvas, fonts.body, objective, color, (958, 424))
    _text(
        canvas,
        fonts.small,
        "Your next attempt uses the same facility layout.",
        theme.MUTED,
        (662, 511),
    )
    glow = round(8 * (1 + sin(clock_ms / 280))) if hovered == "RETRY" else 0
    panel(canvas, RESULT_RETRY, fill=(5, 42 + glow, 56 + glow, 185), border=theme.ACCENT)
    _text(canvas, fonts.small, "R  RETRY MISSION", theme.ACCENT, (678, 605))
    panel(
        canvas,
        RESULT_MENU,
        fill=(6, 34, 45, 230) if hovered == "MENU" else theme.PANEL,
        border=theme.ACCENT if hovered == "MENU" else theme.BORDER,
    )
    _text(canvas, fonts.small, "ENTER  MAIN MENU", theme.TEXT, (678, 663))
    _text(canvas, fonts.micro, "ESC QUIT", theme.MUTED, (1127, 666))
