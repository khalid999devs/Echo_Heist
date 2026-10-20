"""Follow camera in world pixels; smoothing is presentation-only, never simulation."""

from dataclasses import dataclass
from math import exp


@dataclass(slots=True)
class Camera:
    view_width: int
    view_height: int
    world_width: int
    world_height: int
    x: float = 0.0
    y: float = 0.0

    def follow(self, target: tuple[float, float], seconds: float, *, snap: bool = False) -> None:
        goal_x = target[0] - self.view_width / 2
        goal_y = target[1] - self.view_height / 2
        blend = 1.0 if snap else 1.0 - exp(-8.0 * max(0.0, seconds))
        self.x = self._clamp(self.x + (goal_x - self.x) * blend, self.world_width, self.view_width)
        self.y = self._clamp(
            self.y + (goal_y - self.y) * blend, self.world_height, self.view_height
        )

    @staticmethod
    def _clamp(value: float, world: int, view: int) -> float:
        if world <= view:
            return (world - view) / 2  # Center a small map instead of pinning it to a corner.
        return max(0.0, min(value, float(world - view)))

    def to_screen(self, point: tuple[float, float]) -> tuple[int, int]:
        return round(point[0] - self.x), round(point[1] - self.y)
