"""Parse the agreed Tiled JSON subset into typed values, then validate them."""

import json
import re
from dataclasses import dataclass, field
from math import isfinite
from typing import cast

from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import (
    ActorKind,
    MapObject,
    ObstacleBounds,
    Scalar,
    StairLink,
    StaticMap,
    Tile,
)
from echo_heist.level.io.validate import check_level
from echo_heist.level.model import (
    DETAIL_STYLES,
    FURNITURE_APPEARANCES,
    FURNITURE_CONDITIONS,
    FURNITURE_STYLES,
    GUARD_KINDS,
    ROOM_STYLES,
    Chokepoint,
    Deck,
    FloorDetail,
    GuardPost,
    LevelData,
    Marker,
    PatrolRoute,
    Room,
    Zone,
)

SCHEMA = "echo-heist-map/1"
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
TILE_LAYERS = ("floor", "walls", "glass", "cover")
OBJECT_KINDS = {
    "zones": frozenset({"Zone"}),
    "anchors": frozenset({"Spawn", "Exit", "Core"}),
    "patrols": frozenset({"PatrolRoute", "GuardSpawn"}),
    "markers": frozenset(
        {
            "Cover",
            "HideSpot",
            "UnderDesk",
            "Chokepoint",
            "Furniture",
            "Room",
            "FloorDetail",
            "Deck",
            "Stair",
        }
    ),
}
GEOMETRY_FLAGS = ("blocks_movement", "blocks_vision", "blocks_sound")
type Json = dict[str, object]


class MapFormatError(ValueError):
    """The file is not a supported Echo Heist Tiled map; message names the location."""


@dataclass(slots=True)
class RawObject:
    object_id: str
    kind: str
    layer: str
    tile: Tile
    properties: dict[str, Scalar]
    rect: tuple[int, int, int, int] | None = None
    polyline: tuple[Tile, ...] = ()


@dataclass(slots=True)
class RawMap:
    map_id: str
    width: int
    height: int
    tile_size: int
    layers: dict[str, frozenset[Tile]] = field(default_factory=dict)
    flags: dict[str, frozenset[Tile]] = field(default_factory=dict)
    objects: list[RawObject] = field(default_factory=list)


def _dict(value: object, where: str) -> Json:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise MapFormatError(f"{where}: expected a JSON object")
    return value


def _list(value: object, where: str) -> list[object]:
    if not isinstance(value, list):
        raise MapFormatError(f"{where}: expected a JSON array")
    return value


