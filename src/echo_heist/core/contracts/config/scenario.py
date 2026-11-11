"""Deterministic experiment starts (P07-SR2); never used by normal play.

A scenario may start the intruder on another walkable tile, with reduced tool
stock, or already carrying the Core in lockdown. Every field is part of the
Simulation fingerprint, so a scenario result is never confused with a full run.
"""

from dataclasses import dataclass

from echo_heist.core.contracts.world import Inventory, Tile, immutable_tile


@dataclass(frozen=True, slots=True)
class IntruderStart:
    tile: Tile | None = None
    echo_charges: int = 3
    emp_charges: int = 1
    melee_charges: int = 2
    core_held: bool = False

    def __post_init__(self) -> None:
        if self.tile is not None:
            object.__setattr__(self, "tile", immutable_tile(self.tile))
        stock = (self.echo_charges, self.emp_charges, self.melee_charges)
        if (
            any(type(value) is not int for value in stock)
            or not (0 <= self.echo_charges <= 3 and 0 <= self.emp_charges <= 1)
            or not 0 <= self.melee_charges <= 2
        ):
            raise ValueError("A scenario can only reduce the normal tool stock")
        if type(self.core_held) is not bool:
            raise ValueError("core_held must be a boolean")

    def inventory(self) -> Inventory:
        return Inventory(self.echo_charges, self.emp_charges, self.core_held, self.melee_charges)
