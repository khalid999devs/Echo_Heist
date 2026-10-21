# Chapter clarity and compact facility review

2026-10-21, Khalid. Starting main `2106fba`; branch `work/chapter-and-route-balance`. User requested clearer initial options/chapter card, faster movement, a smaller balanced facility and fidelity to the original research-site routes. [Runtime contract](../../../architecture/integration/CHAPTER_AND_ROUTES.md).

## Changes and player meaning

- One Chapter 01 card and one Play Chapter action. Report / Settings / Quit are separate secondary controls. The real report becomes available after a completed run. Oversized stacked mode entries and the duplicated unavailable Workshop entry are removed from the opening.
- Briefing explains the three actual objectives and shows Entry → Service → Security or Research → Core, including their cross-link. Human/Companion are mode choices; only Launch starts a run. Back returns without launching. Companion remains explicitly unavailable; its future Workshop/deployment belongs to P04/P06.
- Settings groups actual Audio and Display choices, with percentage sliders and short descriptions for toggles. The cinematic backdrop, original art, Oxanium and existing music remain connected.
- A compact 64×40 map, 14 purpose-built rooms and 67 physical furnishings replaces the sprawling 80×56 / 23-room revision. This is 42.9% less map bounding area. Lab benches, test cells, specimen storage, surveillance and containment rooms establish the research-site identity. The original connected single-floor topology fits; a second floor was unnecessary for this revision.
- Human walk/sprint is 2.5/3.7 tiles/s instead of 1.8/2.6. Guard defaults return to 1.8/2.4/2.8. Body size, sensing, capture, tools and approved scoring are unchanged. Security is the shorter exposed approach; Research is longer with cover and storage/lab turns. Both return paths and the cross-link remain open.

## Actual checks

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/checks/run.py
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/quality/capture_ui.py --output output/chapter-balance/final
```

PASS: **97 tests**, strict mypy over **77 source files**, Ruff lint/format and authored 1,000-line/six-file rules. Meaningful checks retain mission/capture/collision/replay/perception coverage and add mode-selection-versus-launch/Back behavior. Updated map checks enforce compact bounds, proper branch visitation, shorter Security route, room reachability and physical gangway lanes. They do not skip failures or loosen capture rules.

The seed-1042 native Cocoa source sweep completed **upper WIN at tick 1292**, **lower WIN at 1396**, **deliberate contact CAPTURED at 329**, and actual abort/retry/pause/report navigation. All seven Sentinel states were observed. [Actual playthrough results](PLAYTHROUGH.json). These are optimized scripted inputs using real stock tools; they are not novice completion times or proof that later AI systems are finished.

All **38** current screenshots were inspected: chapter/menu/settings, unavailable mode/report feedback, actual rooms, gameplay/map/dialogs, guard states, tools/Lab, results/hovers/report unlock, small window and letterbox. Full PNGs remain in ignored `output/chapter-balance/final/`; reproduce with the command above. Selected native evidence:

| View | Review |
| --- | --- |
| [Chapter card](screens/ui/chapter.png) | Single primary action; smaller title; secondary options separated |
| [Briefing](screens/ui/briefing.png) | Clear mission steps, mode selection and one Launch action |
| [Unavailable Companion](screens/ui/companion.png) | Honest feedback; Human remains chosen; no accidental launch |
| [Settings](screens/ui/settings.png) | Audio/display groups, real values and clear Back action |
| [Report unlocked](screens/ui/report-unlocked.png) | Enabled only after an actual result; opens that same report |
| [Compact plan](screens/facility/map.png) | Original upper/lower/cross-link shape, 14-room legend, own/objective markers |
| [Entry](screens/facility/entry.png) | Safe opening, clear extraction lift and physical service approach |
| [Research](screens/facility/research.png) | Brighter lab material, benches/test cells, archive and instruments |
| [Core](screens/facility/core.png) | Both approaches reconnect around containment/Core rooms |

Audio-enabled accelerated native source run also finished WIN: **1,300 rendered frames**, all five music contexts from real states, audio ready, **16 assets / 114 cues**. Map viewing froze time and supplied paused audio state. [Actual audio result](AUDIO_PLAYTHROUGH.json). Driver: local `output/chapter-balance/check_audio.py`; command `UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python output/chapter-balance/check_audio.py`. This verifies playback/routing availability, not subjective speaker mix or a general-gamer playtest.

## Packaging and boundary

Clean packaging and hosted CI for this revision are pending at this source checkpoint. The previous macOS ZIP does not yet represent this compact map. Actual build/hash/smoke results will be added after building the committed source.

P03 remains partial: one autonomous Sentinel and three contact posts. Tracker A*, shared registry, Companion/MCTS, Interceptor/minimax, NEXUS, Workshop and approved scoring are still assigned later work. Glass breaking, doors, real hiding and canisters remain P05 by explicit owner choice. Interactive Windows hardware, clean-download behavior and final human balance/feel remain unverified.
