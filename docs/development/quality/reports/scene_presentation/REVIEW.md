# Scene presentation and navigation review

Khalid, 2026-10-21. Baseline main `1d34f3b`; branch `work/complete-visual-scenes`. User-directed visual work, with remaining AI/profile/scoring mechanics later. [Actual contract](../../../architecture/integration/SCENE_PRESENTATION.md).

## Implemented

Title/Chapter, briefing, Human gameplay, paused map, pause/abort, settings, actual success/capture/abort reports, Workshop design, Companion floor preview, four Field Guide tabs and post-extraction transmission are connected. Workshop edits/presets are local drafts; Deployment explicitly stays unavailable. No AI deployment, score/rank or live decision statistics are invented. Human runs and persisted settings remain real.

Chapter clicks cover the full card. Scene changes consume their event batch; pause/map/abort controls now accept mouse input. Settings support drag/release/focus loss and return to the same paused run. Letterbox mapping retains outside coordinates and uses the actual window dimensions. The screenshot review corrected an undersized Companion Back button, a stair/footer/HUD overlap and an unreadably small facility preview. The preview is now a sharp draggable viewport.

The desktop startup also enables SDL's focus-click-through hint before video initialization, respecting an explicit environment override. [SDL's documented default](https://wiki.libsdl.org/SDL2/SDL_HINT_MOUSE_FOCUS_CLICKTHROUGH) discards a click used to activate an inactive window; enabling it removes that additional source of missed clicks. Frozen startup verifies initialization; an actual human OS focus-click sweep remains a manual check.

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

Clean runtime commit **`19b454bdc3a34ef6c5e3a60bac2cc23c6931e953`** built successfully. Native Mac app and fresh ZIP extraction each PASS all eight frozen Cocoa checks with audio ready. Archive `dist/echo-heist-0.1.0a1-macos-arm64.zip`: **55,313,813 bytes**, SHA256 **`d2696bb0c916166645afc9ea5b8777f6ffc3aa30be09cb9fa0c32175875f66c6`**. Python 3.13.16 / PyInstaller 6.22.3 / macOS 26.4.1 arm64; ad-hoc signed, not notarized. [Exact manifest/smoke records](BUILD.json).

[CI 39634968086](https://github.com/khalid999devs/Echo_Heist/actions/runs/39634968086) PASS at that runtime commit: Linux checks, Windows/macOS checks, native primary builds and frozen dummy-video smoke. Source 407be30 also passed its earlier run; the final runtime adds only the documented startup focus hint. Subsequent handoff commits change records only. Previous two-floor archives do not include this revision.

The matching Windows CI ZIP was retrieved, its SHA256 verified, and copied to `dist/echo-heist-0.1.0a1-windows-x64.zip`: **56,619,251 bytes**, SHA256 **`2008d37b35e552202f8c03526bc0b2f9cf01ff375d2b10aa1aeb042c5dae156a`**. Its downloaded frozen report passes all eight dummy-video checks; it is unsigned. This is hosted Windows execution, not Suhita's interactive hardware/audio test.

Native pointer mapping also passed at actual 960×540, 1024×800 and 1920×820 window sizes; the OS clamped the requested 1920×1080 height, so this is not a full-HD hardware claim. [Small window](screens/display/960x540.png), [tall letterbox](screens/display/1024x800.png). Interactive Windows hardware/audio/download, Linux native packaging, minimum hardware, subjective speaker mix and quarantined download acceptance remain separate checks.

This finishes the requested presentation/navigation pass, not P03-P08 or the full V1. Tracker/Interceptor strategy, Companion/MCTS, NEXUS, saved Workshop profiles, approved score/encounter counting and P05 environment interactions remain assigned work. Upcoming scoring and policy consumers have real layouts to connect; their backend completion must still be verified.
