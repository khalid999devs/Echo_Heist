"""Detailed 2.5D facility rendering over Suhita's authoritative map geometry."""

from dataclasses import dataclass
from io import BytesIO
from math import cos, pi, sin

import pygame

from echo_heist.core.contracts.results import PresentationSnapshot
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE, ActorKind, MissionPhase
from echo_heist.infrastructure.resources import resource_bytes
from echo_heist.level.model import LevelData
from echo_heist.ui.render import motifs, theme
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.surfaces.glass import alert_frame
from echo_heist.ui.render.surfaces.vision import draw_vision
from echo_heist.ui.render.theme import Fonts


@dataclass(frozen=True, slots=True)
class VisualPulse:
    """Short lived, purely visual response to a committed game event."""

    position: tuple[int, int]
    kind: str
    started_ms: int


@dataclass(frozen=True, slots=True)
class WorldArt:
    """Cached authored visual assets; no collision or observation data lives here."""

    floor: pygame.Surface
    bulkhead: pygame.Surface
    props: tuple[pygame.Surface, ...]
    operative: tuple[pygame.Surface, ...]
    guard: tuple[pygame.Surface, ...]

    @classmethod
    def load(cls) -> "WorldArt":
        def image(path: str) -> pygame.Surface:
            return pygame.image.load(BytesIO(resource_bytes(path)), path)

        floor = pygame.transform.smoothscale(image("assets/tiles/facility-floor.png"), (256, 256))
        bulkhead = pygame.transform.smoothscale(image("assets/tiles/bulkhead.png"), (256, 256))
        floor.fill((183, 193, 201), special_flags=pygame.BLEND_RGB_MULT)
        bulkhead.fill((160, 175, 185), special_flags=pygame.BLEND_RGB_MULT)
        atlas = image("assets/tiles/facility-props.png")
        # This illustrated atlas has irregular padding; explicit regions prevent
        # a neighboring prop's edge from leaking into another furnishing.
        regions = (
            (100, 8, 280, 500),
            (498, 90, 545, 420),
            (1150, 0, 285, 540),
            (50, 555, 420, 420),
            (565, 544, 400, 435),
            (1046, 570, 465, 410),
        )
        cells = tuple(atlas.subsurface(pygame.Rect(region)) for region in regions)
        props = tuple(cell.subsurface(cell.get_bounding_rect(min_alpha=16)) for cell in cells)

        def frames(path: str, size: tuple[int, int]) -> tuple[pygame.Surface, ...]:
            sheet = image(path)
            width = sheet.get_width() // 4
            cells = tuple(
                sheet.subsurface(pygame.Rect(index * width, 0, width, sheet.get_height()))
                for index in range(4)
            )
            bounds = cells[0].get_bounding_rect(min_alpha=32)
            for cell in cells[1:]:
                bounds.union_ip(cell.get_bounding_rect(min_alpha=32))
            result = []
            for cell in cells:
                frame = pygame.transform.smoothscale(cell.subsurface(bounds), size)
                frame.fill((28, 34, 39), special_flags=pygame.BLEND_RGB_ADD)
                result.append(frame)
            return tuple(result)

        return cls(
            floor,
            bulkhead,
            props,
            frames("assets/characters/operative-motion.png", (52, 66)),
            frames("assets/characters/guard-motion.png", (52, 66)),
        )


def to_pixels(position: tuple[int, int], tile_px: int) -> tuple[float, float]:
    return (
        position[0] * tile_px / POSITION_UNITS_PER_TILE,
        position[1] * tile_px / POSITION_UNITS_PER_TILE,
    )


def _roof_tile(
    surface: pygame.Surface,
    rect: pygame.Rect,
    variant: int,
    texture: pygame.Surface | None = None,
) -> None:
    if texture is None:
        pygame.draw.rect(surface, (8, 19, 27), rect)
    else:
        source = pygame.Rect(
            rect.x % texture.get_width(), rect.y % texture.get_height(), rect.w, rect.h
        )
        surface.blit(texture, rect.topleft, source)
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


def _decorate_cover(surface: pygame.Surface, level: LevelData, art: WorldArt) -> None:
    """Illustrate physical cover cells without placing furnishings on closed roofs."""
    size = level.static_map.tile_size_px
    remaining = set(level.cover_tiles)
    while remaining:
        x, y = min(remaining)
        width = 1
        while (x + width, y) in remaining:
            width += 1
        remaining.difference_update((x + offset, y) for offset in range(width))
        rect = pygame.Rect(x * size, y * size, width * size, size)
        prop = pygame.transform.smoothscale(art.props[3], rect.inflate(-3, -3).size)
        surface.blit(prop, rect.move(1, 0))


