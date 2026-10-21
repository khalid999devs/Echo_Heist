"""Cone/occlusion tests and bounded acoustic flood fill over explicit map flags."""

from collections import deque
from math import cos, radians

from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import Position, StaticMap, Tile, position_tile


def sight_ray(world_map: StaticMap, start: Position, end: Position) -> tuple[bool, Position]:
    """Return visibility and the last clear sample, shared with cone rendering."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    steps = max(1, (max(abs(dx), abs(dy)) + UNIT // 8 - 1) // (UNIT // 8))
    previous = position_tile(start)
    last_clear = start
    for index in range(steps + 1):
        point = start[0] + dx * index // steps, start[1] + dy * index // steps
        tile = position_tile(point)
        if not world_map.contains(tile) or tile in world_map.opaque_tiles:
            return False, last_clear
        if (
            tile[0] != previous[0]
            and tile[1] != previous[1]
            and (
                (tile[0], previous[1]) in world_map.opaque_tiles
                or (previous[0], tile[1]) in world_map.opaque_tiles
            )
        ):
            return False, last_clear
        previous = tile
        last_clear = point
    return True, end


def line_of_sight(world_map: StaticMap, start: Position, end: Position) -> bool:
    return sight_ray(world_map, start, end)[0]


def can_see(
    world_map: StaticMap,
    start: Position,
    end: Position,
    facing: Tile,
    range_tiles: int,
    half_angle: int,
) -> bool:
    dx, dy = end[0] - start[0], end[1] - start[1]
    distance = dx * dx + dy * dy
    if distance > (range_tiles * UNIT) ** 2:
        return False
    dot = dx * facing[0] + dy * facing[1]
    facing_length = facing[0] ** 2 + facing[1] ** 2
    if facing_length == 0:
        return False
    cosine = round(cos(radians(half_angle)) * 1_000_000)
    if dot < 0 or dot * dot * 10**12 < distance * facing_length * cosine * cosine:
        return False
    return line_of_sight(world_map, start, end)


def sound_reaches(
    world_map: StaticMap, blockers: frozenset[Tile], source: Tile, listener: Tile, radius: int
) -> bool:
    if not world_map.contains(source) or not world_map.contains(listener) or radius < 0:
        return False
    pending = deque([(source, 0)])
    visited = {source}
    while pending:
        tile, distance = pending.popleft()
        if tile == listener:
            return True
        if distance == radius:
            continue
        for neighbor in world_map.connections(tile):
            if (
                world_map.contains(neighbor)
                and neighbor not in blockers
                and neighbor not in visited
            ):
                visited.add(neighbor)
                pending.append((neighbor, distance + 1))
    return False
