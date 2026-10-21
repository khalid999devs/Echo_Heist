"""Small zero-order Sugeno inference for uncertain-cue investigation urgency."""

from dataclasses import dataclass


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def triangle(value: float, left: float, peak: float, right: float) -> float:
    if value <= left or value >= right:
        return 0.0
    return (value - left) / (peak - left) if value <= peak else (right - value) / (right - peak)


@dataclass(frozen=True, slots=True)
class FuzzyResult:
    urgency: float
    activations: tuple[float, ...]


def investigate_urgency(distance_tiles: int, salience: float, visibility: float) -> FuzzyResult:
    near = clamp(1 - distance_tiles / 4)
    far = clamp((distance_tiles - 3) / 5)
    loud = clamp((salience - 0.45) / 0.5)
    notable = triangle(salience, 0.15, 0.6, 1.0)
    partial = triangle(visibility, 0.0, 0.5, 1.0)
    quiet = clamp(1 - salience)
    activations = (
        min(loud, near),
        min(partial, near),
        min(notable, far),
        min(1 - clamp(visibility), quiet),
        min(notable, near),
    )
    outputs = (0.95, 0.80, 0.45, 0.10, 0.60)
    total = sum(activations)
    urgency = (
        sum(weight * output for weight, output in zip(activations, outputs, strict=True)) / total
        if total
        else 0.1
    )
    return FuzzyResult(round(clamp(urgency), 4), activations)
