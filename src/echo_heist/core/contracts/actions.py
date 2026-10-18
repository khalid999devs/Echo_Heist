"""One controller intent per actor and observation tick."""

from dataclasses import dataclass
from enum import StrEnum

from echo_heist.core.contracts.world import Tile, immutable_tile


class ActionKind(StrEnum):
    MOVE = "MOVE"
    WAIT = "WAIT"
    INTERACT = "INTERACT"
    ECHO = "ECHO"
    EMP = "EMP"
    MELEE = "MELEE"
    HIDE = "HIDE"


@dataclass(frozen=True, slots=True)
class Action:
    actor_id: str
    kind: ActionKind
    tick_issued: int
    direction: Tile = (0, 0)
    target_tile: Tile | None = None
    target_id: str | None = None
    sprint: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ActionKind):
            raise ValueError("Action kind must be an ActionKind enum")
        object.__setattr__(self, "direction", immutable_tile(self.direction))
        if self.target_tile is not None:
            object.__setattr__(self, "target_tile", immutable_tile(self.target_tile))
