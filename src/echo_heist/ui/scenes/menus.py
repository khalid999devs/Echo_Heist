"""Cinematic front door and unscored mission outcome presentation."""

from dataclasses import dataclass
from io import BytesIO

import pygame

from echo_heist import __version__
from echo_heist.core.contracts.results import MissionEnd, RunOutcome
from echo_heist.infrastructure.resources import resource_bytes
from echo_heist.ui.render import theme
from echo_heist.ui.render.hud import panel
from echo_heist.ui.render.theme import Fonts


@dataclass(frozen=True, slots=True)
class MenuItem:
    label: str
    enabled: bool = True
    note: str = ""


TITLE_ITEMS = (MenuItem("BEGIN INFILTRATION"), MenuItem("QUIT GAME"))
MODE_ITEMS = (
    MenuItem("HUMAN INFILTRATION", note="Direct control  /  tools and stealth"),
    MenuItem("COMPANION INFILTRATION", enabled=False, note="Autonomy arrives in Phase 04"),
)
TITLE_BUTTONS = (pygame.Rect(44, 424, 392, 62), pygame.Rect(44, 503, 392, 62))
MODE_BUTTONS = (pygame.Rect(44, 438, 452, 64), pygame.Rect(44, 514, 452, 64))
LAUNCH_BUTTON = pygame.Rect(44, 609, 452, 65)
RESULT_RETRY = pygame.Rect(660, 590, 552, 48)
RESULT_MENU = pygame.Rect(660, 648, 552, 48)


def load_backdrop(size: tuple[int, int]) -> pygame.Surface:
    """Original 2.5D facility art bundled for source and frozen builds."""
    art = pygame.image.load(
        BytesIO(resource_bytes("assets/scenes/title-facility.png")), "title.png"
    )
    return pygame.transform.smoothscale(art, size)


def load_operative_portrait() -> pygame.Surface:
    art = pygame.image.load(
        BytesIO(resource_bytes("assets/characters/operative-dossier.png")), "operative.png"
    )
    return pygame.transform.smoothscale(art, (225, 252))


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
    canvas.blit(backdrop, (0, 0))
    shade = pygame.Surface((530, canvas.get_height()), pygame.SRCALPHA)
    shade.fill((2, 9, 16, 228))
    canvas.blit(shade, (0, 0))
    pygame.draw.line(canvas, theme.ACCENT_DIM, (529, 0), (529, canvas.get_height()), 1)
    scan = (clock_ms // 18) % canvas.get_height()
    scan_layer = pygame.Surface((canvas.get_width() - 530, 3), pygame.SRCALPHA)
    scan_layer.fill((*theme.ACCENT, 20))
    canvas.blit(scan_layer, (530, scan))
    pygame.draw.rect(canvas, theme.ACCENT, (44, 36, 8, 8))
    _text(canvas, fonts.micro, "NEXUS RESEARCH  /  FACILITY A1", theme.ACCENT, (62, 32))
    _text(canvas, fonts.logo, "ECHO", theme.TEXT, (39, 83))
    _text(canvas, fonts.logo, "HEIST", theme.TEXT, (39, 149))
    pygame.draw.line(canvas, theme.ACCENT, (44, 229), (150, 229), 3)
    _text(canvas, fonts.small, "THE CORE REBELLION", theme.MUTED, (44, 247))
    pygame.draw.line(canvas, theme.BORDER, (44, 298), (494, 298), 1)
    _text(canvas, fonts.small, "STEAL THE CORE. SURVIVE THE LOCKDOWN.", theme.TEXT, (44, 315))
    _text(canvas, fonts.micro, "ONE SITE  /  TWO ROUTES  /  ONE WAY OUT", theme.MUTED, (44, 345))
    _text(canvas, fonts.micro, f"BUILD {__version__}", theme.MUTED, (1149, 692))
    _text(canvas, fonts.micro, "FACILITY VISUALIZATION  //  CORE CHAMBER", theme.ACCENT, (887, 32))


def _button(
    canvas: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    fonts: Fonts,
    *,
    selected: bool,
    enabled: bool,
    note: str = "",
) -> None:
    fill = (7, 45, 59, 228) if selected and enabled else (5, 18, 29, 215)
    panel(canvas, rect, fill=fill, border=theme.ACCENT if selected and enabled else theme.BORDER)
    if selected and enabled:
        pygame.draw.rect(canvas, theme.ACCENT, (rect.x, rect.y, 4, rect.h))
    color = theme.TEXT if enabled else theme.DISABLED
    _text(canvas, fonts.body, label, color, (rect.x + 21, rect.y + (11 if note else 19)))
    if note:
        _text(canvas, fonts.micro, note, theme.MUTED, (rect.x + 22, rect.y + 40))
    _text(canvas, fonts.body, ">" if enabled else "·", color, (rect.right - 32, rect.y + 16))


def draw_menu(
    canvas: pygame.Surface,
    fonts: Fonts,
    backdrop: pygame.Surface,
    portrait: pygame.Surface,
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
            )
        _text(canvas, fonts.small, "WASD / ARROWS  •  ENTER  •  MOUSE", theme.MUTED, (44, 600))
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
            )
        launch_enabled = MODE_ITEMS[selected].enabled
        _button(
            canvas,
            LAUNCH_BUTTON,
            "LAUNCH MISSION",
            fonts,
            selected=launch_enabled,
            enabled=launch_enabled,
        )
        if notice:
            _text(canvas, fonts.micro, notice, theme.WARNING, (44, 587))
        dossier = pygame.Rect(548, 395, 229, 278)
        panel(canvas, dossier, fill=(4, 14, 23, 218), border=theme.ACCENT_DIM)
        canvas.blit(portrait, (dossier.x + 2, dossier.y + 2))
        pygame.draw.rect(canvas, (3, 14, 23), (dossier.x + 1, dossier.bottom - 46, 227, 45))
        _text(canvas, fonts.micro, "HUMAN OPERATIVE  /  DOSSIER", theme.ACCENT, (559, 638))
    _text(canvas, fonts.micro, "ESC  BACK / QUIT", theme.MUTED, (46, 690))