def _floor_shadows(surface: pygame.Surface, level: LevelData) -> None:
    """Bake soft wall contact shadows into the static map's walkable floor."""
    world_map = level.static_map
    size = world_map.tile_size_px
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for y in range(world_map.height):
        for x in range(world_map.width):
            if not world_map.can_walk((x, y)):
                continue
            left, top = x * size, y * size
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                if world_map.can_walk((x + dx, y + dy)):
                    continue
                for offset in range(9):
                    color = (0, 5, 9, round(83 * (1 - offset / 9) ** 2))
                    if dx:
                        px = left + offset if dx < 0 else left + size - 1 - offset
                        start, end = (px, top), (px, top + size - 1)
                    else:
                        py = top + offset if dy < 0 else top + size - 1 - offset
                        start, end = (left, py), (left + size - 1, py)
                    pygame.draw.line(layer, color, start, end)
    surface.blit(layer, (0, 0))


def _furniture_rects(level: LevelData) -> tuple[tuple[pygame.Rect, str], ...]:
    size = level.static_map.tile_size_px
    result = []
    for obj in level.static_map.objects:
        if obj.kind == "Furniture":
            props = dict(obj.properties)
            width, height = props["width_tiles"], props["height_tiles"]
            assert isinstance(width, int) and isinstance(height, int)
            result.append(
                (
                    pygame.Rect(
                        obj.tile[0] * size,
                        obj.tile[1] * size,
                        width * size,
                        height * size,
                    ),
                    str(props["style"]),
                )
            )
    return tuple(result)


def _draw_furniture(surface: pygame.Surface, level: LevelData, art: WorldArt) -> None:
    styles = {"rack": 0, "console": 1, "tank": 2, "crates": 3, "plant": 4, "workbench": 5}
    for footprint, style in _furniture_rects(level):
        # The sprite and its contact shadow stay within the physical footprint.
        # No invisible rectangle extends into a neighboring walking lane.
        prop = pygame.transform.smoothscale(
            art.props[styles[style]], footprint.inflate(-4, -4).size
        )
        prop.fill((205, 220, 232), special_flags=pygame.BLEND_RGB_MULT)
        pygame.draw.rect(surface, (4, 13, 20), footprint.inflate(-1, -1), border_radius=5)
        surface.blit(prop, footprint.move(2, 1))


