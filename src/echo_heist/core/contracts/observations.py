"""Controller knowledge contains values, not handles to mutable entities."""

from dataclasses import dataclass

from echo_heist.core.contracts.events import HeardCue, SecurityReport
from echo_heist.core.contracts.security.model import VisualCue
from echo_heist.core.contracts.world import (
    ActorKind,
    Inventory,
    MissionPhase,
    Position,
    StaticMap,
    Tile,
    immutable_tile,
)


@dataclass(frozen=True, slots=True)
class EntityView:
    actor_id: str
    kind: ActorKind
    tile: Tile
    position: Position | None = None
    disabled: bool = False
    stunned: bool = False
    facing: Tile = (0, -1)

    def __post_init__(self) -> None:
        object.__setattr__(self, "tile", immutable_tile(self.tile))
        object.__setattr__(self, "facing", immutable_tile(self.facing))
        if self.position is not None:
            object.__setattr__(self, "position", immutable_tile(self.position))


@dataclass(frozen=True, slots=True)
class OwnStatus:
    tile: Tile
    inventory: Inventory
    concealed: bool = False
    position: Position | None = None
    interaction_progress_ticks: int = 0
    capture_ticks_remaining: int | None = None
    facing: Tile = (0, -1)
    disabled: bool = False
    stunned: bool = False
    sprint_ticks_remaining: int = 0
    sprint_recharge_remaining: int = 0
    sprinting: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "tile", immutable_tile(self.tile))
        object.__setattr__(self, "facing", immutable_tile(self.facing))
        if self.position is not None:
            object.__setattr__(self, "position", immutable_tile(self.position))


@dataclass(frozen=True, slots=True)
class InteractionHint:
    target_id: str
    kind: str
    required_ticks: int
    progress_ticks: int = 0


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
    interactions: tuple[InteractionHint, ...] = ()
    visual_cues: tuple[VisualCue, ...] = ()

    def __post_init__(self) -> None:
        for field in (
            "visible_entities",
            "heard_events",
            "shared_reports",
            "interactions",
            "visual_cues",
        ):
            object.__setattr__(self, field, tuple(getattr(self, field)))
