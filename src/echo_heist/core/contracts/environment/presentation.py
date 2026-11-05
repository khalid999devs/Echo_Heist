"""Read-only committed prop state and cues; these records do not implement physics."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from echo_heist.core.contracts.world import Position, immutable_tile


class PropKind(StrEnum):
    DOOR = "DOOR"
    GLASS = "GLASS"
    CANISTER = "CANISTER"
    LOCKER = "LOCKER"


class EnvironmentCueKind(StrEnum):
    DOOR = "DOOR"
    GLASS = "GLASS"
    CANISTER_IMPACT = "CANISTER_IMPACT"
    HIDE_ENTER = "HIDE_ENTER"
    HIDE_LEAVE = "HIDE_LEAVE"


def _fraction(value: float) -> None:
    if not isfinite(value) or not 0 <= value <= 1:
        raise ValueError("A committed presentation fraction must be finite and within [0, 1]")


@dataclass(frozen=True, slots=True)
class PropView:
    """Position is the floor-footprint centre; dimensions use fixed-point world units.

    Door/locker openness and canister roll come from committed lifecycle state.
    Actor cover is cosmetic occlusion and only applies when the actor is actually
    concealed in the ordinary snapshot. These values never grant concealment.
    """

    object_id: str
    kind: PropKind
    position: Position
    size: Position
    openness: float = 0.0
    broken: bool = False
    locked: bool = False
    previous_position: Position | None = None
    roll_degrees: float = 0.0
    occupant_id: str | None = None
    occupant_cover: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "position", immutable_tile(self.position))
        object.__setattr__(self, "size", immutable_tile(self.size))
        if self.previous_position is not None:
            object.__setattr__(self, "previous_position", immutable_tile(self.previous_position))
        if not self.object_id or not isinstance(self.kind, PropKind) or min(self.size) <= 0:
            raise ValueError("A prop needs a stable ID, supported kind and positive footprint")
        _fraction(self.openness)
        _fraction(self.occupant_cover)
        if not isfinite(self.roll_degrees):
            raise ValueError("Canister rotation must be finite")
        if self.occupant_cover and (self.kind != PropKind.LOCKER or not self.occupant_id):
            raise ValueError("Only a named locker occupant may have cover occlusion")


@dataclass(frozen=True, slots=True)
class EnvironmentCue:
    """Once-only committed presentation cue, optionally linked to a real NoiseEvent.

    visible is supplied from actual observation, never from inferred audibility.
    Foreign sound needs noise_event_id in the listener's legitimate heard cues.
    A door/locker cosmetic servo without a noise ID does not alert any guard.
    """

    event_id: str
    tick: int
    kind: EnvironmentCueKind
    object_id: str
    position: Position
    actor_id: str = ""
    noise_event_id: str | None = None
    visible: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "position", immutable_tile(self.position))
        if not self.event_id or not self.object_id or self.tick < 0:
            raise ValueError("Environment cues need stable IDs and their original committed tick")
        if not isinstance(self.kind, EnvironmentCueKind):
            raise ValueError("Unknown environment cue kind")


@dataclass(frozen=True, slots=True)
class EnvironmentView:
    """No state means no lifecycle is implemented; never synthesize an open door."""

    props: tuple[PropView, ...] = ()
    cues: tuple[EnvironmentCue, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "props", tuple(self.props))
        object.__setattr__(self, "cues", tuple(self.cues))
        if len({prop.object_id for prop in self.props}) != len(self.props):
            raise ValueError("Environment prop IDs must be unique")
