"""Author the fixed five-zone facility; regenerate its Tiled runtime export explicitly."""

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "src/echo_heist/resources/data/maps/vault-five-zone.json"
WIDTH, HEIGHT, SIZE = 64, 40, 96


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
    RoomPlan("screening", "Personnel Screening", "reception", 2, 13, 8, 5),
    RoomPlan("reception", "Entry / Extraction", "reception", 2, 21, 8, 6),
    RoomPlan("power", "Power & Ventilation", "maintenance", 15, 8, 5, 8),
    RoomPlan("servers", "Service Servers", "server", 24, 8, 5, 8),
    RoomPlan("repair", "Maintenance Bay", "maintenance", 15, 23, 5, 8),
    RoomPlan("logistics", "Equipment Stores", "storage", 24, 23, 5, 8),
    RoomPlan("checkpoint", "Security Checkpoint", "office", 32, 5, 6, 7),
    RoomPlan("control", "Surveillance Control", "office", 40, 5, 6, 7),
    RoomPlan("wet-lab", "Analytical Laboratory", "laboratory", 32, 21, 6, 7),
    RoomPlan("bio-lab", "Biology / Test Cells", "laboratory", 40, 21, 6, 7),
    RoomPlan("lab-stores", "Sample Archive", "storage", 32, 32, 6, 5),
    RoomPlan("electronics", "Instrument Lab", "laboratory", 40, 32, 6, 5),
    RoomPlan("coolant", "Containment Systems", "laboratory", 51, 11, 10, 6),
    RoomPlan("reactor", "Core Chamber", "reactor", 51, 20, 10, 9),
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
        if style == "tank":
            # The collision base is floor area; visual vessel height is separate.
            height = 1
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
    # Blueprint topology: Entry -> Service -> Security OR Research -> Core.
    for name, label, rect in (
        ("ground", "01 / SERVICE", (0, 0, 30, 40)),
        ("upper", "02 / RESEARCH", (32, 0, 32, 40)),
    ):
        facility.object(
            facility.markers,
            name,
            "Deck",
            *rect[:2],
            width=rect[2],
            height=rect[3],
            properties={"label": label},
        )
    zones = (
        ("entry", "Entry / Extraction", 1, 12, 11, 16),
        ("service-wing", "Service Wing", 14, 7, 15, 27),
        ("security-control", "Security Control", 31, 4, 16, 13),
        ("research-floor", "Research Floor", 31, 21, 16, 17),
        ("core-chamber", "Core Chamber", 50, 10, 12, 21),
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
        (10, 15, 1, 2),
        (11, 15, 2, 11),
        (10, 24, 1, 2),
        (13, 19, 10, 2),
        (21, 9, 2, 23),
        (20, 11, 1, 2),
        (23, 11, 1, 2),
        (20, 26, 1, 2),
        (23, 26, 1, 2),
        # Short, exposed Security approach, through a railed access gangway.
        (35, 12, 2, 1),
        (43, 12, 2, 1),
        (32, 13, 20, 2),
        # Research winds through equipment stores, then a furnished laboratory.
        (27, 31, 2, 4),
        (32, 28, 15, 3),
        (35, 31, 2, 1),
        (43, 31, 2, 1),
        (47, 29, 14, 2),
        # Narrow branch cross-link. It remains open in both mission phases.
        (38, 15, 2, 2),
        (38, 17, 1, 4),
        (38, 21, 2, 8),
        # Both branches join the same Core room; no alternate objective anchor.
        (55, 17, 2, 3),
        (51, 18, 10, 1),
    )
    for rect in corridors:
        facility.open(*rect)
    for x, y, width, height in (
        (38, 5, 1, 3),
        (39, 5, 1, 3),
        (32, 20, 6, 1),
        (40, 20, 6, 1),
        (51, 19, 3, 1),
        (58, 19, 3, 1),
    ):
        facility.glass.update((a, b) for a in range(x, x + width) for b in range(y, y + height))


