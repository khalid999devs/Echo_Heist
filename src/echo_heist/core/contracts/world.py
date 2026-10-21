"""Static map boundary for the future Tiled loader; never a live world reference."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

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


@dataclass(frozen=True, slots=True)
class ActorSpawn:
    actor_id: str
    tile: Tile
    kind: ActorKind = ActorKind.OPERATIVE

    def __post_init__(self) -> None:
        if not self.actor_id:
            raise ValueError("Actor ID must not be empty")
        object.__setattr__(self, "tile", immutable_tile(self.tile))