def draw_results(
    canvas: pygame.Surface, end: MissionEnd, fonts: Fonts, *, ticks_per_second: int
) -> None:
    """Report only committed mission facts; final score/rank is a P06 rule."""
    seconds = end.elapsed_ticks // max(1, ticks_per_second)
    title, color, detail = {
        RunOutcome.WIN: ("MISSION COMPLETE", theme.ACCENT, "Core secured  /  operative extracted"),
        RunOutcome.CAPTURED: (
            "OPERATIVE CAPTURED",
            theme.DANGER,
            f"Intercepted by {end.capture_by or 'security'}",
        ),
        RunOutcome.ABORTED: ("MISSION ABORTED", theme.WARNING, "Operation ended by operative"),
    }[end.outcome]
    veil = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
    veil.fill((1, 8, 14, 120))
    canvas.blit(veil, (0, 0))
    if end.outcome == RunOutcome.CAPTURED:
        warning = pygame.Surface((620, canvas.get_height()), pygame.SRCALPHA)
        warning.fill((120, 10, 13, 45))
        canvas.blit(warning, (0, 0))
    card = pygame.Rect(620, 0, 660, canvas.get_height())
    panel(canvas, card, fill=(3, 12, 21, 244), border=theme.BORDER)
    _text(canvas, fonts.micro, "NEXUS RESEARCH  /  AFTER ACTION REPORT", color, (660, 55))
    pygame.draw.line(canvas, color, (660, 88), (1212, 88), 2)
    _text(canvas, fonts.logo, "ECHO HEIST", theme.TEXT, (655, 115))
    _text(canvas, fonts.small, "THE CORE REBELLION", theme.MUTED, (660, 187))
    _text(canvas, fonts.heading, title, color, (658, 249))
    _text(canvas, fonts.body, detail, theme.TEXT, (660, 304))
    pygame.draw.line(canvas, theme.BORDER, (660, 359), (1212, 359), 1)
    _text(canvas, fonts.micro, "MISSION TIME", theme.MUTED, (662, 383))
    _text(canvas, fonts.stat, f"{seconds // 60:02d}:{seconds % 60:02d}", theme.TEXT, (658, 410))
    _text(canvas, fonts.micro, f"{end.elapsed_ticks} SIMULATION TICKS", theme.MUTED, (662, 463))
    _text(canvas, fonts.micro, "SCORE / RANK UNLOCK IN PHASE 06", theme.WARNING, (662, 525))
    panel(canvas, RESULT_RETRY, fill=(5, 46, 56, 222), border=theme.ACCENT)
    _text(canvas, fonts.small, "R  RETRY SAME SEED", theme.ACCENT, (678, 605))
    panel(canvas, RESULT_MENU)
    _text(canvas, fonts.small, "ENTER  MAIN MENU", theme.TEXT, (678, 663))
    _text(canvas, fonts.micro, "ESC QUIT", theme.MUTED, (1127, 666))
