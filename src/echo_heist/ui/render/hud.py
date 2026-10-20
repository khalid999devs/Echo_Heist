"""Mission overlays derived from observations and static map data."""

import pygame

from echo_heist.core.contracts.world import MissionPhase, Tile
from echo_heist.level.model import LevelData
from echo_heist.ui.presenters.objective import ObjectiveView
from echo_heist.ui.render import theme
from echo_heist.ui.render.theme import Color, Fonts

CONTROLS = "WASD MOVE    SHIFT SPRINT    E CORE    Q ECHO    F EMP    SPACE MELEE    ESC PAUSE"


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
    rect = pygame.Rect(20, canvas.get_height() - 190, 244, 169)
    panel(canvas, rect)
    _label(canvas, fonts.micro, "FACILITY A1 / ROUTE", theme.ACCENT, (32, rect.y + 13))
    width, height = level.static_map.width, level.static_map.height
    scale = min(216 / width, 113 / height)
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
    _label(canvas, fonts.micro, "YOU  /  CORE  /  EXIT", theme.MUTED, (33, rect.bottom - 23))


def draw_hud(
    canvas: pygame.Surface,
    view: ObjectiveView,
    zone_label: str,
    fonts: Fonts,
    *,
    level: LevelData,
    operative_tile: Tile,
    phase: MissionPhase,
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
    prompt = view.interaction or view.warning or default_prompt
    color = theme.WARNING if view.interaction else theme.DANGER if view.warning else theme.MUTED
    _label(canvas, fonts.small, prompt, color, (37, 107))
    status = pygame.Rect(canvas.get_width() - 282, 20, 262, 137)
    panel(canvas, status)
    _label(canvas, fonts.micro, "MISSION TIME", theme.ACCENT, (status.x + 15, 32))
    _label(canvas, fonts.heading, view.elapsed, theme.TEXT, (status.x + 15, 52))
    pygame.draw.line(canvas, theme.BORDER, (status.x + 14, 100), (status.right - 14, 100), 1)
    _label(canvas, fonts.small, view.inventory, theme.MUTED, (status.x + 15, 109))
    if phase == MissionPhase.LOCKDOWN:
        bar = pygame.Rect(477, 20, 292, 41)
        panel(canvas, bar, fill=(57, 9, 16, 233), border=theme.DANGER)
        _label(
            canvas,
            fonts.small,
            "LOCKDOWN  /  REACH EXTRACTION",
            theme.TEXT,
            (bar.x + 13, bar.y + 12),
        )
    draw_minimap(canvas, level, operative_tile, phase, fonts)
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
