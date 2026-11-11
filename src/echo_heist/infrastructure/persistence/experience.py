"""Versioned profile, run-history and desktop-preference files (P06-SR2/SR3).

Every file is written atomically. A missing file is an empty/default store. A
damaged file is moved aside as ``<name>.corrupt-<ns>.json`` (never silently
discarded) and reported once; a file from a newer build is left untouched and
the store refuses to overwrite it. All expected failures become
``ExperienceUnavailable`` with a readable reason.
"""

import json
from collections.abc import Callable
from pathlib import Path
from time import time_ns
from typing import TypeVar

from echo_heist.core.contracts.autonomy.model import ControlMode
from echo_heist.core.contracts.autonomy.policy import (
    Emergency,
    GuardReaction,
    Navigation,
    PolicySelection,
    Risk,
)
from echo_heist.core.contracts.events import EventKind, GameEvent
from echo_heist.core.contracts.experience.model import (
    Achievement,
    DesktopPreferences,
    KeyAssignment,
    RunReport,
    SavedProfile,
    ToolUsage,
)
from echo_heist.core.contracts.experience.ports import ExperienceUnavailable
from echo_heist.core.contracts.results import RunOutcome, RunResult
from echo_heist.infrastructure.persistence.atomic import atomic_write_json

SCHEMA = 1
PROFILES_FILE = "policy-profiles.json"
HISTORY_FILE = "run-history.json"
PREFERENCES_FILE = "desktop-preferences.json"
MAX_PROFILES = 32
MAX_HISTORY = 100

T = TypeVar("T")


def encode_policy(policy: PolicySelection) -> dict[str, str]:
    return {
        "navigation": policy.navigation.value,
        "guard_reaction": policy.guard_reaction.value,
        "emergency": policy.emergency.value,
        "risk": policy.risk.value,
    }


def decode_policy(value: object) -> PolicySelection:
    if not isinstance(value, dict):
        raise ValueError("A policy must be an object of four enum names")
    return PolicySelection(
        Navigation(str(value["navigation"])),
        GuardReaction(str(value["guard_reaction"])),
        Emergency(str(value["emergency"])),
        Risk(str(value["risk"])),
    )


def _event(value: object) -> GameEvent:
    if not isinstance(value, dict) or not isinstance(value.get("details"), list):
        raise ValueError("Malformed decisive event")
    return GameEvent(
        str(value["event_id"]),
        int(value["tick"]),
        EventKind(str(value["kind"])),
        str(value["actor_id"]),
        tuple((str(k), v) for k, v in value["details"]),
    )


def encode_report(report: RunReport) -> dict[str, object]:
    r = report.result
    return {
        "run_key": report.run_key,
        "map_id": report.map_id,
        "ticks_per_second": report.ticks_per_second,
        "tools": [report.tools.echo, report.tools.emp, report.tools.melee],
        "achievements": [value.value for value in report.achievements],
        "policy_label": report.policy_label,
        "result": {
            "mode": r.mode,
            "seed": r.seed,
            "outcome": r.outcome.value,
            "elapsed_ticks": r.elapsed_ticks,
            "score": r.score,
            "grade": r.grade,
            "detection_encounters": r.detection_encounters,
            "completion_points": r.completion_points,
            "stealth_points": r.stealth_points,
            "pace_points": r.pace_points,
            "scoring_version": r.scoring_version,
            "pace_reference_ticks": r.pace_reference_ticks,
            "policy_id": r.policy_id,
            "decisive_events": [
                {
                    "event_id": e.event_id,
                    "tick": e.tick,
                    "kind": e.kind.value,
                    "actor_id": e.actor_id,
                    "details": [list(item) for item in e.details],
                }
                for e in r.decisive_events
            ],
        },
    }


def decode_report(value: object) -> RunReport:
    if not isinstance(value, dict) or not isinstance(value.get("result"), dict):
        raise ValueError("Malformed saved report")
    r = value["result"]
    tools = value["tools"]
    if not isinstance(tools, list) or len(tools) != 3:
        raise ValueError("Malformed tool counts")
    policy_id = r.get("policy_id")
    result = RunResult(
        ControlMode(str(r["mode"])).value,
        int(r["seed"]),
        RunOutcome(str(r["outcome"])),
        int(r["elapsed_ticks"]),
        int(r["score"]),
        str(r["grade"]),
        int(r["detection_encounters"]),
        int(r["completion_points"]),
        int(r["stealth_points"]),
        int(r["pace_points"]),
        int(r["scoring_version"]),
        int(r["pace_reference_ticks"]),
        None if policy_id is None else str(policy_id),
        tuple(_event(e) for e in r.get("decisive_events", [])),
    )
    return RunReport(
        str(value["run_key"]),
        str(value["map_id"]),
        result,
        int(value["ticks_per_second"]),
        ToolUsage(*(int(count) for count in tools)),
        tuple(Achievement(str(a)) for a in value.get("achievements", [])),
        str(value.get("policy_label", "Current policy")),
    )


