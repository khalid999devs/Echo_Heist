# Khalid — closer camera and room-detail handoff

2026-10-22. Baseline main `9b308e4`, branch `work/close-camera-detail`. [Actual review/screens](../../../../quality/reports/close_camera/REVIEW.md), [consumer contract](../../../../architecture/integration/SCENE_PRESENTATION.md). P02 remains complete; P03 partial, P04-P08 open. Approved scoring and ownership remain unchanged.

## Run and inspect

```sh
git switch main
git pull --ff-only
uv sync --locked --all-extras
uv run --locked echo-heist
```

PowerShell uses the same commands; run them in Suhita's existing checkout after preserving local changes and selecting her work branch from current main. The Mac app is not a Windows executable. The latest code must be integrated/pushed before this pull retrieves it.

Click Play Chapter → Launch Mission. Move with WASD/arrows, hold Shift for the existing timed sprint, Q Echo, F EMP, Space stun, hold E for core / press E on stairs. Tab pauses on the floor map; Escape pauses. Inspect the larger foot-anchored operative, close room framing, normal stops/turns, equipment occlusion, specimen tanks, translucent glass and locally lit rooms. Both Security and Research approaches remain playable. Core theft starts the existing siren/red light cycle; return downstairs to the green exit. No new menu copy or settings interaction is required.

## Consumer changes

- Same tile IDs, room coordinates, two decks, stairs and routes; pixel size changes **48→96**. Use map `tile_size_px` and shared fixed-point units, never hardcode a pixel conversion. Map author/export must move together.
- **101** map-owned furniture footprints, including new room equipment IDs. Upright tank depth is now one floor tile; art extends north. Existing collision/vision/sound flags remain authoritative. Read current map before planning paths or interactions.
- Bare map surfaces no longer include furniture. `prepare_furniture` caches separate floor/render bounds, sprites/shadows/indicators; `GameFlow` shares them with the heist and Companion preview. Draw these when embedding a map-only view.
- `WorldArt` supplies 32 walk and 32 run frames; `ActorMotion` exposes previous committed position and distance-driven phase for presentation only. UI interpolation never enters controller observations or changes simulation. New rendering responsibilities live under `ui/render/actors/` and `environment/furnishings/` to respect directory budgets.
- Character assets are grouped in `characters/operative/`; tiles and architecture integration directories are full at six direct files. This day_02 handoff directory now also has six files; group the next handoff instead of adding a seventh.

## Evidence and delivery

117 tests, strict types over 94 source files, lint/format/structure pass. Native 48-state sweep passes both real extractions (1505/1620 ticks), contact capture (759), stairs, all five context tracks and siren lifecycle. 378 native walk/run frames cover all directions/eight phase slots; every draw preserves the simulation fingerprint. All 14 room previews were inspected separately. Exact commands/timings and source asset provenance are linked in the review.

Implementation commits: `5eee828` (original assets/provenance), **`ac2edfe62a007aa72f98c3f67356d0717a7fca2e`** (verified runtime/map/rendering). Subsequent delivery changes are records only. [Exact build manifest and smoke evidence](../../../../quality/reports/close_camera/BUILD.json).

Clean Mac archive `dist/echo-heist-0.1.0a1-macos-arm64.zip`: **59,444,312 bytes**, SHA256 `bad5acbb228d78062b732ca545cdb3460aa1bc38b16dcfdbb40567cb00d31e41`. The app and fresh extraction each pass all eight native Cocoa checks with audio ready; ad-hoc signed, not notarized. This replaces the previous download at that filename.

[CI 39650365624](https://github.com/khalid999devs/Echo_Heist/actions/runs/39650365624) passes all three hosted platform jobs, including native Windows/macOS builds and frozen dummy-video smoke at the runtime commit. Suhita can download `foundation-windows-x64`, extract the included game ZIP and run `EchoHeist/EchoHeist.exe`, keeping its support folder. This is a hosted Windows execution check; her interactive hardware/audio playtest remains open. Main integration preserves both implementation commits and the delivery record; the temporary branch is removed after verified integration.

No deferred glass breaking, door/hiding/canister mechanics, advanced AI, policy persistence or scoring is represented as finished. Continue the existing owner queues and consume these visuals in later slices. An interactive Windows playtest remains required before claiming Windows desktop quality.
