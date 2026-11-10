"""Door, glass, canister and locker rules invoked by Simulation at fixed points.

Ordering inside one tick (see ``Simulation.step``):

1. ``push`` before movement: pushing into a closed door starts opening it; a
   sprint into intact glass shatters it. The pushing body is still blocked
   this tick because geometry only changes at the start of the next tick.
2. Movement, then ``interact``/``hide`` after every move (revalidated reach).
3. ``bump`` after movement: an intruder stepping onto a resting canister kicks it.
4. ``advance``: door travel, canister rolling/final impact, cue expiry.
5. Simulation applies one combined geometry revision at the next tick start.

Every gameplay sound is a single committed NoiseEvent; cues reference it.
"""

from collections.abc import Callable
from dataclasses import dataclass, replace

from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.environment.model import EnvironmentSpec
from echo_heist.core.contracts.environment.presentation import (
    EnvironmentCue,
    EnvironmentCueKind,
    PropKind,
)
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.observations import InteractionHint
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import ActorKind, Position, StaticMap, Tile, tile_center
from echo_heist.core.environment.state import (
    CanisterState,
    DoorState,
    EnvironmentState,
    GlassState,
    LockerState,
)
from echo_heist.core.simulation.systems.motion import body_fits, clear_reach, distance_squared
from echo_heist.core.simulation.world import ActorState, Emit, WorldState

INTRUDERS = frozenset({ActorKind.OPERATIVE, ActorKind.COMPANION})
HINT_KINDS = {
    PropKind.DOOR: "Door",
    PropKind.GLASS: "Glass",
    PropKind.CANISTER: "Canister",
    PropKind.LOCKER: "HideSpot",
}

type Visibility = Callable[[Position, str], bool]


@dataclass(frozen=True, slots=True)
class Tick:
    """Everything one rule call may read or emit for the current tick."""

    world: WorldState
    world_map: StaticMap
    rules: GameRules
    emit: Emit
    visible: Visibility

    @property
    def env(self) -> EnvironmentState:
        return self.world.environment


def initial_state(spec: EnvironmentSpec) -> EnvironmentState:
    cycle = spec.rules.door_cycle_ticks
    state = EnvironmentState(spec.rules)
    for prop in spec.props:
        if prop.kind == PropKind.DOOR:
            state.doors[prop.object_id] = DoorState(prop, cycle)
        elif prop.kind == PropKind.GLASS:
            state.glass[prop.object_id] = GlassState(prop)
        elif prop.kind == PropKind.CANISTER:
            center = tile_center(prop.tile)
            state.canisters[prop.object_id] = CanisterState(prop, prop.tile, center, center)
        else:
            state.lockers[prop.object_id] = LockerState(prop)
    return state


def effective_map(base: StaticMap, env: EnvironmentState) -> StaticMap:
    """The physical map: closed doors block bodies and sight; intact glass bodies."""
    closed = frozenset(
        tile for door in env.doors.values() if door.blocked for tile in door.spec.tiles
    )
    panes = frozenset(
        tile for pane in env.glass.values() if not pane.broken for tile in pane.spec.tiles
    )
    doors = frozenset(tile for door in env.doors.values() for tile in door.spec.tiles)
    if not (closed or panes or doors):
        return base
    return replace(
        base,
        blocked_tiles=base.blocked_tiles | closed | panes,
        opaque_tiles=base.opaque_tiles | closed,
        door_tiles=base.door_tiles | doors,
    )


def _cardinal(dx: int, dy: int) -> Tile:
    """One rolling/pushing axis; x wins an exact diagonal tie (stable rule)."""
    if dx == 0 and dy == 0:
        return 0, 0
    if abs(dx) >= abs(dy):
        return (1 if dx > 0 else -1), 0
    return 0, (1 if dy > 0 else -1)