def build_map_surface(
    level: LevelData, fonts: Fonts, art: WorldArt | None = None
) -> pygame.Surface:
    """Prepaint the facility once; visual motifs never affect map collision tags."""
    world_map, size = level.static_map, level.static_map.tile_size_px
    surface = pygame.Surface((world_map.width * size, world_map.height * size))
    surface.fill(theme.BACKGROUND)
    roof_texture = art.bulkhead.copy() if art else None
    if roof_texture is not None:
        roof_texture.fill((88, 108, 125), special_flags=pygame.BLEND_RGB_MULT)
    furniture_tiles = {
        (x, y)
        for rect, _ in _furniture_rects(level)
        for x in range(rect.left // size, rect.right // size)
        for y in range(rect.top // size, rect.bottom // size)
    }
    for y in range(world_map.height):
        for x in range(world_map.width):
            tile = (x, y)
            rect = pygame.Rect(x * size, y * size, size, size)
            variant = (x * 73 + y * 37 + x * y * 3) & 255
            zone = level.zone_at(tile)
            zone_id = zone.zone_id if zone else None
            if tile in furniture_tiles:
                motifs.floor_tile(
                    surface, rect, zone_id, variant, texture=art.floor if art else None
                )
            elif tile in level.glass_tiles:
                motifs.glass_tile(surface, rect)
            elif tile in level.cover_tiles:
                motifs.cover_tile(surface, rect, variant)
            elif world_map.can_walk(tile):
                motifs.floor_tile(
                    surface, rect, zone_id, variant, texture=art.floor if art else None
                )
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
                        variant=variant,
                        texture=art.bulkhead if art else None,
                    )
                else:
                    _roof_tile(surface, rect, variant, roof_texture)
    _floor_shadows(surface, level)
    if art is not None:
        _decorate_cover(surface, level, art)
        _draw_furniture(surface, level, art)
    anchors = {obj.object_id: obj.tile for obj in world_map.objects}
    for object_id, painter in (
        (level.exit_id, motifs.extraction_floor),
        (level.core_id, motifs.core_floor),
    ):
        tile = anchors[object_id]
        painter(surface, ((tile[0] * size) + size // 2, (tile[1] * size) + size // 2))
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
    clock_ms: int = 0,
) -> None:
    point = camera.to_screen(((tile[0] + 0.5) * size, (tile[1] + 0.5) * size))
    color = theme.ACCENT
    if kind == "CORE" and not active:
        color = theme.DANGER if alert else theme.DISABLED
    motifs.beacon_glow(canvas, point, color, 48 if kind == "CORE" else 38, pulse)
    if kind == "CORE":
        pygame.draw.circle(canvas, (8, 27, 35), point, 16)
        pygame.draw.circle(canvas, color, point, 13, 3)
        if active:
            angle = clock_ms / 800
            for quarter in range(4):
                theta = angle + quarter * pi / 2
                orbit = (round(point[0] + 22 * cos(theta)), round(point[1] + 22 * sin(theta)))
                pygame.draw.circle(canvas, color, orbit, 2)
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
        if pulse > 0.5:
            pygame.draw.polygon(
                canvas,
                color,
                (
                    (point[0] + 3, point[1] - 4),
                    (point[0] + 8, point[1]),
                    (point[0] + 3, point[1] + 4),
                ),
            )
    label = fonts.micro.render(
        "EMPTY SOCKET" if kind == "CORE" and not active else kind, True, color
    )
    label_y = point[1] + 65 if kind == "CORE" else point[1] - 55
    canvas.blit(label, (point[0] - label.get_width() // 2, label_y))


def draw_world(
    canvas: pygame.Surface,
    level: LevelData,
    map_surface: pygame.Surface,
    snapshot: PresentationSnapshot,
    camera: Camera,
    fonts: Fonts,
    pulse: float,
    *,
    actor_motion: dict[str, motifs.ActorMotion] | None = None,
    clock_ms: int = 0,
    pulses: tuple[VisualPulse, ...] = (),
    art: WorldArt | None = None,
) -> None:
    size = level.static_map.tile_size_px
    canvas.fill(theme.BACKGROUND)
    canvas.blit(map_surface, camera.to_screen((0, 0)))
    if snapshot.phase == MissionPhase.LOCKDOWN:
        canvas.fill((244, 205, 212), special_flags=pygame.BLEND_RGB_MULT)
        for choke in level.chokepoints:
            screen_point = camera.to_screen(
                ((choke.tile[0] + 0.5) * size, (choke.tile[1] + 0.5) * size)
            )
            motifs.light_pool(canvas, screen_point, theme.DANGER, 90)
    draw_vision(canvas, level.static_map, snapshot, camera)
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
        clock_ms=clock_ms,
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
        clock_ms=clock_ms,
    )
    captures = {capture.target_id: capture for capture in snapshot.captures}
    for echo in snapshot.echoes:
        point = camera.to_screen(to_pixels(echo.position, size))
        radius = 12 + round(3 * pulse)
        pygame.draw.circle(canvas, theme.ACCENT, point, radius, 2)
        pygame.draw.circle(canvas, theme.ACCENT_DIM, point, 8, 1)
        for index in range(3):
            theta = clock_ms / 400 + index * 2 * pi / 3
            trace = (round(point[0] + 19 * cos(theta)), round(point[1] + 19 * sin(theta)))
            pygame.draw.circle(canvas, theme.ACCENT, trace, 2)
    for visual in pulses:
        age = clock_ms - visual.started_ms
        if not 0 <= age < 650:
            continue
        point = camera.to_screen(to_pixels(visual.position, size))
        radius = 8 + age // (7 if visual.kind == "EMP" else 12)
        color = theme.ACCENT if visual.kind == "ECHO" else theme.WARNING
        alpha = max(0, 170 - age // 4)
        pulse_surface = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(pulse_surface, (*color, alpha), (radius + 4, radius + 4), radius, 3)
        canvas.blit(pulse_surface, (point[0] - radius - 4, point[1] - radius - 4))
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
            motion=(actor_motion or {}).get(entity.actor_id, motifs.ActorMotion()),
            clock_ms=clock_ms,
            sprites=(art.operative if entity.kind == ActorKind.OPERATIVE else art.guard)
            if art is not None
            else None,
        )
        capture = captures.get(entity.actor_id)
        if capture is not None:
            progress = 1 - capture.remaining_ticks / max(1, capture.total_ticks)
            ring = pygame.Rect(0, 0, 38, 38)
            ring.center = point
            pygame.draw.arc(canvas, theme.WARNING, ring, pi / 2, pi / 2 + 2 * pi * progress, 4)
        if entity.kind != ActorKind.OPERATIVE and 150 < point[1] < canvas.get_height() - 65:
            label = fonts.micro.render(entity.kind.value.upper(), True, theme.MUTED)
            canvas.blit(label, (point[0] - label.get_width() // 2, point[1] + 14))
    if snapshot.phase == MissionPhase.LOCKDOWN:
        canvas.blit(alert_frame(canvas.get_size()), (0, 0))
