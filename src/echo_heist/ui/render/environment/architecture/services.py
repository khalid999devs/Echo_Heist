"""Baked wall service trunks, bolted junctions and equipment feeds; no colliders."""

from hashlib import blake2b
from itertools import pairwise

import pygame

from echo_heist.core.contracts.world import MapObject
from echo_heist.level.model import LevelData
from echo_heist.ui.render.environment.furnishings.catalogue import FurnitureVisual

POWERED = frozenset({"pump", "tank", "rack", "console", "desk", "labbench", "workbench"})


def _bundle(surface: pygame.Surface, points: list[tuple[int, int]], *, data: bool = False) -> None:
    if len(points) < 2:
        return
    # A recessed tray, two insulated runs and a restrained ID stripe.
    pygame.draw.lines(surface, (8, 14, 16), False, [(x + 2, y + 3) for x, y in points], 11)
    pygame.draw.lines(surface, (24, 32, 33), False, points, 10)
    pygame.draw.lines(surface, (81, 89, 83), False, points, 8)
    pygame.draw.lines(surface, (23, 32, 34), False, points, 5)
    pygame.draw.lines(surface, (78, 111, 124) if data else (143, 119, 72), False, points, 2)
    if data:
        pygame.draw.lines(surface, (123, 104, 68), False, [(x + 3, y + 2) for x, y in points], 1)
        pygame.draw.lines(surface, (14, 22, 25), False, [(x - 3, y - 2) for x, y in points], 2)
    # Real mounting saddles interrupt the long runs at measured intervals.
    for a, b in pairwise(points):
        distance = abs(b[0] - a[0]) + abs(b[1] - a[1])
        if distance < 22:
            continue
        dx, dy = (b[0] - a[0]) / distance, (b[1] - a[1]) / distance
        for offset in range(16, distance, 35):
            x, y = round(a[0] + dx * offset), round(a[1] + dy * offset)
            pygame.draw.line(
                surface,
                (19, 26, 27),
                (x - round(dy * 6), y + round(dx * 6)),
                (x + round(dy * 6), y - round(dx * 6)),
                4,
            )
            pygame.draw.circle(surface, (122, 129, 116), (x, y), 1)


def _junction(surface: pygame.Surface, point: tuple[int, int], data: bool = False) -> None:
    rect = pygame.Rect(0, 0, 17, 14)
    rect.center = point
    pygame.draw.rect(surface, (10, 18, 21), rect.inflate(4, 4), border_radius=3)
    pygame.draw.rect(surface, (61, 73, 75), rect, border_radius=2)
    pygame.draw.rect(surface, (110, 124, 119), rect, 1, border_radius=2)
    for x in (rect.left + 3, rect.right - 3):
        pygame.draw.circle(surface, (16, 25, 28), (x, rect.top + 3), 1)
    pygame.draw.line(
        surface,
        (101, 156, 169) if data else (175, 143, 77),
        (rect.left + 4, rect.bottom - 4),
        (rect.right - 4, rect.bottom - 4),
        2,
    )


def _socket(item: FurnitureVisual, direction: tuple[int, int]) -> tuple[int, int]:
    bounds = item.sprite.get_bounding_rect(min_alpha=80)
    horizontal = direction[0] != 0
    # Scan into the opaque hull/table edge, avoiding transparent atlas gutters.
    fixed = round(bounds.top + bounds.h * 0.55) if horizontal else bounds.centerx
    start = bounds.left if horizontal else bounds.top
    stop = bounds.right if horizontal else bounds.bottom
    indices = range(start, stop)
    if direction[0] > 0 or direction[1] > 0:
        indices = range(stop - 1, start - 1, -1)
    for index in indices:
        point = (index, fixed) if horizontal else (fixed, index)
        if item.sprite.get_at(point).a >= 80:
            return point[0] + item.render_rect.x, point[1] + item.render_rect.y
    return item.render_rect.center


