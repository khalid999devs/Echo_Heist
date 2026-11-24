"""Typed guard registry: validated posts, patrols, roles and chokepoints for Simulation.

Built from the already-imported LevelData; it never edits map data or infers
anything from art. Every problem is collected so an authoring mistake is
reported in one pass.
"""

import json
from dataclasses import dataclass, replace
from hashlib import sha256

from echo_heist.ai.navigation.grid import bfs, distances_from
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.security.director import (
    ActiveProtocol,
    DirectorRules,
    RouteGraph,
    RouteNode,
    ZoneArea,
)
from echo_heist.core.contracts.security.model import (
    GuardPatrol,
    GuardRole,
    SecuritySpec,
    SensorRules,
)
from echo_heist.core.contracts.world import (
    POSITION_UNITS_PER_TILE,
    ActorKind,
    StaticMap,
    Tile,
    tile_center,
)
from echo_heist.core.simulation.systems.motion import body_fits
from echo_heist.level.model import Chokepoint, LevelData

ROLES = {
    ActorKind.SENTINEL: GuardRole.SENTINEL,
    ActorKind.TRACKER: GuardRole.TRACKER,
    ActorKind.INTERCEPTOR: GuardRole.INTERCEPTOR,
}


class SecurityRegistryError(ValueError):
    def __init__(self, problems: list[str]) -> None:
        super().__init__("Invalid guard registry:\n- " + "\n- ".join(problems))
        self.problems = tuple(problems)


@dataclass(frozen=True, slots=True)
class GuardAssignment:
    guard_id: str
    kind: ActorKind
    role: GuardRole
    route_id: str
    patrol: GuardPatrol
    zone_id: str
    chokepoint_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SecurityRegistry:
    assignments: tuple[GuardAssignment, ...]
    chokepoints: tuple[Chokepoint, ...]
    sound_blocking_tiles: frozenset[Tile]
    revision: str
    graph: RouteGraph | None = None
    director: DirectorRules | None = None
    view_regions: tuple[tuple[int, int, int, int], ...] = ()

    def assignment(self, guard_id: str) -> GuardAssignment:
        return next(value for value in self.assignments if value.guard_id == guard_id)

    def spec(self, rules: SensorRules, protocol: ActiveProtocol | None = None) -> SecuritySpec:
        """The shipped defender team: guards, route graph and NEXUS with one protocol."""
        director = replace(self.director, protocol=protocol) if self.director is not None else None
        return SecuritySpec(
            tuple(value.patrol for value in self.assignments),
            rules,
            self.sound_blocking_tiles,
            self.graph,
            director,
            self.view_regions,
        )


