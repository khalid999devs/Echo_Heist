# Scene presentation and navigation review

Khalid, 2026-10-21. Baseline main `1d34f3b`; branch `work/complete-visual-scenes`. User-directed visual work, with remaining AI/profile/scoring mechanics later. [Actual contract](../../../architecture/integration/SCENE_PRESENTATION.md).

## Implemented

Title/Chapter, briefing, Human gameplay, paused map, pause/abort, settings, actual success/capture/abort reports, Workshop design, Companion floor preview, four Field Guide tabs and post-extraction transmission are connected. Workshop edits/presets are local drafts; Deployment explicitly stays unavailable. No AI deployment, score/rank or live decision statistics are invented. Human runs and persisted settings remain real.

Chapter clicks cover the full card. Scene changes consume their event batch; pause/map/abort controls now accept mouse input. Settings support drag/release/focus loss and return to the same paused run. Letterbox mapping retains outside coordinates and uses the actual window dimensions. The screenshot review corrected an undersized Companion Back button, a stair/footer/HUD overlap and an unreadably small facility preview. The preview is now a sharp draggable viewport.

New directional Human, three distinct defender silhouettes, Companion, clinical instruments and stairwell art are original generated assets. Atlas cells preserve proportions, including non-divisible image dimensions; expensive crops/scales/static furnishings are cached. Lab floors have brighter clinical seams. Existing cinematic title, distinct exterior extraction scene and alpha-correct feathered contact shadows are retained. [Exact prompts](PROMPTS.md) and asset register record origin/hash.

Stairs take 24 simulation ticks, animate ascent/descent and recheck occupancy at arrival. Movement/tool use can interrupt; pause/map freeze travel. Lockdown has an independent looping siren, smooth red emergency fixtures, 20% faster guard movement, shorter patrol pauses and longer search. Reduced flashing keeps lights steady. No sensing advantage or hidden target position was added.

## Actual verification

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/checks/run.py
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/quality/capture_scenes.py --output output/scene-presentation/verified
```

PASS: **117 tests**, strict mypy over **88 source files**, Ruff lint/format, structure limits and diff check. New meaningful regressions cover full-card/batch clicks, unavailable AI deployment, slider release/letterbox handling, pause→settings→same mission, stair interruption, late occupied landings, real lockdown speed and siren lifecycle/volume. Existing mission/replay/sensing/capture/tool tests pass.

Actual native Cocoa sweep: **48 screen states**, **3,862 rendered/audio/display frames**, all five context tracks and **1,560 frames with the siren active**. Security route WIN tick **1505**; Research route WIN **1620**; deliberate contact CAPTURED **759**. Actual abort, settings return, both stair directions at three progress points, six Sentinel states and eight route rooms were captured. Routes use real HumanInput and stock tools; they are optimized QA inputs, not novice timing or full-V1 balance evidence. [Raw results](PLAYTHROUGH.json).

All 48 layouts were reviewed through six contact sheets plus full-size checks of title, Workshop, Companion, guide, stairs, lab, lockdown and outcomes. Full files: ignored `output/scene-presentation/verified/screens/`. Selected durable screenshots below. On this native run, render/audio/display median **8.10 ms**, p95 **9.99 ms**, max **311.36 ms** (first-use startup). These exclude simulation time and are not minimum-hardware or Windows performance claims. Audio device/playback lifecycle was exercised; subjective speaker mix remains a human playtest.

| Menus/designs | Playable scene | Outcomes |
| --- | --- | --- |
| [Chapter](screens/menus/title.png) | [Lab](screens/facility/lab.png) | [Extraction](screens/endings/extraction.png) |
| [Workshop](screens/menus/workshop.png) | [Stairs](screens/facility/stairs.png) | [Capture](screens/endings/capture.png) |
| [Companion preview](screens/menus/companion.png) | [Lockdown](screens/facility/lockdown.png) | [Epilogue](screens/endings/epilogue.png) |
| [Guide](screens/menus/guide.png) | [Pause](screens/facility/pause.png) | [Abort](screens/endings/abort.png) |

## Build boundary

Native archive/frozen checks and hosted CI are recorded separately in BUILD.json after execution. Previous two-floor archives do not include this revision. Interactive Windows hardware/audio/download, Linux native packaging, minimum hardware and quarantined download acceptance remain separate checks.

This finishes the requested presentation/navigation pass, not P03-P08 or the full V1. Tracker/Interceptor strategy, Companion/MCTS, NEXUS, saved Workshop profiles, approved score/encounter counting and P05 environment interactions remain assigned work. Upcoming scoring and policy consumers have real layouts to connect; their backend completion must still be verified.
