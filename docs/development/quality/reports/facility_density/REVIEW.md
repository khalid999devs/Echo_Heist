# Facility density and pacing review

2026-10-21, Khalid; `work/facility-density`, based on main `41ce939`. User-requested revision: smaller rooms, more room components/greenery, narrower and more involved approaches, visible steps, slower Human movement. [Runtime/map/tuning contract](../../../architecture/integration/FACILITY_DENSITY.md). P03 remains partial; full V1 is still pending.

## Result

The actual five-zone map now contains **23 compact rooms and 104 physical furnishings**, instead of the first nine-object cluster. Desks/chairs, lab benches, sample tanks, equipment shelves, server racks, pumps, plants and planters have authored positions and collision/sight/sound flags. Upper/lower routes bend around equipment, room entrances and railed stair gangways. Every declared walkable room tile, both branches, cross-link and all four patrol routes validate. Room sizes range from 5 to 10 tiles wide and 4 to 10 high.

Human walking changed 2.2→1.8 tiles/s; sprint 3.6→2.6. Defender speed defaults were reduced alongside these, retaining a faster Human escape speed. Tool/capture rules and scoring were preserved. The paused Tab map shows a room legend and own/objective locations without exposing guards. Actor art is smaller for the lanes; committed movement still drives gait/facing. Repeated zone/room signs discovered in native screenshots were removed.

## Actual checks

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/checks/run.py
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/quality/capture_ui.py --output output/density/reviewed
```

PASS: **96 tests**, Ruff lint/format, strict mypy over **77 source files**, 1,000-line/six-direct-file structure checks. Focused checks cover room reachability/bounds/overlap, physical furniture flags/layer order, walkable gangway center lanes, both branches/cross-link, deterministic replay, actual Core theft/extraction/capture and map freeze/input release. Timing fixtures now derive arrival from actual movement/config rather than the former speed.

The native Cocoa screenshot sweep used seed **1042**, real GameFlow/HumanInput actions, stock tools and unchanged Simulation. It completed upper WIN at tick **2346** (78.2 active seconds), lower WIN at **2590** (86.3 seconds) and deliberate contact CAPTURED at **583**. Voluntary abort, pause/retry, unavailable modes, sliders, result hovers, resize and all seven observed Sentinel states were also exercised. [Machine-readable results](PLAYTHROUGH.json). Routes are optimized QA paths; these times are not a normal-player timing claim or the finished 10–20 minute mission target.

## Native visual inspection

All **38** current native screenshots were inspected: six menu/settings states, two unavailable notices, six gameplay/map/dialog states, six furnished-room views, seven guard states, four feedback/Lab views, five outcomes/hovers and two window sizes. Source captures are at ignored `output/density/reviewed/`; reproduce them with the command above. A small selection is retained here; the full 38 MB capture sweep stays out of Git.

| Retained view | Inspection |
| --- | --- |
| [Entry](screens/gameplay/entry.png) | Furniture is visible from the first frame; player/Exit and compact HUD remain readable |
| [Facility map](screens/gameplay/map.png) | 23-room legend, separate YOU/EXIT labels, no Core-room number overlap |
| [Service servers](screens/rooms/01-service-servers.png) | Server aisles, pumps, plants and distinct compact room signs |
| [Security gangway](screens/rooms/02-security-gangway.png) | Real input traverses the narrow center lane between physical rails |
| [Security Control](screens/rooms/03-security-control.png) | Furnished desks/control rooms, fixed glass and route turns |
| [Core chamber](screens/rooms/04-core-chamber.png) | Furnished reactor approach and clear objective beacon |
| [Research gangway](screens/rooms/05-research-gangway.png) | Second usable approach with clear stair/rail silhouette |
| [Biology lab](screens/rooms/06-biology-lab.png) | Lab benches, sample tanks and greenery; real player inside the room |
| [Lockdown](screens/gameplay/lockdown.png) | Empty socket, carried core, changed return objective and emergency lights |

The cinematic title/briefing/settings/results share the existing illustrated 3D scene and continuous UI gradients. Menus remain intentionally honest about unavailable Companion/Workshop functionality. No layout clipping was observed at the two checked window sizes. This is agent visual inspection and scripted native input, not a general-gamer study or a claim of a perfect finished experience.

## Build and remaining boundary

Current revision's clean native packaging and hosted CI are pending at this source checkpoint. The earlier macOS ZIP is stale until rebuilt; do not represent its old manifest as this map revision. Actual results will be attached here after the clean build.

The original CC0 music/cue sources remain unchanged. [Audio integration](../../../assets/AUDIO.md) records the five context tracks and eleven cues. The map now uses the same pause ducking. No new audio downloads were needed for this environment revision.

An audio-enabled accelerated native upper-route run also finished WIN: **2,333 rendered frames**, Cocoa audio device ready, **16 decoded assets / 199 played cues**, and all five music contexts selected from actual states. The map supplied paused audio state while simulation time stayed frozen. [Actual audio results](AUDIO_PLAYTHROUGH.json). The generated driver is retained locally at `output/density/check_audio.py`, run with `UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python output/density/check_audio.py`; this checks routing/playback availability, not subjective speaker balance.

Continue shared P03/Tracker/registry work next, then later Companion/MCTS, Interceptor/minimax, NEXUS, Workshop and scoring. Doors, glass breaking, actual hiding and canisters remain P05. Human play-feel/balance, interactive Windows speakers/input, clean-machine download/Gatekeeper and final art/mix quality remain unverified release work.
