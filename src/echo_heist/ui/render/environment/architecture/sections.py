"""Cutaway wall caps, front elevations and floor-level architectural contacts."""

from functools import lru_cache
from io import BytesIO

import pygame

from echo_heist.infrastructure.resources import resource_bytes
from echo_heist.level.model import LevelData


@lru_cache(maxsize=4)
def wall_skin(size: int) -> pygame.Surface:
    source = pygame.image.load(BytesIO(resource_bytes("assets/tiles/bulkhead.png")))
    skin = pygame.transform.smoothscale(source, (size, size))
    skin.fill((147, 150, 139), special_flags=pygame.BLEND_RGB_MULT)
    return skin


def paint_mounts(surface: pygame.Surface, level: LevelData) -> None:
    """Bolted equipment bases and short covered service feeds; no new obstacles."""
    size = level.static_map.tile_size_px
    for obj in level.static_map.objects:
        if obj.kind != "Furniture":
            continue
        data = dict(obj.properties)
        if data.get("style") not in ("pump", "tank", "rack", "labbench"):
            continue
        room = level.room_at(obj.tile)
        if room is None:
            continue
        width, height = data["width_tiles"], data["height_tiles"]
        assert isinstance(width, int) and isinstance(height, int)
        rect = pygame.Rect(obj.tile[0] * size, obj.tile[1] * size, width * size, height * size)
        if data["style"] in ("pump", "tank", "rack"):
            plinth = rect.inflate(-14, -10)
            pygame.draw.rect(surface, (48, 55, 52), plinth, border_radius=4)
            pygame.draw.rect(surface, (88, 96, 86), plinth, 1, border_radius=4)
            pygame.draw.line(surface, (27, 36, 34), plinth.bottomleft, plinth.bottomright, 3)
            for point in (plinth.topleft, plinth.topright, plinth.bottomleft, plinth.bottomright):
                pygame.draw.circle(
                    surface,
                    (111, 117, 103),
                    (
                        point[0] + (4 if point[0] == plinth.left else -4),
                        point[1] + (4 if point[1] == plinth.top else -4),
                    ),
                    2,
                )
        endpoint = (rect.centerx, rect.top + 5)
        feeds = (
            (endpoint[0], room.top * size),
            (room.left * size, endpoint[1]),
            ((room.left + room.width) * size, endpoint[1]),
        )
        start = min(feeds, key=lambda p: abs(p[0] - endpoint[0]) + abs(p[1] - endpoint[1]))
        if abs(start[0] - endpoint[0]) + abs(start[1] - endpoint[1]) <= size * 2:
            pygame.draw.line(surface, (28, 35, 33), start, endpoint, 6)
            pygame.draw.line(surface, (80, 90, 83), start, endpoint, 3)
            pygame.draw.circle(surface, (127, 136, 119), endpoint, 4)


def wall_section(surface: pygame.Surface, level: LevelData, tile: tuple[int, int]) -> None:
    size = level.static_map.tile_size_px
    x, y = tile
    rect = pygame.Rect(x * size, y * size, size, size)
    below = (x, y + 1) in level.floor_tiles
    above = (x, y - 1) in level.floor_tiles
    left = (x - 1, y) in level.floor_tiles
    right = (x + 1, y) in level.floor_tiles
    surface.fill((20, 25, 26), rect)
    cap = rect.copy()
    cap.h = round(size * 0.57) if below else size
    skin = wall_skin(size * 4)
    surface.blit(
        skin, cap.topleft, (cap.x % skin.get_width(), cap.y % skin.get_height(), cap.w, cap.h)
    )
    pygame.draw.line(surface, (67, 73, 69), cap.topleft, cap.topright, 2)
    if below:
        face = pygame.Rect(rect.x, cap.bottom, size, rect.bottom - cap.bottom)
        for row in range(face.h):
            value = 30 + row * 9 // max(1, face.h)
            pygame.draw.line(
                surface,
                (value, value + 6, value + 6),
                (face.x, face.y + row),
                (face.right, face.y + row),
            )
        pygame.draw.line(surface, (90, 99, 91), face.topleft, face.topright, 3)
        pygame.draw.line(surface, (9, 16, 18), face.bottomleft, face.bottomright, 5)
        pygame.draw.line(
            surface, (87, 94, 85), (face.x, face.bottom - 5), (face.right, face.bottom - 5)
        )
        if x % 3 == 1:
            panel = pygame.Rect(face.x + 13, face.y + 9, size - 26, max(8, face.h - 18))
            pygame.draw.rect(surface, (22, 30, 31), panel, border_radius=2)
            pygame.draw.rect(surface, (52, 61, 58), panel, 1, border_radius=2)
    if above:
        pygame.draw.line(surface, (70, 78, 72), rect.topleft, rect.topright, 3)
    if left:
        pygame.draw.line(surface, (61, 70, 64), rect.topleft, rect.bottomleft, 4)
        pygame.draw.line(
            surface, (12, 21, 23), (rect.left + 4, rect.top), (rect.left + 4, rect.bottom), 4
        )
    if right:
        pygame.draw.line(surface, (73, 82, 75), rect.topright, rect.bottomright, 4)
        pygame.draw.line(
            surface, (11, 20, 22), (rect.right - 5, rect.top), (rect.right - 5, rect.bottom), 4
        )