def furnish(facility: Facility) -> None:
    # Room purpose determines its fittings; keep genuine working aisles.
    items = (
        (
            "screening",
            (
                ("desk", 0, 0, 3, 1),
                ("planter", 5, 0, 3, 1),
                ("shelf", 0, 3, 2, 2),
                ("plant", 7, 4, 1, 1),
            ),
        ),
        (
            "reception",
            (
                ("desk", 0, 0, 3, 1),
                ("planter", 5, 0, 3, 1),
                ("shelf", 6, 4, 2, 2),
                ("plant", 0, 5, 1, 1),
            ),
        ),
        (
            "power",
            (
                ("pump", 0, 0, 2, 2),
                ("pump", 4, 0, 1, 3),
                ("workbench", 0, 6, 3, 2),
                ("plant", 4, 6, 1, 1),
            ),
        ),
        (
            "servers",
            (
                ("rack", 0, 0, 1, 3),
                ("rack", 3, 0, 1, 3),
                ("rack", 0, 6, 1, 2),
                ("rack", 3, 6, 1, 2),
                ("plant", 4, 0, 1, 1),
            ),
        ),
        (
            "repair",
            (
                ("shelf", 0, 0, 3, 1),
                ("pump", 0, 2, 1, 2),
                ("workbench", 2, 6, 3, 2),
                ("plant", 0, 7, 1, 1),
            ),
        ),
        (
            "logistics",
            (
                ("shelf", 0, 0, 3, 1),
                ("crates", 0, 4, 2, 2),
                ("shelf", 0, 6, 2, 2),
                ("plant", 4, 0, 1, 1),
            ),
        ),
        (
            "checkpoint",
            (
                ("console", 0, 0, 3, 1),
                ("planter", 4, 0, 2, 1),
                ("desk", 3, 3, 3, 2),
                ("shelf", 0, 4, 2, 1),
            ),
        ),
        (
            "control",
            (
                ("console", 0, 0, 3, 1),
                ("console", 4, 0, 2, 1),
                ("desk", 0, 3, 3, 2),
                ("rack", 5, 3, 1, 2),
                ("plant", 0, 6, 1, 1),
            ),
        ),
        (
            "wet-lab",
            (
                ("tank", 0, 0, 1, 3),
                ("labbench", 3, 0, 3, 1),
                ("labbench", 3, 5, 3, 2),
                ("plant", 0, 4, 1, 1),
            ),
        ),
        (
            "bio-lab",
            (
                ("labbench", 0, 0, 3, 1),
                ("tank", 5, 0, 1, 3),
                ("tank", 3, 3, 1, 2),
                ("planter", 0, 6, 3, 1),
            ),
        ),
        (
            "lab-stores",
            (
                ("shelf", 0, 0, 2, 1),
                ("shelf", 4, 0, 2, 1),
                ("crates", 0, 3, 2, 2),
                ("plant", 5, 4, 1, 1),
            ),
        ),
        (
            "electronics",
            (
                ("labbench", 0, 0, 2, 1),
                ("desk", 3, 1, 3, 1),
                ("workbench", 3, 3, 3, 2),
                ("plant", 0, 4, 1, 1),
            ),
        ),
        (
            "coolant",
            (
                ("tank", 0, 0, 1, 3),
                ("labbench", 3, 0, 3, 1),
                ("tank", 9, 0, 1, 3),
                ("console", 0, 4, 3, 1),
                ("plant", 9, 4, 1, 1),
            ),
        ),
        (
            "reactor",
            (
                ("console", 0, 0, 3, 1),
                ("console", 7, 0, 3, 1),
                ("pump", 0, 6, 2, 2),
                ("planter", 7, 7, 3, 1),
            ),
        ),
    )
    rooms = {room.name: room for room in ROOMS}
    for name, fixtures in items:
        room = rooms[name]
        for index, (style, x, y, width, height) in enumerate(fixtures):
            fixture_id = (
                "entry-console" if name == "reception" and index == 0 else f"{name}-{index + 1}"
            )
            facility.furniture(fixture_id, style, room.x + x, room.y + y, width, height)
    # Perimeter instruments and compact islands, with the original doorways,
    # stair landings, core approach and patrol lanes kept open.
    extras = {
        "screening": (("rack", 0, 1, 1, 2), ("console", 3, 4, 2, 1)),
        "reception": (("shelf", 0, 1, 1, 2), ("plant", 7, 1, 1, 1), ("workbench", 4, 5, 1, 1)),
        "power": (("rack", 0, 3, 1, 2), ("console", 3, 2, 1, 1)),
        "servers": (("console", 1, 7, 2, 1), ("workbench", 1, 0, 1, 1)),
        "repair": (("console", 3, 0, 2, 1), ("pump", 0, 4, 1, 1), ("workbench", 4, 2, 1, 1)),
        "logistics": (("rack", 4, 1, 1, 2), ("workbench", 2, 6, 1, 1), ("rack", 3, 0, 1, 1)),
        "checkpoint": (("rack", 5, 1, 1, 2), ("console", 0, 2, 2, 1), ("plant", 5, 5, 1, 1)),
        "control": (("rack", 0, 1, 1, 2), ("plant", 5, 6, 1, 1), ("console", 1, 1, 2, 1)),
        "wet-lab": (("labbench", 1, 2, 2, 1), ("workbench", 2, 4, 1, 1), ("shelf", 0, 6, 2, 1)),
        "bio-lab": (("labbench", 0, 2, 2, 1), ("shelf", 0, 4, 2, 1)),
        "lab-stores": (("rack", 0, 1, 1, 1), ("workbench", 2, 4, 1, 1)),
        "electronics": (("shelf", 0, 1, 1, 2), ("workbench", 1, 2, 1, 1)),
        "coolant": (("console", 7, 4, 2, 1), ("pump", 4, 2, 2, 2), ("plant", 8, 0, 1, 1)),
        "reactor": (
            ("tank", 0, 2, 1, 2),
            ("tank", 9, 2, 1, 2),
            ("rack", 0, 8, 2, 1),
            ("workbench", 3, 7, 1, 1),
            ("plant", 9, 5, 1, 1),
        ),
    }
    for name, fixtures in extras.items():
        room = rooms[name]
        for index, (style, x, y, width, height) in enumerate(fixtures, 1):
            facility.furniture(
                f"{name}-equipment-{index}", style, room.x + x, room.y + y, width, height
            )
    for name, style, x, y, width, height in (
        ("service-baffle", "pump", 21, 22, 1, 2),
        ("research-cover", "planter", 41, 29, 3, 1),
        ("research-screen", "labbench", 35, 29, 2, 1),
        ("security-panel", "console", 32, 13, 2, 1),
    ):
        facility.furniture(name, style, x, y, width, height)
    for name, y in (("security", 11), ("research", 34)):
        for suffix, x, destination in (("up", 28, "down"), ("down", 32, "up")):
            stair_id = f"stairs-{name}-{suffix}"
            facility.object(
                facility.markers,
                stair_id,
                "Stair",
                x,
                y,
                properties={"destination": f"stairs-{name}-{destination}"},
            )
            facility.detail(stair_id + "-treads", "stairs", x, y, 1, 1, 270)
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


