"""Private mutable state, passed only to Simulation-owned rule systems."""

from collections.abc import Callable
from dataclasses import dataclass, field

from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.results import MissionEnd
from echo_heist.core.contracts.world import (
    ActorKind,
    Inventory,
    MissionPhase,
    Position,
    Scalar,
    Tile,
    position_tile,
)

type Emit = Callable[[EventKind, str, tuple[tuple[str, Scalar], ...]], None]
GUARD_KINDS = frozenset({ActorKind.SENTINEL, ActorKind.TRACKER, ActorKind.INTERCEPTOR})


@dataclass(slots=True)
class ActorState:
    actor_id: str
    kind: ActorKind
    position: Position
    inventory: Inventory = field(default_factory=Inventory)
    disabled_until: int = 0
    stunned_until: int = 0
    melee_immune_until: int = 0
    path: list[Position] = field(default_factory=list)
    next_footstep_tick: int = 0
    traversed_tiles: tuple[Tile, ...] = ()

    @property
    def tile(self) -> Tile:
        return position_tile(self.position)

    def incapacitated(self, tick: int) -> bool:
        return tick < max(self.disabled_until, self.stunned_until)


@dataclass(slots=True)
class CaptureState:
    target_id: str
    completes_at: int


@dataclass(slots=True)
class EchoState:
    echo_id: str
    owner_id: str
    path: tuple[Position, ...]
    index: int = 0


@dataclass(slots=True)
class WorldState:
    actors: dict[str, ActorState]
    tick: int = 0
    phase: MissionPhase = MissionPhase.INFILTRATE
    next_event_id: int = 0
    core_owner: str | None = None
    interaction_actor: str | None = None
    interaction_ticks: int = 0
    captures: dict[str, CaptureState] = field(default_factory=dict)
    echoes: dict[str, EchoState] = field(default_factory=dict)
    next_echo_id: int = 0
    mission_end: MissionEnd | None = None
