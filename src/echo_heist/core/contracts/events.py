"""Immutable committed events and evidence with original observation timestamps."""

from dataclasses import dataclass
from enum import StrEnum

from echo_heist.core.contracts.world import Scalar, Tile, immutable_properties, immutable_tile


class EventKind(StrEnum):
    ACTION_ACCEPTED = "ACTION_ACCEPTED"
    ACTION_REJECTED = "ACTION_REJECTED"
    ACTOR_MOVED = "ACTOR_MOVED"
    STAIR_USED = "STAIR_USED"
    CORE_TAKEN = "CORE_TAKEN"
    NOISE_CREATED = "NOISE_CREATED"
    SIGHTING_CONFIRMED = "SIGHTING_CONFIRMED"
    REPORT_SENT = "REPORT_SENT"
    CAPTURE_STARTED = "CAPTURE_STARTED"
    CAPTURE_CANCELED = "CAPTURE_CANCELED"
    CAPTURE_COMPLETED = "CAPTURE_COMPLETED"
    GUARD_DISABLED = "GUARD_DISABLED"
    GUARD_STUNNED = "GUARD_STUNNED"
    TOOL_USED = "TOOL_USED"
    LOCKDOWN_STARTED = "LOCKDOWN_STARTED"
    MISSION_ENDED = "MISSION_ENDED"
    POLICY_DECISION = "POLICY_DECISION"


@dataclass(frozen=True, slots=True)
class GameEvent:
    event_id: str
    tick: int
    kind: EventKind
    actor_id: str
    details: tuple[tuple[str, Scalar], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", immutable_properties(self.details))


@dataclass(frozen=True, slots=True)
class HeardCue:
    event_id: str
    kind: str
    tile: Tile
    tick: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "tile", immutable_tile(self.tile))


@dataclass(frozen=True, slots=True)
class SecurityReport:
    source_guard: str
    report_kind: str
    tile: Tile
    tick: int
    confidence: float
    event_id: str
    expires_at_tick: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "tile", immutable_tile(self.tile))
        if not 0 <= self.confidence <= 1 or self.expires_at_tick < self.tick:
            raise ValueError("Report confidence or expiry is invalid")