def dress_research(facility: Facility) -> None:
    """Authored station roles and interrupted work, separate from physical layout."""
    appearances = {
        "entry-console": "hiding-desk",
        "electronics-2": "hiding-desk",
        "coolant-4": "hiding-desk",
        "screening-1": "security-console",
        "screening-equipment-2": "broken-console",
        "power-equipment-2": "broken-console",
        "power-1": "vacuum",
        "repair-1": "cable-cabinet",
        "repair-equipment-2": "coolant",
        "repair-equipment-3": "displaced-chair",
        "logistics-1": "sample-drawers",
        "logistics-3": "cable-cabinet",
        "checkpoint-1": "security-console",
        "checkpoint-3": "security-console",
        "control-1": "security-console",
        "control-2": "abandoned-station",
        "control-3": "security-console",
        "control-equipment-3": "broken-console",
        "wet-lab-2": "fume-hood",
        "wet-lab-3": "unfinished-bench",
        "wet-lab-equipment-1": "spectrometer",
        "wet-lab-equipment-2": "centrifuge",
        "bio-lab-1": "reagents",
        "bio-lab-equipment-1": "abandoned-station",
        "bio-lab-equipment-2": "freezer",
        "lab-stores-1": "sample-drawers",
        "lab-stores-2": "freezer",
        "lab-stores-equipment-2": "sample-cart",
        "electronics-1": "robot-arm",
        "electronics-3": "spectrometer",
        "electronics-equipment-2": "displaced-chair",
        "coolant-2": "vacuum",
        "coolant-equipment-2": "coolant",
        "reactor-1": "security-console",
        "reactor-equipment-4": "sample-cart",
        "reception-4": "wilted-plant",
        "power-4": "wilted-plant",
        "lab-stores-4": "wilted-plant",
        "electronics-4": "wilted-plant",
    }
    for obj in facility.markers:
        if obj["type"] != "Furniture":
            continue
        name = obj["name"]
        appearance = appearances.get(name, "standard")
        condition = (
            "kept"
            if name.startswith(("reception", "entry", "checkpoint"))
            else "interrupted"
            if appearance
            in ("abandoned-station", "unfinished-bench", "broken-console", "displaced-chair")
            else "dusty"
            if name.startswith(("power", "repair", "lab-stores"))
            else "used"
        )
        obj["properties"].extend(
            (
                {"name": "appearance", "type": "string", "value": appearance},
                {"name": "condition", "type": "string", "value": condition},
            )
        )
        if appearance == "displaced-chair":
            for prop in obj["properties"]:
                if prop["name"] in ("blocks_vision", "blocks_sound"):
                    prop["value"] = False
    for desk_name in ("entry-console", "electronics-2", "coolant-4"):
        desk = next(obj for obj in facility.markers if obj["name"] == desk_name)
        facility.object(
            facility.markers,
            "under-" + desk_name,
            "UnderDesk",
            desk["x"] // SIZE + 1,
            desk["y"] // SIZE,
            properties={"furniture_id": desk_name},
        )
    for name, x, y, width, height in (
        ("entry-disruption", 7, 24, 2, 2),
        ("screening-scuffle", 5, 15, 2, 2),
        ("repair-unfinished", 17, 26, 2, 2),
        ("control-abandoned", 42, 9, 2, 2),
        ("analysis-spill", 34, 25, 2, 2),
        ("biology-interrupted", 43, 24, 2, 2),
        ("archive-notes", 34, 35, 2, 1),
        ("instrument-work", 43, 34, 2, 2),
        ("core-scuffs", 54, 24, 2, 2),
        ("coolant-work", 58, 14, 2, 2),
    ):
        facility.detail(name, "aftermath", x, y, width, height)
    for name, x, y, width, height in (
        ("power-trunk", 15, 8, 1, 8),
        ("repair-trunk", 15, 23, 1, 8),
        ("analysis-return", 32, 21, 1, 7),
        ("biology-return", 40, 21, 1, 7),
        ("containment-supply", 51, 16, 10, 1),
        ("core-supply", 51, 28, 10, 1),
    ):
        facility.detail(name, "utility", x, y, width, height)


