"""Read-only routes for scripted native QA; never inputs to a gameplay controller."""

from dataclasses import replace
from typing import Literal

from echo_heist.ai.navigation.grid import bfs
from echo_heist.core.contracts.world import Tile
from echo_heist.level.model import LevelData

type Branch = Literal["upper", "lower", "cross"]


def anchor(level: LevelData, object_id: str) -> Tile:
    return next(obj.tile for obj in level.static_map.objects if obj.object_id == object_id)


def walk_path(
    level: LevelData, start: Tile, goal: Tile, *, avoid_zone: str | None = None
) -> tuple[Tile, ...]:
    blocked = level.static_map.blocked_tiles
    if avoid_zone is not None:
        zone = next(zone for zone in level.zones if zone.zone_id == avoid_zone)
        blocked |= frozenset(
            (x, y)
            for x in range(zone.left, zone.left + zone.width)
            for y in range(zone.top, zone.top + zone.height)
        )
    result = bfs(replace(level.static_map, blocked_tiles=blocked), start, goal)
    if not result.path:
        raise ValueError(f"No QA route from {start} to {goal} avoiding {avoid_zone}")
    return result.path


def mission_path(level: LevelData, branch: Branch, *, returning: bool = False) -> tuple[Tile, ...]:
    core = anchor(level, level.core_id)
    approach = core
    start = approach if returning else level.spawn_tile
    goal = anchor(level, level.exit_id) if returning else approach
    if branch == "cross":
        crossing = next(
            point.tile for point in level.chokepoints if point.point_id == "choke-cross-link"
        )
        first = walk_path(level, start, crossing, avoid_zone="research-floor")
        second = walk_path(level, crossing, goal, avoid_zone="security-control")
        return first + second[1:]
    avoid = "research-floor" if branch == "upper" else "security-control"
    return walk_path(level, start, goal, avoid_zone=avoid)
