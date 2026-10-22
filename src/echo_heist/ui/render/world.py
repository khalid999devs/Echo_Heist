"""Detailed 2.5D facility rendering over Suhita's authoritative map geometry."""

from dataclasses import dataclass
from io import BytesIO
from math import cos, pi, sin

import pygame

from echo_heist.core.contracts.observations import EntityView
from echo_heist.core.contracts.results import PresentationSnapshot
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE, ActorKind, MissionPhase
from echo_heist.infrastructure.resources import resource_bytes
from echo_heist.level.model import LevelData
from echo_heist.ui.render import motifs, theme
from echo_heist.ui.render.actors.model import (
    COMPANION_SIZE,
    DEFENDER_SIZE,
    OPERATIVE_SIZE,
    position_at,
)
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.environment.architecture.materials import material_floor
from echo_heist.ui.render.environment.architecture.sections import (
    paint_mounts,
    wall_section,
    wall_skin,
)
from echo_heist.ui.render.environment.art import (
    clinical_props,
    laboratory_props,
    research_props,
    sprite_grid,
)
from echo_heist.ui.render.environment.furnishings.catalogue import FurnitureVisual, draw_instrument
from echo_heist.ui.render.environment.furnishings.story import paint_room_story
from echo_heist.ui.render.environment.interiors import draw_details, draw_room_trim, room_floors
from echo_heist.ui.render.environment.lighting import bake_lighting, draw_equipment
from echo_heist.ui.render.surfaces.formats import opaque_surface
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
    companion: tuple[pygame.Surface, ...]
    operative_walk: tuple[pygame.Surface, ...]
    operative_run: tuple[pygame.Surface, ...]
    operative_crouch: tuple[pygame.Surface, ...] = ()

    @classmethod
    def load(cls) -> "WorldArt":
        def image(path: str) -> pygame.Surface:
            return pygame.image.load(BytesIO(resource_bytes(path)), path)

        floor = material_floor("corridor")
        bulkhead = pygame.transform.smoothscale(image("assets/tiles/bulkhead.png"), (384, 384))
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
        interior_atlas = image("assets/tiles/interior-props.png")
        interiors = tuple(
            interior_atlas.subsurface((x * 512, y * 512, 512, 512))
            for y in range(2)
            for x in range(3)
        )
        props += tuple(cell.subsurface(cell.get_bounding_rect(min_alpha=32)) for cell in interiors)

        return cls(
            floor,
            bulkhead,
            props + laboratory_props() + clinical_props() + research_props(),
            sprite_grid(
                "assets/characters/operative-directions.png",
                4,
                4,
                OPERATIVE_SIZE,
                row_edges=(0, 312, 615, 926, 1254),
            ),
            sprite_grid("assets/characters/defenders.png", 4, 3, DEFENDER_SIZE),
            sprite_grid("assets/characters/companion.png", 2, 2, COMPANION_SIZE),
            sprite_grid(
                "assets/characters/operative/walk.png",
                4,
                4,
                OPERATIVE_SIZE,
                row_edges=(0, 290, 579, 874, 1190),
                column_edges=(0, 384, 647, 990, 1322),
            ),
            sprite_grid(
                "assets/characters/operative/run.png",
                4,
                4,
                OPERATIVE_SIZE,
                row_edges=(0, 321, 614, 909, 1189),
                column_edges=(0, 406, 681, 1026, 1323),
            ),
            sprite_grid("assets/characters/operative/crouch.png", 4, 4, (110, 86)),
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
        return
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
                if (x + dx, y + dy) in level.floor_tiles:
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


def _furniture_rects(level: LevelData) -> tuple[tuple[pygame.Rect, str, int], ...]:
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
                    int(props.get("rotation") or 0),
                )
            )
    return tuple(result)


