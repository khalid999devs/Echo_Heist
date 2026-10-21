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


TITLE_ITEMS = (
    MenuItem("PLAY CHAPTER"),
    MenuItem("MISSION REPORT"),
    MenuItem("SETTINGS"),
    MenuItem("QUIT"),
)
MODE_ITEMS = (
    MenuItem("HUMAN", note="Direct control. Tools and stealth."),
    MenuItem("COMPANION", enabled=False, note="Watch your AI infiltrate."),
    MenuItem("LAUNCH MISSION"),
    MenuItem("BACK"),
)
CHAPTER_CARD = pygame.Rect(44, 238, 456, 242)
TITLE_BUTTONS = (
    pygame.Rect(60, 417, 424, 46),
    pygame.Rect(44, 510, 160, 48),
    pygame.Rect(216, 510, 160, 48),
    pygame.Rect(388, 510, 112, 48),
)
LAUNCH_BUTTON = pygame.Rect(620, 548, 576, 54)
BACK_BUTTON = pygame.Rect(44, 650, 130, 42)
MODE_BUTTONS = (
    pygame.Rect(620, 212, 280, 114),
    pygame.Rect(916, 212, 280, 114),
    LAUNCH_BUTTON,
    BACK_BUTTON,
)
RESULT_RETRY = pygame.Rect(660, 590, 552, 48)
RESULT_MENU = pygame.Rect(660, 648, 552, 48)


def load_backdrop(
    size: tuple[int, int], path: str = "assets/scenes/title-facility.png"
) -> pygame.Surface:
    """Perspective 3D-rendered chamber artwork bundled with the game."""
    art = pygame.image.load(BytesIO(resource_bytes(path)), path)
    return pygame.transform.smoothscale(
        art, (size[0] + 2 * BACKDROP_PAD, size[1] + 2 * BACKDROP_PAD)
    )


def move_selection(index: int, items: tuple[MenuItem, ...], key: int) -> int:
    if key in (pygame.K_UP, pygame.K_LEFT, pygame.K_w, pygame.K_a):
        return (index - 1) % len(items)
    if key in (pygame.K_DOWN, pygame.K_RIGHT, pygame.K_s, pygame.K_d):
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


def _frame(
    canvas: pygame.Surface,
    backdrop: pygame.Surface,
    fonts: Fonts,
    clock_ms: int,
    reduced_motion: bool,
    *,
    briefing: bool,
) -> None:
    draw_scene(canvas, backdrop, clock_ms, reduced_motion=reduced_motion)
    _text(canvas, fonts.micro, "NEXUS RESEARCH  /  SITE A1", theme.ACCENT, (44, 35))
    _text(canvas, fonts.title, "ECHO HEIST", theme.TEXT, (40, 69))
    _text(
        canvas,
        fonts.small,
        "MISSION BRIEFING" if briefing else "THE CORE REBELLION",
        theme.MUTED,
        (44, 138),
    )
    if not briefing:
        _text(canvas, fonts.small, "Steal the Core. Survive the lockdown.", theme.TEXT, (44, 195))
        _text(canvas, fonts.micro, __version__, theme.MUTED, (1160, 692))


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
    face = fonts.small if rect.width < 200 else fonts.body
    top = rect.y + 11 if note else rect.centery - face.get_height() // 2
    _text(canvas, face, label, color, (rect.x + 16, top))
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


def _chapter_card(
    canvas: pygame.Surface, fonts: Fonts, backdrop: pygame.Surface, selected: int, clock_ms: int
) -> None:
    panel(canvas, CHAPTER_CARD, fill=(6, 20, 30, 224), border=theme.ACCENT_DIM)
    source = pygame.Rect(round(backdrop.get_width() * 0.59), 65, 450, 350)
    thumb = pygame.transform.smoothscale(backdrop.subsurface(source), (128, 128))
    canvas.blit(thumb, (60, 254))
    _text(canvas, fonts.micro, "CHAPTER 01", theme.ACCENT, (206, 258))
    _text(canvas, fonts.body, "The Core", theme.TEXT, (204, 282))
    _text(canvas, fonts.body, "Rebellion", theme.TEXT, (204, 309))
    _button(
        canvas,
        TITLE_BUTTONS[0],
        "PLAY CHAPTER",
        fonts,
        selected=selected == 0,
        enabled=True,
        clock_ms=clock_ms,
    )


