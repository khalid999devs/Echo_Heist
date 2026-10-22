"""Export reviewed physical fixture bounds from current art; never used by Simulation."""

import json

from author_facility import TARGET, write_map

from echo_heist.level.io import load_tiled_map
from echo_heist.ui.render.environment.furnishings.catalogue import prepare_furniture
from echo_heist.ui.render.world import WorldArt


def main() -> None:
    data = json.loads(TARGET.read_text())
    level = load_tiled_map(TARGET.read_bytes())
    visuals = prepare_furniture(level, WorldArt.load().props)
    visual_by_id = {item.object_id: item for item in visuals}
    covers = {item.tile: item for item in visuals if item.style == "cover"}
    count = 0
    keys = ("collision_left", "collision_top", "collision_right", "collision_bottom")
    for layer in data["layers"]:
        for obj in layer.get("objects", []):
            kind = obj.get("class", obj.get("type"))
            if kind not in ("Furniture", "Cover"):
                continue
            tile = (int(obj["x"] // data["tilewidth"]), int(obj["y"] // data["tileheight"]))
            if kind == "Cover":
                matches = [
                    point
                    for point in covers
                    if abs(point[0] - tile[0]) + abs(point[1] - tile[1]) == 1
                ]
                assert len(matches) == 1, (obj["name"], matches)
                tile = matches[0]  # The marker is the adjacent standing approach.
            item = visual_by_id.get(obj["name"]) if kind == "Furniture" else covers[tile]
            assert item is not None
            footprint = item.footprint
            visible = item.sprite.get_bounding_rect(min_alpha=48).move(item.render_rect.topleft)
            base = visible.clip(footprint)
            props = {p["name"]: p["value"] for p in obj.get("properties", [])}
            if props.get("appearance") == "hiding-desk":
                base = footprint.copy()  # Full worktop, with explicit crouch-only knee clearance.
            elif item.style == "plant":
                # Foliage may overhang: the pot, not its leaves, is solid.
                base.width = round(base.width * 0.55)
                base.centerx = visible.centerx
                base.height = round(footprint.h * 0.32)
                base.bottom = visible.bottom
                base = base.clip(footprint)
            values = (
                (base.left - footprint.left) * 1000 // footprint.w,
                (base.top - footprint.top) * 1000 // footprint.h,
                (base.right - footprint.left) * 1000 // footprint.w,
                (base.bottom - footprint.top) * 1000 // footprint.h,
            )
            obj["properties"] = [p for p in obj.get("properties", []) if p["name"] not in keys]
            obj["properties"].extend(
                {"name": key, "type": "int", "value": value}
                for key, value in zip(keys, values, strict=True)
            )
            if kind == "Cover":
                obj["properties"] = [
                    p
                    for p in obj["properties"]
                    if p["name"] not in ("collision_tile_x", "collision_tile_y")
                ]
                obj["properties"].extend(
                    {"name": key, "type": "int", "value": value}
                    for key, value in zip(
                        ("collision_tile_x", "collision_tile_y"), tile, strict=True
                    )
                )
            count += 1
    write_map(data)
    load_tiled_map(TARGET.read_bytes())
    print(f"Exported {count} explicit fixture bounds; route grid and walls unchanged")


if __name__ == "__main__":
    main()
