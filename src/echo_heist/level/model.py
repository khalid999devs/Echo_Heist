"""Validated static level values; Simulation owns every live mutation."""

from dataclasses import dataclass

from echo_heist.core.contracts.results import MissionSpec
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, StaticMap, Tile

ZONE_IDS = ("entry", "service-wing", "security-control", "research-floor", "core-chamber")
GUARD_KINDS = frozenset({ActorKind.SENTINEL, ActorKind.TRACKER, ActorKind.INTERCEPTOR})
FURNITURE_STYLES = frozenset(
    {
        "rack",
        "console",
        "tank",
        "crates",
        "plant",
        "workbench",
        "desk",
        "planter",
        "labbench",
        "pump",
        "shelf",
        "railing",
    }
)
ROOM_STYLES = frozenset(
    {"reception", "storage", "maintenance", "server", "office", "laboratory", "reactor"}
)
DETAIL_STYLES = frozenset({"stairs", "grate", "cables", "threshold", "aftermath", "utility"})
FURNITURE_APPEARANCES = frozenset(
    {
        "standard",
        "hiding-desk",
        "centrifuge",
        "spectrometer",
        "fume-hood",
        "freezer",
        "vacuum",
        "robot-arm",
        "cable-cabinet",
        "screen",
        "sample-drawers",
        "coolant",
        "security-console",
        "reagents",
        "displaced-chair",
        "abandoned-station",
        "sample-cart",
        "broken-console",
        "wilted-plant",
        "unfinished-bench",
    }
)
FURNITURE_CONDITIONS = frozenset({"kept", "used", "dusty", "interrupted"})


@dataclass(frozen=True, slots=True)
class Zone:
    zone_id: str
    label: str
    left: int
    top: int
    width: int
    height: int

    def contains(self, tile: Tile) -> bool:
        return (
            self.left <= tile[0] < self.left + self.width
            and self.top <= tile[1] < self.top + self.height
        )


@dataclass(frozen=True, slots=True)
class PatrolRoute:
    """Ordered axis-aligned waypoints; P03 drives guards along them."""

    route_id: str
    points: tuple[Tile, ...]

    def tiles(self) -> tuple[Tile, ...]:
        visited: list[Tile] = [self.points[0]]
        for start, end in zip(self.points, self.points[1:], strict=False):
            dx = (end[0] > start[0]) - (end[0] < start[0])
            dy = (end[1] > start[1]) - (end[1] < start[1])
            x, y = start
            while (x, y) != end:
                x, y = x + dx, y + dy
                visited.append((x, y))
        return tuple(visited)


@dataclass(frozen=True, slots=True)
class GuardPost:
    guard_id: str
    kind: ActorKind
    tile: Tile
    route_id: str


@dataclass(frozen=True, slots=True)
class Chokepoint:
    point_id: str
    tile: Tile
    zones: tuple[str, str]


@dataclass(frozen=True, slots=True)
class Marker:
    """Cover or HideSpot position; hiding behavior itself arrives with P05."""

    marker_id: str
    kind: str
    tile: Tile


@dataclass(frozen=True, slots=True)
class Room:
    room_id: str
    label: str
    style: str
    left: int
    top: int
    width: int
    height: int

    def contains(self, tile: Tile) -> bool:
        return (
            self.left <= tile[0] < self.left + self.width
            and self.top <= tile[1] < self.top + self.height
        )


@dataclass(frozen=True, slots=True)
class FloorDetail:
    detail_id: str
    style: str
    left: int
    top: int
    width: int
    height: int
    rotation: int = 0


@dataclass(frozen=True, slots=True)
class Deck:
    deck_id: str
    label: str
    left: int
    top: int
    width: int
    height: int

    def contains(self, tile: Tile) -> bool:
        return (
            self.left <= tile[0] < self.left + self.width
            and self.top <= tile[1] < self.top + self.height
        )


@dataclass(frozen=True, slots=True)
class LevelData:
    static_map: StaticMap
    operative_id: str
    spawn_id: str
    spawn_tile: Tile
    core_id: str
    exit_id: str
    zones: tuple[Zone, ...]
    routes: tuple[PatrolRoute, ...]
    guards: tuple[GuardPost, ...]
    chokepoints: tuple[Chokepoint, ...]
    markers: tuple[Marker, ...]
    floor_tiles: frozenset[Tile]
    glass_tiles: frozenset[Tile]
    cover_tiles: frozenset[Tile]
    sound_blocking_tiles: frozenset[Tile]
    rooms: tuple[Room, ...] = ()
    floor_details: tuple[FloorDetail, ...] = ()
    decks: tuple[Deck, ...] = ()

    def deck_at(self, tile: Tile) -> Deck | None:
        return next((deck for deck in self.decks if deck.contains(tile)), None)

    def spawns(self) -> tuple[ActorSpawn, ...]:
        operative = ActorSpawn(self.operative_id, self.spawn_tile, ActorKind.OPERATIVE)
        posts = tuple(ActorSpawn(post.guard_id, post.tile, post.kind) for post in self.guards)
        return (operative, *posts)

    def mission(self, mode: str = "HUMAN") -> MissionSpec:
        return MissionSpec(self.operative_id, self.core_id, self.exit_id, mode=mode)

    def zone_at(self, tile: Tile) -> Zone | None:
        return next((zone for zone in self.zones if zone.contains(tile)), None)

    def room_at(self, tile: Tile) -> Room | None:
        return next((room for room in self.rooms if room.contains(tile)), None)
