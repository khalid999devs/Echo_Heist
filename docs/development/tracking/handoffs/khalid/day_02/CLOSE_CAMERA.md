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

Fresh native packaging and hosted verification are pending the clean implementation commit. Previous ZIPs are stale for this revision; do not present them as current. This section will be replaced with actual source/archive/CI evidence after execution.

No deferred glass breaking, door/hiding/canister mechanics, advanced AI, policy persistence or scoring is represented as finished. Continue the existing owner queues and consume these visuals in later slices. An interactive Windows playtest remains required before claiming Windows desktop quality.