def anchors_and_patrols(facility: Facility) -> None:
    for name, kind, tile in (
        ("entry-spawn", "Spawn", (5, 24)),
        ("entry-exit", "Exit", (3, 24)),
        ("vault-core", "Core", (56, 22)),
    ):
        facility.object(
            facility.anchors,
            name,
            kind,
            *tile,
            properties={"actor_id": "operative"} if kind == "Spawn" else {},
        )
    routes = (
        (
            "service",
            "SENTINEL",
            ((18, 12), (22, 12), (22, 20), (17, 20), (22, 20), (22, 12), (18, 12)),
        ),
        ("security", "SENTINEL", ((44, 8), (43, 8), (43, 10), (44, 10), (44, 8))),
        ("research", "TRACKER", ((37, 34), (35, 34), (35, 33), (37, 33), (37, 34))),
        ("core", "INTERCEPTOR", ((59, 26), (54, 26), (54, 25), (59, 25), (59, 26))),
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
        ("entry-service", (13, 19), "entry|service-wing"),
        ("service-security", (28, 11), "service-wing|security-control"),
        ("service-research", (28, 34), "service-wing|research-floor"),
        ("cross-link", (38, 19), "security-control|research-floor"),
        ("security-core", (48, 14), "security-control|core-chamber"),
        ("research-core", (48, 30), "research-floor|core-chamber"),
    ):
        facility.object(
            facility.markers, "choke-" + name, "Chokepoint", *tile, properties={"zones": pair}
        )
    # Stable marker IDs for P05, beside actual cover rather than decorative walls.
    for index, (cover, hide) in enumerate(
        (
            ((20, 19), (20, 18)),
            ((26, 25), (29, 26)),
            ((36, 15), (35, 15)),
            ((44, 28), (44, 29)),
            ((53, 23), (50, 24)),
        ),
        1,
    ):
        facility.floor.update((cover, hide, (cover[0] - 1, cover[1])))
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
    # Preserve calibrated bounds only for fixtures whose placement/size remains
    # identical. Changed/new art must be reviewed with calibrate_colliders.py.
    previous = json.loads(TARGET.read_text()) if TARGET.exists() else {"layers": []}
    old_objects = {
        obj["name"]: obj for layer in previous["layers"] for obj in layer.get("objects", [])
    }
    for layer in data["layers"]:
        for obj in layer.get("objects", []):
            old = old_objects.get(obj["name"])
            if old is None or any(
                old.get(key) != obj.get(key) for key in ("x", "y", "width", "height")
            ):
                continue
            existing = {p["name"] for p in obj.get("properties", [])}
            obj.setdefault("properties", []).extend(
                p
                for p in old.get("properties", [])
                if p["name"].startswith("collision_") and p["name"] not in existing
            )
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
    dress_research(facility)
    anchors_and_patrols(facility)
    write_map(export(facility))
    print(f"Authored {len(ROOMS)} rooms; exported {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
