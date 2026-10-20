"""Playability rules for imported levels: anchors, tags, patrols and reachability."""

from collections import deque
from collections.abc import Iterable

from echo_heist.core.contracts.world import Tile
from echo_heist.level.model import ZONE_IDS, LevelData

MIN_GUARD_SPAWN_DISTANCE = 3
NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def reachable(level: LevelData, starts: Iterable[Tile], avoid: frozenset[Tile]) -> set[Tile]:
    """Four-neighbor flood fill over walkable tiles, never entering `avoid`."""
    world_map = level.static_map
    frontier = deque(tile for tile in starts if world_map.can_walk(tile) and tile not in avoid)
    seen = set(frontier)
    while frontier:
        x, y = frontier.popleft()
        for dx, dy in NEIGHBORS:
            tile = (x + dx, y + dy)
            if tile not in seen and tile not in avoid and world_map.can_walk(tile):
                seen.add(tile)
                frontier.append(tile)
    return seen


def zone_tiles(level: LevelData, zone_id: str) -> frozenset[Tile]:
    zone = next(zone for zone in level.zones if zone.zone_id == zone_id)
    return frozenset(
        (x, y)
        for x in range(zone.left, zone.left + zone.width)
        for y in range(zone.top, zone.top + zone.height)
    )


def _geometry(level: LevelData) -> list[str]:
    world_map = level.static_map
    problems: list[str] = []
    walkable = {
        (x, y)
        for x in range(world_map.width)
        for y in range(world_map.height)
        if world_map.can_walk((x, y))
    }
    unfloored = sorted(walkable - level.floor_tiles)
    if unfloored:
        problems.append(f"walkable tiles without floor (first {unfloored[0]}): {len(unfloored)}")
    edge = sorted(
        tile
        for tile in walkable
        if tile[0] in (0, world_map.width - 1) or tile[1] in (0, world_map.height - 1)
    )
    if edge:
        problems.append(f"map border must block movement; walkable edge tile {edge[0]}")
    if not level.glass_tiles <= world_map.blocked_tiles - world_map.opaque_tiles:
        problems.append("glass must block movement but not vision")
    if not level.cover_tiles <= world_map.blocked_tiles & world_map.opaque_tiles:
        problems.append("cover must block movement and vision")
    return problems


def _zones(level: LevelData) -> list[str]:
    problems: list[str] = []
    ids = sorted(zone.zone_id for zone in level.zones)
    if ids != sorted(ZONE_IDS):
        problems.append(f"zones must be exactly {', '.join(ZONE_IDS)}; found {', '.join(ids)}")
        return problems
    for zone in level.zones:
        if zone.left + zone.width > level.static_map.width or (
            zone.top + zone.height > level.static_map.height
        ):
            problems.append(f"zone {zone.zone_id!r} extends outside the map")
    for index, first in enumerate(level.zones):
        for second in level.zones[index + 1 :]:
            if zone_tiles(level, first.zone_id) & zone_tiles(level, second.zone_id):
                problems.append(f"zones {first.zone_id!r} and {second.zone_id!r} overlap")
    return problems


def _anchors(level: LevelData) -> list[str]:
    world_map = level.static_map
    problems: list[str] = []
    anchors = {obj.object_id: obj for obj in world_map.objects}
    expected = (
        (level.spawn_id, "entry"),
        (level.exit_id, "entry"),
        (level.core_id, "core-chamber"),
    )
    for object_id, zone_id in expected:
        tile = anchors[object_id].tile
        if not world_map.can_walk(tile):
            problems.append(f"anchor {object_id!r} at {tile} is not walkable")
        zone = level.zone_at(tile)
        if zone is None or zone.zone_id != zone_id:
            problems.append(f"anchor {object_id!r} must lie inside zone {zone_id!r}")
    if anchors[level.exit_id].tile == anchors[level.core_id].tile:
        problems.append("Exit and Core must use different tiles")
    for marker in level.markers:
        if not world_map.can_walk(marker.tile):
            problems.append(f"{marker.kind} {marker.marker_id!r} at {marker.tile} is not walkable")
        if marker.kind == "HideSpot" and not any(
            (marker.tile[0] + dx, marker.tile[1] + dy) in world_map.opaque_tiles
            for dx, dy in NEIGHBORS
        ):
            problems.append(f"hide spot {marker.marker_id!r} has no adjacent vision blocker")
    known = {zone.zone_id for zone in level.zones}
    for point in level.chokepoints:
        if not world_map.can_walk(point.tile):
            problems.append(f"chokepoint {point.point_id!r} at {point.tile} is not walkable")
        if point.zones[0] == point.zones[1] or not set(point.zones) <= known:
            problems.append(f"chokepoint {point.point_id!r} must link two distinct known zones")
    return problems


