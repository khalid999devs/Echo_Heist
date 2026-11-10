"""Private mutable per-run prop state; only Simulation-owned rules change it."""

from dataclasses import dataclass, field

from echo_heist.core.contracts.environment.model import EnvironmentRules, PropSpec
from echo_heist.core.contracts.environment.presentation import EnvironmentCue
from echo_heist.core.contracts.world import Position, Tile


@dataclass(slots=True)
class DoorState:
    spec: PropSpec
    # 0 = fully closed ... cycle = fully open. Bodies/sight are blocked only
    # while ``blocked``: from the end of a complete close until a complete open.
    open_ticks: int
    opening: bool = True
    blocked: bool = False
    mover: str = ""


@dataclass(slots=True)
class GlassState:
    spec: PropSpec
    broken: bool = False
    broken_tick: int = -1


@dataclass(slots=True)
class CanisterState:
    spec: PropSpec
    tile: Tile
    position: Position
    previous_position: Position
    direction: Tile = (0, 0)
    steps_left: int = 0
    step_progress: int = 0
    roll_degrees: int = 0
    mover: str = ""

    @property
    def rolling(self) -> bool:
        return self.direction != (0, 0)


@dataclass(slots=True)
class LockerState:
    spec: PropSpec
    occupant: str | None = None
    # Committed cosmetic hatch motion: the hatch is open at ``moved_tick`` and
    # closed again ``locker_cycle_ticks`` later.
    moved_tick: int = -10_000


@dataclass(slots=True)
class EnvironmentState:
    rules: EnvironmentRules = field(default_factory=EnvironmentRules)
    doors: dict[str, DoorState] = field(default_factory=dict)
    glass: dict[str, GlassState] = field(default_factory=dict)
    canisters: dict[str, CanisterState] = field(default_factory=dict)
    lockers: dict[str, LockerState] = field(default_factory=dict)
    cues: list[EnvironmentCue] = field(default_factory=list)
    # Reasons for a geometry change committed this tick; applied next tick.
    geometry_reasons: list[str] = field(default_factory=list)
