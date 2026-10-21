# Chapter flow and compact research facility

2026-10-21, Khalid; user-requested correction after main `2106fba`. Branch `work/chapter-and-route-balance`. This supersedes the [previous facility revision](FACILITY_DENSITY.md) for menu flow, map coordinates and movement tuning. Remaining P03/P04-P08 ownership and simulation contracts are unchanged.

## Purposeful opening flow

Title presents one Chapter 01 card with Play Chapter, then Report, Settings and Quit. Play opens the briefing. Report is visibly unavailable before a real completed run; afterward it opens that run's committed result. The chapter thumbnail reuses bundled original cinematic art; no new downloaded/generated bitmap is introduced.

Briefing explains Infiltrate / Recover / Extract, actual controls and the canonical two-route topology. Mode cards choose how to play; only Launch Mission starts Simulation. `GameFlow.mode_choice` is separate from `selected` navigation focus. Human is selected initially; focus starts on Launch so Enter from title then Enter from briefing still starts a Human run. Choosing Human does not launch; choosing unavailable Companion explains availability while retaining Human. Mouse Back or Escape returns without starting a run. Arrow keys navigate; left/right now work alongside up/down.

`TITLE_BUTTONS` indexes are Play / Report / Settings / Quit. `MODE_BUTTONS` indexes are Human / Companion / Launch / Back. `MODE_ITEMS` matches all four focus targets; only the first two are mode cards. Input uses these same rectangles. Later P04/P06 work must connect Companion deployment and its Workshop within the mission setup context, without restoring duplicated launch actions or pretending unavailable systems exist.

Settings uses explicit Audio and Display groups, with actual music/effect sliders, reduced-flashing/fullscreen switches and a separate Back action. Storage, audio routing and setting meaning are unchanged. The existing illustrated background, motion, fonts, event sounds and result screen are retained.

## Original routes in a smaller footprint

Blueprint pp. 3-4 require one connected map: Entry/Extraction → Service Wing → upper Security OR lower Research → Core Chamber, plus a narrow cross-link. Both branches remain usable for return. Its 80×56 default is tunable. The owner's second-floor suggestion was conditional; this revision fits the connected layout on one **64×40** floor, 42.9% less bounding area. No floor-switching, teleport or elevation rule is introduced. The two existing stair illustrations remain static railed gangways.

The map now has **14 rooms / 67 physical furnishings**. Personnel screening and the Entry lift lead to power/ventilation, servers, maintenance and equipment stores. Security has a checkpoint, surveillance control and a shorter exposed corridor. Research has analytical/biology labs, test cells, an archive/instrument lab and the longer covered approach. Containment systems lead into the same Core chamber. Lab floors and identification trim are lighter to distinguish scientific spaces from service equipment. Keep furnishings and their explicit collision/sight/sound geometry authoritative.

Stable map, zone, anchor, guard, route and cover/hide IDs remain. Coordinates changed:

| Anchor | Tile |
| --- | --- |
| Spawn `entry-spawn` | (5,24) |
| Exit `entry-exit` | (3,24) |
| Core `vault-core` | (56,22) |
| Sentinel post `guard-service` | (18,12) |
| Security / Research gangway center | (30,11) / (30,34) |
| Branch cross-link | (38,19) |

`scripts/level/author_facility.py` remains the maintained map authoring source. Regenerate its JSON explicitly. All walkable room cells, both branches, cross-link, guard paths and markers validate. Geometry-only QA paths have **75 upper / 81 lower / 89 cross-link edges** outbound. The Sentinel starts in the power room and physically patrols the shared service approach; its stationary diagnostic post no longer sits across a required passage. Source checks retain both no-controller mission loops and the live default Sentinel.

## Movement and verification boundary

`phase02.json` now configures Human walk **75,000 units/s (2.5 tiles/s)** and sprint **111,000 (3.7)**, up from 54,000 / 78,000. Guard defaults return to Sentinel 54,000 (1.8), Tracker 72,000 (2.4), Interceptor 84,000 (2.8). Radius, simulation frequency, sensing, tools, capture ordering and scoring remain unchanged. Only the first Sentinel currently has autonomous movement; future configured speeds are not proof of completed controllers.

The QA keyboard driver now handles the overhang of a visible disabled/stunned body and uses its own committed movement feedback to align around a blocked corner. It never bypasses collision, changes actor state or supplies Companion logic. Normal Human input and simulation physics are unchanged.

See [actual review](../../quality/reports/chapter_balance/REVIEW.md). The requested UI/map/tuning revision does not close shared P03 or implement the owner-deferred P05 doors, glass breaking, hiding and canisters. Human balance/feel and primary platform release acceptance remain separate from optimized scripted routes.