def _int(value: object, where: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise MapFormatError(f"{where}: expected an integer >= {minimum}")
    return value


def _number(value: object, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise MapFormatError(f"{where}: expected a finite number")
    return float(value)


def _text(value: object, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise MapFormatError(f"{where}: expected nonempty text")
    return value


def _properties(container: Json, where: str) -> dict[str, Scalar]:
    result: dict[str, Scalar] = {}
    expected = {"bool": bool, "int": int, "float": float, "string": str}
    for index, item in enumerate(_list(container.get("properties", []), f"{where}.properties")):
        entry = _dict(item, f"{where}.properties[{index}]")
        name = _text(entry.get("name"), f"{where}.properties[{index}].name")
        kind = entry.get("type", "string")
        value = entry.get("value")
        if kind not in expected or type(value) is not expected[str(kind)]:
            raise MapFormatError(f"{where}: property {name!r} must be a valid {kind} value")
        if name in result:
            raise MapFormatError(f"{where}: duplicate property {name!r}")
        assert isinstance(value, (str, int, float, bool))
        result[name] = value
    return result


def _tile_at(x: float, y: float, raw: RawMap, where: str) -> Tile:
    tile = int(x // raw.tile_size), int(y // raw.tile_size)
    if not (0 <= tile[0] < raw.width and 0 <= tile[1] < raw.height) or x < 0 or y < 0:
        raise MapFormatError(f"{where}: position ({x:g}, {y:g}) is outside the map")
    return tile


def _tile_layer(layer: Json, raw: RawMap, gids: range, where: str) -> None:
    name = str(layer["name"])
    if layer.get("width") != raw.width or layer.get("height") != raw.height:
        raise MapFormatError(f"{where}: layer size must match the map")
    data = _list(layer.get("data"), f"{where}.data")
    if len(data) != raw.width * raw.height:
        raise MapFormatError(f"{where}: expected {raw.width * raw.height} tiles")
    tiles: set[Tile] = set()
    for index, gid in enumerate(data):
        value = _int(gid, f"{where}.data[{index}]")
        if value and value not in gids:
            raise MapFormatError(f"{where}: tile {value} has no embedded tileset entry")
        if value:
            tiles.add((index % raw.width, index // raw.width))
    properties = _properties(layer, where)
    if name == "floor":
        if properties.get("role") != "ground":
            raise MapFormatError(f"{where}: floor must be marked role=ground (render only)")
    else:
        for flag in GEOMETRY_FLAGS:
            if type(properties.get(flag)) is not bool:
                raise MapFormatError(f"{where}: missing explicit boolean {flag} tag")
            if properties[flag]:
                raw.flags[flag] = raw.flags.get(flag, frozenset()) | tiles
    raw.layers[name] = frozenset(tiles)


def _object(item: object, layer: str, raw: RawMap, where: str) -> RawObject | None:
    entry = _dict(item, where)
    properties = _properties(entry, where)
    kind = _text(entry.get("type", entry.get("class")), f"{where}.type")
    if kind not in OBJECT_KINDS[layer]:
        if properties.get("cosmetic") is True:
            return None
        raise MapFormatError(f"{where}: unknown object type {kind!r} in {layer}")
    object_id = _text(entry.get("name"), f"{where}.name")
    if not ID_PATTERN.fullmatch(object_id):
        raise MapFormatError(f"{where}: ID {object_id!r} must be lowercase letters/digits/-")
    x, y = _number(entry.get("x"), f"{where}.x"), _number(entry.get("y"), f"{where}.y")
    found = RawObject(object_id, kind, layer, _tile_at(x, y, raw, where), properties)
    if kind in ("Zone", "Furniture", "Room", "FloorDetail", "Deck"):
        size = raw.tile_size
        if _number(entry.get("rotation", 0), f"{where}.rotation") != 0:
            raise MapFormatError(
                f"{where}: physical rectangles must be axis-aligned; "
                "use the rotation property for sprite orientation"
            )
        w, h = _number(entry.get("width"), where), _number(entry.get("height"), where)
        if any(value % size for value in (x, y, w, h)) or w <= 0 or h <= 0:
            raise MapFormatError(f"{where}: {kind} {object_id!r} must align to whole tiles")
        found.rect = (int(x) // size, int(y) // size, int(w) // size, int(h) // size)
    elif kind == "PatrolRoute":
        points = _list(entry.get("polyline"), f"{where}.polyline")
        found.polyline = tuple(
            _tile_at(
                x + _number(_dict(p, where).get("x"), where),
                y + _number(_dict(p, where).get("y"), where),
                raw,
                where,
            )
            for p in points
        )
    elif entry.get("point") is not True:
        raise MapFormatError(f"{where}: {kind} {object_id!r} must be a point object")
    return found


def parse_tiled(payload: bytes | str) -> RawMap:
    try:
        root = _dict(json.loads(payload), "map")
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise MapFormatError(f"map: not valid JSON ({error})") from error
    if root.get("type") != "map" or root.get("orientation") != "orthogonal":
        raise MapFormatError("map: expected an orthogonal Tiled map")
    if root.get("infinite") is not False:
        raise MapFormatError("map: infinite maps are not supported")
    size = _int(root.get("tilewidth"), "map.tilewidth", minimum=1)
    if root.get("tileheight") != size:
        raise MapFormatError("map: tiles must be square")
    properties = _properties(root, "map")
    if properties.get("schema") != SCHEMA:
        raise MapFormatError(f"map: schema property must be {SCHEMA!r}")
    map_id = _text(properties.get("map_id"), "map.map_id")
    if not ID_PATTERN.fullmatch(map_id):
        raise MapFormatError(f"map: map_id {map_id!r} must be lowercase letters/digits/-")
    raw = RawMap(
        map_id,
        _int(root.get("width"), "map.width", minimum=1),
        _int(root.get("height"), "map.height", minimum=1),
        size,
    )
    gids: list[int] = []
    for index, item in enumerate(_list(root.get("tilesets"), "map.tilesets")):
        tileset = _dict(item, f"map.tilesets[{index}]")
        if "source" in tileset:
            raise MapFormatError(f"map.tilesets[{index}]: external tileset is not supported")
        first = _int(tileset.get("firstgid"), f"map.tilesets[{index}].firstgid", minimum=1)
        gids.extend(range(first, first + _int(tileset.get("tilecount"), "tilecount", minimum=1)))
    seen: set[str] = set()
    for index, item in enumerate(_list(root.get("layers"), "map.layers")):
        layer = _dict(item, f"map.layers[{index}]")
        name = _text(layer.get("name"), f"map.layers[{index}].name")
        where = f"layer {name!r}"
        if name in seen:
            raise MapFormatError(f"{where}: duplicate layer name")
        seen.add(name)
        if name in TILE_LAYERS and layer.get("type") == "tilelayer":
            _tile_layer(layer, raw, range(min(gids, default=1), max(gids, default=0) + 1), where)
        elif name in OBJECT_KINDS and layer.get("type") == "objectgroup":
            for number, obj in enumerate(_list(layer.get("objects"), f"{where}.objects")):
                parsed = _object(obj, name, raw, f"{where} object {number}")
                if parsed is not None:
                    raw.objects.append(parsed)
        elif _properties(layer, where).get("cosmetic") is not True:
            raise MapFormatError(f"{where}: unknown layer (mark cosmetic=true to allow)")
    missing = [name for name in (*TILE_LAYERS, *OBJECT_KINDS) if name not in seen]
    if missing:
        raise MapFormatError(f"map: missing required layers {', '.join(missing)}")
    ids = [obj.object_id for obj in raw.objects]
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
        raise MapFormatError(f"map: duplicate object IDs {', '.join(duplicates)}")
    return raw


def _apply_furniture(raw: RawMap) -> None:
    for obj in raw.objects:
        if obj.kind != "Furniture":
            continue
        assert obj.rect is not None
        left, top, width, height = obj.rect
        if left + width > raw.width or top + height > raw.height:
            raise MapFormatError(f"{obj.object_id!r}: furniture footprint extends outside the map")
        footprint = frozenset(
            (a, b) for a in range(left, left + width) for b in range(top, top + height)
        )
        if footprint & raw.flags.get("blocks_movement", frozenset()):
            raise MapFormatError(f"{obj.object_id!r}: furniture overlaps existing solid geometry")
        if obj.properties.get("style") not in FURNITURE_STYLES:
            raise MapFormatError(f"{obj.object_id!r}: unknown furniture style")
        if obj.properties.get("appearance", "standard") not in FURNITURE_APPEARANCES:
            raise MapFormatError(f"{obj.object_id!r}: unknown furniture appearance")
        if obj.properties.get("condition", "used") not in FURNITURE_CONDITIONS:
            raise MapFormatError(f"{obj.object_id!r}: unknown furniture condition")
        rotation = obj.properties.get("rotation", 0)
        if type(rotation) is not int or rotation not in (0, 90, 180, 270):
            raise MapFormatError(f"{obj.object_id!r}: unsupported furniture rotation")
        for flag in GEOMETRY_FLAGS:
            if type(obj.properties.get(flag)) is not bool:
                raise MapFormatError(f"{obj.object_id!r}: furniture requires explicit {flag}")
            if obj.properties[flag]:
                raw.flags[flag] = raw.flags.get(flag, frozenset()) | footprint
        if obj.properties["blocks_movement"] is not True:
            raise MapFormatError(f"{obj.object_id!r}: furniture must have a physical footprint")
        obj.properties.update(width_tiles=width, height_tiles=height)


def _obstacles(raw: RawMap) -> tuple[ObstacleBounds, ...]:
    result = []
    keys = ("collision_left", "collision_top", "collision_right", "collision_bottom")
    for obj in raw.objects:
        if obj.kind not in ("Furniture", "Cover") or not any(key in obj.properties for key in keys):
            continue
        values = tuple(obj.properties.get(key) for key in keys)
        if any(type(value) is not int or not 0 <= value <= 1000 for value in values):
            raise MapFormatError(
                f"{obj.object_id!r}: collision bounds require four integers 0-1000"
            )
        a, b, c, d = cast(tuple[int, int, int, int], values)
        if a >= c or b >= d:
            raise MapFormatError(f"{obj.object_id!r}: collision bounds must have positive area")
        left, top, width, height = obj.rect or (*obj.tile, 1, 1)
        if obj.kind == "Cover":
            x, y = obj.properties.get("collision_tile_x"), obj.properties.get("collision_tile_y")
            if (
                type(x) is not int
                or type(y) is not int
                or (x, y) not in raw.layers.get("cover", frozenset())
            ):
                raise MapFormatError(
                    f"{obj.object_id!r}: collision must reference its physical cover tile"
                )
            left, top, width, height = x, y, 1, 1
        reserved = frozenset(
            (x, y) for x in range(left, left + width) for y in range(top, top + height)
        )
        result.append(
            ObstacleBounds(
                obj.object_id,
                left * UNIT + a * width * UNIT // 1000,
                top * UNIT + b * height * UNIT // 1000,
                left * UNIT + c * width * UNIT // 1000,
                top * UNIT + d * height * UNIT // 1000,
                reserved,
                bool(obj.properties.get("blocks_vision", obj.kind == "Cover")),
            )
        )
    return tuple(result)


def build_level(raw: RawMap) -> LevelData:
    """Construct typed values; validate.check_level decides whether they are playable."""

    def of(kind: str) -> list[RawObject]:
        return [obj for obj in raw.objects if obj.kind == kind]

    def one(kind: str) -> RawObject:
        found = of(kind)
        if len(found) != 1:
            raise MapFormatError(f"map: expected exactly one {kind} anchor, found {len(found)}")
        return found[0]

    _apply_furniture(raw)
    for space in of("UnderDesk"):
        owner = next(
            (
                obj
                for obj in of("Furniture")
                if obj.object_id == space.properties.get("furniture_id")
            ),
            None,
        )
        if (
            owner is None
            or owner.rect is None
            or owner.properties.get("appearance") != "hiding-desk"
        ):
            raise MapFormatError(
                f"{space.object_id!r}: under-desk space requires its hiding-desk furniture"
            )
        left, top, width, height = owner.rect
        if not (width >= 3 and height == 1 and space.tile == (left + width // 2, top)):
            raise MapFormatError(
                f"{space.object_id!r}: opening must be the middle of a wide single-depth desk"
            )
    rooms: list[Room] = []
    details: list[FloorDetail] = []
    for obj in of("Room") + of("FloorDetail"):
        assert obj.rect is not None
        style = obj.properties.get("style")
        choices = ROOM_STYLES if obj.kind == "Room" else DETAIL_STYLES
        if style not in choices:
            raise MapFormatError(f"{obj.object_id!r}: unsupported {obj.kind} style")
        if obj.kind == "Room":
            label = _text(obj.properties.get("label"), f"{obj.object_id!r} label")
            rooms.append(Room(obj.object_id, label, str(style), *obj.rect))
        else:
            rotation = obj.properties.get("rotation", 0)
            if type(rotation) is not int or rotation not in (0, 90, 180, 270):
                raise MapFormatError(f"{obj.object_id!r}: unsupported floor detail rotation")
            details.append(FloorDetail(obj.object_id, str(style), *obj.rect, rotation))
    spawn, exit_anchor, core = one("Spawn"), one("Exit"), one("Core")
    operative = _text(spawn.properties.get("actor_id", "operative"), "Spawn actor_id")
    guards: list[GuardPost] = []
    for obj in of("GuardSpawn"):
        kind_name = obj.properties.get("guard_kind")
        if kind_name not in {kind.value for kind in GUARD_KINDS}:
            raise MapFormatError(f"guard {obj.object_id!r}: guard_kind must name a guard type")
        route = _text(obj.properties.get("route_id"), f"guard {obj.object_id!r} route_id")
        guards.append(GuardPost(obj.object_id, ActorKind(str(kind_name)), obj.tile, route))
    chokepoints: list[Chokepoint] = []
    for obj in of("Chokepoint"):
        where = f"chokepoint {obj.object_id!r}"
        pair = _text(obj.properties.get("zones"), f"{where} zones").split("|")
        if len(pair) != 2:
            raise MapFormatError(f"chokepoint {obj.object_id!r}: zones must be 'zone-a|zone-b'")
        chokepoints.append(Chokepoint(obj.object_id, obj.tile, (pair[0], pair[1])))
    zones: list[Zone] = []
    for obj in of("Zone"):
        assert obj.rect is not None
        zone_label = obj.properties.get("label", obj.object_id)
        zones.append(Zone(obj.object_id, str(zone_label), *obj.rect))
    blocked = raw.flags.get("blocks_movement", frozenset())
    visible_kinds = (
        "Spawn",
        "Exit",
        "Core",
        "Cover",
        "HideSpot",
        "UnderDesk",
        "Chokepoint",
        "Furniture",
        "Stair",
    )
    stairs = {obj.object_id: obj for obj in of("Stair")}
    links = []
    for obj in stairs.values():
        destination_id = _text(obj.properties.get("destination"), f"{obj.object_id!r} destination")
        if destination_id not in stairs:
            raise MapFormatError(f"{obj.object_id!r}: missing stair destination {destination_id!r}")
        links.append(
            StairLink(obj.object_id, obj.tile, destination_id, stairs[destination_id].tile)
        )
    static_map = StaticMap(
        raw.map_id,
        raw.width,
        raw.height,
        blocked,
        raw.flags.get("blocks_vision", frozenset()),
        tuple(
            MapObject(
                obj.object_id,
                obj.kind,
                obj.tile,
                tuple(sorted(obj.properties.items(), key=lambda item: item[0])),
            )
            for obj in raw.objects
            if obj.kind in visible_kinds
        ),
        raw.tile_size,
        tuple(links),
        frozenset(obj.tile for obj in of("UnderDesk")),
        _obstacles(raw),
    )
    return LevelData(
        static_map,
        operative,
        spawn.object_id,
        spawn.tile,
        core.object_id,
        exit_anchor.object_id,
        tuple(zones),
        tuple(PatrolRoute(obj.object_id, obj.polyline) for obj in of("PatrolRoute")),
        tuple(guards),
        tuple(chokepoints),
        tuple(
            Marker(obj.object_id, obj.kind, obj.tile)
            for obj in of("Cover") + of("HideSpot") + of("UnderDesk")
        ),
        raw.layers["floor"],
        raw.layers["glass"],
        raw.layers["cover"],
        raw.flags.get("blocks_sound", frozenset()),
        tuple(rooms),
        tuple(details),
        tuple(
            Deck(obj.object_id, _text(obj.properties.get("label"), "Deck label"), *obj.rect)
            for obj in of("Deck")
            if obj.rect is not None
        ),
    )


def load_tiled_map(payload: bytes | str, *, expected_map_id: str | None = None) -> LevelData:
    try:
        level = build_level(parse_tiled(payload))
    except MapFormatError:
        raise
    except ValueError as error:
        raise MapFormatError(f"map: {error}") from error
    if expected_map_id is not None and level.static_map.map_id != expected_map_id:
        raise MapFormatError(
            f"map: expected map_id {expected_map_id!r}, found {level.static_map.map_id!r}"
        )
    problems = check_level(level)
    if problems:
        raise MapFormatError(
            f"map {level.static_map.map_id!r} failed validation:\n- " + "\n- ".join(problems)
        )
    return level