def _patrols(level: LevelData) -> list[str]:
    world_map = level.static_map
    problems: list[str] = []
    routes = {route.route_id: route for route in level.routes}
    for route in level.routes:
        if len(route.points) < 2:
            problems.append(f"patrol {route.route_id!r} needs at least two points")
            continue
        pairs = zip(route.points, route.points[1:], strict=False)
        if any(a[0] != b[0] and a[1] != b[1] for a, b in pairs):
            problems.append(f"patrol {route.route_id!r} segments must be horizontal/vertical")
            continue
        blocked = [tile for tile in route.tiles() if not world_map.can_walk(tile)]
        if blocked:
            problems.append(f"patrol {route.route_id!r} crosses blocked tile {blocked[0]}")
    reserved = {
        obj.tile
        for obj in world_map.objects
        if obj.object_id in (level.spawn_id, level.exit_id, level.core_id)
    }
    spawn = level.spawn_tile
    for post in level.guards:
        post_route = routes.get(post.route_id)
        if post_route is None:
            problems.append(f"guard {post.guard_id!r} references missing route {post.route_id!r}")
        elif post_route.points[0] != post.tile:
            problems.append(f"guard {post.guard_id!r} must start on its route's first point")
        if post.guard_id == level.operative_id or post.tile in reserved:
            problems.append(f"guard {post.guard_id!r} collides with the operative or an anchor")
        if abs(post.tile[0] - spawn[0]) + abs(post.tile[1] - spawn[1]) < MIN_GUARD_SPAWN_DISTANCE:
            problems.append(f"guard {post.guard_id!r} starts too close to the operative spawn")
    return problems


def _connectivity(level: LevelData) -> list[str]:
    problems: list[str] = []
    anchors = {obj.object_id: obj.tile for obj in level.static_map.objects}
    spawn, core, exit_tile = level.spawn_tile, anchors[level.core_id], anchors[level.exit_id]
    from_spawn = reachable(level, (spawn,), frozenset())
    if core not in from_spawn:
        problems.append("Core is unreachable from the operative spawn")
    if exit_tile not in reachable(level, (core,), frozenset()):
        problems.append("lockdown return: Exit is unreachable from the Core")
    for zone in level.zones:
        if not zone_tiles(level, zone.zone_id) & from_spawn:
            problems.append(f"zone {zone.zone_id!r} is unreachable from the spawn")
    for kind, tiles in (
        ("marker", [marker.tile for marker in level.markers]),
        ("chokepoint", [point.tile for point in level.chokepoints]),
        ("guard", [post.tile for post in level.guards]),
    ):
        if any(tile not in from_spawn for tile in tiles):
            problems.append(f"a {kind} anchor is unreachable from the spawn")
    service = zone_tiles(level, "service-wing")
    security, research = zone_tiles(level, "security-control"), zone_tiles(level, "research-floor")
    chamber = zone_tiles(level, "core-chamber")
    if core not in reachable(level, service, research):
        problems.append("upper branch: Core unreachable via Security Control alone")
    if core not in reachable(level, service, security):
        problems.append("lower branch: Core unreachable via Research Floor alone")
    if not reachable(level, security, service | chamber) & research:
        problems.append("cross-link: Security Control and Research Floor are not directly joined")
    return problems


def check_level(level: LevelData) -> list[str]:
    """Return every playability problem; an empty list means the level is valid."""
    problems = _zones(level) + _geometry(level)
    if problems:
        return problems
    return _anchors(level) + _patrols(level) + _connectivity(level)
