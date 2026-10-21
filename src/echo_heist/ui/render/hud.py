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
    rect = pygame.Rect(20, canvas.get_height() - 202, 172, 182)
    panel(canvas, rect, fill=(5, 15, 25, 170))
    deck = level.deck_at(operative_tile)
    left, top = (deck.left, deck.top) if deck else (0, 0)
    width, height = (
        (deck.width, deck.height) if deck else (level.static_map.width, level.static_map.height)
    )
    _label(
        canvas,
        fonts.micro,
        "FLOOR 01" if deck and deck.deck_id == "ground" else "FLOOR 02" if deck else "FACILITY A1",
        theme.ACCENT,
        (32, rect.y + 9),
    )
    scale = min(148 / width, 120 / height)
    origin = rect.centerx - width * scale / 2, rect.y + 33
    for y in range(top, top + height):
        for x in range(left, left + width):
            if level.static_map.can_walk((x, y)):
                pygame.draw.rect(
                    canvas,
                    (55, 86, 96),
                    (
                        round(origin[0] + (x - left) * scale),
                        round(origin[1] + (y - top) * scale),
                        max(1, round(scale)),
                        max(1, round(scale)),
                    ),
                )
    anchors = {obj.object_id: obj.tile for obj in level.static_map.objects}
    markers = [(anchors[level.exit_id], theme.ACCENT), (operative_tile, theme.TEXT)]
    if phase == MissionPhase.INFILTRATE:
        markers.append((anchors[level.core_id], theme.WARNING))
    for tile, color in markers:
        if deck and not deck.contains(tile):
            continue
        pygame.draw.circle(
            canvas,
            color,
            (
                round(origin[0] + (tile[0] - left + 0.5) * scale),
                round(origin[1] + (tile[1] - top + 0.5) * scale),
            ),
            3,
        )
    for link in level.static_map.stairs:
        if deck and deck.contains(link.tile):
            point = (
                round(origin[0] + (link.tile[0] - left + 0.5) * scale),
                round(origin[1] + (link.tile[1] - top + 0.5) * scale),
            )
            pygame.draw.rect(canvas, theme.ACCENT, (*point, 4, 4), 1)
    _label(canvas, fonts.micro, "TAB  Map", theme.MUTED, (32, rect.bottom - 24))


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
    deck = level.deck_at(operative_tile)
    if deck and not deck.contains(target):
        links = [link for link in level.static_map.stairs if deck.contains(link.tile)]
        if links:
            target = min(
                links,
                key=lambda link: (
                    abs(link.tile[0] - operative_tile[0]) + abs(link.tile[1] - operative_tile[1])
                ),
            ).tile
    angle = atan2(target[1] - operative_tile[1], target[0] - operative_tile[0])
    center = 51, 56
    pygame.draw.circle(canvas, color, center, 19, 1)
    points = [
        (round(center[0] + r * cos(angle + a)), round(center[1] + r * sin(angle + a)))
        for r, a in ((12, 0), (9, 2.5), (4, 3.14), (9, -2.5))
    ]
    pygame.draw.polygon(canvas, color, points)
    prompt = view.warning or view.interaction
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
    sprint_duration_ticks: int = 90,
    sprint_recharge_ticks: int = 120,
    ticks_per_second: int = 30,
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
    boost = pygame.Rect(canvas.get_width() - 372, canvas.get_height() - 140, 346, 34)
    panel(canvas, boost, fill=(5, 15, 25, 175), border=theme.BORDER)
    recharge = view.sprint_recharge_remaining
    fraction = (
        (1 - recharge / max(1, sprint_recharge_ticks))
        if recharge
        else view.sprint_ticks_remaining / max(1, sprint_duration_ticks)
    )
    label = f"READY IN  {recharge / max(1, ticks_per_second):.1f}s" if recharge else "SHIFT  Sprint"
    _label(
        canvas,
        fonts.micro,
        label,
        theme.MUTED if recharge else theme.ACCENT,
        (boost.x + 10, boost.y + 7),
    )
    pygame.draw.rect(canvas, theme.BORDER, (boost.x + 158, boost.y + 14, 174, 4), border_radius=2)
    pygame.draw.rect(
        canvas,
        theme.MUTED if recharge else theme.ACCENT,
        (boost.x + 158, boost.y + 14, round(174 * max(0, min(1, fraction))), 4),
        border_radius=2,
    )
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
        banner = pygame.Rect(0, canvas.get_height() - 194, width, 36)
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
