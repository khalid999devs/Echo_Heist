"""Detailed 2.5D facility rendering over Suhita's authoritative map geometry."""

from math import pi

import pygame

from echo_heist.core.contracts.results import PresentationSnapshot
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE, ActorKind, MissionPhase
from echo_heist.level.model import LevelData
from echo_heist.ui.render import motifs, theme
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.theme import Fonts


def to_pixels(position: tuple[int, int], tile_px: int) -> tuple[float, float]:
    return (
        position[0] * tile_px / POSITION_UNITS_PER_TILE,
        position[1] * tile_px / POSITION_UNITS_PER_TILE,
    )


def _roof_tile(surface: pygame.Surface, rect: pygame.Rect, variant: int) -> None:
    pygame.draw.rect(surface, (8, 19, 27), rect)
    pygame.draw.line(surface, (21, 35, 44), rect.topleft, rect.topright, 1)
    pygame.draw.line(surface, (15, 28, 36), rect.topleft, rect.bottomleft, 1)
    if variant % 29 == 0:
        rack = rect.inflate(-5, -4)
        pygame.draw.rect(surface, (21, 36, 46), rack, border_radius=2)
        pygame.draw.rect(surface, (57, 78, 87), rack, 1, border_radius=2)
        for dy in (7, 12, 17, 22):
            pygame.draw.line(
                surface,
                (7, 22, 31),
                (rack.left + 3, rack.top + dy),
                (rack.right - 3, rack.top + dy),
                2,
            )
            pygame.draw.circle(
                surface,
                theme.ACCENT_DIM,
                (rack.right - 5, rack.top + dy),
                1,
            )
    elif variant % 13 == 0:
        pygame.draw.rect(surface, (20, 42, 51), rect.inflate(-11, -10), 1)
        pygame.draw.line(
            surface,
            (32, 73, 83),
            (rect.left + 9, rect.top + 11),
            (rect.right - 8, rect.top + 11),
            1,
        )


