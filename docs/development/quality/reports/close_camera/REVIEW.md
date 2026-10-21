# Closer gameplay camera and grounded lab detail

Khalid, 2026-10-21/22; baseline main `9b308e4`, implementation branch `work/close-camera-detail`. User-requested refinement of the existing Human draft. [Consumer contract](../../../architecture/integration/SCENE_PRESENTATION.md), [runnable handoff](../../../tracking/handoffs/khalid/day_02/CLOSE_CAMERA.md).

## Result

The native 1280×720 game view covers **13⅓×7½ tiles**, formerly 26⅔×15, using 96px tiles without enlarging a low-resolution framebuffer. A room and its immediate approaches fill the view; neighboring edges may remain visible. The intermediate 80px framing was tightened after inspection showed both narrow Service rooms could still fit together. The operative uses a 110×124 sprite canvas, about twice the previous visible height. This changes presentation, not body radius, simulation speed, tool range or sensing.

There are **101 authoritative furnishings**, formerly 63, across the same two floors / 14 rooms / five zones. Additional microscopes, samples, consoles, storage, trolleys, racks, plants and coolant apparatus occupy purposeful perimeters and islands. Original branch alternatives, cross-link, patrol lanes, stairs, objectives and room access remain connected. Tank floor bases are separated from their visual height. Full-room reachability validation caught and corrected three early placements that isolated floor pockets.

New overhead prop sources avoid turning perspective furniture sideways. Fit aspect ratios and repeat cabinet modules instead of stretching images. Furniture/actors sort by ground depth, so an operative can pass behind equipment. Soft silhouette shadows start at actual foot/base pivots with feathered contact ellipses. No rectangular backing is drawn. Room light is clipped locally; actual equipment indicators/bubbles stay on their instruments; lockdown tint includes actors/props. Glass now shows floor through restrained reflections rather than opaque cyan blocks. Breaking remains P05.

Human walk/run each use eight ordered slots per facing, derived from traveled distance; stopping stops the cycle. Render-only interpolation bridges the 30Hz simulation without changing its state. Atlas decoding uses measured row boundaries and connected silhouettes after review found neighboring fragments. Passing slots use the matching closed stance. These improve the previous two-pose gait; they are raster cycles, with interaction-specific capture/hide/tool animation still pending. Source PNGs, exact prompts and hashes are preserved in [PROMPTS](PROMPTS.md) and [ASSETS](ASSETS.json).

## Actual verification

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/checks/run.py
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/quality/capture_scenes.py --output output/close-camera/final-review
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/quality/capture_motion.py --output output/close-camera/release-motion --realtime
```

PASS: **117 tests**, strict mypy over **94 source files**, Ruff lint/format, authored structure rules and diff check. Existing map reachability/overlap/patrol checks cover the new footprints. The motion regression now verifies draw fingerprints, interpolation endpoints/bounds and phase freezing on stop. The alpha regression checks transparent corners with the larger fully visible figure. No cosmetic test files were added.

Final native Cocoa sweep: **48 screen states / 3,862 rendered/audio/display frames**. Security branch WIN **1505 ticks**, Research WIN **1620**, deliberate contact CAPTURED **759**. Both stair directions at three progress points, six real Sentinel states, eight route rooms, all five music contexts and 1,560 active-siren frames were exercised. [Raw playthrough](PLAYTHROUGH.json). Optimized QA Human inputs use stock tools; this is route viability, not novice balance or full-V1 evidence.

Motion review: **378 source frames at a 60Hz step**, all eight cycle slots for walking/running, all four directions, turns/rest/recharge and unchanged simulation fingerprint on every draw. Native visual fixture disables security explicitly; route wins above retain default security. **14 separately labeled architectural previews** cover every room; these are camera inspections, not a claim the operative visited all 14. [Raw motion results](MOTION.json). Local footage: `output/close-camera/release-motion/walk-run.mp4`; full frame captures stay ignored.

Final render/audio/display timings: median **2.75 ms**, p95 **3.89 ms**, max **319.12 ms** (first-use/startup). Realtime motion drawing median **4.35 ms**, max **19.31 ms**. These exclude simulation and are named local-run measurements, not minimum hardware or cross-platform performance promises. Static map/props, alpha masks and projected shadows are cached rather than rebuilt every frame.

Reviewed scene/room contact sheets and full-size entry, lab, control, lockdown, Sentinel and stairs. The final crop removes wide room overviews while preserving nearby guard cones, suspicion and capture cues. Existing title/briefing/settings/Workshop/guide/endings remain navigable with unchanged copy and context-specific cinematics.

| Playable captures | Architectural inspection |
| --- | --- |
| [Entry and enlarged operative](screens/gameplay/entry.png) | [Analytical laboratory](screens/rooms/wet-lab.png) |
| [Containment instruments](screens/gameplay/containment.png) | [Surveillance equipment](screens/rooms/control.png) |
| [Sentinel warning](screens/gameplay/sentinel.png) | [Paused two-floor map](screens/gameplay/map.png) |
| [Lockdown](screens/gameplay/lockdown.png) | [Timed stairs](screens/gameplay/stairs.png) |

Rendering principles used: [depth sorting](https://docs.godotengine.org/en/stable/classes/class_canvasitem.html#class-canvasitem-property-y-sort-enabled), [ambient/point lighting and occluders](https://docs.godotengine.org/en/stable/tutorials/2d/2d_lights_and_shadows.html), and [pygame transforms](https://pyga.me/docs/ref/transform.html). These inform the pygame implementation; no engine replacement or live 3D renderer was added.

## Build boundary

Clean runtime **`ac2edfe62a007aa72f98c3f67356d0717a7fca2e`**, following asset commit `5eee828`, built successfully with Python 3.13.16 / PyInstaller 6.22.3 / macOS 26.4.1 arm64. The Mac app and fresh ZIP extraction each PASS all eight frozen Cocoa checks from an unrelated working directory, with native audio ready. The app is ad-hoc signed, not notarized. [Exact manifest, smoke and CI evidence](BUILD.json).

Current `dist/echo-heist-0.1.0a1-macos-arm64.zip`: **59,444,312 bytes**, SHA256 **`bad5acbb228d78062b732ca545cdb3460aa1bc38b16dcfdbb40567cb00d31e41`**. This replaces the older file at the same path; the preceding scene-presentation ZIP did not contain this refinement.

[Source CI 39650365624](https://github.com/khalid999devs/Echo_Heist/actions/runs/39650365624) PASS at that runtime: all Linux/Windows/macOS check jobs, native Windows/macOS packages and eight-check frozen dummy-video smoke. Windows interactive desktop/audio testing is still NOT_RUN. Source runs use the commands above; Windows can retrieve its artifact from the linked CI or build natively with the documented packaging command.

This completes the requested camera/character/room-detail source refinement. It does not close P03-P08, implement advanced defenders/Companion/NEXUS, persist Workshop policies, add scoring or bring forward deferred environment interactions. Interactive Windows hardware/audio/download, subjective audio/animation playtest and public-release QA remain separate gates.
