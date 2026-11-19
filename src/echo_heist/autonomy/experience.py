"""The real ExperienceGateway: scored reports, run history, profiles and preferences.

Scores come only from the Simulation's own terminal result for the attempt that
just ended (see ``AutonomousMission``); this service never recomputes or
estimates them. A report is matched to the Flow's request by map, seed, mode,
outcome, elapsed ticks, tick rate and own tool counts, stored once per run key
and returned. Disk access happens on explicit calls and at the end of a run,
never while drawing.
"""

from collections import deque
from contextlib import suppress
from pathlib import Path

from echo_heist.core.contracts.autonomy.model import ControlMode
from echo_heist.core.contracts.autonomy.policy import (
    DeploymentRequest,
    PolicySelection,
    preset_name,
)
from echo_heist.core.contracts.config.scoring import ScoringRules
from echo_heist.core.contracts.experience.model import (
    DesktopPreferences,
    ResultRequest,
    RunReport,
    SavedProfile,
    ToolUsage,
)
from echo_heist.core.contracts.experience.ports import ExperienceUnavailable
from echo_heist.core.contracts.results import RunResult
from echo_heist.core.scoring.score import achievements
from echo_heist.infrastructure.persistence.experience import (
    HISTORY_FILE,
    MAX_HISTORY,
    MAX_PROFILES,
    PREFERENCES_FILE,
    PROFILES_FILE,
    HistoryStore,
    PreferenceStore,
    ProfileStore,
)


class ExperienceService:
    def __init__(
        self,
        map_id: str,
        scoring: ScoringRules,
        data_dir: Path | None,
        *,
        ticks_per_second: int = 30,
    ) -> None:
        self.map_id, self.scoring = map_id, scoring
        self.ticks_per_second = ticks_per_second
        self.profile_store = ProfileStore(data_dir / PROFILES_FILE if data_dir else None)
        self.history_store = HistoryStore(data_dir / HISTORY_FILE if data_dir else None)
        self.preference_store = PreferenceStore(data_dir / PREFERENCES_FILE if data_dir else None)
        # Finished attempts awaiting their report request (newest last).
        self._finished: deque[tuple[DeploymentRequest, RunResult, ToolUsage]] = deque(maxlen=8)
        self._reported: dict[str, RunReport] = {}
        self.profile_names: dict[PolicySelection, str] = {}

    # Fed by AutonomousMission when an attempt ends ------------------------
    def attempt_finished(
        self, request: DeploymentRequest, result: RunResult, tools: ToolUsage
    ) -> None:
        self._finished.append((request, result, tools))

    def _label(self, request: DeploymentRequest) -> str:
        if request.mode == ControlMode.HUMAN:
            return "Human"
        named = preset_name(request.policy)
        if named is not None:
            return named.title()
        return self.profile_names.get(request.policy, "Custom policy")[:24]

    # ExperienceGateway ----------------------------------------------------
    def report(self, request: ResultRequest) -> RunReport | None:
        existing = self._reported.get(request.run_key)
        if existing is not None:
            return existing if existing.matches(request) else None
        if request.map_id != self.map_id or request.ticks_per_second != self.ticks_per_second:
            return None
        match = next(
            (
                (deployment, result, tools)
                for deployment, result, tools in reversed(self._finished)
                if result.seed == request.seed
                and result.mode == request.mode.value
                and result.outcome == request.end.outcome
                and result.elapsed_ticks == request.end.elapsed_ticks
                and tools == request.tools
            ),
            None,
        )
        if match is None:
            return None
        deployment, result, tools = match
        self._finished.remove(match)
        report = RunReport(
            request.run_key,
            request.map_id,
            result,
            request.ticks_per_second,
            tools,
            achievements(result, self.scoring),
            self._label(deployment),
        )
        self._reported[request.run_key] = report
        if len(self._reported) > MAX_HISTORY:
            del self._reported[next(iter(self._reported))]
        try:
            history = self.history_store.load()
        except ExperienceUnavailable:
            history = ()  # damaged history was moved aside; keep this report
        # A failed history write never hides the authoritative score of this run;
        # in that case this run is simply missing from the saved history.
        with suppress(ExperienceUnavailable):
            self.history_store.save((report, *history)[:MAX_HISTORY])
        return report

    def history(self) -> tuple[RunReport, ...]:
        return self.history_store.load()

    def profiles(self) -> tuple[SavedProfile, ...]:
        profiles = self.profile_store.load()[1]
        self.profile_names = {p.policy: p.name for p in profiles}
        return profiles

    def save_profile(self, name: str, policy: PolicySelection) -> SavedProfile:
        """Saving an existing name (case-insensitive) updates that profile in place."""
        name = name.strip()
        SavedProfile("validation", name, policy)  # bounded printable name, before any IO
        next_id, profiles = self.profile_store.load()
        existing = next((p for p in profiles if p.name.casefold() == name.casefold()), None)
        if existing is not None:
            saved = SavedProfile(existing.profile_id, name, policy)
            updated = tuple(saved if p is existing else p for p in profiles)
        else:
            if len(profiles) >= MAX_PROFILES:
                raise ExperienceUnavailable(
                    f"At most {MAX_PROFILES} profiles can be saved; delete one first."
                )
            saved = SavedProfile(f"profile-{next_id}", name, policy)
            updated, next_id = (*profiles, saved), next_id + 1
        self.profile_store.save(next_id, updated)
        self.profile_names = {p.policy: p.name for p in updated}
        return saved

    def delete_profile(self, profile_id: str) -> None:
        next_id, profiles = self.profile_store.load()
        kept = tuple(p for p in profiles if p.profile_id != profile_id)
        if len(kept) == len(profiles):
            raise ExperienceUnavailable("That profile no longer exists.")
        self.profile_store.save(next_id, kept)
        self.profile_names = {p.policy: p.name for p in kept}

    def preferences(self) -> DesktopPreferences:
        return self.preference_store.load()

    def save_preferences(self, preferences: DesktopPreferences) -> None:
        self.preference_store.save(preferences)
