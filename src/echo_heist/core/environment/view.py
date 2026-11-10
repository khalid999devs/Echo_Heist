"""Privileged read-only prop state for presentation; never given to controllers."""

from echo_heist.core.contracts.environment.presentation import EnvironmentView, PropKind, PropView
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import Position, Tile, tile_center
from echo_heist.core.environment.state import EnvironmentState

LEAF = UNIT // 4


def _span(tiles: tuple[Tile, ...], horizontal: bool) -> tuple[Position, Position]:
    centers = [tile_center(tile) for tile in tiles]
    center = (
        sum(point[0] for point in centers) // len(centers),
        sum(point[1] for point in centers) // len(centers),
    )
    length = UNIT * len(tiles)
    return center, ((length, LEAF) if horizontal else (LEAF, length))


def environment_view(env: EnvironmentState, tick: int) -> EnvironmentView:
    props: list[PropView] = []
    cycle = env.rules.door_cycle_ticks
    for door in env.doors.values():
        position, size = _span(door.spec.tiles, door.spec.horizontal)
        props.append(
            PropView(door.spec.object_id, PropKind.DOOR, position, size, door.open_ticks / cycle)
        )
    for pane in env.glass.values():
        position, size = _span(pane.spec.tiles, pane.spec.horizontal)
        props.append(
            PropView(pane.spec.object_id, PropKind.GLASS, position, size, broken=pane.broken)
        )
    for can in env.canisters.values():
        props.append(
            PropView(
                can.spec.object_id,
                PropKind.CANISTER,
                can.position,
                (UNIT * 45 // 100, UNIT * 65 // 100),
                previous_position=can.previous_position,
                roll_degrees=float(can.roll_degrees),
            )
        )
    hatch = env.rules.locker_cycle_ticks
    for locker in env.lockers.values():
        x, y = tile_center(locker.spec.tile)
        elapsed = tick - locker.moved_tick
        props.append(
            PropView(
                locker.spec.object_id,
                PropKind.LOCKER,
                # The cabinet stands at the back of its recess tile.
                (x, y + UNIT // 5),
                (UNIT * 9 // 10, UNIT * 6 // 10),
                openness=max(0.0, 1 - elapsed / hatch) if 0 <= elapsed < hatch else 0.0,
                occupant_id=locker.occupant,
                occupant_cover=1.0 if locker.occupant else 0.0,
            )
        )
    return EnvironmentView(tuple(props), tuple(env.cues))
