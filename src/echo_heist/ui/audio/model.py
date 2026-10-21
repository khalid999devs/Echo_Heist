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
    listener_id: str = "operative"
    audible_event_ids: frozenset[str] = frozenset()
    room_style: str = ""
    sprint_recharge_remaining: int = 0
    settings_values: tuple[float, float, bool, bool] = (0.5, 0.7, False, False)
    suspicious: bool = False
    ui_feedback_serial: int = 0
    ui_feedback_cue: str = "hover"
