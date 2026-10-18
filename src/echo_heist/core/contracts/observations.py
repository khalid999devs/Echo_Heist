"""Controller knowledge contains values, not handles to mutable entities."""

from dataclasses import dataclass

from echo_heist.core.contracts.events import HeardCue, SecurityReport
from echo_heist.core.contracts.world import (
    ActorKind,
    Inventory,
    MissionPhase,
    StaticMap,
    Tile,
    immutable_tile,
)


@dataclass(frozen=True, slots=True)
class EntityView:
    actor_id: str
    kind: ActorKind
    tile: Tile

    def __post_init__(self) -> None:
        object.__setattr__(self, "tile", immutable_tile(self.tile))


@dataclass(frozen=True, slots=True)
class OwnStatus:
    tile: Tile
    inventory: Inventory
    concealed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "tile", immutable_tile(self.tile))


@dataclass(frozen=True, slots=True)
class Observation:
    agent_id: str
    tick: int
    map_static: StaticMap
    phase: MissionPhase
    own_status: OwnStatus
    visible_entities: tuple[EntityView, ...] = ()
    heard_events: tuple[HeardCue, ...] = ()
    shared_reports: tuple[SecurityReport, ...] = ()
    schema_version: int = 1

    def __post_init__(self) -> None:
        for field in ("visible_entities", "heard_events", "shared_reports"):
            object.__setattr__(self, field, tuple(getattr(self, field)))
