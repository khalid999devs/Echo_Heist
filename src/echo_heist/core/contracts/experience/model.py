"""Immutable result/profile/preferences data; no scoring or storage implementation."""

from dataclasses import dataclass
from enum import StrEnum

from echo_heist.core.contracts.autonomy.model import ControlMode
from echo_heist.core.contracts.autonomy.policy import PolicySelection
from echo_heist.core.contracts.results import MissionEnd, RunOutcome, RunResult


def text(value: str, limit: int) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > limit
        or any(ord(c) < 32 for c in value)
    ):
        raise ValueError("Text must be nonempty, bounded and single-line")


def count(value: int) -> None:
    if type(value) is not int or not 0 <= value <= 2**31 - 1:
        raise ValueError("Expected a bounded nonnegative integer")


class Achievement(StrEnum):
    GHOST = "GHOST"
    AI_MASTER = "AI_MASTER"
    SPEEDRUNNER = "SPEEDRUNNER"


@dataclass(frozen=True, slots=True)
class ToolUsage:
    echo: int = 0
    emp: int = 0
    melee: int = 0

    def __post_init__(self) -> None:
        for value in (self.echo, self.emp, self.melee):
            count(value)


@dataclass(frozen=True, slots=True)
class ResultRequest:
    run_key: str
    map_id: str
    seed: int
    mode: ControlMode
    end: MissionEnd
    ticks_per_second: int
    tools: ToolUsage = ToolUsage()

    def __post_init__(self) -> None:
        text(self.run_key, 96)
        text(self.map_id, 96)
        count(self.end.elapsed_ticks)
        if type(self.seed) is not int or not 1 <= self.ticks_per_second <= 240:
            raise ValueError("Result metadata needs an integer seed and supported tick rate")
        object.__setattr__(self, "mode", ControlMode(self.mode))


@dataclass(frozen=True, slots=True)
class RunReport:
    """Only the backend supplies score, grade, encounter totals and achievements."""

    run_key: str
    map_id: str
    result: RunResult
    ticks_per_second: int
    tools: ToolUsage = ToolUsage()
    achievements: tuple[Achievement, ...] = ()
    policy_label: str = "Current policy"

    def __post_init__(self) -> None:
        text(self.run_key, 96)
        text(self.map_id, 96)
        text(self.policy_label, 24)
        if not 1 <= self.ticks_per_second <= 240:
            raise ValueError("Unsupported result tick rate")
        r = self.result
        ControlMode(r.mode)
        RunOutcome(r.outcome)
        for value in (
            r.elapsed_ticks,
            r.score,
            r.detection_encounters,
            r.completion_points,
            r.stealth_points,
            r.pace_points,
        ):
            count(value)
        if not (r.scoring_version > 0 and r.pace_reference_ticks > 0):
            raise ValueError("Results must identify scoring and pace versions")
        if r.score != r.completion_points + r.stealth_points + r.pace_points:
            raise ValueError("Reported score components disagree")
        if r.outcome == RunOutcome.WIN:
            bands = {"S": (90, 100), "A": (75, 89), "B": (60, 74), "C": (50, 59)}
            if r.grade not in bands or not bands[r.grade][0] <= r.score <= bands[r.grade][1]:
                raise ValueError("Reported grade disagrees with approved score bands")
            if r.completion_points != 50 or r.stealth_points > 40 or r.pace_points > 10:
                raise ValueError("Reported components exceed the approved contract")
        elif r.score != 0 or r.grade != "F":
            raise ValueError("An unsuccessful run cannot receive a success score/grade")
        achievements = tuple(Achievement(value) for value in self.achievements)
        if len(set(achievements)) != len(achievements) or (
            r.outcome != RunOutcome.WIN and achievements
        ):
            raise ValueError("Achievements must be unique and win-only")
        object.__setattr__(self, "achievements", achievements)

    def matches(self, request: ResultRequest) -> bool:
        r = self.result
        return (
            self.run_key == request.run_key
            and self.map_id == request.map_id
            and r.seed == request.seed
            and r.mode == request.mode
            and r.outcome == request.end.outcome
            and r.elapsed_ticks == request.end.elapsed_ticks
            and self.ticks_per_second == request.ticks_per_second
            and self.tools == request.tools
        )


@dataclass(frozen=True, slots=True)
class SavedProfile:
    profile_id: str
    name: str
    policy: PolicySelection

    def __post_init__(self) -> None:
        text(self.profile_id, 96)
        text(self.name, 24)


@dataclass(frozen=True, slots=True)
class KeyAssignment:
    action: str
    keys: tuple[int, ...]

    def __post_init__(self) -> None:
        text(self.action, 24)
        object.__setattr__(self, "keys", tuple(self.keys))
        if not self.keys or any(type(key) is not int or not 0 <= key < 2**31 for key in self.keys):
            raise ValueError("Key assignments need supported integer keycodes")


@dataclass(frozen=True, slots=True)
class DesktopPreferences:
    controls: tuple[KeyAssignment, ...] = ()
    subtitles: bool = True
    high_contrast: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "controls", tuple(self.controls))
        if len({item.action for item in self.controls}) != len(self.controls):
            raise ValueError("Duplicate control assignment")
        if type(self.subtitles) is not bool or type(self.high_contrast) is not bool:
            raise ValueError("Accessibility switches must be booleans")
