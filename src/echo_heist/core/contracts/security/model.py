"""Security values cross boundaries without exposing the mutable simulation world."""

from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Self

from echo_heist.core.contracts.actions import Action
from echo_heist.core.contracts.world import Tile, immutable_tile


class GuardState(StrEnum):
    PATROL = "PATROL"
    INVESTIGATE = "INVESTIGATE"
    SPOTTED = "SPOTTED"
    CHASE = "CHASE"
    SEARCH = "SEARCH"
    RETURN = "RETURN"


@dataclass(frozen=True, slots=True)
class SensorRules:
    sight_range_tiles: int
    half_angle_degrees: int
    identification_ticks: int
    near_identification_ticks: int
    memory_ticks: int
    search_ticks: int
    report_ttl_ticks: int
    patrol_pause_ticks: int

    def __post_init__(self) -> None:
        if any(
            type(getattr(self, field.name)) is not int or not 0 < getattr(self, field.name) <= 1000
            for field in fields(self)
        ):
            raise ValueError("Security rules must be bounded positive integers")
        if not 0 < self.half_angle_degrees < 90:
            raise ValueError("Guard cone half angle must be between 0 and 90 degrees")

    @classmethod
    def from_payload(cls, payload: object) -> Self:
        if not isinstance(payload, dict) or set(payload) != {field.name for field in fields(cls)}:
            raise ValueError("Security config must contain exactly the supported fields")
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class GuardPatrol:
    actor_id: str
    points: tuple[Tile, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "points", tuple(immutable_tile(point) for point in self.points))
        if not self.actor_id or len(self.points) < 2:
            raise ValueError("A patrol needs an actor ID and at least two waypoints")


@dataclass(frozen=True, slots=True)
class SecuritySpec:
    patrols: tuple[GuardPatrol, ...]
    rules: SensorRules
    sound_blocking_tiles: frozenset[Tile] = frozenset()

    def __post_init__(self) -> None:
        object.__setattr__(self, "patrols", tuple(self.patrols))
        object.__setattr__(
            self,
            "sound_blocking_tiles",
            frozenset(immutable_tile(tile) for tile in self.sound_blocking_tiles),
        )
        if len({patrol.actor_id for patrol in self.patrols}) != len(self.patrols):
            raise ValueError("Duplicate active guard ID")


@dataclass(frozen=True, slots=True)
class VisualCue:
    cue_id: str
    tile: Tile
    tick: int
    kind: str = "UNIDENTIFIED_MOTION"

    def __post_init__(self) -> None:
        object.__setattr__(self, "tile", immutable_tile(self.tile))


@dataclass(frozen=True, slots=True)
class GuardMemory:
    state: GuardState = GuardState.PATROL
    patrol_index: int = 0
    identity_ticks: int = 0
    last_seen_tile: Tile | None = None
    last_seen_tick: int = -1
    target: Tile | None = None
    path: tuple[Tile, ...] = ()
    path_goal: Tile | None = None
    search_until: int = 0
    search_index: int = 0
    wait_until: int = 0
    urgency: float = 0.0
    expanded_nodes: int = 0
    last_report_tick: int = -1
    search_origin: Tile | None = None

    def __post_init__(self) -> None:
        for name in ("last_seen_tile", "target", "path_goal", "search_origin"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, immutable_tile(value))
        object.__setattr__(self, "path", tuple(immutable_tile(tile) for tile in self.path))


@dataclass(frozen=True, slots=True)
class GuardDecision:
    action: Action
    memory: GuardMemory
    facing: Tile


@dataclass(frozen=True, slots=True)
class GuardView:
    actor_id: str
    state: GuardState
    facing: Tile
    identification_ticks: int
    identification_required_ticks: int
    sight_range_tiles: int
    half_angle_degrees: int
    target: Tile | None
    last_seen_tile: Tile | None
    last_seen_tick: int
    path: tuple[Tile, ...]
    expanded_nodes: int
    fuzzy_urgency: float
