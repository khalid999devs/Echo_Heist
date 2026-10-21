"""Fixed-point swept movement and conservative line-of-reach queries."""

from math import isqrt

from echo_heist.core.contracts.actions import Action
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.world import (
    POSITION_UNITS_PER_TILE as UNIT,
)
from echo_heist.core.contracts.world import (
    ActorKind,
    MissionPhase,
    Position,
    StaticMap,
    position_tile,
)
from echo_heist.core.simulation.world import Emit, WorldState


def distance_squared(first: Position, second: Position) -> int:
    return (first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2


def clear_reach(
    world_map: StaticMap, start: Position, end: Position, *, allow_solid_end: bool = False
) -> bool:
    dx, dy = end[0] - start[0], end[1] - start[1]
    steps = max(1, (max(abs(dx), abs(dy)) + UNIT // 8 - 1) // (UNIT // 8))
    previous, target = position_tile(start), position_tile(end)

    def clear(tile: tuple[int, int]) -> bool:
        return (allow_solid_end and tile == target and world_map.contains(tile)) or (
            world_map.can_walk(tile) and tile not in world_map.opaque_tiles
        )

    for index in range(steps + 1):
        tile = position_tile((start[0] + dx * index // steps, start[1] + dy * index // steps))
        if not clear(tile):
            return False
        if (tile[0] != previous[0] and tile[1] != previous[1]) and (
            not clear((tile[0], previous[1])) or not clear((previous[0], tile[1]))
        ):
            return False
        previous = tile
    return True


def body_fits(
    world_map: StaticMap, position: Position, radius: int, *, crouched: bool = False
) -> bool:
    left, top = (position[0] - radius) // UNIT, (position[1] - radius) // UNIT
    right, bottom = (position[0] + radius - 1) // UNIT, (position[1] + radius - 1) // UNIT
    return all(
        world_map.can_walk((x, y), crouched=crouched)
        for x in range(left, right + 1)
        for y in range(top, bottom + 1)
    )


def move_actor(
    world: WorldState, world_map: StaticMap, rules: GameRules, action: Action, emit: Emit
) -> None:
    actor = world.actors[action.actor_id]
    sprint = (
        action.sprint
        and not actor.crouched
        and actor.sprint_ready_at == 0
        and actor.sprint_ticks_remaining > 0
    )
    speed = {
        ActorKind.SENTINEL: rules.sentinel_speed_units_per_second,
        ActorKind.TRACKER: rules.tracker_speed_units_per_second,
        ActorKind.INTERCEPTOR: rules.interceptor_speed_units_per_second,
    }.get(
        actor.kind,
        rules.sprint_speed_units_per_second if sprint else rules.walk_speed_units_per_second,
    )
    if (
        actor.kind not in (ActorKind.OPERATIVE, ActorKind.COMPANION)
        and world.phase == MissionPhase.LOCKDOWN
    ):
        speed = speed * rules.lockdown_guard_speed_percent // 100
    step = speed // rules.simulation_hz
    if actor.crouched:
        step = step * rules.crouch_speed_percent // 100
    dx, dy = action.direction[0] * step, action.direction[1] * step
    if dx and dy:
        # Integer sqrt keeps diagonal normalization independent of floating point.
        denominator = isqrt(2 * 10**12)
        # Use symmetric rounding for opposite directions.
        dx = action.direction[0] * (step * 10**6 // denominator)
        dy = action.direction[1] * (step * 10**6 // denominator)
    max_substep = max(1, rules.actor_radius_units // 2)
    count = max(1, (max(abs(dx), abs(dy)) + max_substep - 1) // max_substep)
    origin = actor.position
    visited = [actor.tile]
    for index in range(count):
        delta = (
            dx * (index + 1) // count - dx * index // count,
            dy * (index + 1) // count - dy * index // count,
        )
        for axis in (0, 1):
            candidate = list(actor.position)
            candidate[axis] += delta[axis]
            target = candidate[0], candidate[1]
            occupied = any(
                other.actor_id != actor.actor_id
                and distance_squared(target, other.position) < (2 * rules.actor_radius_units) ** 2
                for other in world.actors.values()
            )
            if (
                body_fits(world_map, target, rules.actor_radius_units, crouched=actor.crouched)
                and not occupied
            ):
                actor.position = target
        if actor.tile != visited[-1]:
            visited.append(actor.tile)
    actor.traversed_tiles = tuple(visited)
    if actor.position == origin:
        emit(EventKind.ACTION_REJECTED, actor.actor_id, (("reason", "blocked"),))
        return
    actor.facing = action.direction
    actor.sprinting = sprint
    if sprint:
        actor.sprint_ticks_remaining -= 1
        if actor.sprint_ticks_remaining == 0:
            actor.sprint_ready_at = world.tick + rules.sprint_recharge_ticks
    emit(
        EventKind.ACTOR_MOVED, actor.actor_id, (("x", actor.position[0]), ("y", actor.position[1]))
    )
    if (
        actor.kind in (ActorKind.OPERATIVE, ActorKind.COMPANION)
        and world.tick >= actor.next_footstep_tick
    ):
        radius = rules.sprint_noise_radius_tiles if sprint else rules.walk_noise_radius_tiles
        emit(
            EventKind.NOISE_CREATED,
            actor.actor_id,
            (
                ("kind", "CROUCH" if actor.crouched else "SPRINT" if sprint else "FOOTSTEP"),
                ("x", actor.tile[0]),
                ("y", actor.tile[1]),
                ("radius_tiles", radius),
            ),
        )
        actor.next_footstep_tick = world.tick + (
            rules.crouch_footstep_interval_ticks
            if actor.crouched
            else rules.footstep_interval_ticks
        )


def remember_paths(world: WorldState, rules: GameRules) -> None:
    for actor in world.actors.values():
        actor.path.append(actor.position)
        del actor.path[: -rules.echo_history_ticks]
