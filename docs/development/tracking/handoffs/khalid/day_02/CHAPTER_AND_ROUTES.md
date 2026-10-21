# Khalid — chapter and compact-route handoff

2026-10-21. User-requested UI/map/tuning revision complete; full **P03 remains IN_PROGRESS**. Starting main `2106fba`; branch `work/chapter-and-route-balance`; implementation/build commit **`e92d96ef2acef2727179e353bade18cf19e7a8fa`**. Subsequent record edits change documentation only. [Runtime contract](../../../../architecture/integration/CHAPTER_AND_ROUTES.md) supersedes the previous density checkpoint's menu flow, coordinates, dimensions and speeds.

## Run and inspect

```sh
uv sync --locked --extra dev --extra build
uv run --locked echo-heist
uv run --locked python scripts/checks/run.py
```

The same uv commands work on Windows PowerShell. Suhita should synchronize current main into her own branch while preserving local work, then use the [Windows setup](../../../../workflow/setup/WINDOWS_SUHITA.md). Her next owned work remains P03 registry/geometry adapter and cues/fixtures. The Mac ZIP is not a Windows executable.

Title now has one Chapter 01 card. Choose **Play Chapter → Launch Mission**; Human is already selected. Choosing a mode is separate from launching. Unavailable Companion explains its status and retains Human. Back or Escape returns without starting a run. Report is unavailable until a real attempt ends, then opens that actual result. Settings has Audio and Display groups. Keyboard arrows/Enter and pointer controls use the same target rectangles.

Default seed **1042**. WASD/arrows move; Shift sprints; Q Echo, F EMP, Space stun, hold E beside the Core. Tab opens the paused map; Tab/Esc returns, then press movement again. Escape pauses; F3 shows actual developer telemetry. The facility is 64×40 with 14 purposeful rooms and 67 physical furnishings. Entry connects to Service, then upper Security or lower Research, both meeting at Core. The cross-link and both return routes remain open. Security is shorter/exposed; Research is longer with cover and storage/lab turns. A disabled/stunned body remains solid.

The revised walking/sprinting speeds are **2.5/3.7 tiles/s**, with original defender defaults restored. The conditional two-storey suggestion was not needed: the original connected topology fits on a 42.9% smaller single floor. Stair gangways remain static art with physical rails. Doors, glass breaking, actual hiding and canisters stay P05 as agreed.

## Consumer changes

Retrieve all coordinates through LevelData: Spawn `(5,24)`, Exit `(3,24)`, Core `(56,22)`, first Sentinel `(18,12)`, upper/lower gangways `(30,11)` / `(30,34)`, cross-link `(38,19)`. Map/zone/anchor/guard/route/cover/hide IDs remain stable. Room fittings and the export are authored by `scripts/level/author_facility.py`; rerun it after changing its source layout. The existing importer validates every room's walkable floor, patrol, branch and marker. No schema or new dependency was added.

`GameFlow.mode_choice` is now distinct from `selected` keyboard/pointer focus. `MODE_BUTTONS` / `MODE_ITEMS` order: Human, Companion, Launch, Back. Default focus is Launch. `TITLE_BUTTONS`: Play, Report, Settings, Quit. Future Companion/Workshop integration belongs in mission setup; do not reintroduce duplicated launch behavior or fake mode functionality. Simulation, observations and normal HumanInput remain independent of presentation.

QA-only `HumanDriver` uses actual movement feedback and filtered visible body positions to navigate a body overhanging its tile and a blocked corner. It never bypasses collision, forces outcomes or acts as Companion AI. Canonical replay comparisons still require the same code/map/config; speed/map changes legitimately change hashes.

## Actual evidence

- **97 tests PASS**, Ruff lint/format, strict mypy over 77 source files and the 1,000-line/six-file rules. New meaningful coverage separates mode selection from launch/Back. Compact bounds and route visitation/relative length are checked; original capture, body collision, replay and sensing assertions remain.
- **38 native Cocoa screen states inspected**, including all changed menus, options, furnished rooms, seven Sentinel states, map/dialogs, genuine outcomes and report unlock. Upper WIN tick 1292, lower WIN 1396, deliberate contact CAPTURED 329. [Review/screens/results](../../../../quality/reports/chapter_balance/REVIEW.md). These optimized inputs are not normal-player timing/balance evidence.
- Audio-enabled native source WIN: 1,300 rendered frames, all five music contexts, 16 decoded assets / 114 cues; paused map freezes time and supplies paused audio state. No new audio source or license change.
- Clean `e92d96e` macOS arm64 app/ZIP built with Python 3.13.16 and PyInstaller 6.22.3 on macOS 26.4.1; ad-hoc signed, not notarized. Archive `dist/echo-heist-0.1.0a1-macos-arm64.zip`, **44,050,293 bytes**, SHA256 **`bfa09ce8cb37ae6e5fe68956c9aaeef0d894de198ccf64feb4f530fe63585892`**. Native app and fresh ZIP extraction each PASS all eight Cocoa smoke checks with audio ready / 16 assets. [Build record](../../../../quality/reports/chapter_balance/BUILD.json).
- [Hosted CI 39599989680](https://github.com/khalid999devs/Echo_Heist/actions/runs/39599989680) **PASS** for exact implementation commit `e92d96e`: Linux/Windows/macOS checks, native primary builds and frozen dummy-video smoke. Later record edits change documentation only; `git diff e92d96e -- src scripts packaging pyproject.toml uv.lock tests` is empty.

Commands actually run include `scripts/quality/capture_ui.py --output output/chapter-balance/final`, `scripts/packaging/build.py`, `scripts/packaging/smoke.py "dist/Echo Heist.app" --output-dir output/chapter-balance/frozen-app`, and a fresh `ditto -x -k` extraction followed by smoke at `output/chapter-balance/extracted-e92d96e/Echo Heist.app`. All use the locked uv environment; build/smoke use `--all-extras`.

Frozen smoke covers startup/resources/settings and matching headless hashes, not a complete frozen mission or downloaded quarantine acceptance. Interactive Windows hardware/audio/download, Linux native packaging, final human balance and subjective mix remain NOT_RUN. Hours were not tracked; no invented workload total or shared phase completion is recorded.

Continue the remaining P03 registry/Tracker/replay/cues integration against these contracts. Only the first Sentinel is autonomous; three other posts retain contact behavior. Companion/MCTS, Interceptor/minimax, NEXUS, Workshop and scoring still need their assigned phases. This revision ends at the requested chapter/menu/compact-route boundary.