def _route_diagram(canvas: pygame.Surface, fonts: Fonts) -> None:
    _text(canvas, fonts.micro, "01 / SERVICE", theme.MUTED, (620, 354))
    _text(canvas, fonts.micro, "02 / RESEARCH", theme.MUTED, (1028, 354))
    boxes = (
        ("ENTRY", pygame.Rect(620, 416, 92, 40)),
        ("SERVICE", pygame.Rect(732, 416, 100, 40)),
        ("SECURITY", pygame.Rect(858, 388, 132, 40)),
        ("RESEARCH", pygame.Rect(858, 452, 132, 40)),
        ("CORE", pygame.Rect(1028, 416, 168, 40)),
    )
    color = theme.ACCENT_DIM
    for points in (
        ((712, 436), (732, 436)),
        ((832, 436), (844, 436), (844, 408), (858, 408)),
        ((832, 436), (844, 436), (844, 472), (858, 472)),
        ((990, 408), (1008, 408), (1008, 436), (1028, 436)),
        ((990, 472), (1008, 472), (1008, 436)),
        ((924, 428), (924, 452)),
    ):
        pygame.draw.lines(canvas, color, False, points, 2)
    for label, rect in boxes:
        panel(canvas, rect, fill=(5, 23, 31, 225), border=color)
        text = fonts.micro.render(label, True, theme.TEXT)
        canvas.blit(text, text.get_rect(center=rect.center))
    _text(
        canvas,
        fonts.micro,
        "A  Security / exposed       B  Research / cover",
        theme.MUTED,
        (620, 510),
    )


