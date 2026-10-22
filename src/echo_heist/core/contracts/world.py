"""Static map boundary for the future Tiled loader; never a live world reference."""

from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import field as data_field
from enum import StrEnum
from math import isfinite
from types import MappingProxyType

type Tile = tuple[int, int]
type Position = tuple[int, int]
type Scalar = str | int | float | bool | None
SIMULATION_HZ = 30
POSITION_UNITS_PER_TILE = 30_000


def tile_center(tile: Tile) -> Position:
    half = POSITION_UNITS_PER_TILE // 2
    return tile[0] * POSITION_UNITS_PER_TILE + half, tile[1] * POSITION_UNITS_PER_TILE + half


def position_tile(position: Position) -> Tile:
    return position[0] // POSITION_UNITS_PER_TILE, position[1] // POSITION_UNITS_PER_TILE


class ActorKind(StrEnum):
    OPERATIVE = "OPERATIVE"
    COMPANION = "COMPANION"
    SENTINEL = "SENTINEL"
    TRACKER = "TRACKER"
    INTERCEPTOR = "INTERCEPTOR"


class MissionPhase(StrEnum):
    INFILTRATE = "INFILTRATE"
    LOCKDOWN = "LOCKDOWN"
    WON = "WON"
    CAPTURED = "CAPTURED"
    ABORTED = "ABORTED"


def immutable_tile(tile: Tile) -> Tile:
    x, y = tile
    if type(x) is not int or type(y) is not int:
        raise ValueError("Tile coordinates must be integers")
    return x, y


def immutable_properties(values: tuple[tuple[str, Scalar], ...]) -> tuple[tuple[str, Scalar], ...]:
    frozen = tuple((key, value) for key, value in values)
    for key, value in frozen:
        if not isinstance(key, str) or not isinstance(value, (str, int, float, bool, type(None))):
            raise ValueError("Properties must be named immutable scalar values")
        if isinstance(value, float) and not isfinite(value):
            raise ValueError("Properties must be finite")
    return frozen


@dataclass(frozen=True, slots=True)
class Inventory:
    echo_charges: int = 3
    emp_charges: int = 1
    core_held: bool = False


@dataclass(frozen=True, slots=True)
class MapObject:
    object_id: str
    kind: str
    tile: Tile
    properties: tuple[tuple[str, Scalar], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "tile", immutable_tile(self.tile))
        object.__setattr__(self, "properties", immutable_properties(self.properties))


@dataclass(frozen=True, slots=True)
class StairLink:
    object_id: str
    tile: Tile
    destination_id: str
    destination: Tile

    def __post_init__(self) -> None:
        object.__setattr__(self, "tile", immutable_tile(self.tile))
        object.__setattr__(self, "destination", immutable_tile(self.destination))


