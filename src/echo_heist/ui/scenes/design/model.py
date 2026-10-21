"""In-memory presentation choices; these are never used as live AI policy."""

from dataclasses import dataclass, field

POLICIES = (
    ("Navigation", ("Safest", "Balanced", "Shortest")),
    ("Guard reaction", ("Hide", "Retreat and replan", "Consider Echo")),
    ("Emergency", ("Escape first", "Melee if adjacent", "EMP if trapped")),
    ("Risk tolerance", ("Cautious", "Balanced", "Bold")),
)
PRESETS = ("GHOST", "BALANCED", "RUSH")
PRESET_VALUES = ((0, 0, 0, 0), (1, 1, 2, 1), (2, 2, 1, 2))


@dataclass(slots=True)
class WorkshopDraft:
    preset: int = 1
    choices: list[int] = field(default_factory=lambda: list(PRESET_VALUES[1]))

    def select_preset(self, index: int) -> None:
        self.preset, self.choices = index, list(PRESET_VALUES[index])

    def cycle(self, index: int, direction: int = 1) -> None:
        self.choices[index] = (self.choices[index] + direction) % len(POLICIES[index][1])
        self.preset = next(
            (i for i, values in enumerate(PRESET_VALUES) if tuple(self.choices) == values), -1
        )
