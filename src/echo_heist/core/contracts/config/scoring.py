"""Versioned approved scoring constants (docs/development/planning/SCORING.md).

The weights and rank bands are the user-approved 2026-10-18 rules; changing them
needs a new approval. ``pace_reference_ticks`` and ``speedrunner_ticks`` are the
draft calibration values the specification allows to be tuned from playtests.
"""

from dataclasses import dataclass, fields
from typing import Self


@dataclass(frozen=True, slots=True)
class ScoringRules:
    scoring_version: int = 1
    completion_points: int = 50
    stealth_points: int = 40
    encounter_penalty: int = 12
    pace_points: int = 10
    # Draft reference: 900 simulation seconds at 30 Hz (SCORING.md).
    pace_reference_ticks: int = 27_000
    # Draft Speedrunner threshold, pending a physical playtest.
    speedrunner_ticks: int = 9_000

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or not 0 < value <= 10_000_000:
                raise ValueError(f"Scoring rule {field.name} must be a bounded positive integer")
        approved = (
            self.completion_points,
            self.stealth_points,
            self.encounter_penalty,
            self.pace_points,
        )
        if approved != (50, 40, 12, 10):
            raise ValueError("Scoring weights differ from the approved 50/40/12/10 rules")

    @classmethod
    def from_payload(cls, payload: object) -> Self:
        names = {field.name for field in fields(cls)}
        if not isinstance(payload, dict) or set(payload) != names:
            raise ValueError("Scoring rules must contain exactly the supported fields")
        return cls(**payload)