def build_map_surface(
    level: LevelData, fonts: Fonts, art: WorldArt | None = None
) -> pygame.Surface:
    """Prepaint the facility once; visual motifs never affect map collision tags."""
    world_map, size = level.static_map, level.static_map.tile_size_px
    surface = opaque_surface((world_map.width * size, world_map.height * size))
    surface.fill(theme.BACKGROUND)
    roof_texture = wall_skin(size * 4).copy()
    roof_texture.fill((118, 125, 120), special_flags=pygame.BLEND_RGB_MULT)
    furniture_tiles = {
        (x, y)
        for rect, _, _ in _furniture_rects(level)
        for x in range(rect.left // size, rect.right // size)
        for y in range(rect.top // size, rect.bottom // size)
    }
    floors = room_floors(art.floor) if art else {}
    for y in range(world_map.height):
        for x in range(world_map.width):
            tile = (x, y)
            rect = pygame.Rect(x * size, y * size, size, size)
            variant = (x * 73 + y * 37 + x * y * 3) & 255
            zone = level.zone_at(tile)
            zone_id = zone.zone_id if zone else None
            room = level.room_at(tile)
            floor_texture = (
                floors.get(room.style, art.floor)
                if art is not None and room
                else art.floor
                if art
                else None
            )
            if tile in furniture_tiles:
                motifs.floor_tile(surface, rect, zone_id, variant, texture=floor_texture)
            elif tile in level.glass_tiles:
                motifs.floor_tile(surface, rect, zone_id, variant, texture=floor_texture)
                motifs.glass_tile(surface, rect)
            elif tile in level.cover_tiles:
                if art:
                    motifs.floor_tile(surface, rect, zone_id, variant, texture=floor_texture)
                else:
                    motifs.cover_tile(surface, rect, variant)
            elif world_map.can_walk(tile):
                motifs.floor_tile(surface, rect, zone_id, variant, texture=floor_texture)
            else:
                adjacent_walk = any(
                    world_map.can_walk((x + dx, y + dy))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                )
                if adjacent_walk:
                    wall_section(surface, level, tile)
                else:
                    _roof_tile(surface, rect, variant, roof_texture)
    _floor_shadows(surface, level)
    paint_mounts(surface, level)
    bake_lighting(surface, level)
    draw_details(surface, level, art.props[11] if art else None)
    paint_room_story(surface, level)
    draw_room_trim(surface, level, fonts)
    anchors = {obj.object_id: obj.tile for obj in world_map.objects}
    for object_id, painter in (
        (level.exit_id, motifs.extraction_floor),
        (level.core_id, motifs.core_floor),
    ):
        tile = anchors[object_id]
        painter(surface, ((tile[0] * size) + size // 2, (tile[1] * size) + size // 2))
    for link in world_map.stairs:
        up = link.destination_id.endswith("down")
        label = fonts.micro.render("UP / 02" if up else "DOWN / 01", True, theme.ACCENT)
        stair_label_point = ((link.tile[0] + 0.5) * size, link.tile[1] * size - 6)
        rect = label.get_rect(midbottom=stair_label_point)
        pygame.draw.rect(surface, (6, 21, 29), rect.inflate(8, 4), border_radius=3)
        surface.blit(label, rect)
    for marker in level.markers:
        if marker.kind == "HideSpot" and not level.rooms:
            x, y = marker.tile
            rect = pygame.Rect(x * size + 7, y * size + 7, size - 14, size - 14)
            pygame.draw.rect(surface, theme.ACCENT_DIM, rect, 1, border_radius=3)
            pygame.draw.line(surface, theme.ACCENT_DIM, rect.topleft, rect.bottomright, 1)
    for point in level.chokepoints:
        if any(link.tile == point.tile for link in level.static_map.stairs):
            continue
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
        if level.rooms:
            continue  # Detailed room luminaires already use the floor-only mask.
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
    reduced_motion: bool = False,
    furnishings: tuple[FurnitureVisual, ...] = (),
    fraction: float = 1.0,
) -> None:
    size = level.static_map.tile_size_px
    canvas.fill(theme.BACKGROUND)
    operative = next(actor for actor in snapshot.actors if actor.actor_id == level.operative_id)
    deck = level.deck_at(operative.tile)
    original_clip = canvas.get_clip()
    if deck is not None:
        bounds = pygame.Rect(
            deck.left * size, deck.top * size, deck.width * size, deck.height * size
        )
        dest = camera.to_screen(bounds.topleft)
        canvas.set_clip(pygame.Rect(dest, bounds.size).clip(original_clip))
        canvas.blit(map_surface, dest, bounds)
    else:
        canvas.blit(map_surface, camera.to_screen((0, 0)))
    draw_equipment(canvas, level, camera, 0 if reduced_motion else clock_ms, deck)
    layers: list[tuple[float, str, FurnitureVisual | EntityView]] = []
    for item in furnishings:
        screen_rect = pygame.Rect(camera.to_screen(item.render_rect.topleft), item.render_rect.size)
        if (deck is not None and not deck.contains(item.tile)) or not screen_rect.colliderect(
            canvas.get_rect()
        ):
            continue
        feet = camera.to_screen(item.footprint.midbottom)
        canvas.blit(
            item.shadow.surface,
            (feet[0] - item.shadow.pivot[0], feet[1] - item.shadow.pivot[1]),
        )
        layers.append((item.depth, item.object_id, item))
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
        if entity.position is None or (deck is not None and not deck.contains(entity.tile)):
            continue
        motion = (actor_motion or {}).get(entity.actor_id, motifs.ActorMotion())
        render_position = position_at(entity.position, motion, fraction)
        layers.append(
            (render_position[1] * size / POSITION_UNITS_PER_TILE, entity.actor_id, entity)
        )
    for _, _, layer_item in sorted(layers, key=lambda entry: (entry[0], entry[1])):
        if isinstance(layer_item, FurnitureVisual):
            draw_instrument(canvas, layer_item, camera, 0 if reduced_motion else clock_ms)
            continue
        entity = layer_item
        assert entity.position is not None
        motion = (actor_motion or {}).get(entity.actor_id, motifs.ActorMotion())
        render_position = position_at(entity.position, motion, fraction)
        point = camera.to_screen(
            (
                render_position[0] * size / POSITION_UNITS_PER_TILE,
                render_position[1] * size / POSITION_UNITS_PER_TILE,
            )
        )
        if entity.concealed:
            # Match the shallow ground-depth projection of the desk opening.
            # Blend from zero at its front edge, preserving smooth entry/exit;
            # this is an art socket, not a different authoritative position.
            front = (entity.tile[1] + 1) * POSITION_UNITS_PER_TILE
            depth = max(0, min(POSITION_UNITS_PER_TILE, front - render_position[1]))
            point = (point[0], point[1] + round(depth * size * 0.8 / POSITION_UNITS_PER_TILE))
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
            sprites=(
                art.operative
                if entity.kind == ActorKind.OPERATIVE
                else art.companion
                if entity.kind == ActorKind.COMPANION
                else art.guard[4:8]
                if entity.kind == ActorKind.TRACKER
                else art.guard[8:12]
                if entity.kind == ActorKind.INTERCEPTOR
                else art.guard[:4]
            )
            if art is not None
            else None,
            walk=art.operative_walk
            if art is not None and entity.kind == ActorKind.OPERATIVE
            else (),
            run=art.operative_run if art is not None and entity.kind == ActorKind.OPERATIVE else (),
            crouch=art.operative_crouch
            if art is not None and entity.kind == ActorKind.OPERATIVE
            else (),
            fraction=fraction,
        )
        capture = captures.get(entity.actor_id)
        if capture is not None:
            progress = 1 - capture.remaining_ticks / max(1, capture.total_ticks)
            ring = pygame.Rect(0, 0, 38, 38)
            ring.center = point
            pygame.draw.arc(canvas, theme.WARNING, ring, pi / 2, pi / 2 + 2 * pi * progress, 4)
    if snapshot.phase == MissionPhase.LOCKDOWN:
        cycle = 0.55 if reduced_motion else (1 + sin(clock_ms / 440)) / 2
        canvas.fill(
            (255, round(244 - 64 * cycle), round(246 - 64 * cycle)),
            special_flags=pygame.BLEND_RGB_MULT,
        )
        for room in level.rooms:
            bounds = pygame.Rect(
                camera.to_screen((room.left * size, room.top * size)),
                (room.width * size, room.height * size),
            )
            canvas.set_clip(bounds.clip(original_clip))
            lamp = (bounds.centerx, bounds.top + round(0.2 * size))
            color = (round(140 + 115 * cycle), round(30 + 18 * cycle), 32)
            motifs.light_pool(canvas, lamp, color, 155)
            pygame.draw.line(canvas, color, (lamp[0] - 22, lamp[1]), (lamp[0] + 22, lamp[1]), 3)
    canvas.set_clip(original_clip)
    if snapshot.phase == MissionPhase.LOCKDOWN:
        canvas.blit(alert_frame(canvas.get_size()), (0, 0))