def _equipment_feed(
    surface: pygame.Surface,
    level: LevelData,
    obj: MapObject,
    bodies: dict[tuple[int, int], str],
    visual: FurnitureVisual | None,
) -> None:
    size = level.static_map.tile_size_px
    values = dict(obj.properties)
    w, h = values["width_tiles"], values["height_tiles"]
    assert isinstance(w, int) and isinstance(h, int)
    rect = pygame.Rect(obj.tile[0] * size, obj.tile[1] * size, w * size, h * size)
    data = values["style"] in ("rack", "console", "desk")
    candidates = []
    for port, direction in (
        (rect.midtop, (0, -1)),
        (rect.midleft, (-1, 0)),
        (rect.midright, (1, 0)),
        (rect.midbottom, (0, 1)),
    ):
        if visual is not None:
            port = _socket(visual, direction)
        for distance in range(6, size * 2, 5):
            point = (port[0] + direction[0] * distance, port[1] + direction[1] * distance)
            tile = (point[0] // size, point[1] // size)
            if (
                not level.static_map.contains(tile)
                or (tile in bodies and bodies[tile] != obj.object_id)
                or any(link.tile == tile for link in level.static_map.stairs)
            ):
                break
            if tile not in level.floor_tiles:
                # Only an actual solid wall can receive a wall-feed gland.
                if (
                    tile in level.static_map.blocked_tiles
                    and tile not in level.static_map.door_tiles
                ):
                    wall = (tile[0] * size + size // 2, tile[1] * size + size // 2)
                    elbow = (port[0], wall[1]) if direction[0] == 0 else (wall[0], port[1])
                    candidates.append((distance, [wall, elbow, port]))
                break
    if candidates:
        _, route = min(candidates, key=lambda value: value[0])
        route = [point for i, point in enumerate(route) if i == 0 or point != route[i - 1]]
        _bundle(surface, route, data=data)
        _junction(surface, route[0], data)
        pygame.draw.circle(surface, (15, 24, 26), route[-1], 5)
        pygame.draw.circle(surface, (115, 128, 121), route[-1], 3, 1)
    else:
        # Islands use an under-bench floor service box, never a cable across an aisle.
        plate = pygame.Rect(rect.left + 5, rect.bottom - 14, 20, 11)
        pygame.draw.rect(surface, (46, 57, 56), plate, border_radius=2)
        pygame.draw.rect(surface, (99, 109, 99), plate, 1, border_radius=2)
        _bundle(surface, [plate.midtop, (plate.centerx, rect.centery)], data=data)


def paint_services(
    surface: pygame.Surface, level: LevelData, furnishings: tuple[FurnitureVisual, ...] = ()
) -> None:
    """Route on exposed solid wall tiles. Doors/aisles remain visually unobstructed."""
    size = level.static_map.tile_size_px
    walls = set()
    for room in level.rooms:
        if room.style not in ("laboratory", "server", "maintenance", "reactor", "office"):
            continue
        perimeter = {
            *((x, room.top - 1) for x in range(room.left - 1, room.left + room.width + 1)),
            *(
                (x, room.top + room.height)
                for x in range(room.left - 1, room.left + room.width + 1)
            ),
            *((room.left - 1, y) for y in range(room.top, room.top + room.height)),
            *((room.left + room.width, y) for y in range(room.top, room.top + room.height)),
        }
        walls |= {
            tile
            for tile in perimeter
            if tile in level.static_map.blocked_tiles
            and tile not in level.floor_tiles
            and tile not in level.static_map.door_tiles
        }
    # All neighbouring wall runs share the same node: bends/junctions genuinely connect.
    for x, y in sorted(walls):
        point = (x * size + size // 2, y * size + size // 2)
        links = 0
        for dx, dy in ((1, 0), (0, 1)):
            if (x + dx, y + dy) in walls:
                _bundle(
                    surface,
                    [point, (point[0] + dx * size, point[1] + dy * size)],
                    data=True,
                )
                links += 1
        fingerprint = int.from_bytes(blake2b(f"{x}:{y}".encode(), digest_size=2).digest(), "big")
        if links and fingerprint % 7 == 0:
            # A service loop stays inside this wall tile, with both ends terminated.
            if fingerprint % 3 == 0:
                loop = [
                    (point[0] + x, point[1] + y)
                    for x, y in ((0, 5), (2, 14), (10, 19), (19, 14), (20, 3), (14, -8))
                ]
                pygame.draw.lines(surface, (5, 11, 14), False, loop, 5)
                pygame.draw.aalines(surface, (60, 80, 83), False, loop)
                pygame.draw.circle(surface, (114, 125, 111), loop[-1], 3, 1)
            _junction(surface, point, bool(fingerprint % 2))
    bodies = {}
    powered = []
    for obj in level.static_map.objects:
        if obj.kind != "Furniture":
            continue
        values = dict(obj.properties)
        w, h = values["width_tiles"], values["height_tiles"]
        assert isinstance(w, int) and isinstance(h, int)
        for x in range(obj.tile[0], obj.tile[0] + w):
            for y in range(obj.tile[1], obj.tile[1] + h):
                bodies[x, y] = obj.object_id
        if values["style"] in POWERED and values.get("appearance") != "displaced-chair":
            powered.append(obj)
    visuals = {item.object_id: item for item in furnishings}
    for obj in powered:
        _equipment_feed(surface, level, obj, bodies, visuals.get(obj.object_id))
