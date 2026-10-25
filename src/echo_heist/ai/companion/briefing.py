"""Public pre-mission knowledge and the Companion's policy weights.

The briefing holds facts a human player also has before launching: geometry,
zones/chokepoints, cover, Core/Exit anchors, gadget stock and the defender
roster (type and home sector). It never contains a live or hidden position.
"""

from dataclasses import dataclass

from echo_heist.core.contracts.autonomy.policy import (
    Emergency,
    GuardReaction,
    Navigation,
    PolicySelection,
    Risk,
)
from echo_heist.core.contracts.security.director import RouteGraph
from echo_heist.core.contracts.world import ActorKind, Tile, immutable_tile


@dataclass(frozen=True, slots=True)
class GuardBrief:
    guard_id: str
    kind: ActorKind
    home_zone: str


@dataclass(frozen=True, slots=True)
class MissionBriefing:
    core_id: str
    core_tile: Tile
    exit_tile: Tile
    graph: RouteGraph
    hide_tiles: tuple[Tile, ...]
    guards: tuple[GuardBrief, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "core_tile", immutable_tile(self.core_tile))
        object.__setattr__(self, "exit_tile", immutable_tile(self.exit_tile))
        object.__setattr__(self, "hide_tiles", tuple(immutable_tile(t) for t in self.hide_tiles))
        object.__setattr__(self, "guards", tuple(self.guards))


@dataclass(frozen=True, slots=True)
class PolicyWeights:
    """Workshop blocks translated into bounded decision weights (never physics)."""

    risk_weight: int  # A* extra cost per unit of observed danger on a tile
    time_cost: float  # MCTS reward lost per abstract second
    detection_penalty: float
    capture_penalty: float
    sprint: bool  # sprint while carrying the Core (always allowed when fleeing)
    sprint_always: bool
    preferred: str  # guard-reaction response tried first
    emergency: Emergency
    policy_id: str

    def __post_init__(self) -> None:
        if not 0 <= self.risk_weight <= 12 or not 0 <= self.time_cost <= 3:
            raise ValueError("Policy weights are outside safe bounds")


def policy_weights(policy: PolicySelection) -> PolicyWeights:
    risk = {Navigation.SAFEST: 8, Navigation.BALANCED: 4, Navigation.SHORTEST: 0}
    time = {Navigation.SAFEST: 0.4, Navigation.BALANCED: 0.8, Navigation.SHORTEST: 1.0}
    scale = {Risk.CAUTIOUS: 1.5, Risk.BALANCED: 1.0, Risk.BOLD: 0.6}[policy.risk]
    preferred = {
        GuardReaction.HIDE: "HIDE",
        GuardReaction.RETREAT: "RETREAT",
        GuardReaction.CONSIDER_ECHO: "ECHO",
    }[policy.guard_reaction]
    return PolicyWeights(
        min(12, round(risk[policy.navigation] * scale)),
        time[policy.navigation] / scale,
        25 * scale,
        100 * scale,
        policy.risk != Risk.CAUTIOUS,
        policy.risk == Risk.BOLD,
        preferred,
        policy.emergency,
        "-".join(
            (
                policy.navigation.value,
                policy.guard_reaction.value,
                policy.emergency.value,
                policy.risk.value,
            )
        ),
    )
