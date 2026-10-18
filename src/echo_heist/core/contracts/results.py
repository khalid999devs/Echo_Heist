"""Committed step/results and a separate read-only presentation boundary."""

from dataclasses import dataclass
from enum import StrEnum

from echo_heist.core.contracts.events import GameEvent
from echo_heist.core.contracts.observations import EntityView, Observation
from echo_heist.core.contracts.world import MissionPhase, StaticMap


class RunOutcome(StrEnum):
    WIN = "WIN"
    CAPTURED = "CAPTURED"
    ABORTED = "ABORTED"


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


@dataclass(frozen=True, slots=True)
class PresentationSnapshot:
    """For UI/diagnostics only; never supplied to controllers or rollouts."""

    tick: int
    world_map: StaticMap
    actors: tuple[EntityView, ...]
    phase: MissionPhase
