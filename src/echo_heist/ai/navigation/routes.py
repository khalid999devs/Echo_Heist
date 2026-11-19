"""Plausible zone-level routes over the public chokepoint graph.

Used by the Interceptor (to hypothesize an intruder's branch from evidence) and
by the Companion (to choose its own branch). Distances come from static legal
geometry only.
"""

from dataclasses import dataclass

from echo_heist.core.contracts.security.director import RouteGraph
from echo_heist.core.contracts.world import Tile

MAX_ROUTES = 3
MAX_ROUTE_NODES = 4


@dataclass(frozen=True, slots=True)
class ZoneRoute:
    """One plausible branch: ordered chokepoints and the walking steps to reach each."""

    nodes: tuple[str, ...]
    arrival_steps: tuple[int, ...]
    total_steps: int
    weight: float

    @property
    def label(self) -> str:
        return ">".join(self.nodes) or "direct"


def zone_routes(
    graph: RouteGraph, evidence: Tile, goal: Tile, steps: dict[Tile, int]
) -> tuple[ZoneRoute, ...]:
    """Up to three cheapest simple chokepoint routes from the evidence zone to the goal."""
    start_zone, goal_zone = graph.zone_of(evidence), graph.zone_of(goal)
    if not start_zone or not goal_zone or start_zone == goal_zone:
        return ()
    goal_name = graph.anchor_name(goal)
    found: list[tuple[int, tuple[str, ...], tuple[int, ...]]] = []

    def extend(zone: str, path: tuple[str, ...], arrivals: tuple[int, ...]) -> None:
        if zone == goal_zone and path:
            tail = graph.distance(path[-1], goal_name)
            if tail is not None:
                found.append((arrivals[-1] + tail, path, arrivals))
            return
        if len(path) >= MAX_ROUTE_NODES:
            return
        for node in graph.nodes:
            if zone not in node.zones or node.node_id in path:
                continue
            reach = (
                steps.get(node.tile)
                if not path
                else (
                    None
                    if (leg := graph.distance(path[-1], node.node_id)) is None
                    else arrivals[-1] + leg
                )
            )
            if reach is None:
                continue
            other = node.zones[1] if node.zones[0] == zone else node.zones[0]
            extend(other, (*path, node.node_id), (*arrivals, reach))

    extend(start_zone, (), ())
    found.sort(key=lambda item: (item[0], item[1]))
    chosen = found[:MAX_ROUTES]
    if not chosen:
        return ()
    best = chosen[0][0]
    return tuple(
        ZoneRoute(path, arrivals, total, 1.0 / (1.0 + (total - best) / 12.0))
        for total, path, arrivals in chosen
    )
