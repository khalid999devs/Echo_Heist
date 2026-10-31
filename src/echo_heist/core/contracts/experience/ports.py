"""Suhita supplies actual score/profile/preferences persistence through this port."""

from typing import Protocol

from echo_heist.core.contracts.autonomy.policy import PolicySelection
from echo_heist.core.contracts.experience.model import (
    DesktopPreferences,
    ResultRequest,
    RunReport,
    SavedProfile,
)


class ExperienceUnavailable(RuntimeError):
    """An expected unavailable operation, IO failure or invalid saved-data recovery."""


class ExperienceGateway(Protocol):
    def report(self, request: ResultRequest) -> RunReport | None: ...
    def history(self) -> tuple[RunReport, ...]: ...
    def profiles(self) -> tuple[SavedProfile, ...]: ...
    def save_profile(self, name: str, policy: PolicySelection) -> SavedProfile: ...
    def delete_profile(self, profile_id: str) -> None: ...
    def preferences(self) -> DesktopPreferences: ...
    def save_preferences(self, preferences: DesktopPreferences) -> None: ...