@dataclass(frozen=True, slots=True)
class ObstacleBounds:
    object_id: str
    left: int
    top: int
    right: int
    bottom: int
    reserved_tiles: frozenset[Tile]
    opaque: bool = True

    def __post_init__(self) -> None:
        tiles = frozenset(immutable_tile(tile) for tile in self.reserved_tiles)
        object.__setattr__(self, "reserved_tiles", tiles)
        if any(type(value) is not int for value in (self.left, self.top, self.right, self.bottom)):
            raise ValueError("Obstacle bounds must be integer simulation units")
        if (
            not self.object_id
            or not tiles
            or not (0 <= self.left < self.right and 0 <= self.top < self.bottom)
        ):
            raise ValueError("Obstacle needs positive bounds and reserved tiles")
        unit = POSITION_UNITS_PER_TILE
        if any(
            (x, y) not in tiles
            for x in range(self.left // unit, (self.right - 1) // unit + 1)
            for y in range(self.top // unit, (self.bottom - 1) // unit + 1)
        ):
            raise ValueError("Obstacle bounds extend beyond their reserved tiles")

    def contains(self, point: Position) -> bool:
        return self.left <= point[0] < self.right and self.top <= point[1] < self.bottom


@dataclass(frozen=True, slots=True)
class StaticMap:
    map_id: str
    width: int
    height: int
    blocked_tiles: frozenset[Tile] = frozenset()
    opaque_tiles: frozenset[Tile] = frozenset()
    objects: tuple[MapObject, ...] = ()
    tile_size_px: int = 32
    stairs: tuple[StairLink, ...] = ()
    crouch_tiles: frozenset[Tile] = frozenset()
    obstacles: tuple[ObstacleBounds, ...] = ()
    obstacle_index: Mapping[Tile, tuple[ObstacleBounds, ...]] = data_field(
        init=False, repr=False, compare=False
    )
    hard_blocked: frozenset[Tile] = data_field(init=False, repr=False)
    hard_opaque: frozenset[Tile] = data_field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0 or self.tile_size_px <= 0:
            raise ValueError("Map dimensions and tile size must be positive")
        for field in ("blocked_tiles", "opaque_tiles"):
            tiles = frozenset(immutable_tile(tile) for tile in getattr(self, field))
            if any(not self.contains(tile) for tile in tiles):
                raise ValueError("Map flags contain an out-of-bounds tile")
            object.__setattr__(self, field, tiles)
        object.__setattr__(self, "objects", tuple(self.objects))
        crouch_tiles = frozenset(immutable_tile(tile) for tile in self.crouch_tiles)
        if not crouch_tiles <= self.blocked_tiles & self.opaque_tiles:
            raise ValueError("Under-desk space must be inside solid, opaque furniture")
        object.__setattr__(self, "crouch_tiles", crouch_tiles)
        object.__setattr__(self, "obstacles", tuple(self.obstacles))
        index: dict[Tile, list[ObstacleBounds]] = {}
        if len({obstacle.object_id for obstacle in self.obstacles}) != len(self.obstacles):
            raise ValueError("Duplicate obstacle ID")
        for obstacle in self.obstacles:
            if not obstacle.reserved_tiles <= self.blocked_tiles:
                raise ValueError("Obstacle must reserve blocked map tiles")
            for tile in obstacle.reserved_tiles:
                index.setdefault(tile, []).append(obstacle)
        object.__setattr__(
            self,
            "obstacle_index",
            MappingProxyType({tile: tuple(values) for tile, values in index.items()}),
        )
        object.__setattr__(self, "hard_blocked", frozenset(self.blocked_tiles - index.keys()))
        object.__setattr__(self, "hard_opaque", frozenset(self.opaque_tiles - index.keys()))
        if any(not self.contains(obj.tile) for obj in self.objects):
            raise ValueError("Map object is outside the map")
        object.__setattr__(self, "stairs", tuple(self.stairs))
        links = {link.object_id: link for link in self.stairs}
        if len(links) != len(self.stairs) or len({s.tile for s in self.stairs}) != len(links):
            raise ValueError("Stair IDs and landing tiles must be unique")
        for link in self.stairs:
            other = links.get(link.destination_id)
            if (
                other is None
                or other.destination_id != link.object_id
                or other.tile != link.destination
                or other.destination != link.tile
                or link.tile == link.destination
                or not self.contains(link.tile)
                or not self.contains(link.destination)
            ):
                raise ValueError("Stairs need reciprocal, distinct in-bounds landings")

    def connections(self, tile: Tile) -> tuple[Tile, ...]:
        x, y = tile
        steps = ((x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y))
        return steps + tuple(link.destination for link in self.stairs if link.tile == tile)

    def contains(self, tile: Tile) -> bool:
        return 0 <= tile[0] < self.width and 0 <= tile[1] < self.height

    def can_walk(self, tile: Tile, *, crouched: bool = False) -> bool:
        return self.contains(tile) and (
            tile not in self.blocked_tiles or (crouched and tile in self.crouch_tiles)
        )

    def point_blocked(self, point: Position, *, vision: bool = False) -> bool:
        tile = position_tile(point)
        return (
            not self.contains(tile)
            or tile in (self.hard_opaque if vision else self.hard_blocked)
            or any(
                obstacle.contains(point) and (not vision or obstacle.opaque)
                for obstacle in self.obstacle_index.get(tile, ())
            )
        )


@dataclass(frozen=True, slots=True)
class ActorSpawn:
    actor_id: str
    tile: Tile
    kind: ActorKind = ActorKind.OPERATIVE

    def __post_init__(self) -> None:
        if not self.actor_id:
            raise ValueError("Actor ID must not be empty")
        object.__setattr__(self, "tile", immutable_tile(self.tile))