def _briefing(
    canvas: pygame.Surface, fonts: Fonts, selected: int, mode_choice: int, clock_ms: int
) -> None:
    panel(canvas, pygame.Rect(44, 184, 520, 440), fill=(5, 18, 28, 227), border=theme.BORDER)
    _text(canvas, fonts.micro, "CHAPTER 01", theme.ACCENT, (64, 204))
    _text(canvas, fonts.heading, "The Core Rebellion", theme.TEXT, (62, 229))
    steps = (
        ("01  INFILTRATE", "Take either stairway to the upper floor."),
        ("02  RECOVER", "Hold E beside the experimental Core."),
        ("03  EXTRACT", "Escape lockdown. Return downstairs."),
    )
    for index, (label, description) in enumerate(steps):
        y = 323 + index * 67
        _text(canvas, fonts.micro, label, theme.ACCENT, (64, y))
        _text(canvas, fonts.small, description, theme.TEXT, (64, y + 23))
    pygame.draw.line(canvas, theme.BORDER, (64, 527), (544, 527))
    _text(
        canvas,
        fonts.micro,
        "WASD  Move    SHIFT  Sprint burst    E  Stairs / Core",
        theme.MUTED,
        (64, 546),
    )
    _text(
        canvas,
        fonts.micro,
        "Q  Echo    F  EMP    SPACE  Stun    TAB  Map",
        theme.MUTED,
        (64, 578),
    )
    panel(canvas, pygame.Rect(600, 184, 616, 440), fill=(5, 18, 28, 219), border=theme.BORDER)
    _text(canvas, fonts.micro, "PLAY MODE", theme.MUTED, (620, 187))
    for index, item in enumerate(MODE_ITEMS[:2]):
        rect = MODE_BUTTONS[index]
        chosen = index == mode_choice
        border = theme.ACCENT if chosen else theme.BORDER
        panel(canvas, rect, fill=(7, 34, 44, 220 if chosen else 150), border=border)
        pygame.draw.circle(canvas, border, (rect.x + 21, rect.y + 25), 6, 2)
        if chosen:
            pygame.draw.circle(canvas, theme.ACCENT, (rect.x + 21, rect.y + 25), 3)
        color = theme.TEXT if item.enabled else theme.DISABLED
        _text(canvas, fonts.small, item.label, color, (rect.x + 39, rect.y + 12))
        _text(
            canvas,
            fonts.micro,
            "DIRECT CONTROL" if chosen else "COMING LATER",
            border,
            (rect.x + 16, rect.y + 49),
        )
        if index == 0:
            _text(canvas, fonts.micro, "Tools and stealth", theme.MUTED, (rect.x + 16, rect.y + 78))
        if selected == index:
            pygame.draw.rect(canvas, theme.TEXT, rect.inflate(-6, -6), 1, border_radius=4)
    _route_diagram(canvas, fonts)
    _button(
        canvas,
        LAUNCH_BUTTON,
        "LAUNCH MISSION",
        fonts,
        selected=selected == 2,
        enabled=MODE_ITEMS[mode_choice].enabled,
        clock_ms=clock_ms,
    )
    _button(
        canvas, BACK_BUTTON, "BACK", fonts, selected=selected == 3, enabled=True, clock_ms=clock_ms
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
    reduced_motion: bool = False,
    mode_choice: int = 0,
    report_available: bool = False,
) -> None:
    briefing = scene == "MODE"
    _frame(canvas, backdrop, fonts, clock_ms, reduced_motion, briefing=briefing)
    if not briefing:
        _chapter_card(canvas, fonts, backdrop, selected, clock_ms)
        for index, label in enumerate(("REPORT", "SETTINGS", "QUIT"), 1):
            _button(
                canvas,
                TITLE_BUTTONS[index],
                label,
                fonts,
                selected=selected == index,
                enabled=index != 1 or report_available,
                clock_ms=clock_ms,
            )
        message = notice or (
            "Finish a mission to unlock its report."
            if selected == 1 and not report_available
            else ""
        )
        if message:
            _text(canvas, fonts.micro, message, theme.WARNING if notice else theme.MUTED, (44, 612))
        _text(
            canvas,
            fonts.micro,
            "ARROWS  Select    ENTER  Confirm    ESC  Quit",
            theme.MUTED,
            (44, 674),
        )
    else:
        _briefing(canvas, fonts, selected, mode_choice, clock_ms)
        if notice:
            panel(canvas, pygame.Rect(600, 640, 616, 32), fill=(5, 18, 28, 240))
            _text(canvas, fonts.micro, notice, theme.WARNING, (612, 647))
        panel(canvas, pygame.Rect(600, 676, 610, 23), fill=(5, 18, 28, 220))
        _text(
            canvas,
            fonts.micro,
            "ENTER  Confirm    ARROWS  Select    ESC  Back",
            theme.MUTED,
            (600, 680),
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
    color = {
        RunOutcome.WIN: theme.ACCENT,
        RunOutcome.CAPTURED: theme.DANGER,
        RunOutcome.ABORTED: theme.WARNING,
    }[end.outcome]
    if end.outcome == RunOutcome.CAPTURED:
        warning = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
        warning.fill((75, 8, 10, 28))
        canvas.blit(warning, (0, 0))
    _text(canvas, fonts.micro, "CHAPTER 01  /  MISSION REPORT", color, (660, 115))
    pygame.draw.line(canvas, color, (660, 148), (1212, 148), 2)
    headline = {
        RunOutcome.WIN: ("CORE", "EXTRACTED"),
        RunOutcome.CAPTURED: ("OPERATIVE", "CAPTURED"),
        RunOutcome.ABORTED: ("MISSION", "ABORTED"),
    }[end.outcome]
    _text(canvas, fonts.title, headline[0], theme.TEXT, (655, 185))
    _text(canvas, fonts.title, headline[1], color, (655, 246))
    pygame.draw.line(canvas, theme.BORDER, (660, 359), (1212, 359), 1)
    _text(canvas, fonts.micro, "MISSION TIME", theme.MUTED, (662, 383))
    _text(canvas, fonts.stat, f"{seconds // 60:02d}:{seconds % 60:02d}", theme.TEXT, (658, 410))
    objective = "RECOVERED" if end.outcome == RunOutcome.WIN else "NOT EXTRACTED"
    _text(canvas, fonts.micro, "CORE STATUS", theme.MUTED, (960, 383))
    _text(canvas, fonts.body, objective, color, (958, 424))
    _text(
        canvas,
        fonts.small,
        "The core is safe. You made it out."
        if end.outcome == RunOutcome.WIN
        else "Break line of sight. Choose another route."
        if end.outcome == RunOutcome.CAPTURED
        else "Ready when you are.",
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
