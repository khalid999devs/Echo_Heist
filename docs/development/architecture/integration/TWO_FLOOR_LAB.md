# Two-floor laboratory and timed movement

Follow-up: [scene presentation contract](SCENE_PRESENTATION.md) supersedes immediate stair transfer, fingerprint schema 4 and the earlier menu/lockdown presentation. It adds timed interruptible travel and all navigable screen designs; existing map/deck/route/sprint geometry below remains valid.

Khalid, 2026-10-21; user-directed refinement of `2be5f61` on `work/two-floor-atmosphere`. Supersedes CHAPTER_AND_ROUTES for stairs, presentation and sprint. P03 and later shared gates stay open. Scoring is unchanged. Glass, doors, hiding and canisters remain P05.

## Contracts being implemented

- Ground floor: Entry and Service. Upper floor: Security, Research, Core. Preserve the two alternative routes and their upper-floor cross-link. The Tiled map is an atlas of disjoint floor footprints, not two floors rendered simultaneously in gameplay.
- Two reciprocal stair pairs connect walkable landings. `StaticMap.stairs` is immutable navigation data. BFS, validation and acoustic flood fill include stair edges; sight and physical/tool reach never cross the solid atlas gap. Stair use is an `INTERACT`, committed by Simulation only. Guards use the same stairs. Occupied destinations reject travel; no overlap or external teleport API.
- `Deck` rectangles in LevelData drive camera/minimap/overview presentation. They never expose hidden actor knowledge to controllers. Stair hints use actual reachable map links, including during lockdown. E uses a stair; holding E cannot repeatedly bounce between floors without a fresh press.
- User approved replacing unlimited sprint with a 3-second burst and 4-second recharge. Fixed simulation ticks own charge, recharge and actual sprint state. Releasing a used burst starts the full recharge; blocked attempts consume no charge. Holding Shift through exhaustion walks while recharging and resumes when ready. Pause/map freeze all timers. Effective sprint footsteps, rather than requested Shift, use the louder existing hearing radius. OwnStatus exposes only the actor's own sprint state.
- Keep the existing title bitmap. Successful extraction uses separate original exterior extraction art; capture/abort show the actual interrupted mission. No invented ranks or achievements before P06.
- Static room lighting/material depth and soft silhouette/contact shadows are presentation only. Cache expensive static work. Keep HUD copy to objective, floor, interaction, time, tools and movement readiness.

## Consumer handoff

Suhita's map importer, render and scene changes are explicitly authorized by the owner for this revision. Existing stable anchor/guard/route/marker IDs remain. Chokepoint coordinates at the stairways change to the lower landings. New stair/deck records must be preserved by future map edits. Runtime/QA consumers must follow stair edges using E rather than trying to move through the atlas gap. Historical one-floor coordinates, unrestricted sprint timings and screenshots are superseded.

Verification and actual resulting values will be recorded after implementation under `quality/reports/two_floor_lab/` and the matching Khalid handoff. This document is a design contract, not evidence of a passing build.

## Actual values and compatibility

The atlas remains 64×40 tiles; display tile size is now 48 px, independent of fixed-point physics (30,000 units/tile). Ground rectangle `(0,0,30,40)`, upper `(32,0,32,40)`; the intervening solid gap separates physical reach and sight. 14 rooms / 63 furnishings. Four original gangway rail fixtures were replaced by reciprocal stair landings: Security `(28,11)` ↔ `(32,11)`; Research `(28,34)` ↔ `(32,34)`. Existing chokepoint IDs now use the lower landings. Entry `(5,24)`, Exit `(3,24)`, Core `(56,22)` and cross-link `(38,19)` remain stable.

New frozen `StairLink(object_id,tile,destination_id,destination)` entries extend StaticMap with default `stairs=()`. `connections(tile)` supplies orthogonal neighbors plus stair edges. Construction checks unique reciprocal in-bounds links; the importer additionally checks walkable landings and deck coverage. Temporary routing maps may block a landing; BFS still respects those blockers. `LevelData.decks=()` / `deck_at(tile)` preserve old single-floor diagnostic fixtures. A landing transfer checks body fit/occupancy after all ordinary movement, before perception/capture/extraction.

`INTERACT` uses its explicit target ID or current reachable hint. `STAIR_USED` contains stair ID, destination ID and actor kind. OwnStatus adds own sprint ticks, recharge remaining and actual sprinting. GameRules JSON adds `sprint_duration_ticks=90` and `sprint_recharge_ticks=120` at 30 Hz; all rule fields are still strictly required. Existing speed values remain 75,000 / 111,000 units/s. Fingerprint schema 4 includes stair links and all mutable movement timers. Old map/config hashes are legitimately different.

HumanInput edge-triggers stairs; Core interactions retain hold semantics. A blocked destination stays on the source landing and reports `stair_landing_occupied`. The Sentinel's filtered-observation BFS chooses the same legal stair interaction. No hidden enemy position is supplied by these new APIs. The UI draws only the active deck, snaps/fades on actual transfers and draws both deck plans on Tab. Static lighting is baked once; glow/contact caches are bounded. The ending uses its own PNG without mirroring; failure uses the interrupted real world. No new dependency or audio asset was added.

Native compositing correction: the Mac display exposes alpha masks on default opaque surfaces. Multiple alpha blits could clear destination alpha and leave rectangular sprite/prop backgrounds. `ui/render/surfaces/formats.py:opaque_surface` explicitly creates a 32-bit RGB target without an alpha channel. The desktop canvas, static map and native QA use it; transparent effect layers retain SRCALPHA. A meaningful layered-alpha regression and native screenshot comparison cover this bug.
