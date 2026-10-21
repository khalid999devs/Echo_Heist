"""Author the fixed five-zone facility; regenerate its Tiled runtime export explicitly."""

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "src/echo_heist/resources/data/maps/vault-five-zone.json"
WIDTH, HEIGHT, SIZE = 80, 56, 32


@dataclass(frozen=True)
class RoomPlan:
    name: str
    label: str
    style: str
    x: int
    y: int
    width: int
    height: int


ROOMS = (
    RoomPlan("screening", "Visitor Screening", "reception", 2, 11, 10, 7),
    RoomPlan("reception", "Receiving / Extraction", "reception", 2, 21, 10, 7),
    RoomPlan("freight", "Freight Locker", "storage", 2, 30, 10, 5),
    RoomPlan("dock", "Dock Maintenance", "maintenance", 2, 38, 10, 8),
    RoomPlan("power", "Power Intake", "maintenance", 17, 5, 5, 8),
    RoomPlan("repair", "Repair Bay", "maintenance", 17, 16, 5, 7),
    RoomPlan("service-office", "Engineering Office", "office", 17, 29, 5, 7),
    RoomPlan("logistics", "Logistics", "storage", 17, 39, 5, 10),
    RoomPlan("servers", "Service Servers", "server", 27, 5, 6, 8),
    RoomPlan("workshop", "Tool Workshop", "maintenance", 27, 16, 6, 7),
    RoomPlan("filtration", "Air Filtration", "maintenance", 27, 29, 6, 7),
    RoomPlan("relay", "Data Relay", "server", 27, 39, 6, 10),
    RoomPlan("checkpoint", "Security Checkpoint", "office", 37, 5, 7, 8),
    RoomPlan("dispatch", "Surveillance", "server", 49, 5, 10, 8),
    RoomPlan("archive", "Secure Archive", "storage", 37, 18, 7, 6),
    RoomPlan("control", "Security Control", "office", 49, 18, 10, 6),
    RoomPlan("wet-lab", "Wet Laboratory", "laboratory", 37, 29, 7, 8),
    RoomPlan("bio-lab", "Biology / Samples", "laboratory", 49, 29, 10, 8),
    RoomPlan("lab-stores", "Research Supplies", "storage", 37, 42, 7, 9),
    RoomPlan("electronics", "Electronics Lab", "laboratory", 49, 42, 10, 9),
    RoomPlan("coolant", "Coolant Control", "laboratory", 68, 17, 9, 4),
    RoomPlan("reactor", "Core Chamber", "reactor", 68, 23, 9, 9),
    RoomPlan("auxiliary", "Auxiliary Cells", "maintenance", 68, 34, 9, 5),
)


