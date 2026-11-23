"""Fixed-point swept movement and conservative line-of-reach queries."""

from math import isqrt

from echo_heist.core.contracts.actions import Action
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.security.model import GuardState
from echo_heist.core.contracts.world import (
    POSITION_UNITS_PER_TILE as UNIT,
)
from echo_heist.core.contracts.world import (
    ActorKind,
    MissionPhase,
    Position,
    StaticMap,
    Tile,
    position_tile,
)
from echo_heist.core.simulation.world import GUARD_KINDS, ActorState, Emit, WorldState


def distance_squared(first: Position, second: Position) -> int:
    return (first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2


def body_occupied(
    world: WorldState,
    actor: ActorState,
    target: Position,
    rules: GameRules,
    desks: frozenset[Tile] = frozenset(),
) -> ActorState | None:
    """The body ``target`` would press into, or None when the way is clear.

    Guards and intruders block each other. Guards slide past fellow guards, so
    two patrols meeting head-on in a one-tile corridor cannot deadlock. A
    stunned or EMP-disabled guard is a slumped body anyone can step past, and
    an actor already inside another's clearance (a guard waking up beside it)
    may always move apart, so no case freezes motion against a wall. Someone
    shut inside a locker is out of the walkway entirely, and an intruder tucked
    under a desk (``desks``) only blocks by plain body contact: the wider
    guard margin let a thief at a desk's edge wall off the corridor in front.
    """
    guard = actor.kind in GUARD_KINDS

    def tucked(body: ActorState) -> bool:
        return body.kind not in GUARD_KINDS and body.crouched and body.tile in desks

    for other in world.actors.values():
        if (
            other is actor
            or other.hidden_in is not None  # shut inside a locker, out of the walkway
            or (other.kind in GUARD_KINDS and (guard or other.incapacitated(world.tick)))
        ):
            continue
        wide = guard != (other.kind in GUARD_KINDS) and not (tucked(actor) or tucked(other))
        clearance = rules.guard_intruder_clearance_units if wide else 2 * rules.actor_radius_units
        gap = distance_squared(target, other.position)
        if gap < clearance**2 and gap <= distance_squared(actor.position, other.position):
            return other
    return None


def toward(origin: Position, target: Position) -> Tile:
    """The closest of the eight facings from ``origin`` to ``target``."""
    dx, dy = target[0] - origin[0], target[1] - origin[1]
    big = max(abs(dx), abs(dy))
    return (
        (dx > 0) - (dx < 0) if 2 * abs(dx) >= big else 0,
        (dy > 0) - (dy < 0) if 2 * abs(dy) >= big else 0,
    )


def clear_reach(
    world_map: StaticMap, start: Position, end: Position, *, allow_solid_end: bool = False
) -> bool:
    dx, dy = end[0] - start[0], end[1] - start[1]
    steps = max(1, (max(abs(dx), abs(dy)) + UNIT // 8 - 1) // (UNIT // 8))
    previous, target = position_tile(start), position_tile(end)

    def clear(point: Position) -> bool:
        tile = position_tile(point)
        return (allow_solid_end and tile == target and world_map.contains(tile)) or (
            not world_map.point_blocked(point) and not world_map.point_blocked(point, vision=True)
        )

    for index in range(steps + 1):
        point = start[0] + dx * index // steps, start[1] + dy * index // steps
        tile = position_tile(point)
        if not clear(point):
            return False
        if (tile[0] != previous[0] and tile[1] != previous[1]) and any(
            corner in world_map.hard_blocked or corner in world_map.hard_opaque
            for corner in ((tile[0], previous[1]), (previous[0], tile[1]))
        ):
            return False
        previous = tile
    return True


def body_fits(
    world_map: StaticMap, position: Position, radius: int, *, crouched: bool = False
) -> bool:
    left, top = (position[0] - radius) // UNIT, (position[1] - radius) // UNIT
    right, bottom = (position[0] + radius - 1) // UNIT, (position[1] + radius - 1) // UNIT
    tiles = tuple((x, y) for x in range(left, right + 1) for y in range(top, bottom + 1))
    if any(
        not world_map.contains(tile)
        or (tile in world_map.hard_blocked and not (crouched and tile in world_map.crouch_tiles))
        for tile in tiles
    ):
        return False
    checked: set[str] = set()
    for tile in tiles:
        for obstacle in world_map.obstacle_index.get(tile, ()):
            if obstacle.object_id in checked:
                continue
            checked.add(obstacle.object_id)
            x0, y0 = (
                max(position[0] - radius, obstacle.left),
                max(position[1] - radius, obstacle.top),
            )
            x1, y1 = (
                min(position[0] + radius, obstacle.right),
                min(position[1] + radius, obstacle.bottom),
            )
            if x0 >= x1 or y0 >= y1:
                continue
            if crouched and all(
                (x, y) in world_map.crouch_tiles
                for x in range(x0 // UNIT, (x1 - 1) // UNIT + 1)
                for y in range(y0 // UNIT, (y1 - 1) // UNIT + 1)
            ):
                continue
            return False
    return True


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
    if actor.kind not in (ActorKind.OPERATIVE, ActorKind.COMPANION):
        memory = world.guard_memories.get(actor.actor_id)
        # CHASE follows confirmed observation, including pursuit to the last
        # seen location. Hearing/partial suspicion never unlock this boost.
        chase = memory is not None and memory.state == GuardState.CHASE
        multiplier = max(
            rules.chase_guard_speed_percent if chase else 100,
            rules.lockdown_guard_speed_percent if world.phase == MissionPhase.LOCKDOWN else 100,
        )
        speed = speed * multiplier // 100
        if (
            memory is not None
            and chase
            and memory.last_seen_tick == world.tick - 1
            and memory.live_pursuit_ticks > rules.pursuit_grace_ticks
        ):
            speed = max(
                speed, rules.sprint_speed_units_per_second * rules.pursuit_pressure_percent // 100
            )
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
    bumped: ActorState | None = None
    for index in range(count):
        delta = (
            dx * (index + 1) // count - dx * index // count,
            dy * (index + 1) // count - dy * index // count,
        )
        for axis in (0, 1):
            candidate = list(actor.position)
            candidate[axis] += delta[axis]
            target = candidate[0], candidate[1]
            if delta[axis] and body_fits(
                world_map, target, rules.actor_radius_units, crouched=actor.crouched
            ):
                blocker = body_occupied(world, actor, target, rules, world_map.crouch_tiles)
                if blocker is None:
                    actor.position = target
                elif blocker.kind not in GUARD_KINDS:
                    bumped = blocker
        if actor.tile != visited[-1]:
            visited.append(actor.tile)
    actor.traversed_tiles = tuple(visited)
    if actor.position == origin:
        if bumped is not None and actor.kind in GUARD_KINDS:
            # Walking into a body is felt: the guard turns toward it, and its own
            # sight then decides what it is (an unseen thief at its shoulder no
            # longer holds it in a shoving match).
            actor.facing = toward(actor.position, bumped.position)
        emit(EventKind.ACTION_REJECTED, actor.actor_id, (("reason", "blocked"),))
        return
    if actor.actor_id not in world.guard_memories:
        # Registry guards face where their decision looks (a chaser watches its quarry).
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
            else rules.sprint_footstep_interval_ticks
            if sprint
            else rules.footstep_interval_ticks
        )


def remember_paths(world: WorldState, rules: GameRules) -> None:
    for actor in world.actors.values():
        actor.path.append(actor.position)
        del actor.path[: -rules.echo_history_ticks]
