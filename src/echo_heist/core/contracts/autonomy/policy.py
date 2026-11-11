"""Validated deployment selections; interpretation and persistence belong to logic."""

from dataclasses import dataclass
from enum import StrEnum

from echo_heist.core.contracts.autonomy.model import ControlMode


class Navigation(StrEnum):
    SAFEST = "SAFEST"
    BALANCED = "BALANCED"
    SHORTEST = "SHORTEST"


class GuardReaction(StrEnum):
    HIDE = "HIDE"
    RETREAT = "RETREAT"
    CONSIDER_ECHO = "CONSIDER_ECHO"


class Emergency(StrEnum):
    ESCAPE = "ESCAPE"
    MELEE_IF_ADJACENT = "MELEE_IF_ADJACENT"
    EMP_IF_TRAPPED = "EMP_IF_TRAPPED"


class Risk(StrEnum):
    CAUTIOUS = "CAUTIOUS"
    BALANCED = "BALANCED"
    BOLD = "BOLD"


@dataclass(frozen=True, slots=True)
class PolicySelection:
    navigation: Navigation = Navigation.BALANCED
    guard_reaction: GuardReaction = GuardReaction.RETREAT
    emergency: Emergency = Emergency.EMP_IF_TRAPPED
    risk: Risk = Risk.BALANCED

    def __post_init__(self) -> None:
        for name, kind in (
            ("navigation", Navigation),
            ("guard_reaction", GuardReaction),
            ("emergency", Emergency),
            ("risk", Risk),
        ):
            object.__setattr__(self, name, kind(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class DeploymentRequest:
    mode: ControlMode
    seed: int
    map_id: str
    policy: PolicySelection = PolicySelection()

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", ControlMode(self.mode))
        if type(self.seed) is not int or not self.map_id:
            raise ValueError("Deployment needs an integer seed and map identity")


# Documented starting presets (blueprint p. 14); not secret buffs.
PRESETS: dict[str, PolicySelection] = {
    "GHOST": PolicySelection(
        Navigation.SAFEST, GuardReaction.HIDE, Emergency.ESCAPE, Risk.CAUTIOUS
    ),
    "BALANCED": PolicySelection(),
    "RUSH": PolicySelection(
        Navigation.SHORTEST, GuardReaction.CONSIDER_ECHO, Emergency.MELEE_IF_ADJACENT, Risk.BOLD
    ),
}


def preset_name(policy: PolicySelection) -> str | None:
    return next((name for name, value in PRESETS.items() if value == policy), None)
