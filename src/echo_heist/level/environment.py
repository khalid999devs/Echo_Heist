"""Authored interactive props from the map: doors, glass racks, canisters, lockers.

Placement is data (Tiled point markers). A Door marker names the first tile of
its passage and an optional ``span`` along the leaf; its orientation is derived
from the surrounding walls, so a door is always a real controlled passage. A
Glass marker is a free-standing breakable pane (``span``/``horizontal``). Every
HideSpot recess is a locker. A Canister is a loose prop on open floor.
"""

from echo_heist.core.contracts.environment.model import EnvironmentRules, EnvironmentSpec, PropSpec
from echo_heist.core.contracts.environment.presentation import PropKind
from echo_heist.core.contracts.world import MapObject, StaticMap, Tile
from echo_heist.level.model import LevelData

PROP_KINDS = {
    "Door": PropKind.DOOR,
    "Glass": PropKind.GLASS,
    "Canister": PropKind.CANISTER,
    "HideSpot": PropKind.LOCKER,
}


def _span(obj: MapObject) -> int:
    span = dict(obj.properties).get("span", 1)
    if type(span) is not int or not 1 <= span <= 3:
        raise ValueError(f"{obj.object_id!r}: span must be an integer 1-3")
    return span


def _run(tile: Tile, span: int, horizontal: bool) -> tuple[Tile, ...]:
    return tuple(
        (tile[0] + index, tile[1]) if horizontal else (tile[0], tile[1] + index)
        for index in range(span)
    )


def door_layout(world_map: StaticMap, obj: MapObject) -> tuple[tuple[Tile, ...], bool]:
    """The door's tiles and leaf axis: exactly one passage orientation must fit.

    A horizontal leaf spans x, closed off by blocked tiles at both ends, with
    open floor directly above and below every leaf tile (and the transpose).
    """
    span = _span(obj)
    fits = []
    for horizontal in (True, False):
        tiles = _run(obj.tile, span, horizontal)
        step = (1, 0) if horizontal else (0, 1)
        across = (0, 1) if horizontal else (1, 0)
        before = (tiles[0][0] - step[0], tiles[0][1] - step[1])
        after = (tiles[-1][0] + step[0], tiles[-1][1] + step[1])
        if (
            all(world_map.can_walk(tile) for tile in tiles)
            and before in world_map.blocked_tiles
            and after in world_map.blocked_tiles
            and all(
                world_map.can_walk((x + sign * across[0], y + sign * across[1]))
                for x, y in tiles
                for sign in (-1, 1)
            )
        ):
            fits.append((tiles, horizontal))
    if len(fits) != 1:
        raise ValueError(f"door {obj.object_id!r} must close exactly one wall passage")
    return fits[0]


def prop_spec(world_map: StaticMap, obj: MapObject) -> PropSpec:
    kind = PROP_KINDS[obj.kind]
    if kind == PropKind.DOOR:
        tiles, horizontal = door_layout(world_map, obj)
        return PropSpec(obj.object_id, kind, tiles, horizontal)
    if kind == PropKind.GLASS:
        value = dict(obj.properties).get("horizontal", True)
        if not isinstance(value, bool):
            raise ValueError(f"glass {obj.object_id!r}: horizontal must be a boolean")
        return PropSpec(obj.object_id, kind, _run(obj.tile, _span(obj), value), value)
    return PropSpec(obj.object_id, kind, (obj.tile,))


def build_environment(level: LevelData, rules: EnvironmentRules) -> EnvironmentSpec:
    world_map = level.static_map
    return EnvironmentSpec(
        tuple(prop_spec(world_map, obj) for obj in world_map.objects if obj.kind in PROP_KINDS),
        rules,
    )
