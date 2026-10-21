"""Presentation-only motion derived from committed simulation displacement."""

from dataclasses import dataclass

OPERATIVE_SIZE = (110, 124)
DEFENDER_SIZE = (114, 124)
COMPANION_SIZE = (88, 104)


@dataclass(frozen=True, slots=True)
class ActorMotion:
    direction: tuple[int, int] = (0, -1)
    moving: bool = False
    sprinting: bool = False
    phase: float = 0.0
    phase_step: float = 0.0
    previous_position: tuple[int, int] | None = None
    crouched: bool = False


def position_at(
    current: tuple[int, int], motion: ActorMotion, fraction: float
) -> tuple[float, float]:
    previous = motion.previous_position
    if previous is None:
        return float(current[0]), float(current[1])
    weight = max(0.0, min(1.0, fraction))
    return (
        previous[0] + (current[0] - previous[0]) * weight,
        previous[1] + (current[1] - previous[1]) * weight,
    )
