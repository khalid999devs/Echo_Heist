# Furnished facility and movement revision

2026-10-21, Khalid; user-requested follow-up to [the first stealth slice](STEALTH_SLICE.md). Starting main: `41ce939`; branch: `work/facility-density`. This extends the playable environment without closing the remaining P03 gate.

## Map authoring and compatibility

`scripts/level/author_facility.py` deterministically exports the packaged Tiled JSON at `resources/data/maps/vault-five-zone.json`. Run `uv run --locked python scripts/level/author_facility.py` after editing its room/corridor/furnishing definitions. The runtime still loads that JSON through the existing typed importer, never the authoring script. Numeric layers retain one map row per line; each object is one complete record. No runtime dependency was added.

The map is now 80×56 tiles with 23 rooms and 104 physical Furniture objects. The five zone IDs, mission anchor IDs, four guard/route IDs and cover/hide/chokepoint IDs remain stable. Coordinates changed: Spawn `(5,25)`, Exit `(3,25)`, Core `(72,27)`, active Sentinel post `(24,19)`. Retrieve positions from LevelData instead of hard-coding old coordinates. Entry connects to Service; separate upper Security and lower Research branches reach Core, with their original cross-link retained. Shortest authored outbound routes have 99 upper / 105 lower / 115 cross-link edges; these are geometry-only routes, not recommended stealth tactics.

Optional rectangular `Room` and `FloorDetail` markers are additive to the map schema. Both require whole-tile positive dimensions. Room has a nonempty label and a known style; FloorDetail has a known style and optional integer rotation 0/90/180/270. `LevelData.rooms`, `floor_details` and `room_at(tile)` expose frozen values to presentation. They are not added to the controller's StaticMap object list. Old maps without them still load. Room rectangles must not overlap or escape bounds, and every walkable room tile must be reachable from Spawn.

Furniture retains explicit movement/vision/sound flags and exact map-owned footprints. New styles are desk, planter, labbench, pump, shelf and railing. Optional custom `rotation` property is validated to 0/90/180/270 and rotates the illustration inside the same footprint; it does not rotate physics a second time. Tiled's native object rotation must remain zero: non-axis-aligned rectangles are rejected instead of silently loading mismatched collision. Plants/planters block movement and sight but pass sound. Railings block movement and pass sight/sound. Other current furnishings block all three. Required branches and every guard patrol remain validated after furniture geometry is applied, independent of layer order.

Security and Research gangways are static top-down stair illustrations with physical rails, at `(33,9,4,3)` and `(33,43,4,3)`. Only their center rows, y=10 / y=44, are walkable. They do not introduce elevation, climbing, jumps or a second floor. Grates and cables are visual details. Glass remains fixed tagged geometry; breaking, doors, hiding and canisters remain P05 by explicit owner choice.

## Tuned speeds

Values are configuration defaults in `resources/data/gameplay/phase02.json`; one tile is 30,000 position units. Simulation stays at 30 Hz. Actor radius, sensor rules, tool ranges/timings, capture ordering and approved scoring are unchanged.

| Actor / action | Before units/s (tiles/s) | Now units/s (tiles/s) |
| --- | --- | --- |
| Human walk | 66,000 (2.2) | 54,000 (1.8) |
| Human sprint | 108,000 (3.6) | 78,000 (2.6) |
| Sentinel | 54,000 (1.8) | 45,000 (1.5) |
| Tracker configured speed | 72,000 (2.4) | 60,000 (2.0) |
| Interceptor configured speed | 84,000 (2.8) | 69,000 (2.3) |

The owner requested slower movement. Defender defaults were reduced alongside it to preserve room for escape in narrow approaches; only the first Sentinel currently moves autonomously. The Tracker/Interceptor rows are tuning for future integration, not evidence their controllers exist. Walking is 18.2% slower; sprinting is 27.8% slower. Both native branches still extract using actual tools and body collision.

## Presentation and input

The six new atlas props are original generated transparent cutouts; [provenance/prompt](../../quality/reports/facility_density/PROMPTS.md) records the exact asset/hash. Desks, plants, shelves, pumps and laboratory benches fit their physics rectangles. Room-specific floor tint, contact shadows, readable wall signs, service grates and static cables distinguish interiors. Broad zone signs are omitted when room signs exist, avoiding overlapping labels. Smaller 36×46 actor frames preserve walk/sprint/facing animation in tighter lanes; physical radius stays unchanged.

Tab opens an architectural facility map with numbered room legend, known Core/Exit anchors, own position and current camera extent. It contains no enemy telemetry. Map viewing freezes simulation and mission/animation time, clears held input and ducks audio like pause. Tab or Esc closes it; Esc from this map does not also open pause. Press movement again after returning. Focus loss still enters the normal pause flow. F3 retains the separate privileged developer telemetry.

`diagnostics/facility_routes.py` and `human_driver.py` serve scripted Human-input QA only. They never control the Companion or change Simulation. The keyboard driver uses actual EMP/melee and filtered visible incapacitated bodies; it centers its lane before detouring around a solid disabled robot. Real contact still captures. These routes do not prove autonomous AI or average player completion time.

See [review/results](../../quality/reports/facility_density/REVIEW.md) for current evidence. Continue the shared P03 registry, Tracker and replay work against the original ownership boundaries. No owner slice outside this requested environment/tuning revision is marked complete.
