"""Static menu, mode-select and results screens; outcomes come from MissionEnd only."""

from dataclasses import dataclass

import pygame

from echo_heist import __version__
from echo_heist.core.contracts.results import MissionEnd, RunOutcome
from echo_heist.ui.render import theme
from echo_heist.ui.render.hud import draw_dialog, panel
from echo_heist.ui.render.theme import Fonts


@dataclass(frozen=True, slots=True)
class MenuItem:
    label: str
    enabled: bool = True
    note: str = ""


TITLE_ITEMS = (MenuItem("Start heist"), MenuItem("Quit"))
MODE_ITEMS = (
    MenuItem("Human operative", note="You control the operative directly"),
    MenuItem("Companion operative", enabled=False, note="In development until Phase 04"),
)


def move_selection(index: int, items: tuple[MenuItem, ...], key: int) -> int:
    if key in (pygame.K_UP, pygame.K_w):
        return (index - 1) % len(items)
    if key in (pygame.K_DOWN, pygame.K_s):
        return (index + 1) % len(items)
    return index


def draw_menu(
    canvas: pygame.Surface,
    fonts: Fonts,
    *,
    heading: str,
    items: tuple[MenuItem, ...],
    selected: int,
    notice: str,
    footer: str,
) -> None:
    canvas.fill(theme.BACKGROUND)
    canvas.blit(fonts.small.render("DEVELOPMENT BUILD / PHASE 02", True, theme.ACCENT), (80, 92))
    canvas.blit(fonts.title.render("ECHO HEIST", True, theme.TEXT), (76, 120))
    pygame.draw.line(canvas, theme.ACCENT, (80, 196), (1200, 196), 2)
    canvas.blit(fonts.heading.render(heading, True, theme.MUTED), (80, 232))
    for index, item in enumerate(items):
        top = 300 + index * 66
        if index == selected:
            panel(canvas, pygame.Rect(70, top - 10, 620, 56))
        color = theme.TEXT if item.enabled else theme.DISABLED
        prefix = "> " if index == selected else "  "
        canvas.blit(fonts.heading.render(prefix + item.label, True, color), (84, top))
        if item.note:
            note_color = theme.MUTED if item.enabled else theme.WARNING
            canvas.blit(fonts.small.render(item.note, True, note_color), (720, top + 10))
    if notice:
        canvas.blit(fonts.body.render(notice, True, theme.WARNING), (80, 520))
    canvas.blit(fonts.small.render(footer, True, theme.MUTED), (80, 646))
    canvas.blit(fonts.small.render(f"v{__version__}", True, theme.MUTED), (1120, 646))


def draw_results(
    canvas: pygame.Surface, end: MissionEnd, fonts: Fonts, *, ticks_per_second: int
) -> None:
    seconds = end.elapsed_ticks // max(1, ticks_per_second)
    elapsed = f"Time {seconds // 60:02d}:{seconds % 60:02d}  ({end.elapsed_ticks} ticks)"
    title, color, detail = {
        RunOutcome.WIN: ("CORE EXTRACTED", theme.ACCENT, "The operative escaped with the core."),
        RunOutcome.CAPTURED: (
            "CAPTURED",
            theme.DANGER,
            f"Captured by {end.capture_by or 'a guard'}.",
        ),
        RunOutcome.ABORTED: ("RUN ABORTED", theme.WARNING, "Aborted runs are unsuccessful."),
    }[end.outcome]
    lines = (
        (detail, theme.TEXT),
        (elapsed, theme.MUTED),
        ("Score and rank arrive with Phase 06 scoring", theme.MUTED),
        ("R: retry same seed    Enter: main menu    Esc: quit", theme.TEXT),
    )
    draw_dialog(canvas, title, lines, fonts, title_color=color)
