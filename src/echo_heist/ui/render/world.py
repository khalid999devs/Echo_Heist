"""Draw the static five-zone map once, then actors/objects from each snapshot."""

from math import pi

import pygame

from echo_heist.core.contracts.results import PresentationSnapshot
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE, ActorKind, MissionPhase
from echo_heist.level.model import LevelData
from echo_heist.ui.render import theme
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.theme import Fonts

GUARD_LABELS = {
    ActorKind.SENTINEL: "Sentinel post",
    ActorKind.TRACKER: "Tracker post",
    ActorKind.INTERCEPTOR: "Interceptor post",
}


def to_pixels(position: tuple[int, int], tile_px: int) -> tuple[float, float]:
    return (
        position[0] * tile_px / POSITION_UNITS_PER_TILE,
        position[1] * tile_px / POSITION_UNITS_PER_TILE,
    )


def build_map_surface(level: LevelData, fonts: Fonts) -> pygame.Surface:
    """Static layers only; they never change during a P02 run."""
    world_map, size = level.static_map, level.static_map.tile_size_px
    surface = pygame.Surface((world_map.width * size, world_map.height * size))
    surface.fill(theme.BACKGROUND)
    for x in range(world_map.width):
        for y in range(world_map.height):
            rect = pygame.Rect(x * size, y * size, size, size)
            zone = level.zone_at((x, y))
            if (x, y) in level.glass_tiles:
                pygame.draw.rect(surface, theme.CORRIDOR_FLOOR, rect)
                pygame.draw.rect(surface, theme.GLASS, rect.inflate(-size // 2, -4))
            elif (x, y) in level.cover_tiles:
                floor = theme.ZONE_FLOORS.get(zone.zone_id) if zone else None
                pygame.draw.rect(surface, floor or theme.CORRIDOR_FLOOR, rect)
                pygame.draw.rect(surface, theme.COVER, rect.inflate(-4, -4), border_radius=3)
            elif world_map.can_walk((x, y)):
                floor = theme.ZONE_FLOORS.get(zone.zone_id) if zone else None
                pygame.draw.rect(surface, floor or theme.CORRIDOR_FLOOR, rect)
                pygame.draw.rect(surface, theme.BACKGROUND, rect, 1)
            elif any(
                world_map.can_walk((x + dx, y + dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            ):
                pygame.draw.rect(surface, theme.WALL, rect)
                pygame.draw.rect(surface, theme.WALL_EDGE, rect, 1)
    for marker in level.markers:
        if marker.kind == "HideSpot":
            rect = pygame.Rect(marker.tile[0] * size, marker.tile[1] * size, size, size)
            pygame.draw.rect(surface, theme.MUTED, rect.inflate(-10, -10), 1, border_radius=4)
    for zone in level.zones:
        label = fonts.small.render(zone.label.upper(), True, theme.MUTED)
        surface.blit(label, (zone.left * size + 8, zone.top * size + 6))
    return surface


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

    def tile_rect(tile: tuple[int, int], inset: int) -> pygame.Rect:
        left, top = camera.to_screen((tile[0] * size, tile[1] * size))
        return pygame.Rect(left, top, size, size).inflate(-inset, -inset)

    lockdown = snapshot.phase == MissionPhase.LOCKDOWN
    exit_rect = tile_rect(anchors[level.exit_id], 4)
    exit_width = 3 + int(2 * pulse) if lockdown else 3
    pygame.draw.rect(canvas, theme.ACCENT, exit_rect, exit_width, border_radius=4)
    canvas.blit(fonts.small.render("EXIT", True, theme.ACCENT), exit_rect.move(-2, -18).topleft)
    if snapshot.core_owner is None:
        core = tile_rect(anchors[level.core_id], 8)
        points = [core.midtop, core.midright, core.midbottom, core.midleft]
        pygame.draw.polygon(canvas, theme.WARNING, points)
        canvas.blit(fonts.small.render("CORE", True, theme.WARNING), core.move(-4, -20).topleft)
    radius = max(6, size * 3 // 10)
    captures = {capture.target_id: capture for capture in snapshot.captures}
    for echo in snapshot.echoes:
        point = camera.to_screen(to_pixels(echo.position, size))
        pygame.draw.circle(canvas, theme.OPERATIVE, point, radius, 2)
    for actor in snapshot.actors:
        if actor.position is None:
            continue
        point = camera.to_screen(to_pixels(actor.position, size))
        if actor.kind == ActorKind.OPERATIVE:
            color = theme.OPERATIVE
        elif actor.disabled:
            color = theme.DISABLED
        elif actor.stunned:
            color = theme.WARNING
        else:
            color = theme.DANGER
        pygame.draw.circle(canvas, color, point, radius)
        if actor.actor_id == snapshot.core_owner:
            pygame.draw.circle(canvas, theme.WARNING, point, radius // 2)
        if actor.kind in GUARD_LABELS:
            label = fonts.small.render(GUARD_LABELS[actor.kind], True, color)
            canvas.blit(label, (point[0] - label.get_width() // 2, point[1] + radius + 2))
        capture = captures.get(actor.actor_id)
        if capture is not None:
            done = 1 - capture.remaining_ticks / max(1, capture.total_ticks)
            ring = pygame.Rect(0, 0, radius * 3, radius * 3)
            ring.center = point
            pygame.draw.arc(canvas, theme.WARNING, ring, pi / 2, pi / 2 + 2 * pi * done, 4)
    if lockdown:
        border = canvas.get_rect().inflate(-4, -4)
        pygame.draw.rect(canvas, theme.DANGER, border, 3 + int(3 * pulse))
