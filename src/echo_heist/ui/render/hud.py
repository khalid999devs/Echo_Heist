"""Mission overlays derived from observations and static map data."""

from math import atan2, cos, sin

import pygame

from echo_heist.core.contracts.world import MissionPhase, Tile
from echo_heist.level.model import LevelData
from echo_heist.ui.presenters.objective import ObjectiveView
from echo_heist.ui.render import theme
from echo_heist.ui.render.theme import Color, Fonts

CONTROLS = "WASD MOVE    SHIFT SPRINT    E CORE    Q ECHO    F EMP    SPACE MELEE    TAB GUIDE"


def panel(
    canvas: pygame.Surface,
    rect: pygame.Rect,
    *,
    fill: tuple[int, int, int, int] = theme.PANEL,
    border: Color = theme.BORDER,
) -> None:
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    layer.fill(fill)
    canvas.blit(layer, rect.topleft)
    pygame.draw.rect(canvas, border, rect, 1, border_radius=7)
    pygame.draw.line(canvas, border, (rect.x + 10, rect.y), (rect.x + 29, rect.y), 2)
    pygame.draw.line(
        canvas, border, (rect.right - 29, rect.bottom - 1), (rect.right - 10, rect.bottom - 1), 2
    )


def _label(
    canvas: pygame.Surface,
    font: pygame.font.Font,
    value: str,
    color: Color,
    pos: tuple[int, int],
) -> None:
    canvas.blit(font.render(value, True, color), pos)


def draw_minimap(
    canvas: pygame.Surface,
    level: LevelData,
    operative_tile: Tile,
    phase: MissionPhase,
    fonts: Fonts,
) -> None:
    rect = pygame.Rect(20, canvas.get_height() - 216, 244, 195)
    panel(canvas, rect)
    _label(canvas, fonts.micro, "FACILITY A1 / ROUTE", theme.ACCENT, (32, rect.y + 13))
    width, height = level.static_map.width, level.static_map.height
    scale = min(216 / width, 112 / height)
    start_x = rect.x + 16
    start_y = rect.y + 39
    map_view = pygame.Surface((round(width * scale), round(height * scale)))
    map_view.fill((5, 15, 24))
    for y in range(height):
        for x in range(width):
            tile = (x, y)
            if level.static_map.can_walk(tile):
                zone = level.zone_at(tile)
                color = (
                    theme.ZONE_FLOORS.get(zone.zone_id, theme.CORRIDOR_FLOOR)
                    if zone
                    else theme.CORRIDOR_FLOOR
                )
                pygame.draw.rect(
                    map_view,
                    color,
                    (int(x * scale), int(y * scale), max(1, int(scale)), max(1, int(scale))),
                )
    anchors = {obj.object_id: obj.tile for obj in level.static_map.objects}
    core_color = theme.WARNING if phase == MissionPhase.INFILTRATE else theme.DANGER
    for tile, color in (
        (anchors[level.exit_id], theme.ACCENT),
        (anchors[level.core_id], core_color),
        (operative_tile, theme.TEXT),
    ):
        pygame.draw.circle(
            map_view,
            color,
            (int((tile[0] + 0.5) * scale), int((tile[1] + 0.5) * scale)),
            4,
        )
    canvas.blit(map_view, (start_x, start_y))
    for index, (name, color) in enumerate(
        (("YOU", theme.TEXT), ("CORE", core_color), ("EXIT", theme.ACCENT))
    ):
        left = rect.x + 17 + index * 74
        pygame.draw.circle(canvas, color, (left, rect.bottom - 21), 4)
        _label(canvas, fonts.micro, name, theme.MUTED, (left + 9, rect.bottom - 29))


def _waypoint(
    canvas: pygame.Surface,
    level: LevelData,
    operative_tile: Tile,
    phase: MissionPhase,
    fonts: Fonts,
) -> None:
    core = phase == MissionPhase.INFILTRATE
    anchors = {obj.object_id: obj.tile for obj in level.static_map.objects}
    target = anchors[level.core_id if core else level.exit_id]
    dx, dy = target[0] - operative_tile[0], target[1] - operative_tile[1]
    color = theme.WARNING if core else theme.ACCENT
    rect = pygame.Rect(446, 20, 532, 75)
    panel(canvas, rect, fill=(6, 20, 31, 232), border=color)
    center = rect.x + 34, rect.y + 37
    pygame.draw.circle(canvas, color, center, 21, 2)
    if dx or dy:
        angle = atan2(dy, dx)
        tip = (round(center[0] + 14 * cos(angle)), round(center[1] + 14 * sin(angle)))
        base = (round(center[0] - 6 * cos(angle)), round(center[1] - 6 * sin(angle)))
        pygame.draw.line(canvas, color, base, tip, 3)
        pygame.draw.polygon(
            canvas,
            color,
            (
                tip,
                (round(tip[0] - 7 * cos(angle - 0.6)), round(tip[1] - 7 * sin(angle - 0.6))),
                (round(tip[0] - 7 * cos(angle + 0.6)), round(tip[1] - 7 * sin(angle + 0.6))),
            ),
        )
    else:
        pygame.draw.circle(canvas, color, center, 6)
    _label(
        canvas,
        fonts.micro,
        "CURRENT TARGET  /  " + ("01" if core else "02"),
        color,
        (rect.x + 70, rect.y + 12),
    )
    _label(
        canvas,
        fonts.body,
        "TAKE THE CORE" if core else "REACH EXTRACTION",
        theme.TEXT,
        (rect.x + 70, rect.y + 34),
    )


