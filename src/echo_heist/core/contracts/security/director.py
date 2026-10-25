"""NEXUS director and route-graph values; static or legitimately observed data only."""

from dataclasses import dataclass, replace
from enum import StrEnum

from echo_heist.core.contracts.world import Tile, immutable_tile

NEXUS_ID = "nexus"


@dataclass(frozen=True, slots=True)
class ZoneArea:
    zone_id: str
    left: int
    top: int
    width: int
    height: int

    def contains(self, tile: Tile) -> bool:
        return (
            self.left <= tile[0] < self.left + self.width
            and self.top <= tile[1] < self.top + self.height
        )


@dataclass(frozen=True, slots=True)
class RouteNode:
    """An authored chokepoint linking two zones (Security Junction, Research Return...)."""

    node_id: str
    tile: Tile
    zones: tuple[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "tile", immutable_tile(self.tile))
        object.__setattr__(self, "zones", tuple(self.zones))


@dataclass(frozen=True, slots=True)
class RouteGraph:
    """Public facility abstraction: zones, chokepoints and walking distances.

    ``distances`` holds legal-graph step counts between chokepoints and to the
    Core/Exit anchors. It is built from static geometry by the registry.
    """

    zones: tuple[ZoneArea, ...]
    nodes: tuple[RouteNode, ...]
    core_tile: Tile
    exit_tile: Tile
    distances: tuple[tuple[str, str, int], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "zones", tuple(self.zones))
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "core_tile", immutable_tile(self.core_tile))
        object.__setattr__(self, "exit_tile", immutable_tile(self.exit_tile))
        object.__setattr__(self, "distances", tuple(self.distances))
        if len({node.node_id for node in self.nodes}) != len(self.nodes):
            raise ValueError("Route nodes need unique IDs")

    def zone_of(self, tile: Tile) -> str:
        return next((zone.zone_id for zone in self.zones if zone.contains(tile)), "")

    def node(self, node_id: str) -> RouteNode:
        return next(node for node in self.nodes if node.node_id == node_id)

    def distance(self, first: str, second: str) -> int | None:
        if first == second:
            return 0
        for a, b, steps in self.distances:
            if (a, b) in ((first, second), (second, first)):
                return steps
        return None


class ProtocolId(StrEnum):
    VERIFY_ECHO = "VERIFY_ECHO"
    REINFORCE_ROUTE = "REINFORCE_ROUTE"
    SPREAD_FORMATION = "SPREAD_FORMATION"


@dataclass(frozen=True, slots=True)
class ActiveProtocol:
    protocol_id: ProtocolId
    sector: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "protocol_id", ProtocolId(self.protocol_id))
        if (self.protocol_id == ProtocolId.REINFORCE_ROUTE) != bool(self.sector):
            raise ValueError("Only REINFORCE_ROUTE names a reinforced sector")


@dataclass(frozen=True, slots=True)
class DirectorRules:
    """Dispatch caps keep sector coverage; at most one protocol per attempt.

    Travel estimates are ticks per tile at the Interceptor's speed and at the
    intruder's walking speed, derived from the gameplay rules by the registry.
    """

    support_cap: int = 1
    noise_cap: int = 1
    routine_coverage: int = 1
    support_radius_tiles: int = 18
    interceptor_depth: int = 3
    guard_ticks_per_tile: int = 11
    intruder_ticks_per_tile: int = 13
    dispatch_ttl_ticks: int = 150
    protocol: ActiveProtocol | None = None

    def __post_init__(self) -> None:
        values = (self.support_cap, self.noise_cap, self.routine_coverage)
        if any(type(value) is not int or not 0 <= value <= 4 for value in values):
            raise ValueError("NEXUS caps must be small nonnegative integers")
        if not 1 <= self.support_radius_tiles <= 64 or self.interceptor_depth not in (2, 3):
            raise ValueError("Unsupported NEXUS radius or Interceptor depth")
        timing = (self.guard_ticks_per_tile, self.intruder_ticks_per_tile, self.dispatch_ttl_ticks)
        if any(type(value) is not int or not 0 < value <= 10_000 for value in timing):
            raise ValueError("NEXUS timing values must be bounded positive ticks")

    def effective(self) -> "DirectorRules":
        """SPREAD_FORMATION trades pursuit support for wider routine coverage."""
        if self.protocol is not None and self.protocol.protocol_id == ProtocolId.SPREAD_FORMATION:
            return replace(self, support_cap=0, routine_coverage=min(4, self.routine_coverage + 1))
        return self


class TaskKind(StrEnum):
    PROTECT_EXIT = "PROTECT_EXIT"
    INTERCEPT = "INTERCEPT"
    SUPPORT_PURSUIT = "SUPPORT_PURSUIT"
    INVESTIGATE_NOISE = "INVESTIGATE_NOISE"


TASK_PRIORITY = {
    TaskKind.PROTECT_EXIT: 100,
    TaskKind.INTERCEPT: 90,
    TaskKind.SUPPORT_PURSUIT: 80,
    TaskKind.INVESTIGATE_NOISE: 45,
}


@dataclass(frozen=True, slots=True)
class Dispatch:
    guard_id: str
    task: TaskKind
    target: Tile
    evidence_id: str
    evidence_tick: int
    expires_at_tick: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "task", TaskKind(self.task))
        object.__setattr__(self, "target", immutable_tile(self.target))
        if self.expires_at_tick < self.evidence_tick:
            raise ValueError("A dispatch cannot expire before its evidence")


@dataclass(frozen=True, slots=True)
class NexusEvidence:
    """Counts NEXUS legitimately observed in one attempt (persisted between attempts)."""

    echo_witnessed: int = 0
    contacts: tuple[tuple[str, int], ...] = ()
    bypassed_groups: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "contacts", tuple(sorted(tuple(item) for item in self.contacts)))
        if min(self.echo_witnessed, self.bypassed_groups, *(n for _, n in self.contacts)) < 0:
            raise ValueError("Evidence counts must be nonnegative")


@dataclass(frozen=True, slots=True)
class NexusStatus:
    """Privileged display/persistence view of NEXUS; never a controller input."""

    evaluated_tick: int
    dispatches: tuple[Dispatch, ...]
    announcement: str
    announcement_tick: int | None
    evidence: NexusEvidence
    protocol: ActiveProtocol | None = None


@dataclass(frozen=True, slots=True)
class NexusMemory:
    """NEXUS working memory inside Simulation; built only from its permitted view."""

    evaluated_tick: int = -1
    handled: tuple[str, ...] = ()
    dispatches: tuple[Dispatch, ...] = ()
    announcement: str = ""
    announcement_tick: int | None = None
    lockdown_handled: bool = False
    contact_active: bool = False
    echo_ids: tuple[str, ...] = ()
    evidence: NexusEvidence = NexusEvidence()

    def __post_init__(self) -> None:
        for name in ("handled", "dispatches", "echo_ids"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
