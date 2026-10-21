"""Committed step/results and a separate read-only presentation boundary."""

from dataclasses import dataclass
from enum import StrEnum

from echo_heist.core.contracts.events import GameEvent
from echo_heist.core.contracts.observations import EntityView, Observation
from echo_heist.core.contracts.security.model import GuardView
from echo_heist.core.contracts.world import MissionPhase, Position, StaticMap, Tile, immutable_tile


class RunOutcome(StrEnum):
    WIN = "WIN"
    CAPTURED = "CAPTURED"
    ABORTED = "ABORTED"


@dataclass(frozen=True, slots=True)
class MissionSpec:
    operative_id: str
    core_object_id: str
    exit_object_id: str
    mode: str = "HUMAN"


@dataclass(frozen=True, slots=True)
class MissionEnd:
    """Unscored outcome; real RunResult scoring is added in P06."""

    outcome: RunOutcome
    elapsed_ticks: int
    operative_id: str
    capture_by: str | None = None


@dataclass(frozen=True, slots=True)
class EchoView:
    echo_id: str
    position: Position
    remaining_ticks: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "position", immutable_tile(self.position))


@dataclass(frozen=True, slots=True)
class CaptureView:
    guard_id: str
    target_id: str
    remaining_ticks: int
    total_ticks: int


@dataclass(frozen=True, slots=True)
class StairView:
    actor_id: str
    source: Tile
    destination: Tile
    remaining_ticks: int
    total_ticks: int


@dataclass(frozen=True, slots=True)
class RunResult:
    mode: str
    seed: int
    outcome: RunOutcome
    elapsed_ticks: int
    score: int
    grade: str
    detection_encounters: int
    completion_points: int
    stealth_points: int
    pace_points: int
    scoring_version: int
    pace_reference_ticks: int
    policy_id: str | None = None
    decisive_events: tuple[GameEvent, ...] = ()


@dataclass(frozen=True, slots=True)
class StepResult:
    tick: int
    events: tuple[GameEvent, ...]
    observations: tuple[Observation, ...]
    terminal: RunResult | None = None
    mission_end: MissionEnd | None = None


@dataclass(frozen=True, slots=True)
class PresentationSnapshot:
    """For UI/diagnostics only; never supplied to controllers or rollouts."""

    tick: int
    world_map: StaticMap
    actors: tuple[EntityView, ...]
    phase: MissionPhase
    echoes: tuple[EchoView, ...] = ()
    captures: tuple[CaptureView, ...] = ()
    core_owner: str | None = None
    mission_end: MissionEnd | None = None
    guards: tuple[GuardView, ...] = ()
    stairs: tuple[StairView, ...] = ()
