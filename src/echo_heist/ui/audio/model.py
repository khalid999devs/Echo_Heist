"""Immutable audio input assembled from scene state and committed simulation events."""

from dataclasses import dataclass

from echo_heist.core.contracts.events import GameEvent
from echo_heist.core.contracts.results import RunOutcome
from echo_heist.core.contracts.world import MissionPhase


@dataclass(frozen=True, slots=True)
class AudioFrame:
    scene: str
    selection: str
    run_id: int
    phase: MissionPhase | None = None
    paused: bool = False
    alerted: bool = False
    outcome: RunOutcome | None = None
    events: tuple[GameEvent, ...] = ()
