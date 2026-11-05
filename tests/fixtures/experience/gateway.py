"""Explicit in-memory UI fixture, not scoring, algorithms or persistence evidence."""

from dataclasses import replace

from echo_heist.core.contracts.autonomy.model import ControlMode
from echo_heist.core.contracts.autonomy.policy import PolicySelection
from echo_heist.core.contracts.experience.model import (
    Achievement,
    DesktopPreferences,
    ResultRequest,
    RunReport,
    SavedProfile,
    ToolUsage,
)
from echo_heist.core.contracts.experience.ports import ExperienceUnavailable
from echo_heist.core.contracts.results import MissionEnd, RunOutcome, RunResult


def request() -> ResultRequest:
    return ResultRequest(
        "fixture:1",
        "vault-five-zone",
        1042,
        ControlMode.HUMAN,
        MissionEnd(RunOutcome.WIN, 3600, "operative"),
        30,
        ToolUsage(1, 2, 1),
    )


def report() -> RunReport:
    """A fixed, approved example; no production encounter/pace calculation here."""
    return RunReport(
        "fixture:1",
        "vault-five-zone",
        RunResult("HUMAN", 1042, RunOutcome.WIN, 3600, 100, "S", 0, 50, 40, 10, 1, 27000),
        30,
        ToolUsage(1, 2, 1),
        (Achievement.GHOST,),
        "Ghost",
    )


class MemoryGateway:
    def __init__(self) -> None:
        self.answer: RunReport | None = report()
        self.runs = (report(),)
        self.saved = (SavedProfile("fixture-policy", "Ghost", PolicySelection()),)
        self.prefs = DesktopPreferences()
        self.fail = False
        self.calls: list[str] = []

    def check(self, operation: str) -> None:
        self.calls.append(operation)
        if self.fail:
            raise ExperienceUnavailable("Fixture storage unavailable; retry later.")

    def report(self, request: ResultRequest) -> RunReport | None:
        self.check("report")
        return self.answer

    def history(self) -> tuple[RunReport, ...]:
        self.check("history")
        return self.runs

    def profiles(self) -> tuple[SavedProfile, ...]:
        self.check("profiles")
        return self.saved

    def save_profile(self, name: str, policy: PolicySelection) -> SavedProfile:
        self.check("save-profile")
        entry = SavedProfile(f"fixture-{len(self.saved)}", name, policy)
        self.saved = (*self.saved, entry)
        return entry

    def delete_profile(self, profile_id: str) -> None:
        self.check("delete-profile")
        self.saved = tuple(p for p in self.saved if p.profile_id != profile_id)

    def preferences(self) -> DesktopPreferences:
        self.check("preferences")
        return self.prefs

    def save_preferences(self, preferences: DesktopPreferences) -> None:
        self.check("save-preferences")
        self.prefs = replace(preferences)
