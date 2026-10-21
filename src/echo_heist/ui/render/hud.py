"""Compact mission overlays; all counters come from committed observations."""

from math import atan2, cos, sin

import pygame

from echo_heist.core.contracts.security.model import GuardState, GuardView
from echo_heist.core.contracts.world import MissionPhase, Tile
from echo_heist.level.model import LevelData
from echo_heist.ui.presenters.objective import ObjectiveView
from echo_heist.ui.render import theme
from echo_heist.ui.render.surfaces.glass import panel as panel
from echo_heist.ui.render.theme import Color, Fonts


def _label(
    canvas: pygame.Surface, font: pygame.font.Font, value: str, color: Color, pos: tuple[int, int]
) -> None:
    canvas.blit(font.render(value, True, color), pos)


def draw_minimap(
    canvas: pygame.Surface,
    level: LevelData,
    operative_tile: Tile,
    phase: MissionPhase,
    fonts: Fonts,
) -> None:
    rect = pygame.Rect(20, canvas.get_height() - 162, 196, 142)
    panel(canvas, rect, fill=(5, 15, 25, 170))
    _label(canvas, fonts.micro, "FACILITY A1", theme.ACCENT, (32, rect.y + 9))
    width, height = level.static_map.width, level.static_map.height
    scale = min(172 / width, 80 / height)
    origin = rect.x + 12, rect.y + 33
    for y in range(height):
        for x in range(width):
            if level.static_map.can_walk((x, y)):
                pygame.draw.rect(
                    canvas,
                    (55, 86, 96),
                    (
                        round(origin[0] + x * scale),
                        round(origin[1] + y * scale),
                        max(1, round(scale)),
                        max(1, round(scale)),
                    ),
                )
    anchors = {obj.object_id: obj.tile for obj in level.static_map.objects}
    markers = [(anchors[level.exit_id], theme.ACCENT), (operative_tile, theme.TEXT)]
    if phase == MissionPhase.INFILTRATE:
        markers.append((anchors[level.core_id], theme.WARNING))
    for tile, color in markers:
        pygame.draw.circle(
            canvas,
            color,
            (
                round(origin[0] + (tile[0] + 0.5) * scale),
                round(origin[1] + (tile[1] + 0.5) * scale),
            ),
            3,
        )
    _label(canvas, fonts.micro, "TAB  Route / controls", theme.MUTED, (32, rect.bottom - 24))


def _objective(
    canvas: pygame.Surface,
    view: ObjectiveView,
    zone_label: str,
    level: LevelData,
    operative_tile: Tile,
    phase: MissionPhase,
    fonts: Fonts,
) -> None:
    rect = pygame.Rect(20, 20, 400, 72)
    color = theme.ACCENT if view.core_held else theme.WARNING
    panel(canvas, rect, border=color, fill=(5, 15, 25, 180))
    _label(canvas, fonts.micro, zone_label.upper(), theme.MUTED, (83, 30))
    _label(
        canvas,
        fonts.body,
        "Escape to Extraction" if view.core_held else "Reach the Core",
        theme.TEXT,
        (83, 52),
    )
    anchors = {obj.object_id: obj.tile for obj in level.static_map.objects}
    target = anchors[level.exit_id if view.core_held else level.core_id]
    angle = atan2(target[1] - operative_tile[1], target[0] - operative_tile[0])
    center = 51, 56
    pygame.draw.circle(canvas, color, center, 19, 1)
    points = [
        (round(center[0] + r * cos(angle + a)), round(center[1] + r * sin(angle + a)))
        for r, a in ((12, 0), (9, 2.5), (4, 3.14), (9, -2.5))
    ]
    pygame.draw.polygon(canvas, color, points)
    prompt = view.warning or ("Hold E to recover Core" if view.interaction else "")
    if prompt:
        panel(
            canvas,
            pygame.Rect(20, 102, 400, 38),
            border=theme.DANGER if view.warning else theme.WARNING,
        )
        _label(
            canvas, fonts.micro, prompt, theme.DANGER if view.warning else theme.WARNING, (34, 114)
        )
    if view.interaction_progress is not None:
        done, total = view.interaction_progress
        pygame.draw.rect(
            canvas, theme.WARNING, (22, 138, round(396 * min(done, total) / max(1, total)), 3)
        )


