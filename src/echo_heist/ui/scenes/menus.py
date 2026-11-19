"""Cinematic front door and unscored mission outcome presentation."""

from dataclasses import dataclass
from io import BytesIO
from math import sin

import pygame

from echo_heist import __version__
from echo_heist.core.contracts.autonomy.model import ProtocolState
from echo_heist.infrastructure.resources import resource_bytes
from echo_heist.ui.render import theme
from echo_heist.ui.render.hud import panel
from echo_heist.ui.render.layout.text import fit, lines
from echo_heist.ui.render.surfaces.cinematic import BACKDROP_PAD, draw_scene
from echo_heist.ui.render.theme import Fonts
from echo_heist.ui.scenes.experience.report import (
    RESULT_MENU as RESULT_MENU,
)
from echo_heist.ui.scenes.experience.report import (
    RESULT_RETRY as RESULT_RETRY,
)
from echo_heist.ui.scenes.experience.report import (
    RESULT_STORY as RESULT_STORY,
)
from echo_heist.ui.scenes.experience.report import (
    draw_results as draw_results,
)


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
    MenuItem("FIELD GUIDE"),
)
MODE_ITEMS = (
    MenuItem("HUMAN", note="Direct control. Tools and stealth."),
    MenuItem("COMPANION", note="Configure your AI companion."),
    MenuItem("LAUNCH MISSION"),
    MenuItem("BACK"),
)
CHAPTER_CARD = pygame.Rect(44, 238, 456, 242)
TITLE_BUTTONS = (
    pygame.Rect(60, 417, 424, 46),
    pygame.Rect(44, 510, 160, 48),
    pygame.Rect(216, 510, 160, 48),
    pygame.Rect(388, 510, 112, 48),
    pygame.Rect(44, 576, 456, 48),
)
LAUNCH_BUTTON = pygame.Rect(620, 548, 576, 54)
BACK_BUTTON = pygame.Rect(44, 650, 130, 42)
MODE_BUTTONS = (
    pygame.Rect(620, 236, 280, 104),
    pygame.Rect(916, 236, 280, 104),
    LAUNCH_BUTTON,
    BACK_BUTTON,
)


def load_backdrop(
    size: tuple[int, int], path: str = "assets/scenes/title-facility.png"
) -> pygame.Surface:
    """Perspective 3D-rendered chamber artwork bundled with the game."""
    art = pygame.image.load(BytesIO(resource_bytes(path)), path)
    target = size[0] + 2 * BACKDROP_PAD, size[1] + 2 * BACKDROP_PAD
    scale = max(target[0] / art.get_width(), target[1] / art.get_height())
    fitted = pygame.transform.smoothscale(
        art, (round(art.get_width() * scale), round(art.get_height() * scale))
    )
    return fitted.subsurface(
        fitted.get_rect().inflate(target[0] - fitted.get_width(), target[1] - fitted.get_height())
    ).copy()


def move_selection(index: int, items: tuple[MenuItem, ...], key: int) -> int:
    if key in (pygame.K_UP, pygame.K_LEFT, pygame.K_w, pygame.K_a):
        return (index - 1) % len(items)
    if key in (pygame.K_DOWN, pygame.K_RIGHT, pygame.K_s, pygame.K_d):
        return (index + 1) % len(items)
    return index


def menu_hit(scene: str, pos: tuple[int, int]) -> int | None:
    if scene == "TITLE" and CHAPTER_CARD.collidepoint(pos):
        return 0
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
    paint_background: bool = True,
    control_hints: tuple[str, str, str] = (
        "E",
        "W/A/S/D Move  C Crouch  SHIFT Sprint",
        "Q Echo  F EMP  SPACE Stun",
    ),
) -> None:
    if paint_background:
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
    canvas: pygame.Surface,
    fonts: Fonts,
    selected: int,
    mode_choice: int,
    clock_ms: int,
    companion_available: bool = False,
    protocols: ProtocolState | None = None,
    control_hints: tuple[str, str, str] = (
        "E",
        "W/A/S/D Move  C Crouch  SHIFT Sprint",
        "Q Echo  F EMP  SPACE Stun",
    ),
) -> None:
    panel(canvas, pygame.Rect(44, 184, 520, 440), fill=(5, 18, 28, 227), border=theme.BORDER)
    _text(canvas, fonts.micro, "CHAPTER 01", theme.ACCENT, (64, 204))
    _text(canvas, fonts.heading, "The Core Rebellion", theme.TEXT, (62, 229))
    steps = (
        ("01  INFILTRATE", "Take either stairway to the upper floor."),
        ("02  RECOVER", f"Hold {control_hints[0]} beside the experimental Core."),
        ("03  EXTRACT", "Return downstairs to the entry or cargo exit."),
    )
    for index, (label, description) in enumerate(steps):
        y = 323 + index * 67
        _text(canvas, fonts.micro, label, theme.ACCENT, (64, y))
        _text(canvas, fonts.small, fit(fonts.small, description, 480), theme.TEXT, (64, y + 23))
    pygame.draw.line(canvas, theme.BORDER, (64, 527), (544, 527))
    if protocols is not None and protocols.active is not None:
        active = protocols.active
        _text(
            canvas,
            fonts.micro,
            fit(fonts.micro, "NEXUS / " + active.label, 480),
            theme.WARNING,
            (64, 544),
        )
        for index, line in enumerate(lines(fonts.micro, active.reason, 480, 2)):
            _text(canvas, fonts.micro, line, theme.MUTED, (64, 568 + index * 20))
    else:
        _text(
            canvas,
            fonts.micro,
            fit(fonts.micro, control_hints[1], 480),
            theme.MUTED,
            (64, 546),
        )
        _text(
            canvas,
            fonts.micro,
            fit(fonts.micro, control_hints[2] + "  TAB Map", 480),
            theme.MUTED,
            (64, 578),
        )
    panel(canvas, pygame.Rect(600, 184, 616, 440), fill=(5, 18, 28, 219), border=theme.BORDER)
    _text(canvas, fonts.micro, "PLAY MODE", theme.MUTED, (620, 204))
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
            "DIRECT CONTROL"
            if index == 0
            else "AI CONTROL"
            if companion_available
            else "PREPARATION",
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
        "CONFIGURE COMPANION" if mode_choice else "LAUNCH MISSION",
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
    companion_available: bool = False,
    protocols: ProtocolState | None = None,
    paint_background: bool = True,
    control_hints: tuple[str, str, str] = (
        "E",
        "W/A/S/D Move  C Crouch  SHIFT Sprint",
        "Q Echo  F EMP  SPACE Stun",
    ),
) -> None:
    briefing = scene == "MODE"
    _frame(
        canvas,
        backdrop,
        fonts,
        clock_ms,
        reduced_motion,
        briefing=briefing,
        paint_background=paint_background,
    )
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
        _button(
            canvas,
            TITLE_BUTTONS[4],
            "FIELD GUIDE",
            fonts,
            selected=selected == 4,
            enabled=True,
            clock_ms=clock_ms,
        )
        message = notice or (
            "Finish a mission to unlock its report."
            if selected == 1 and not report_available
            else ""
        )
        if message:
            _text(canvas, fonts.micro, message, theme.WARNING if notice else theme.MUTED, (44, 638))
        _text(
            canvas,
            fonts.micro,
            "ARROWS  Select    ENTER  Confirm    ESC  Quit",
            theme.MUTED,
            (44, 674),
        )
    else:
        _briefing(
            canvas,
            fonts,
            selected,
            mode_choice,
            clock_ms,
            companion_available,
            protocols,
            control_hints,
        )
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
