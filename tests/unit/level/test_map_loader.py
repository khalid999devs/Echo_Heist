"""Importer validation on the packaged map and small targeted corruptions of it."""

import json
from collections.abc import Callable
from typing import Any

import pytest

from echo_heist.infrastructure.resources import resource_bytes
from echo_heist.level.io import MapFormatError, load_tiled_map
from echo_heist.level.model import ZONE_IDS

MAP_ID = "vault-five-zone"
type Edit = Callable[[dict[str, Any]], None]


def packaged() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(resource_bytes(f"data/maps/{MAP_ID}.json"))
    return data


def layer(data: dict[str, Any], name: str) -> dict[str, Any]:
    found: dict[str, Any] = next(item for item in data["layers"] if item["name"] == name)
    return found


def named(data: dict[str, Any], group: str, object_id: str) -> dict[str, Any]:
    found: dict[str, Any] = next(
        item for item in layer(data, group)["objects"] if item["name"] == object_id
    )
    return found


def set_tile(data: dict[str, Any], name: str, tile: tuple[int, int], gid: int) -> None:
    layer(data, name)["data"][tile[1] * data["width"] + tile[0]] = gid


def wall_off(*tiles: tuple[int, int]) -> Edit:
    def edit(data: dict[str, Any]) -> None:
        for tile in tiles:
            set_tile(data, "walls", tile, 2)

    return edit


def test_packaged_map_loads_with_stable_anchors_zones_and_tags() -> None:
    level = load_tiled_map(resource_bytes(f"data/maps/{MAP_ID}.json"), expected_map_id=MAP_ID)
    assert (level.spawn_id, level.exit_id, level.core_id) == (
        "entry-spawn",
        "entry-exit",
        "vault-core",
    )
    assert sorted(zone.zone_id for zone in level.zones) == sorted(ZONE_IDS)
    world_map = level.static_map
    assert level.glass_tiles and not level.glass_tiles & world_map.opaque_tiles
    assert level.cover_tiles <= world_map.blocked_tiles & world_map.opaque_tiles
    assert level.glass_tiles <= level.sound_blocking_tiles
    assert not level.cover_tiles & level.sound_blocking_tiles
    # Guard posts/routes stay out of the controller-visible static map.
    kinds = {obj.kind for obj in world_map.objects}
    assert not kinds & {"GuardSpawn", "PatrolRoute"}
    assert {post.guard_id for post in level.guards} == {
        "guard-service",
        "guard-security",
        "guard-research",
        "guard-core",
    }


def _second_core(data: dict[str, Any]) -> None:
    extra = dict(named(data, "anchors", "vault-core"), name="vault-core-2", id=999)
    layer(data, "anchors")["objects"].append(extra)


def _drop_zone(data: dict[str, Any]) -> None:
    objects = layer(data, "zones")["objects"]
    objects[:] = [item for item in objects if item["name"] != "research-floor"]


def _duplicate_id(data: dict[str, Any]) -> None:
    named(data, "markers", "hide-1")["name"] = "cover-1"


def _external_tileset(data: dict[str, Any]) -> None:
    data["tilesets"] = [{"firstgid": 1, "source": "missing/greybox.tsx"}]


def _untagged_glass(data: dict[str, Any]) -> None:
    layer(data, "glass")["properties"] = []


def _unknown_object(data: dict[str, Any]) -> None:
    named(data, "markers", "cover-1")["type"] = "Teleporter"


def _patrol_through_crate(data: dict[str, Any]) -> None:
    set_tile(data, "cover", (18, 8), 4)


def _core_outside_chamber(data: dict[str, Any]) -> None:
    core = named(data, "anchors", "vault-core")
    core["x"], core["y"] = 40 * 32 + 16, 8 * 32 + 16


CASES: list[tuple[str, Edit, str]] = [
    ("duplicate core", _second_core, "exactly one Core"),
    ("missing zone", _drop_zone, "zones must be exactly"),
    ("duplicate id", _duplicate_id, "duplicate object IDs"),
    ("external tileset", _external_tileset, "external tileset"),
    ("untagged geometry", _untagged_glass, "blocks_movement"),
    ("unknown object", _unknown_object, "unknown object type"),
    ("patrol blocked", _patrol_through_crate, "patrol 'route-service' crosses blocked"),
    ("misplaced core", _core_outside_chamber, "inside zone 'core-chamber'"),
    (
        "core unreachable",
        wall_off((45, 12), (45, 13), (45, 22), (45, 23)),
        "Core is unreachable",
    ),
    ("upper branch cut", wall_off((25, 7), (25, 8), (25, 9)), "upper branch"),
    ("lower branch cut", wall_off((25, 26), (25, 27), (25, 28)), "lower branch"),
    ("cross-link cut", wall_off((35, 17), (36, 17), (37, 17)), "cross-link"),
    ("entry sealed", wall_off((11, 16), (11, 17), (11, 18)), "Core is unreachable"),
]


@pytest.mark.parametrize(("label", "edit", "message"), CASES, ids=[case[0] for case in CASES])
def test_invalid_maps_fail_with_a_specific_reason(label: str, edit: Edit, message: str) -> None:
    data = packaged()
    edit(data)
    with pytest.raises(MapFormatError) as failure:
        load_tiled_map(json.dumps(data))
    assert message in str(failure.value), (label, str(failure.value))


def test_wrong_expected_map_id_is_rejected() -> None:
    with pytest.raises(MapFormatError, match="expected map_id"):
        load_tiled_map(resource_bytes(f"data/maps/{MAP_ID}.json"), expected_map_id="other-map")


def test_furniture_has_matching_physical_opaque_acoustic_footprints() -> None:
    level = load_tiled_map(resource_bytes(f"data/maps/{MAP_ID}.json"))
    fixtures = [obj for obj in level.static_map.objects if obj.kind == "Furniture"]
    assert len(fixtures) == 9
    for fixture in fixtures:
        props = dict(fixture.properties)
        footprint = {
            (x, y)
            for x in range(fixture.tile[0], fixture.tile[0] + int(props["width_tiles"]))
            for y in range(fixture.tile[1], fixture.tile[1] + int(props["height_tiles"]))
        }
        assert (
            footprint
            <= level.static_map.blocked_tiles
            & level.static_map.opaque_tiles
            & level.sound_blocking_tiles
        )

    reordered = packaged()
    reordered["layers"].reverse()
    reversed_level = load_tiled_map(json.dumps(reordered))
    assert reversed_level.static_map.blocked_tiles == level.static_map.blocked_tiles
    assert reversed_level.static_map.opaque_tiles == level.static_map.opaque_tiles
    assert reversed_level.sound_blocking_tiles == level.sound_blocking_tiles


@pytest.mark.parametrize("invalid", ["overlap", "bounds", "untagged", "patrol"])
def test_invalid_furniture_cannot_silently_break_physical_room(invalid: str) -> None:
    data = packaged()
    fixture = named(data, "markers", "entry-console")
    if invalid == "overlap":
        fixture["x"] = 0
    elif invalid == "bounds":
        fixture["width"] = 100 * 32
    elif invalid == "untagged":
        fixture["properties"] = [
            prop for prop in fixture["properties"] if prop["name"] != "blocks_vision"
        ]
    else:
        fixture["x"], fixture["y"] = 18 * 32, 8 * 32
    with pytest.raises(MapFormatError):
        load_tiled_map(json.dumps(data))