def build_map_surface(level: LevelData, fonts: Fonts) -> pygame.Surface:
    """Prepaint the facility once; visual motifs never affect map collision tags."""
    world_map, size = level.static_map, level.static_map.tile_size_px
    surface = pygame.Surface((world_map.width * size, world_map.height * size))
    surface.fill(theme.BACKGROUND)
    for y in range(world_map.height):
        for x in range(world_map.width):
            tile = (x, y)
            rect = pygame.Rect(x * size, y * size, size, size)
            variant = (x * 73 + y * 37 + x * y * 3) & 255
            zone = level.zone_at(tile)
            zone_id = zone.zone_id if zone else None
            if tile in level.glass_tiles:
                motifs.glass_tile(surface, rect)
            elif tile in level.cover_tiles:
                motifs.cover_tile(surface, rect, variant)
            elif world_map.can_walk(tile):
                motifs.floor_tile(surface, rect, zone_id, variant)
            else:
                adjacent_walk = any(
                    world_map.can_walk((x + dx, y + dy))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                )
                if adjacent_walk:
                    motifs.wall_tile(
                        surface,
                        rect,
                        edge=world_map.can_walk((x, y + 1)),
                        beacon=(x + 2 * y) % 6 == 0,
                    )
                else:
                    _roof_tile(surface, rect, variant)
    for marker in level.markers:
        if marker.kind == "HideSpot":
            x, y = marker.tile
            rect = pygame.Rect(x * size + 7, y * size + 7, size - 14, size - 14)
            pygame.draw.rect(surface, theme.ACCENT_DIM, rect, 1, border_radius=3)
            pygame.draw.line(surface, theme.ACCENT_DIM, rect.topleft, rect.bottomright, 1)
    for point in level.chokepoints:
        x, y = point.tile
        marker_rect = pygame.Rect(x * size + 6, y * size + 12, size - 12, 8)
        pygame.draw.rect(surface, theme.WARNING, marker_rect, 1)
        pygame.draw.line(
            surface,
            theme.WARNING,
            marker_rect.topleft,
            (marker_rect.left + 7, marker_rect.bottom),
            2,
        )
    for zone in level.zones:
        center = (
            int((zone.left + zone.width / 2) * size),
            int((zone.top + zone.height / 2) * size),
        )
        color = (
            theme.ACCENT
            if zone.zone_id in ("entry", "research-floor", "core-chamber")
            else theme.WARNING
        )
        motifs.light_pool(surface, center, color, min(185, max(90, zone.width * size // 3)))
        position = (zone.left * size + 9, zone.top * size + 8)
        title = fonts.small.render(zone.label.upper(), True, theme.MUTED)
        badge = pygame.Surface((title.get_width() + 18, title.get_height() + 7), pygame.SRCALPHA)
        badge.fill((3, 12, 20, 190))
        surface.blit(badge, (position[0] - 7, position[1] - 3))
        surface.blit(title, position)
    return surface


def _anchor(
    canvas: pygame.Surface,
    tile: tuple[int, int],
    size: int,
    camera: Camera,
    *,
    kind: str,
    active: bool,
    pulse: float,
    fonts: Fonts,
    alert: bool = False,
) -> None:
    point = camera.to_screen(((tile[0] + 0.5) * size, (tile[1] + 0.5) * size))
    color = theme.WARNING if kind == "CORE" else theme.ACCENT
    if kind == "CORE" and not active:
        color = theme.DANGER if alert else theme.DISABLED
    motifs.beacon_glow(canvas, point, color, 48 if kind == "CORE" else 38, pulse)
    if kind == "CORE":
        pygame.draw.circle(canvas, (8, 27, 35), point, 16)
        pygame.draw.circle(canvas, color, point, 13, 3)
        if active:
            pygame.draw.polygon(
                canvas,
                theme.TEXT,
                (
                    (point[0], point[1] - 9),
                    (point[0] + 7, point[1]),
                    (point[0], point[1] + 9),
                    (point[0] - 7, point[1]),
                ),
            )
    else:
        pygame.draw.rect(canvas, (7, 28, 35), (point[0] - 11, point[1] - 11, 22, 22))
        pygame.draw.rect(canvas, color, (point[0] - 11, point[1] - 11, 22, 22), 2)
        pygame.draw.line(
            canvas,
            color,
            (point[0] - 4, point[1]),
            (point[0] + 5, point[1]),
            2,
        )
    label = fonts.micro.render(kind, True, color)
    canvas.blit(label, (point[0] - label.get_width() // 2, point[1] - 31))


def draw_world(
    canvas: pygame.Surface,
    level: LevelData,
    map_surface: pygame.Surface,
    snapshot: PresentationSnapshot,
    camera: Camera,
    fonts: Fonts,
    pulse: float,
) -> None:
    size = level.static_map.tile_size_px
    canvas.fill(theme.BACKGROUND)
    canvas.blit(map_surface, camera.to_screen((0, 0)))
    anchors = {obj.object_id: obj.tile for obj in level.static_map.objects}
    _anchor(
        canvas,
        anchors[level.exit_id],
        size,
        camera,
        kind="EXIT",
        active=True,
        pulse=pulse,
        fonts=fonts,
    )
    _anchor(
        canvas,
        anchors[level.core_id],
        size,
        camera,
        kind="CORE",
        active=snapshot.core_owner is None,
        alert=snapshot.phase == MissionPhase.LOCKDOWN,
        pulse=pulse,
        fonts=fonts,
    )
    captures = {capture.target_id: capture for capture in snapshot.captures}
    for echo in snapshot.echoes:
        point = camera.to_screen(to_pixels(echo.position, size))
        pygame.draw.circle(canvas, theme.ACCENT, point, 13, 2)
        pygame.draw.circle(canvas, theme.ACCENT_DIM, point, 8, 1)
    for entity in snapshot.actors:
        if entity.position is None:
            continue
        point = camera.to_screen(to_pixels(entity.position, size))
        if entity.kind == ActorKind.OPERATIVE:
            motifs.light_pool(canvas, point, theme.ACCENT, 65)
        motifs.actor(
            canvas,
            point,
            entity.kind,
            disabled=entity.disabled,
            stunned=entity.stunned,
            carries_core=entity.actor_id == snapshot.core_owner,
            pulse=pulse,
        )
        capture = captures.get(entity.actor_id)
        if capture is not None:
            progress = 1 - capture.remaining_ticks / max(1, capture.total_ticks)
            ring = pygame.Rect(0, 0, 38, 38)
            ring.center = point
            pygame.draw.arc(canvas, theme.WARNING, ring, pi / 2, pi / 2 + 2 * pi * progress, 4)
        if entity.kind != ActorKind.OPERATIVE:
            label = fonts.micro.render(entity.actor_id.upper(), True, theme.MUTED)
            canvas.blit(label, (point[0] - label.get_width() // 2, point[1] + 14))
    if snapshot.phase == MissionPhase.LOCKDOWN:
        border = canvas.get_rect().inflate(-5, -5)
        pygame.draw.rect(canvas, theme.DANGER, border, 2 + int(2 * pulse))