def _ticks_per_tile(rules: GameRules, speed: int) -> int:
    return -(-POSITION_UNITS_PER_TILE * rules.simulation_hz // speed)


def build_route_graph(level: LevelData) -> RouteGraph:
    """Zones, chokepoints and legal walking distances, from static geometry only."""
    world_map = level.static_map
    anchors = {
        "CORE": next(obj.tile for obj in world_map.objects if obj.object_id == level.core_id),
        "EXIT": next(obj.tile for obj in world_map.objects if obj.object_id == level.exit_id),
    }
    exit_tiles = tuple(
        next(obj.tile for obj in world_map.objects if obj.object_id == key)
        for key in level.alternate_exit_ids
    )
    anchors.update((f"EXIT-{index}", tile) for index, tile in enumerate(exit_tiles, 2))
    nodes = tuple(
        RouteNode(point.point_id, point.tile, point.zones)
        for point in sorted(level.chokepoints, key=lambda value: value.point_id)
    )
    distances: list[tuple[str, str, int]] = []
    for index, node in enumerate(nodes):
        steps = distances_from(world_map, node.tile)
        for other in nodes[index + 1 :]:
            if other.tile in steps:
                distances.append((node.node_id, other.node_id, steps[other.tile]))
        for name, tile in anchors.items():
            if tile in steps:
                distances.append((node.node_id, name, steps[tile]))
    return RouteGraph(
        tuple(ZoneArea(z.zone_id, z.left, z.top, z.width, z.height) for z in level.zones),
        nodes,
        anchors["CORE"],
        anchors["EXIT"],
        tuple(distances),
        exit_tiles,
    )


def _fits(world_map: StaticMap, tile: Tile, radius: int) -> bool:
    return body_fits(world_map, tile_center(tile), radius)  # same test as spawns


def build_security_registry(level: LevelData, rules: GameRules) -> SecurityRegistry:
    problems: list[str] = []
    world_map = level.static_map
    routes = {route.route_id: route for route in level.routes}
    zone_ids = {zone.zone_id for zone in level.zones}
    if len(routes) != len(level.routes):
        problems.append("duplicate patrol route ID")
    if len({post.guard_id for post in level.guards}) != len(level.guards):
        problems.append("duplicate guard ID")
    if len({point.point_id for point in level.chokepoints}) != len(level.chokepoints):
        problems.append("duplicate chokepoint ID")
    for point in level.chokepoints:
        if not world_map.can_walk(point.tile) or not set(point.zones) <= zone_ids:
            problems.append(f"chokepoint {point.point_id!r} is not a walkable known-zone link")
    used: dict[str, str] = {}
    assignments: list[GuardAssignment] = []
    for post in sorted(level.guards, key=lambda value: value.guard_id):
        where = f"guard {post.guard_id!r}"
        role = ROLES.get(post.kind)
        route = routes.get(post.route_id)
        if role is None:
            problems.append(f"{where} has unsupported kind {post.kind}")
            continue
        if route is None:
            problems.append(f"{where} references missing route {post.route_id!r}")
            continue
        if post.route_id in used:
            problems.append(f"{where} shares route {post.route_id!r} with {used[post.route_id]!r}")
        used[post.route_id] = post.guard_id
        points = route.points[:-1] if route.points[0] == route.points[-1] else route.points
        if points[0] != post.tile:
            problems.append(f"{where} must start on its route's first waypoint")
        bad = [tile for tile in points if not _fits(world_map, tile, rules.actor_radius_units)]
        if bad:
            problems.append(f"{where} waypoint {bad[0]} does not fit a guard body")
        legs = zip(points, (*points[1:], points[0]), strict=True)
        if not bad and any(not bfs(world_map, first, second).path for first, second in legs):
            problems.append(f"{where} has disconnected waypoints")
        zone = level.zone_at(post.tile)
        zone_id = zone.zone_id if zone else ""
        chokepoints = tuple(
            sorted(point.point_id for point in level.chokepoints if zone_id in point.zones)
        )
        if role == GuardRole.INTERCEPTOR and not chokepoints:
            problems.append(f"{where} has no chokepoint for its interception role")
        if len(points) >= 2:
            assignments.append(
                GuardAssignment(
                    post.guard_id,
                    post.kind,
                    role,
                    post.route_id,
                    GuardPatrol(post.guard_id, points, role),
                    zone_id,
                    chokepoints,
                )
            )
        else:
            problems.append(f"{where} route needs two distinct waypoints")
    if problems:
        raise SecurityRegistryError(problems)
    canonical = json.dumps(
        [
            {
                "guard": value.guard_id,
                "kind": value.kind.value,
                "role": value.role.value,
                "route": value.route_id,
                "points": value.patrol.points,
                "zone": value.zone_id,
                "chokepoints": value.chokepoint_ids,
            }
            for value in assignments
        ]
        + [
            {"chokepoint": point.point_id, "tile": point.tile, "zones": point.zones}
            for point in sorted(level.chokepoints, key=lambda value: value.point_id)
        ],
        sort_keys=True,
        separators=(",", ":"),
    )
    director = DirectorRules(
        guard_ticks_per_tile=_ticks_per_tile(rules, rules.interceptor_speed_units_per_second),
        intruder_ticks_per_tile=_ticks_per_tile(rules, rules.walk_speed_units_per_second),
    )
    return SecurityRegistry(
        tuple(assignments),
        tuple(sorted(level.chokepoints, key=lambda value: value.point_id)),
        level.sound_blocking_tiles,
        sha256(canonical.encode()).hexdigest(),
        build_route_graph(level),
        director,
        tuple((deck.left, deck.top, deck.width, deck.height) for deck in level.decks),
    )
