"""Private mutable actor state; never pass these objects through observations."""

from dataclasses import dataclass, field

from echo_heist.core.contracts.world import ActorKind, Inventory, MissionPhase, Tile


@dataclass(slots=True)
class ActorState:
    actor_id: str
    kind: ActorKind
    tile: Tile
    inventory: Inventory = field(default_factory=Inventory)


@dataclass(slots=True)
class WorldState:
    actors: dict[str, ActorState]
    tick: int = 0
    phase: MissionPhase = MissionPhase.INFILTRATE
    next_event_id: int = 0