def _body_tiles(actor: ActorState, radius: int) -> frozenset[Tile]:
    x, y = actor.position
    return frozenset(
        (a, b)
        for a in range((x - radius) // UNIT, (x + radius - 1) // UNIT + 1)
        for b in range((y - radius) // UNIT, (y + radius - 1) // UNIT + 1)
    )


def _cue(
    t: Tick,
    kind: EnvironmentCueKind,
    object_id: str,
    position: Position,
    actor_id: str,
    noise: tuple[str, int] | None,
) -> None:
    """Commit one NoiseEvent (if gameplay-relevant) and one presentation cue."""
    noise_id = None
    if noise is not None:
        noise_id = f"{t.world.tick}:{t.world.next_event_id}"
        tile = (position[0] // UNIT, position[1] // UNIT)
        t.emit(
            EventKind.NOISE_CREATED,
            actor_id,
            (("kind", noise[0]), ("x", tile[0]), ("y", tile[1]), ("radius_tiles", noise[1])),
        )
    event_id = f"{t.world.tick}:{t.world.next_event_id}"
    t.emit(
        EventKind.PROP_CHANGED,
        actor_id,
        (("object_id", object_id), ("cue", kind.value), ("noise_event_id", noise_id)),
    )
    t.env.cues.append(
        EnvironmentCue(
            event_id,
            t.world.tick,
            kind,
            object_id,
            position,
            actor_id,
            noise_id,
            t.visible(position, actor_id),
        )
    )


def _state(t: Tick, actor_id: str, object_id: str, state: str) -> None:
    t.emit(EventKind.PROP_CHANGED, actor_id, (("object_id", object_id), ("state", state)))


def _span_center(tiles: tuple[Tile, ...]) -> Position:
    centers = [tile_center(tile) for tile in tiles]
    return (
        sum(point[0] for point in centers) // len(centers),
        sum(point[1] for point in centers) // len(centers),
    )


# --------------------------------------------------------------------------- doors
def door_obstructed(world: WorldState, rules: GameRules, door: DoorState) -> bool:
    """A closing door may not enclose any body or resting/rolling canister."""
    tiles = frozenset(door.spec.tiles)
    if any(_body_tiles(actor, rules.actor_radius_units) & tiles for actor in world.actors.values()):
        return True
    return any(
        can.tile in tiles or (can.rolling and _next(can) in tiles)
        for can in world.environment.canisters.values()
    )


def _move_door(t: Tick, door: DoorState, actor_id: str, opening: bool) -> None:
    door.opening, door.mover = opening, actor_id
    intruder = t.world.actors[actor_id].kind in INTRUDERS
    radius = t.env.rules.door_noise_radius_tiles
    # Guards' own servo motion is not an investigation lead for other guards,
    # just as guard footsteps are silent; an intruder's door is audible.
    _cue(
        t,
        EnvironmentCueKind.DOOR,
        door.spec.object_id,
        _span_center(door.spec.tiles),
        actor_id,
        ("DOOR", radius) if intruder else None,
    )
    _state(t, actor_id, door.spec.object_id, "OPENING" if opening else "CLOSING")


def toggle_door(t: Tick, actor_id: str, door: DoorState) -> str | None:
    if door.opening:
        if door_obstructed(t.world, t.rules, door):
            return "door_obstructed"
        _move_door(t, door, actor_id, opening=False)
    else:
        _move_door(t, door, actor_id, opening=True)
    return None


def _advance_doors(t: Tick) -> None:
    cycle = t.env.rules.door_cycle_ticks
    for door in t.env.doors.values():
        if door.opening and door.open_ticks < cycle:
            door.open_ticks += 1
            if door.open_ticks == cycle:
                _state(t, door.mover, door.spec.object_id, "OPEN")
                if door.blocked:
                    door.blocked = False
                    t.env.geometry_reasons.append(f"door-open:{door.spec.object_id}")
        elif not door.opening and door.open_ticks > 0:
            door.open_ticks -= 1
            if door.open_ticks > 0:
                continue
            if door_obstructed(t.world, t.rules, door):
                # Something entered the doorway while it was closing: bounce
                # open instead of enclosing a body (never a silent overlap).
                door.opening = True
                _state(t, door.mover, door.spec.object_id, "REOPENING")
            else:
                door.blocked = True
                _state(t, door.mover, door.spec.object_id, "CLOSED")
                t.env.geometry_reasons.append(f"door-closed:{door.spec.object_id}")


# --------------------------------------------------------------------------- glass
def break_glass(t: Tick, actor_id: str, pane: GlassState) -> None:
    if pane.broken:
        return  # once-only: never a second break, sound or geometry change
    pane.broken, pane.broken_tick = True, t.world.tick
    _cue(
        t,
        EnvironmentCueKind.GLASS,
        pane.spec.object_id,
        _span_center(pane.spec.tiles),
        actor_id,
        ("GLASS", t.env.rules.glass_noise_radius_tiles),
    )
    _state(t, actor_id, pane.spec.object_id, "SHATTERED")
    t.env.geometry_reasons.append(f"glass-broken:{pane.spec.object_id}")


# ------------------------------------------------------------------------ canisters
def _next(can: CanisterState) -> Tile:
    return can.tile[0] + can.direction[0], can.tile[1] + can.direction[1]


def _roll_blocked(t: Tick, can: CanisterState, tile: Tile) -> bool:
    world_map = t.world_map
    if (
        not world_map.contains(tile)
        or tile in world_map.blocked_tiles
        or any(link.tile == tile for link in world_map.stairs)
    ):
        return True
    radius = t.rules.actor_radius_units
    if any(tile in _body_tiles(actor, radius) for actor in t.world.actors.values()):
        return True
    return any(
        other.spec.object_id != can.spec.object_id
        and (other.tile == tile or (other.rolling and _next(other) == tile))
        for other in t.env.canisters.values()
    )


def _impact(t: Tick, can: CanisterState) -> None:
    can.direction, can.steps_left, can.step_progress = (0, 0), 0, 0
    _cue(
        t,
        EnvironmentCueKind.CANISTER_IMPACT,
        can.spec.object_id,
        can.position,
        can.mover,
        ("METAL", t.env.rules.canister_noise_radius_tiles),
    )


def kick(t: Tick, actor_id: str, can: CanisterState, direction: Tile) -> None:
    if can.rolling or direction == (0, 0):
        return
    can.direction, can.steps_left, can.step_progress = direction, t.env.rules.canister_roll_tiles, 0
    can.mover = actor_id
    _state(t, actor_id, can.spec.object_id, "ROLLING")
    if _roll_blocked(t, can, _next(can)):
        _impact(t, can)  # kicked straight into an obstacle: one clang where it lies


def _advance_canisters(t: Tick) -> None:
    step_ticks = t.env.rules.canister_step_ticks
    for can in t.env.canisters.values():
        can.previous_position = can.position
        if not can.rolling:
            continue
        can.step_progress += 1
        origin = tile_center(can.tile)
        can.position = (
            origin[0] + can.direction[0] * UNIT * can.step_progress // step_ticks,
            origin[1] + can.direction[1] * UNIT * can.step_progress // step_ticks,
        )
        can.roll_degrees = (can.roll_degrees + 36) % 360
        if can.step_progress < step_ticks:
            continue
        can.tile, can.step_progress = _next(can), 0
        can.position = tile_center(can.tile)
        can.steps_left -= 1
        if can.steps_left == 0 or _roll_blocked(t, can, _next(can)):
            _impact(t, can)


def bump(t: Tick, actor_id: str) -> None:
    """An intruder who walks onto a resting canister kicks it along that step."""
    actor = t.world.actors[actor_id]
    if actor.kind not in INTRUDERS or len(actor.traversed_tiles) < 2:
        return
    path = actor.traversed_tiles
    for can in sorted(t.env.canisters.values(), key=lambda value: value.spec.object_id):
        if can.rolling or can.tile not in path[1:]:
            continue
        index = path.index(can.tile, 1)
        before = path[index - 1]
        kick(t, actor_id, can, _cardinal(can.tile[0] - before[0], can.tile[1] - before[1]))


# -------------------------------------------------------------------------- lockers
def enter_locker(t: Tick, actor_id: str, locker: LockerState) -> str | None:
    actor = t.world.actors[actor_id]
    center = tile_center(locker.spec.tile)
    radius = t.rules.actor_radius_units
    if locker.occupant is not None:
        return "hide_spot_occupied"
    if not body_fits(t.world_map, center, radius) or any(
        other.actor_id != actor_id and distance_squared(other.position, center) < (2 * radius) ** 2
        for other in t.world.actors.values()
    ):
        return "hide_spot_blocked"
    actor.position, actor.crouched, actor.hidden_in = center, False, locker.spec.object_id
    locker.occupant, locker.moved_tick = actor_id, t.world.tick
    _cue(t, EnvironmentCueKind.HIDE_ENTER, locker.spec.object_id, center, actor_id, None)
    return None


def leave_locker(t: Tick, actor_id: str) -> None:
    actor = t.world.actors[actor_id]
    locker = t.env.lockers.get(actor.hidden_in or "")
    actor.hidden_in = None
    if locker is None:
        return
    locker.occupant, locker.moved_tick = None, t.world.tick
    _cue(
        t,
        EnvironmentCueKind.HIDE_LEAVE,
        locker.spec.object_id,
        tile_center(locker.spec.tile),
        actor_id,
        None,
    )


# ------------------------------------------------------------------ hints/dispatch
def _anchor(t_world: WorldState, object_id: str) -> tuple[PropKind, Position, tuple[Tile, ...]]:
    env = t_world.environment
    if object_id in env.doors:
        return PropKind.DOOR, (0, 0), env.doors[object_id].spec.tiles
    if object_id in env.glass:
        return PropKind.GLASS, (0, 0), env.glass[object_id].spec.tiles
    if object_id in env.canisters:
        can = env.canisters[object_id]
        return PropKind.CANISTER, can.position, (can.tile,)
    locker = env.lockers[object_id]
    return PropKind.LOCKER, tile_center(locker.spec.tile), locker.spec.tiles


def hints(
    world: WorldState, world_map: StaticMap, rules: GameRules, actor_id: str
) -> tuple[tuple[int, InteractionHint], ...]:
    """Offered prop interactions with their squared reach distance.

    A hidden intruder is only offered leaving its own locker.
    """
    actor = world.actors[actor_id]
    if actor.kind not in INTRUDERS:
        return ()
    if actor.hidden_in is not None:
        return ((0, InteractionHint(actor.hidden_in, "LeaveHide", 1)),)
    env = world.environment
    candidates = [
        *(door.spec for door in env.doors.values()),
        *(pane.spec for pane in env.glass.values() if not pane.broken),
        *(can.spec for can in env.canisters.values() if not can.rolling),
        *(locker.spec for locker in env.lockers.values() if locker.occupant is None),
    ]
    offered: list[tuple[int, str, InteractionHint]] = []
    for spec in candidates:
        kind, point, tiles = _anchor(world, spec.object_id)
        points = (
            [point]
            if kind in (PropKind.CANISTER, PropKind.LOCKER)
            else [tile_center(tile) for tile in tiles]
        )
        reach = min(distance_squared(actor.position, value) for value in points)
        target = min(points, key=lambda value: distance_squared(actor.position, value))
        if reach > rules.interaction_range_units**2:
            continue
        if not clear_reach(world_map, actor.position, target, allow_solid_end=True):
            continue
        offered.append(
            (reach, spec.object_id, InteractionHint(spec.object_id, HINT_KINDS[kind], 1))
        )
    offered.sort(key=lambda value: (value[0], value[1]))
    return tuple((reach, hint) for reach, _, hint in offered)


def interact(t: Tick, actor_id: str, object_id: str) -> str | None:
    """Apply one validated prop interaction; return a rejection reason or None."""
    env = t.env
    actor = t.world.actors[actor_id]
    if actor.hidden_in is not None:
        if object_id != actor.hidden_in:
            return "hidden"
        leave_locker(t, actor_id)
        return None
    if object_id in env.doors:
        return toggle_door(t, actor_id, env.doors[object_id])
    if object_id in env.glass:
        break_glass(t, actor_id, env.glass[object_id])
        return None
    if object_id in env.canisters:
        can = env.canisters[object_id]
        direction = _cardinal(can.tile[0] - actor.tile[0], can.tile[1] - actor.tile[1])
        kick(t, actor_id, can, direction if direction != (0, 0) else _cardinal(*actor.facing))
        return None
    return enter_locker(t, actor_id, env.lockers[object_id])


def push(t: Tick, actor_id: str, direction: Tile, sprint: bool) -> None:
    """Before movement: pressing into a closed door opens it; sprinting shatters glass."""
    actor = t.world.actors[actor_id]
    x, y = actor.tile
    ahead = {(x + direction[0], y), (x, y + direction[1])} - {(x, y)}
    for door in t.env.doors.values():
        if not door.opening and ahead & set(door.spec.tiles):
            _move_door(t, door, actor_id, opening=True)
    if sprint and actor.kind in INTRUDERS:
        for pane in t.env.glass.values():
            if not pane.broken and ahead & set(pane.spec.tiles):
                break_glass(t, actor_id, pane)


def advance(t: Tick) -> None:
    _advance_doors(t)
    _advance_canisters(t)
    ttl = t.env.rules.cue_ttl_ticks
    t.env.cues[:] = [cue for cue in t.env.cues if t.world.tick - cue.tick < ttl]