class Facility:
    def __init__(self) -> None:
        self.floor: set[tuple[int, int]] = set()
        self.glass: set[tuple[int, int]] = set()
        self.cover: set[tuple[int, int]] = set()
        self.zones: list[dict] = []
        self.anchors: list[dict] = []
        self.patrols: list[dict] = []
        self.markers: list[dict] = []
        self.next_id = 1

    def open(self, x: int, y: int, width: int, height: int) -> None:
        self.floor.update((a, b) for a in range(x, x + width) for b in range(y, y + height))

    def object(
        self,
        group: list[dict],
        name: str,
        kind: str,
        x: int,
        y: int,
        *,
        width: int = 0,
        height: int = 0,
        properties: dict | None = None,
        points: tuple = (),
    ) -> None:
        entry = {
            "id": self.next_id,
            "name": name,
            "type": kind,
            "x": x * SIZE,
            "y": y * SIZE,
            "width": width * SIZE,
            "height": height * SIZE,
            "rotation": 0,
            "visible": True,
        }
        self.next_id += 1
        if not width and not points:
            entry.update(point=True, x=x * SIZE + SIZE // 2, y=y * SIZE + SIZE // 2)
        if points:
            entry["polyline"] = [{"x": (a - x) * SIZE, "y": (b - y) * SIZE} for a, b in points]
        entry["properties"] = [
            {
                "name": k,
                "type": "bool"
                if isinstance(v, bool)
                else "int"
                if isinstance(v, int)
                else "string",
                "value": v,
            }
            for k, v in (properties or {}).items()
        ]
        group.append(entry)

    def furniture(
        self,
        name: str,
        style: str,
        x: int,
        y: int,
        width: int = 1,
        height: int = 1,
        rotation: int = 0,
    ) -> None:
        assert all(
            (a, b) in self.floor for a in range(x, x + width) for b in range(y, y + height)
        ), name
        self.object(
            self.markers,
            name,
            "Furniture",
            x,
            y,
            width=width,
            height=height,
            properties={
                "style": style,
                "rotation": rotation,
                "blocks_movement": True,
                "blocks_vision": style != "railing",
                "blocks_sound": style not in ("plant", "planter", "railing"),
            },
        )

    def detail(
        self, name: str, style: str, x: int, y: int, width: int, height: int, rotation: int = 0
    ) -> None:
        self.object(
            self.markers,
            name,
            "FloorDetail",
            x,
            y,
            width=width,
            height=height,
            properties={"style": style, "rotation": rotation},
        )


def architecture(facility: Facility) -> None:
    zones = (
        ("entry", "Entry / Extraction", 1, 10, 14, 38),
        ("service-wing", "Service Wing", 16, 4, 18, 48),
        ("security-control", "Security Control", 36, 3, 24, 22),
        ("research-floor", "Research Floor", 36, 28, 24, 25),
        ("core-chamber", "Core Chamber", 63, 16, 16, 24),
    )
    for name, label, x, y, width, height in zones:
        facility.object(
            facility.zones,
            name,
            "Zone",
            x,
            y,
            width=width,
            height=height,
            properties={"label": label},
        )
    for room in ROOMS:
        facility.open(room.x, room.y, room.width, room.height)
        facility.object(
            facility.markers,
            room.name,
            "Room",
            room.x,
            room.y,
            width=room.width,
            height=room.height,
            properties={"style": room.style, "label": room.label},
        )
    corridors = (
        (13, 13, 2, 31),
        (12, 14, 1, 2),
        (12, 25, 1, 2),
        (12, 31, 1, 2),
        (12, 41, 1, 2),
        (15, 25, 11, 2),
        (23, 5, 3, 46),
        (17, 24, 16, 3),
        (22, 9, 1, 2),
        (22, 19, 1, 2),
        (22, 32, 1, 2),
        (22, 43, 1, 2),
        (26, 9, 1, 2),
        (26, 19, 1, 2),
        (26, 32, 1, 2),
        (26, 43, 1, 2),
        (19, 23, 2, 1),
        (33, 9, 4, 3),
        (33, 43, 4, 3),
        (36, 14, 24, 3),
        (45, 4, 3, 48),
        (40, 13, 2, 1),
        (40, 17, 2, 1),
        (53, 13, 2, 1),
        (53, 17, 2, 1),
        (44, 9, 1, 2),
        (48, 9, 1, 2),
        (44, 20, 1, 2),
        (48, 20, 1, 2),
        (46, 25, 2, 3),
        (36, 38, 24, 3),
        (40, 37, 2, 1),
        (40, 41, 2, 1),
        (53, 37, 2, 1),
        (53, 41, 2, 1),
        (44, 33, 1, 2),
        (48, 33, 1, 2),
        (44, 44, 1, 2),
        (48, 44, 1, 2),
        (59, 20, 5, 2),
        (59, 35, 5, 2),
        (64, 21, 3, 16),
        (64, 21, 14, 2),
        (64, 32, 14, 2),
        (67, 25, 1, 2),
        (71, 32, 2, 1),
        (71, 33, 2, 1),
        (67, 35, 1, 2),
    )
    for rect in corridors:
        facility.open(*rect)
    # Fixed, transparent partitions: movement/sound blockers, never invented doors.
    for x, y, width, height in (
        (44, 18, 1, 2),
        (48, 5, 1, 3),
        (44, 29, 1, 3),
        (48, 29, 1, 3),
        (67, 23, 1, 2),
        (12, 21, 1, 3),
    ):
        facility.glass.update((a, b) for a in range(x, x + width) for b in range(y, y + height))


def furnish(facility: Facility) -> None:
    # Explicit per-room layouts keep entrances, patrols and plausible working aisles clear.
    items = (
        (
            "screening",
            (
                ("desk", 0, 0, 3, 2),
                ("planter", 6, 0, 3, 1),
                ("shelf", 0, 4, 3, 2),
                ("plant", 8, 5, 1, 1),
            ),
        ),
        (
            "reception",
            (
                ("desk", 0, 0, 3, 2),
                ("planter", 5, 0, 3, 1),
                ("shelf", 8, 2, 2, 2),
                ("plant", 8, 5, 1, 1),
            ),
        ),
        (
            "freight",
            (
                ("crates", 0, 0, 2, 2),
                ("shelf", 4, 0, 3, 2),
                ("crates", 0, 3, 2, 2),
                ("plant", 8, 3, 1, 1),
            ),
        ),
        (
            "dock",
            (
                ("pump", 0, 0, 2, 3),
                ("shelf", 5, 0, 4, 2),
                ("workbench", 4, 5, 3, 2),
                ("crates", 0, 6, 2, 2),
                ("plant", 8, 6, 1, 1),
            ),
        ),
        (
            "power",
            (
                ("pump", 0, 0, 2, 3),
                ("rack", 4, 0, 1, 3),
                ("workbench", 0, 6, 2, 2),
                ("plant", 4, 6, 1, 1),
            ),
        ),
        (
            "repair",
            (
                ("shelf", 0, 0, 3, 1),
                ("pump", 0, 2, 1, 2),
                ("workbench", 3, 4, 2, 2),
                ("plant", 0, 6, 1, 1),
            ),
        ),
        ("service-office", (("desk", 0, 0, 3, 2), ("shelf", 0, 4, 2, 2), ("plant", 4, 5, 1, 1))),
        (
            "logistics",
            (
                ("shelf", 0, 0, 3, 2),
                ("crates", 0, 4, 2, 2),
                ("crates", 3, 7, 2, 2),
                ("plant", 0, 8, 1, 1),
            ),
        ),
        (
            "servers",
            (
                ("rack", 0, 0, 1, 3),
                ("rack", 3, 0, 1, 3),
                ("rack", 0, 6, 1, 2),
                ("rack", 3, 6, 1, 2),
                ("plant", 5, 0, 1, 1),
            ),
        ),
        (
            "workshop",
            (
                ("workbench", 0, 0, 3, 2),
                ("shelf", 4, 0, 2, 2),
                ("pump", 0, 4, 2, 2),
                ("plant", 5, 5, 1, 1),
            ),
        ),
        ("filtration", (("pump", 0, 0, 2, 2), ("pump", 4, 0, 2, 2), ("planter", 1, 5, 3, 1))),
        (
            "relay",
            (
                ("rack", 0, 0, 1, 3),
                ("rack", 3, 0, 1, 3),
                ("rack", 0, 7, 1, 3),
                ("rack", 3, 7, 1, 3),
                ("plant", 5, 8, 1, 1),
            ),
        ),
        (
            "checkpoint",
            (
                ("console", 0, 0, 3, 2),
                ("planter", 4, 0, 3, 1),
                ("shelf", 0, 6, 3, 2),
                ("desk", 4, 5, 3, 2),
            ),
        ),
        (
            "dispatch",
            (
                ("rack", 0, 0, 1, 2),
                ("rack", 3, 0, 1, 2),
                ("console", 1, 6, 3, 2),
                ("desk", 6, 6, 3, 2),
                ("plant", 9, 0, 1, 1),
            ),
        ),
        (
            "archive",
            (
                ("shelf", 0, 0, 2, 2),
                ("shelf", 0, 4, 2, 2),
                ("crates", 5, 4, 2, 2),
                ("plant", 6, 0, 1, 1),
            ),
        ),
        (
            "control",
            (
                ("console", 0, 0, 3, 1),
                ("desk", 4, 2, 3, 2),
                ("planter", 0, 5, 3, 1),
                ("plant", 9, 5, 1, 1),
            ),
        ),
        (
            "wet-lab",
            (
                ("tank", 0, 0, 2, 3),
                ("labbench", 4, 0, 3, 2),
                ("labbench", 0, 6, 3, 2),
                ("plant", 6, 6, 1, 1),
            ),
        ),
        (
            "bio-lab",
            (
                ("labbench", 0, 0, 3, 2),
                ("tank", 4, 0, 1, 3),
                ("tank", 7, 0, 1, 3),
                ("planter", 0, 6, 3, 1),
                ("labbench", 4, 6, 3, 2),
            ),
        ),
        (
            "lab-stores",
            (
                ("shelf", 0, 0, 3, 1),
                ("crates", 0, 5, 2, 2),
                ("shelf", 4, 7, 3, 2),
                ("plant", 0, 8, 1, 1),
            ),
        ),
        (
            "electronics",
            (
                ("desk", 0, 0, 3, 2),
                ("labbench", 6, 0, 3, 2),
                ("workbench", 3, 6, 3, 2),
                ("plant", 9, 7, 1, 1),
            ),
        ),
        ("coolant", (("tank", 0, 0, 1, 3), ("labbench", 3, 0, 3, 1), ("tank", 8, 0, 1, 3))),
        (
            "reactor",
            (
                ("console", 0, 0, 3, 1),
                ("console", 6, 0, 3, 1),
                ("pump", 0, 6, 2, 2),
                ("planter", 6, 7, 3, 1),
            ),
        ),
        ("auxiliary", (("pump", 0, 0, 2, 1), ("pump", 7, 0, 2, 1), ("plant", 8, 4, 1, 1))),
    )
    rooms = {room.name: room for room in ROOMS}
    for name, fixtures in items:
        room = rooms[name]
        for index, (style, x, y, width, height) in enumerate(fixtures):
            fixture_id = (
                "entry-console" if name == "reception" and index == 0 else f"{name}-{index + 1}"
            )
            facility.furniture(fixture_id, style, room.x + x, room.y + y, width, height)
    # Corridor equipment creates visible bends and safer observation pockets.
    for name, style, x, y, width, height in (
        ("service-baffle-upper", "pump", 23, 14, 2, 2),
        ("service-baffle-lower", "shelf", 24, 28, 2, 2),
        ("service-baffle-loading", "pump", 23, 37, 2, 2),
        ("junction-planter", "planter", 27, 24, 3, 1),
        ("east-junction-planter", "planter", 54, 15, 3, 1),
        ("lab-junction-planter", "planter", 50, 39, 3, 1),
        ("entry-hall-plant", "plant", 14, 36, 1, 1),
    ):
        facility.furniture(name, style, x, y, width, height)
    for name, y in (("security-steps", 9), ("research-steps", 43)):
        facility.detail(name, "stairs", 33, y, 4, 3, 270)
        facility.furniture(name + "-north-rail", "railing", 33, y, 4, 1)
        facility.furniture(name + "-south-rail", "railing", 33, y + 2, 4, 1)
    for room in ROOMS:
        if room.style in ("server", "maintenance"):
            facility.detail(
                room.name + "-grate", "grate", room.x + room.width - 2, room.y + 2, 1, 3
            )
            facility.detail(
                room.name + "-cables",
                "cables",
                room.x + 1,
                room.y + room.height - 2,
                max(1, room.width - 2),
                1,
            )


def anchors_and_patrols(facility: Facility) -> None:
    for name, kind, tile in (
        ("entry-spawn", "Spawn", (5, 25)),
        ("entry-exit", "Exit", (3, 25)),
        ("vault-core", "Core", (72, 27)),
    ):
        facility.object(
            facility.anchors,
            name,
            kind,
            *tile,
            properties={"actor_id": "operative"} if kind == "Spawn" else {},
        )
    routes = (
        ("service", "SENTINEL", ((24, 19), (24, 25), (19, 25), (19, 19), (24, 19))),
        ("security", "SENTINEL", ((56, 7), (50, 7), (50, 10), (56, 10), (56, 7))),
        ("research", "TRACKER", ((56, 46), (50, 46), (50, 44), (56, 44), (56, 46))),
        ("core", "INTERCEPTOR", ((75, 37), (69, 37), (69, 35), (75, 35), (75, 37))),
    )
    for name, kind, points in routes:
        facility.object(facility.patrols, "route-" + name, "PatrolRoute", *points[0], points=points)
        facility.object(
            facility.patrols,
            "guard-" + name,
            "GuardSpawn",
            *points[0],
            properties={"guard_kind": kind, "route_id": "route-" + name},
        )
    for name, tile, pair in (
        ("entry-service", (15, 25), "entry|service-wing"),
        ("service-security", (35, 10), "service-wing|security-control"),
        ("service-research", (35, 44), "service-wing|research-floor"),
        ("cross-link", (46, 26), "security-control|research-floor"),
        ("security-core", (61, 20), "security-control|core-chamber"),
        ("research-core", (61, 35), "research-floor|core-chamber"),
    ):
        facility.object(
            facility.markers, "choke-" + name, "Chokepoint", *tile, properties={"zones": pair}
        )
    # Retain stable cover/hide marker IDs for the later P05 ownership contract.
    for index, (cover, hide) in enumerate(
        (
            ((28, 26), (28, 25)),
            ((18, 46), (18, 47)),
            ((42, 20), (42, 21)),
            ((57, 49), (57, 48)),
            ((74, 29), (74, 28)),
        ),
        1,
    ):
        facility.cover.add(cover)
        facility.object(facility.markers, f"cover-{index}", "Cover", cover[0] - 1, cover[1])
        facility.object(facility.markers, f"hide-{index}", "HideSpot", *hide)


def export(facility: Facility) -> dict:
    walls = (
        {(x, y) for x in range(WIDTH) for y in range(HEIGHT)}
        - facility.floor
        - facility.glass
        - facility.cover
    )
    layers = []
    for name, cells, gid, flags in (
        ("floor", facility.floor | facility.glass | facility.cover, 1, {"role": "ground"}),
        ("walls", walls, 2, {"blocks_movement": True, "blocks_vision": True, "blocks_sound": True}),
        (
            "glass",
            facility.glass,
            3,
            {"blocks_movement": True, "blocks_vision": False, "blocks_sound": True},
        ),
        (
            "cover",
            facility.cover,
            4,
            {"blocks_movement": True, "blocks_vision": True, "blocks_sound": False},
        ),
    ):
        layers.append(
            {
                "id": len(layers) + 1,
                "name": name,
                "type": "tilelayer",
                "width": WIDTH,
                "height": HEIGHT,
                "properties": [
                    {"name": k, "type": "bool" if isinstance(v, bool) else "string", "value": v}
                    for k, v in flags.items()
                ],
                "data": [
                    gid if (x, y) in cells else 0 for y in range(HEIGHT) for x in range(WIDTH)
                ],
            }
        )
    for name, objects in (
        ("zones", facility.zones),
        ("anchors", facility.anchors),
        ("patrols", facility.patrols),
        ("markers", facility.markers),
    ):
        layers.append(
            {"id": len(layers) + 1, "name": name, "type": "objectgroup", "objects": objects}
        )
    return {
        "type": "map",
        "version": "1.10",
        "tiledversion": "1.11.2",
        "orientation": "orthogonal",
        "renderorder": "right-down",
        "infinite": False,
        "width": WIDTH,
        "height": HEIGHT,
        "tilewidth": SIZE,
        "tileheight": SIZE,
        "nextobjectid": facility.next_id,
        "nextlayerid": len(layers) + 1,
        "properties": [
            {"name": "schema", "type": "string", "value": "echo-heist-map/1"},
            {"name": "map_id", "type": "string", "value": "vault-five-zone"},
        ],
        "tilesets": [
            {
                "firstgid": 1,
                "name": "facility-geometry",
                "tilewidth": SIZE,
                "tileheight": SIZE,
                "tilecount": 4,
                "columns": 4,
            }
        ],
        "layers": layers,
    }


def write_map(data: dict) -> None:
    # Numeric tile data keeps one complete map row per physical line. Tiled
    # objects are one record per line, rather than thousands of boilerplate lines.
    entries = []
    for key, value in data.items():
        if key != "layers":
            entries.append("  " + json.dumps(key) + ": " + json.dumps(value))
            continue
        layers = []
        for layer in value:
            fields = []
            for name, item in layer.items():
                if name == "data":
                    rows = [
                        ", ".join(map(str, item[i : i + WIDTH])) for i in range(0, len(item), WIDTH)
                    ]
                    encoded = "[\n" + ",\n".join("        " + row for row in rows) + "\n      ]"
                elif name == "objects":
                    encoded = (
                        "[\n"
                        + ",\n".join("        " + json.dumps(obj) for obj in item)
                        + "\n      ]"
                    )
                else:
                    encoded = json.dumps(item)
                fields.append("      " + json.dumps(name) + ": " + encoded)
            layers.append("    {\n" + ",\n".join(fields) + "\n    }")
        entries.append('  "layers": [\n' + ",\n".join(layers) + "\n  ]")
    TARGET.write_text("{\n" + ",\n".join(entries) + "\n}\n", encoding="utf-8")


def main() -> None:
    facility = Facility()
    architecture(facility)
    furnish(facility)
    anchors_and_patrols(facility)
    write_map(export(facility))
    print(f"Authored {len(ROOMS)} rooms; exported {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
