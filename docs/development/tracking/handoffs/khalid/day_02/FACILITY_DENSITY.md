# Khalid — furnished facility handoff

2026-10-21. Requested environment/tuning implementation is complete; shared **P03 remains IN_PROGRESS**. Branch `work/facility-density`, starting main `41ce939`, implementation/build commit **`764d8ff17ec8b83081b69b86510f2d8580bd7ba0`**. Subsequent handoff edits change development records only. The original P01/P02 handoffs and [first stealth slice](STEALTH_SLICE.md) remain the prerequisite history.

## Run and inspect

```sh
uv sync --locked --extra dev --extra build
uv run --locked echo-heist
uv run --locked python scripts/checks/run.py
```

These uv commands also work in Windows PowerShell; Suhita should use her own Windows checkout/owner branch and [Windows setup](../../../../workflow/setup/WINDOWS_SUHITA.md). Synchronize this revision before editing the shared importer/map. Preserve local changes and her existing history. The macOS ZIP cannot run on Windows; hosted Windows builds and interactive Windows QA are distinct evidence.

Choose Human Infiltration, then Launch Mission; default seed **1042**. Walk with WASD/arrows; Shift sprints. Tab opens the paused 23-room map; Tab/Esc closes it, then press movement again. Exit is west, Core east. The upper branch passes Service Servers/Security; the lower branch passes Data Relay/Research. Both railed gangways have a narrow center lane. Read the room label in the HUD and wall signs. Explore the desks, server aisles, lab benches, specimen tanks, shelves, pumps and plants; the furniture is physically solid. Guard timing or tools matter at the shared Entry/Service approach.

Q Echo, F EMP, Space melee. Hold E beside the Core until theft completes, then return to the original Entry lift. A disabled robot remains solid: move around it. F3 exposes actual developer telemetry; Esc opens pause/retry/abort. Settings controls music/effects, fullscreen and reduced flashing. Walking is now 1.8 tiles/s, sprint 2.6; capture/tool timings and scoring rules were preserved.

## Actual contracts and file boundaries

Read [FACILITY_DENSITY](../../../../architecture/integration/FACILITY_DENSITY.md) for schema, changed anchor coordinates and speed table. The typed importer remains `level.io.load_tiled_map`; no second loader exists. `LevelData.rooms`, `floor_details` and `room_at(tile)` carry optional frozen presentation metadata. Furniture still owns explicit physical/vision/sound footprints; plants pass sound and rails pass sight/sound. Tiled native object rotation must be zero; the custom rotation property rotates only the sprite in its axis-aligned footprint.

`scripts/level/author_facility.py` is the maintained authoring source for the current export. Change its room/corridor/prop data and rerun it instead of making an export edit that regeneration would erase. The script is byte-for-byte repeatable. IDs are stable; coordinates changed. Spawn `(5,25)`, Exit `(3,25)`, Core `(72,27)`, first Sentinel `(24,19)`. Resolve these from LevelData in consumers. All 23 rooms' walkable tiles, five zones, both routes, cross-link and patrols validate.

Presentation additions live under `ui/render/environment/`; the existing map renderer owns static painting and `HeistSession` owns the map overlay. Atlas [provenance](../../../../quality/reports/facility_density/PROMPTS.md) is recorded. The six new props and existing actor motion remain bitmap presentation; Simulation never reads artwork. `diagnostics/facility_routes.py` / `human_driver.py` are QA keyboard drivers only, not Companion logic. They use real stock tools and filtered visible bodies, without forcing outcomes.

## Verified results

- **96 cases PASS**; structure limits, Ruff lint/format and strict mypy over 77 source files PASS. Tests remain under root `tests/`, grouped by type/subsystem. New risk checks include unreachable optional rooms, bounds/overlap, rotated physical rectangles, stair lanes and paused map/input release. Existing solid-corner capture coverage remains intact.
- **38 native Cocoa screen states inspected**. Both actual routes extract: upper tick 2346, lower 2590; deliberate contact captures at 583. [Report, selected screenshots and actual traces](../../../../quality/reports/facility_density/REVIEW.md). These optimized scripted routes do not measure average player pacing.
- Audio-enabled native source WIN: 2,333 rendered frames, all five music contexts, 16 decoded assets and 199 cues. Map pause/audio state exercised. Subjective speaker mix and human play-feel remain open.
- Clean `764d8ff` macOS arm64 build and freshly extracted ZIP each PASS all eight frozen Cocoa smoke checks, audio ready / 16 assets loaded. ZIP `dist/echo-heist-0.1.0a1-macos-arm64.zip`, **44,047,151 bytes**, SHA256 **`5dd7bebe99cd21308f1601141714cd9ba06c9aab106a02be86f833da5e3c7c8e`**. Python 3.13.16, PyInstaller 6.22.3, macOS 26.4.1 arm64; ad-hoc signed, not notarized. [Manifest and actual smoke results](../../../../quality/reports/facility_density/BUILD.json).
- [GitHub CI 39587400106](https://github.com/khalid999devs/Echo_Heist/actions/runs/39587400106) **PASS** for exact implementation commit `764d8ff`: Linux/Windows/macOS checks and native Windows/macOS build/frozen dummy-video smoke. This is not interactive Windows desktop evidence. Later handoff edits change only documentation; `git diff 764d8ff -- src scripts packaging pyproject.toml uv.lock` is empty.

Native commands actually run:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/quality/capture_ui.py --output output/density/reviewed
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked --all-extras python scripts/packaging/build.py
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked --all-extras python scripts/packaging/smoke.py "dist/Echo Heist.app" --output-dir output/density/frozen-app
ditto -x -k dist/echo-heist-0.1.0a1-macos-arm64.zip output/density/extracted-764d8ff
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked --all-extras python scripts/packaging/smoke.py "output/density/extracted-764d8ff/Echo Heist.app" --output-dir output/density/frozen-extracted
```

The frozen smoke verifies title startup/resources/settings and matching headless fixture hashes, not a full frozen mission or browser-download quarantine. Full source mission checks are separate above. Windows interactive input/audio/download checks and Linux native packaging remain NOT_RUN. No source-PDF/scoring change or invented workload hours.

## Next owner action

Continue the remaining P03 slices from the [stealth contract](../../../../architecture/integration/STEALTH_SLICE.md): Suhita's registry/dynamic geometry adapter and cues/fixtures, Khalid's remaining Tracker A*/replay integration. Only `guard-service` is autonomous; three other posts retain contact behavior. Reuse authored patrols/furniture flags and keep controllers on filtered immutable observations. Do not restart P02 or call this the full V1.

The user explicitly deferred doors, breaking glass, real hiding and canisters to P05. Current stairs are static floor/gangway art with rails, not a new elevation mechanic. Companion/MCTS, Interceptor/minimax, NEXUS, Workshop and approved scoring still require their assigned phases. This handoff ends the requested density/movement revision; no other owner's slice is marked done.