def draw_hud(
    canvas: pygame.Surface,
    view: ObjectiveView,
    zone_label: str,
    fonts: Fonts,
    *,
    level: LevelData,
    operative_tile: Tile,
    phase: MissionPhase,
    clock_ms: int = 0,
    notice: str = "",
    guards: tuple[GuardView, ...] = (),
    unavailable_guards: frozenset[str] = frozenset(),
) -> None:
    _objective(canvas, view, zone_label, level, operative_tile, phase, fonts)
    status = pygame.Rect(canvas.get_width() - 236, 20, 216, 72)
    panel(canvas, status, fill=(5, 15, 25, 180))
    states = {guard.state for guard in guards if guard.actor_id not in unavailable_guards}
    alert = (
        "DETECTED"
        if GuardState.CHASE in states
        else "SUSPICIOUS"
        if GuardState.SPOTTED in states
        else "SEARCHING"
        if GuardState.SEARCH in states or GuardState.INVESTIGATE in states
        else "DISRUPTED"
        if guards and not states
        else "PATROL"
    )
    color = (
        theme.DANGER
        if alert == "DETECTED"
        else theme.WARNING
        if alert != "PATROL"
        else theme.ACCENT
    )
    _label(
        canvas,
        fonts.micro,
        "LOCKDOWN" if phase == MissionPhase.LOCKDOWN else "INFILTRATION",
        theme.DANGER if phase == MissionPhase.LOCKDOWN else theme.MUTED,
        (status.x + 13, 31),
    )
    _label(canvas, fonts.body, view.elapsed, theme.TEXT, (status.x + 13, 54))
    _label(canvas, fonts.micro, alert, color, (status.x + 98, 62))
    draw_minimap(canvas, level, operative_tile, phase, fonts)
    for index, (key, name, count) in enumerate(
        (
            ("Q", "ECHO", str(view.echo_charges)),
            ("F", "EMP", str(view.emp_charges)),
            ("SPACE", "STUN", "CLOSE"),
        )
    ):
        left = canvas.get_width() - 372 + index * 118
        rect = pygame.Rect(left, canvas.get_height() - 94, 110, 74)
        color = theme.DISABLED if count == "0" else theme.ACCENT
        panel(canvas, rect, fill=(5, 15, 25, 175), border=theme.BORDER)
        _label(canvas, fonts.micro, key, color, (left + 10, rect.y + 9))
        _label(canvas, fonts.small, name, theme.TEXT, (left + 10, rect.y + 29))
        _label(canvas, fonts.micro, count, color, (left + 10, rect.y + 53))
    if notice:
        width = min(620, fonts.small.size(notice)[0] + 30)
        banner = pygame.Rect(0, canvas.get_height() - 144, width, 36)
        banner.centerx = canvas.get_width() // 2
        panel(canvas, banner, border=theme.WARNING)
        _label(canvas, fonts.small, notice, theme.TEXT, (banner.x + 15, banner.y + 8))
    elif clock_ms < 7_000:
        hint = "WASD  Move     SHIFT  Sprint     ESC  Pause"
        _label(
            canvas,
            fonts.micro,
            hint,
            theme.MUTED,
            (canvas.get_width() // 2 - fonts.micro.size(hint)[0] // 2, canvas.get_height() - 35),
        )


def draw_dialog(
    canvas: pygame.Surface,
    title: str,
    lines: tuple[tuple[str, Color], ...],
    fonts: Fonts,
    *,
    title_color: Color = theme.TEXT,
) -> None:
    height = 108 + 36 * len(lines)
    rect = pygame.Rect(0, 0, 660, height)
    rect.center = canvas.get_rect().center
    small = pygame.transform.smoothscale(canvas, (160, 90))
    canvas.blit(pygame.transform.smoothscale(small, canvas.get_size()), (0, 0))
    shade = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
    shade.fill((1, 7, 13, 125))
    canvas.blit(shade, (0, 0))
    panel(canvas, rect, fill=(5, 17, 27, 220), border=title_color)
    pygame.draw.line(
        canvas, title_color, (rect.left, rect.top + 16), (rect.left, rect.bottom - 16), 3
    )
    heading = fonts.heading.render(title, True, title_color)
    canvas.blit(heading, (rect.centerx - heading.get_width() // 2, rect.top + 22))
    for index, (value, color) in enumerate(lines):
        line = fonts.body.render(value, True, color)
        canvas.blit(line, (rect.centerx - line.get_width() // 2, rect.top + 81 + index * 36))