def _first_run_help(canvas: pygame.Surface, fonts: Fonts) -> None:
    rect = pygame.Rect(canvas.get_width() - 282, 169, 262, 141)
    panel(canvas, rect, fill=(4, 17, 28, 236), border=theme.ACCENT_DIM)
    _label(canvas, fonts.micro, "QUICK START", theme.ACCENT, (rect.x + 14, rect.y + 11))
    _label(canvas, fonts.small, "WASD  Move", theme.TEXT, (rect.x + 14, rect.y + 35))
    _label(canvas, fonts.small, "SHIFT  Sprint", theme.TEXT, (rect.x + 14, rect.y + 63))
    _label(canvas, fonts.small, "E  Hold near the Core", theme.WARNING, (rect.x + 14, rect.y + 91))
    _label(
        canvas,
        fonts.micro,
        "TAB  Open route and controls",
        theme.MUTED,
        (rect.x + 14, rect.y + 119),
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
) -> None:
    panel(canvas, pygame.Rect(20, 20, 407, 137))
    pygame.draw.rect(canvas, theme.ACCENT, (20, 20, 5, 137))
    _label(canvas, fonts.micro, f"MISSION / {zone_label.upper()}", theme.ACCENT, (37, 34))
    _label(canvas, fonts.body, view.objective, theme.TEXT, (37, 60))
    pygame.draw.line(canvas, theme.BORDER, (37, 95), (409, 95), 1)
    default_prompt = (
        "Carry the core to the original entry lift."
        if phase == MissionPhase.LOCKDOWN
        else "Locate the core and hold E to take it."
    )
    prompt = view.warning or view.interaction or default_prompt
    color = theme.DANGER if view.warning else theme.WARNING if view.interaction else theme.MUTED
    _label(canvas, fonts.small, prompt, color, (37, 107))
    if view.interaction_progress is not None:
        done, total = view.interaction_progress
        interaction = pygame.Rect(20, 168, 407, 47)
        panel(canvas, interaction, fill=(26, 21, 8, 236), border=theme.WARNING)
        _label(
            canvas,
            fonts.micro,
            "CORE LINK  /  HOLD E",
            theme.WARNING,
            (interaction.x + 14, interaction.y + 8),
        )
        track = pygame.Rect(interaction.x + 182, interaction.y + 15, 209, 10)
        pygame.draw.rect(canvas, (42, 49, 45), track, border_radius=4)
        pygame.draw.rect(
            canvas,
            theme.WARNING,
            (track.x, track.y, round(track.w * min(done, total) / max(1, total)), track.h),
            border_radius=4,
        )
    status = pygame.Rect(canvas.get_width() - 282, 20, 262, 137)
    panel(canvas, status)
    _label(canvas, fonts.micro, "MISSION TIME", theme.ACCENT, (status.x + 15, 32))
    _label(canvas, fonts.heading, view.elapsed, theme.TEXT, (status.x + 15, 52))
    pygame.draw.line(canvas, theme.BORDER, (status.x + 14, 100), (status.right - 14, 100), 1)
    _label(canvas, fonts.small, view.inventory, theme.MUTED, (status.x + 15, 109))
    _waypoint(canvas, level, operative_tile, phase, fonts)
    if phase == MissionPhase.LOCKDOWN:
        _label(canvas, fonts.micro, "LOCKDOWN ACTIVE", theme.DANGER, (610, 104))
    elif clock_ms < 10_000:
        _first_run_help(canvas, fonts)
    draw_minimap(canvas, level, operative_tile, phase, fonts)
    if notice:
        text_width = fonts.small.size(notice)[0]
        banner = pygame.Rect(0, canvas.get_height() - 116, max(390, text_width + 42), 40)
        banner.centerx = canvas.get_width() // 2
        panel(canvas, banner, fill=(5, 26, 36, 239), border=theme.WARNING)
        _label(
            canvas,
            fonts.small,
            notice,
            theme.TEXT,
            (banner.centerx - text_width // 2, banner.y + 9),
        )
    footer = pygame.Rect(280, canvas.get_height() - 48, 783, 30)
    panel(canvas, footer)
    _label(canvas, fonts.micro, CONTROLS, theme.MUTED, (footer.x + 13, footer.y + 9))


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
    shade = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 165))
    canvas.blit(shade, (0, 0))
    panel(canvas, rect, fill=(5, 17, 27, 246), border=title_color)
    pygame.draw.rect(canvas, title_color, (rect.left, rect.top, 5, rect.height))
    heading = fonts.heading.render(title, True, title_color)
    canvas.blit(heading, (rect.centerx - heading.get_width() // 2, rect.top + 22))
    for index, (value, color) in enumerate(lines):
        line = fonts.body.render(value, True, color)
        canvas.blit(line, (rect.centerx - line.get_width() // 2, rect.top + 81 + index * 36))
