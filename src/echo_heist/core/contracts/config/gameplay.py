"""Public immutable gameplay rules, supplied by the composition root."""

from dataclasses import dataclass, fields
from typing import Self

from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE


@dataclass(frozen=True, slots=True)
class GameRules:
    schema_version: int
    simulation_hz: int
    walk_speed_units_per_second: int
    sprint_speed_units_per_second: int
    sentinel_speed_units_per_second: int
    tracker_speed_units_per_second: int
    interceptor_speed_units_per_second: int
    actor_radius_units: int
    interaction_range_units: int
    capture_range_units: int
    melee_range_units: int
    core_interaction_ticks: int
    capture_windup_ticks: int
    emp_radius_units: int
    emp_disable_ticks: int
    melee_stun_ticks: int
    melee_immunity_ticks: int
    echo_history_ticks: int
    footstep_interval_ticks: int
    walk_noise_radius_tiles: int
    sprint_noise_radius_tiles: int
    emp_noise_radius_tiles: int
    melee_noise_radius_tiles: int

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or not 0 < value <= 1_000_000:
                raise ValueError(f"Rule {field.name} must be a bounded positive integer")
        if self.schema_version != 1:
            raise ValueError("Unsupported gameplay rules schema")
        if not 1 <= self.simulation_hz <= 240:
            raise ValueError("Unsupported simulation frequency")
        if self.actor_radius_units >= POSITION_UNITS_PER_TILE // 2:
            raise ValueError("Actor radius must be smaller than half a tile")
        if self.sprint_speed_units_per_second < self.walk_speed_units_per_second:
            raise ValueError("Sprint must not be slower than walking")

    @classmethod
    def from_payload(cls, payload: object) -> Self:
        names = {field.name for field in fields(cls)}
        if not isinstance(payload, dict) or set(payload) != names:
            raise ValueError("Gameplay rules must contain exactly the supported fields")
        return cls(**payload)
