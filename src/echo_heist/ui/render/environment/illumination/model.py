"""One deterministic fixture layout shared by light pools and shadow projection.

These lights are cosmetic: they never alter guard sight, hearing or observations.
"""

from dataclasses import dataclass
from functools import lru_cache
from hashlib import blake2b
from math import atan2, cos, hypot, pi, sin

from echo_heist.level.model import LevelData, Room
from echo_heist.ui.render.actors.shadows import ShadowStyle


@dataclass(frozen=True, slots=True)
class Luminaire:
    position: tuple[int, int]
    color: tuple[int, int, int]
    radius: int
    ceiling: bool = False


@lru_cache(maxsize=64)
def room_lights(room: Room, size: int) -> tuple[Luminaire, ...]:
    """Alternate actual fixture walls, with diffuse ceiling fill in clinical rooms."""
    left, top = room.left * size, room.top * size
    width, height = room.width * size, room.height * size
    variant = int.from_bytes(blake2b(room.room_id.encode(), digest_size=2).digest(), "big")
    color = {
        "laboratory": (215, 231, 238),
        "office": (238, 219, 182),
        "reception": (225, 231, 222),
        "storage": (229, 196, 139),
        "maintenance": (233, 184, 110),
        "server": (132, 177, 218),
        "reactor": (99, 193, 220),
    }.get(room.style, (215, 211, 193))
    # Sources sit on the cutaway wall/edge, rather than floating inside the floor.
    offset = -max(5, size // 8)
    corners = (
        ((left + width // 3, top + offset), (left + width - offset, top + height * 2 // 3)),
        ((left + offset, top + height // 3), (left + width * 2 // 3, top + height - offset)),
        ((left + width * 2 // 3, top + offset), (left + offset, top + height * 2 // 3)),
        ((left + width - offset, top + height // 3), (left + width // 3, top + height - offset)),
    )[variant % 4]
    radius = max(size * 2, min(width, height))
    values = [Luminaire(point, color, radius) for point in corners]
    if room.style in ("laboratory", "reception", "office"):
        values.append(Luminaire((left + width // 2, top + height // 2), color, radius, True))
    return tuple(values)


def shadow_at(level: LevelData, position: tuple[float, float], height: int = 70) -> ShadowStyle:
    size = level.static_map.tile_size_px
    room = level.room_at((int(position[0] // size), int(position[1] // size)))
    if room is None:
        # Corridor strips are close to overhead: restrained contact, no fake key sun.
        return ShadowStyle(0, 4, 32)
    lamps = room_lights(room, size)
    ranked = sorted(
        lamps,
        key=lambda lamp: hypot(position[0] - lamp.position[0], position[1] - lamp.position[1]),
    )
    key = ranked[0]
    dx, dy = position[0] - key.position[0], position[1] - key.position[1]
    distance = hypot(dx, dy)
    if key.ceiling or distance < size * 0.4:
        return ShadowStyle(0, 3, 28)
    # High ceiling, short attached projections. Quantized keys bound raster caches.
    angle = round(atan2(dy, dx) / (pi / 8)) * pi / 8
    length = min(23, max(4, height * distance / (size * 9)))
    return ShadowStyle(
        round(cos(angle) * length), round(sin(angle) * length), 40 if len(ranked) > 1 else 56
    )
