"""Immutable measured decision data; never supplied back to AI controllers."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from echo_heist.core.contracts.actions import ActionKind
from echo_heist.core.contracts.world import Tile, immutable_tile


class ControlMode(StrEnum):
    HUMAN = "HUMAN"
    COMPANION = "COMPANION"


@dataclass(frozen=True, slots=True)
class Alternative:
    action: str
    visits: int
    mean_reward: float | None
    legal: bool = True

    def __post_init__(self) -> None:
        if not self.action or type(self.visits) is not int or self.visits < 0:
            raise ValueError("An alternative needs an action and nonnegative visit count")
        if self.mean_reward is not None and (
            not isfinite(self.mean_reward) or not 0 <= self.mean_reward <= 1 or not self.visits
        ):
            raise ValueError("Mean reward needs visits and a finite normalized value")


@dataclass(frozen=True, slots=True)
class CompanionTrace:
    actor_id: str
    evaluated_tick: int
    state: str
    chosen_action: str
    reason: str
    simulations: int
    alternatives: tuple[Alternative, ...] = ()
    path: tuple[Tile, ...] = ()
    path_cost: int | None = None
    expanded_nodes: int = 0
    utility_action: str = ""
    utility_reason: str = ""
    search_trigger: str = ""
    search_depth: int | None = None
    path_goal: Tile | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "alternatives", tuple(self.alternatives))
        object.__setattr__(self, "path", tuple(immutable_tile(tile) for tile in self.path))
        if self.path_goal is not None:
            object.__setattr__(self, "path_goal", immutable_tile(self.path_goal))
        if self.search_depth is not None and self.search_depth < 1:
            raise ValueError("Search depth must be positive")
        if not self.actor_id or not self.state or not self.chosen_action:
            raise ValueError("A decision needs its actor, state and chosen action")
        if min(self.evaluated_tick, self.simulations, self.expanded_nodes) < 0:
            raise ValueError("Decision ticks and search counts must be nonnegative")
        if sum(item.visits for item in self.alternatives) > self.simulations:
            raise ValueError("Alternative visits cannot exceed completed simulations")
        if len({item.action for item in self.alternatives}) != len(self.alternatives):
            raise ValueError("Decision alternatives must have unique action IDs")
        if self.path_cost is not None and self.path_cost < 0:
            raise ValueError("Path cost cannot be negative")


@dataclass(frozen=True, slots=True)
class LearnedProtocol:
    protocol_id: str
    label: str
    reason: str
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", tuple(self.evidence))
        if not self.protocol_id or not self.label or not self.reason:
            raise ValueError("A protocol needs its ID, label and evidence-backed reason")


@dataclass(frozen=True, slots=True)
class ProtocolState:
    revision: int = 0
    enabled: bool = False
    active: LearnedProtocol | None = None
    can_reset: bool = False

    def __post_init__(self) -> None:
        if self.revision < 0 or (self.active is not None and not self.enabled):
            raise ValueError("A protocol needs enabled memory and a nonnegative revision")


@dataclass(frozen=True, slots=True)
class GuardTask:
    guard_id: str
    task: str
    target: Tile
    evidence_tick: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "target", immutable_tile(self.target))


@dataclass(frozen=True, slots=True)
class InterceptorTrace:
    guard_id: str
    evaluated_tick: int
    post_id: str
    target: Tile
    depth: int
    evaluated_nodes: int
    pruned_nodes: int
    value: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "target", immutable_tile(self.target))
        if min(self.evaluated_tick, self.depth, self.evaluated_nodes, self.pruned_nodes) < 0:
            raise ValueError("Interceptor search metrics must be nonnegative")
        if not isfinite(self.value):
            raise ValueError("Interceptor value must be finite")


@dataclass(frozen=True, slots=True)
class NexusTrace:
    evaluated_tick: int
    announcement: str = ""
    announcement_tick: int | None = None
    tasks: tuple[GuardTask, ...] = ()
    interceptor: InterceptorTrace | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "tasks", tuple(self.tasks))
        if self.evaluated_tick < 0:
            raise ValueError("NEXUS telemetry needs its actual evaluation tick")
        if self.announcement and self.announcement_tick is None:
            raise ValueError("An announcement needs its committed tick")


@dataclass(frozen=True, slots=True)
class CompanionExecution:
    """The most recent Companion intent and its resolution by Simulation."""

    tick: int
    action: ActionKind
    rejection: str = ""


@dataclass(frozen=True, slots=True)
class AutonomyTelemetry:
    companion: CompanionTrace | None = None
    nexus: NexusTrace | None = None
    protocols: ProtocolState | None = None
    execution: CompanionExecution | None = None
