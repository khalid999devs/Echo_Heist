# Khalid — two-floor lab handoff

2026-10-21. User-requested refinement implemented; shared P03 remains IN_PROGRESS. Baseline main `2be5f61`, branch `work/two-floor-atmosphere`. Gameplay commit `4132f87`; presentation/native-compositing implementation and clean build **`123225bfda7698f505705436521cc09023118d02`**. Later handoff/record commits contain documentation only. [Current contract](../../../../architecture/integration/TWO_FLOOR_LAB.md), [review/screenshots](../../../../quality/reports/two_floor_lab/REVIEW.md).

## Run on either developer's machine

```sh
uv sync --locked --extra dev --extra build
uv run --locked echo-heist
uv run --locked python scripts/checks/run.py
```

Windows uses the same uv commands in PowerShell. Suhita should synchronize current main into her own work branch while preserving local changes. Read the [Windows setup](../../../../workflow/setup/WINDOWS_SUHITA.md) and current contract first; the Mac ZIP is not a Windows executable.

Play Chapter → Launch Mission. Seed 1042. WASD/arrows move; hold Shift for a three-second louder sprint, followed by four-second recharge. The HUD shows availability; normal walking continues during recharge. E at either stair changes floor; a new press is needed to return. Hold E at the Core. Q Echo, F EMP, Space stun. Tab pauses on a map of both floors; Tab/Esc closes it, then press movement again. Escape pauses, R restarts from pause/results, X confirms an abort from pause; F3 shows real developer telemetry.

Inspect the bright entry, two stairways, upper lab benches/test cells/plants, animated screens/bubbles/fans and responsive idle/walk/run. Entry/Service are downstairs; Security/Research/Core upstairs. Security is shorter/exposed; Research is longer with cover; cross-link and both return routes remain open. The successful ending shows extraction outside the facility; capture/abort keep the actual interrupted scene. The title bitmap is unchanged. Menu/setting/pause copy is shorter.

## Shared API / file changes

- `StaticMap.stairs` / frozen StairLink and `connections(tile)` add genuine navigation edges; BFS and acoustic fill consume them. Vision and physical/tool reach still obey the solid atlas gap. Stair interactions are committed by Simulation after ordinary movement and before sensing/capture/extraction; destination occupancy is authoritative. The Sentinel selects the same INTERACT using its permitted map/observation.
- LevelData adds optional Deck rectangles / `deck_at(tile)`. Tiled Deck/Stair records are validated; preserve their IDs and reciprocity. The atlas is 64×40, 48 px/tile, with 14 rooms and 63 furnishings. Stable Spawn/Exit/Core/guard/route/cover/hide IDs remain. Two lower chokepoints move to `(28,11)` / `(28,34)`, linking upper `(32,11)` / `(32,34)`; cross-link stays `(38,19)`.
- GameRules adds required `sprint_duration_ticks=90` / `sprint_recharge_ticks=120`. OwnStatus adds only its own charge/recharge/actual sprint state. Fingerprint schema 4 includes links and all movement timers. Read rule values; do not duplicate a separate UI/controller cooldown. Pause/map do not advance Simulation.
- `HumanInput` edge-triggers stairs and retains held Core interaction. ObjectiveView carries the real interaction and movement readiness. The QA HumanDriver follows stair hops with E rather than walking through a wall; it remains a QA driver, not Companion AI.
- `opaque_surface` in `ui/render/surfaces/formats.py` creates explicit 32-bit RGB targets. Use it for opaque render canvases/maps. Native Mac default masks caused alpha from one layer to corrupt subsequent sprite compositing, producing rectangular backgrounds; replacing shadow art alone did not fix it. Transparent effects retain SRCALPHA. A layered-alpha regression and actual native captures verify the correction.
- `scripts/level/author_facility.py` is the maintained layout source; regenerate its export after edits. Export SHA256 `427302982f4834dcb8e6df97d06c5a5392ecf8a234a94fc2b9193992c89a108d`. New ending art/provenance is recorded in the asset register. Existing CC0 music/cues remain; no new dependency/audio download.

## Actual checks and archive

**111 tests PASS**, strict mypy over 80 source files, Ruff lint/format, structure and diff checks. Coverage includes real branch/cross-link wins, capture, replay, sight/hearing, stair validity/occupancy/guard traversal/E repeat, exact sprint/recharge/noise behavior and alpha composition. `tests/unit/core/` now has six direct files; group by subsystem before adding another.

**38 native Cocoa states captured and reviewed** at `output/two-floor-lab/alpha-verified/`; selected screenshots are committed in the review. Security WIN 1507 ticks; Research WIN 1568; deliberate contact CAPTURED 698; real abort/retry/report/map/pause. All seven Sentinel states observed. Optimized inputs are not novice timing/balance evidence. Source audio-enabled WIN renders 1,511 frames, exercises all five music contexts, decodes 16 assets and plays 134 cues. The audio report records actual render/audio/display timing; it excludes simulation update time and is not a minimum-hardware claim.

Clean `123225b` Mac arm64 app and freshly extracted ZIP each PASS all eight native frozen Cocoa checks, audio ready. Python 3.13.16, PyInstaller 6.22.3, macOS 26.4.1 arm64, ad-hoc signed/not notarized. Archive `dist/echo-heist-0.1.0a1-macos-arm64.zip`, **46,287,058 bytes**, SHA256 **`2a91cced913430b643e3dfc540f44ed3c53a69a3f41bffe90c08d64cc32ebbc6`**. [Actual build/smoke record](../../../../quality/reports/two_floor_lab/BUILD.json). Frozen checks cover launch/resources/settings/headless hashes, not a full frozen mission or download/quarantine acceptance.

Actual native commands: `scripts/packaging/build.py`; `scripts/packaging/smoke.py "dist/Echo Heist.app" --output-dir output/two-floor-lab/frozen-app`; fresh `ditto -x -k` to `output/two-floor-lab/extracted-123225b`, followed by smoke on its app under `frozen-extracted`. These use locked uv with `--all-extras`. The build manifest is clean; runtime/test/build paths match `123225b` after documentation-only record edits.

Hosted source CI: [39608091170](https://github.com/khalid999devs/Echo_Heist/actions/runs/39608091170). At integration, Linux and Windows checks/builds passed; hosted macOS remained in runner startup with no steps reported. Local native Mac checks/build/smoke passed. BUILD.json keeps those facts separate; do not claim the queued hosted job passed. Windows interactive hardware/audio/download and Linux native packaging remain NOT_RUN. No development hours or external-player usability result is invented.

## Next owner work

Continue remaining P03 registry/Tracker/replay/cues against these contracts. One Sentinel is autonomous; three posts retain contact behavior. Companion/MCTS, Interceptor/minimax, NEXUS, Workshop and approved scoring remain assigned later work. Glass breaking, doors, hiding and canisters remain P05 as explicitly requested. This handoff completes the requested two-floor/atmosphere/movement revision, not the shared P03 or full V1 gate.