class JsonStore:
    """One versioned JSON document with quarantine and newer-schema protection."""

    def __init__(self, path: Path | None, label: str) -> None:
        self.path, self.label = path, label
        self.blocked = ""  # a newer build's file: never overwritten
        self._memory: object | None = None

    def read(self, decode: Callable[[object], T], empty: T) -> T:
        if self.path is None:
            return decode(self._memory) if self._memory is not None else empty
        if self.blocked:
            raise ExperienceUnavailable(self.blocked)
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return empty
        except OSError as error:
            raise ExperienceUnavailable(f"{self.label} could not be read: {error}") from error
        try:
            payload = json.loads(text)
            schema = payload.get("schema") if isinstance(payload, dict) else None
            if type(schema) is int and schema > SCHEMA:
                self.blocked = (
                    f"{self.label} were saved by a newer build (schema {schema}); left unchanged."
                )
                raise ExperienceUnavailable(self.blocked)
            if schema != SCHEMA:
                raise ValueError("unsupported schema")
            return decode(payload)
        except ExperienceUnavailable:
            raise
        except (ValueError, TypeError, KeyError) as error:
            kept = self.path.with_name(f"{self.path.stem}.corrupt-{time_ns()}.json")
            try:
                self.path.replace(kept)
            except OSError as move_error:
                raise ExperienceUnavailable(
                    f"{self.label} are damaged and could not be moved aside: {move_error}"
                ) from move_error
            raise ExperienceUnavailable(
                f"{self.label} were damaged ({error}); kept as {kept.name} and started fresh."
            ) from error

    def write(self, payload: dict[str, object]) -> None:
        payload = {"schema": SCHEMA, **payload}
        if self.path is None:
            self._memory = json.loads(json.dumps(payload))
            return
        if self.blocked:
            raise ExperienceUnavailable(self.blocked)
        try:
            atomic_write_json(self.path, payload)
        except OSError as error:
            raise ExperienceUnavailable(f"{self.label} could not be saved: {error}") from error


class ProfileStore(JsonStore):
    def __init__(self, path: Path | None) -> None:
        super().__init__(path, "Saved policy profiles")

    @staticmethod
    def _decode(payload: object) -> tuple[int, tuple[SavedProfile, ...]]:
        if not isinstance(payload, dict) or not isinstance(payload.get("profiles"), list):
            raise ValueError("profiles list missing")
        profiles = tuple(
            SavedProfile(str(item["id"]), str(item["name"]), decode_policy(item["policy"]))
            for item in payload["profiles"]
        )
        ids = {profile.profile_id for profile in profiles}
        names = {profile.name.casefold() for profile in profiles}
        next_id = payload.get("next_id")
        if (
            len(profiles) > MAX_PROFILES
            or len(ids) != len(profiles)
            or len(names) != len(profiles)
            or type(next_id) is not int
            or next_id < 1
        ):
            raise ValueError("profile identities are inconsistent")
        return next_id, profiles

    def load(self) -> tuple[int, tuple[SavedProfile, ...]]:
        empty: tuple[int, tuple[SavedProfile, ...]] = (1, ())
        return self.read(self._decode, empty)

    def save(self, next_id: int, profiles: tuple[SavedProfile, ...]) -> None:
        self.write(
            {
                "next_id": next_id,
                "profiles": [
                    {"id": p.profile_id, "name": p.name, "policy": encode_policy(p.policy)}
                    for p in profiles
                ],
            }
        )


class HistoryStore(JsonStore):
    def __init__(self, path: Path | None) -> None:
        super().__init__(path, "Saved run reports")

    @staticmethod
    def _decode(payload: object) -> tuple[RunReport, ...]:
        if not isinstance(payload, dict) or not isinstance(payload.get("reports"), list):
            raise ValueError("reports list missing")
        reports = tuple(decode_report(item) for item in payload["reports"])
        if len(reports) > MAX_HISTORY or len({r.run_key for r in reports}) != len(reports):
            raise ValueError("report identities are inconsistent")
        return reports

    def load(self) -> tuple[RunReport, ...]:
        return self.read(self._decode, ())

    def save(self, reports: tuple[RunReport, ...]) -> None:
        self.write({"reports": [encode_report(r) for r in reports[:MAX_HISTORY]]})


class PreferenceStore(JsonStore):
    def __init__(self, path: Path | None) -> None:
        super().__init__(path, "Saved controls and accessibility preferences")

    @staticmethod
    def _decode(payload: object) -> DesktopPreferences:
        if not isinstance(payload, dict) or not isinstance(payload.get("controls"), list):
            raise ValueError("controls list missing")
        subtitles, contrast = payload.get("subtitles"), payload.get("high_contrast")
        if type(subtitles) is not bool or type(contrast) is not bool:
            raise ValueError("accessibility switches must be booleans")
        return DesktopPreferences(
            tuple(
                KeyAssignment(str(item["action"]), tuple(int(key) for key in item["keys"]))
                for item in payload["controls"]
            ),
            subtitles,
            contrast,
        )

    def load(self) -> DesktopPreferences:
        return self.read(self._decode, DesktopPreferences())

    def save(self, preferences: DesktopPreferences) -> None:
        self.write(
            {
                "controls": [
                    {"action": item.action, "keys": list(item.keys)}
                    for item in preferences.controls
                ],
                "subtitles": preferences.subtitles,
                "high_contrast": preferences.high_contrast,
            }
        )
