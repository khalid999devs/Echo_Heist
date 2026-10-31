# P04 Khalid presentation verification

2026-10-25, macOS 26.4.1 / Apple Silicon / Python 3.13.16. Branch `work/khalid-p04`, source `77bcf00d42e824f7b1645033a1b09495a03bc311`, contracts `926d085`. Main remains `65df8b5`. [Draft PR #2](https://github.com/khalid999devs/Echo_Heist/pull/2), [runnable handoff](../../../../tracking/handoffs/khalid/day_02/phase04/P04.md), [exact evidence](EVIDENCE.json).

**Independent KR1/KR2 presentation is implemented and verified. Live-data acceptance is still IN_PROGRESS:** no Suhita P04 runtime/branch was published at this checkpoint. Synthetic QA does not close her algorithms, KR live acceptance or the shared P04 gate.

## Working implementation

- Typed immutable policy/deployment/telemetry ports; actual-actor follow camera, movement and stair art; spectator-only Companion input. Human remains the verified default. Deployment validates actual mode/actor, initial tick, map and tick rate before opening a new attempt.
- F2 Companion/NEXUS/Interceptor tabs display supplied decision times, actual visit/reward values, reported path/cost/expanded nodes, utility reason, evidence tasking and evaluated/pruned minimax metrics. No renderer runs an algorithm or queries hidden positions to invent a trace.
- Workshop policy selection, real protocol summary, explicit reset confirmation/backend success or failure, and review before retry. Cached telemetry is read-only; pause/map/settings/entrance do not step the runtime. NEXUS announcements use original timestamps and one explicit audio serial per repeated record.
- Existing full-display pointer mapping, guard F3 view, Human controls, physical map, scoring and fingerprint **9** are preserved. Teaching panels remain behind stair cinematics; unavailable Companion browsing preserves Human selection.
- No new assets, dependencies, music or license obligations. Fixtures live only under root `tests/`; they are not imported by application code or used by default deployment. Label/Surface caches are bounded. Full performance/memory acceptance remains P07.

## Commands and actual results

All `uv` commands below used `--locked --cache-dir .cache/uv`. Native commands used Cocoa display and normal audio, without dummy video or mute.

| Command after `uv run --locked --cache-dir .cache/uv` | Actual result |
| --- | --- |
| `python scripts/checks/run.py` | PASS: structure limits, Ruff, 269 formatted files, strict mypy 129 source files, **207 tests in 26.66 s** |
| `python -m pytest -q tests/integration/mission/test_five_zone_scene.py::test_mode_selection_does_not_launch_and_back_does_not_start_a_run tests/integration/presentation/test_autonomy.py` | PASS: 8 focused cases in 10.97 s |
| `python scripts/experiments/p03_evidence.py --output output/phase04-presentation/human-replay.json` | PASS: five scenarios exactly match P03 outcome, ticks, event-chain hash and final fingerprint; each replay matches |
| `python scripts/quality/defenders/capture.py --output output/phase04-presentation/human-native` | PASS: native actual Human upper WIN at 1483 ticks, lower WIN at 1604, careless CAPTURED at 694; unseen under-desk hiding and read-only F3 |
| `python -m tests.fixtures.autonomy.capture --output output/phase04-presentation/final-native` | PASS: **34 labeled presentation states**, both robot stair directions/decks, policy/reset/error, panels, pause/map/settings/review and three actual display layouts |
| `--all-extras python scripts/packaging/build.py` | PASS: clean-tree native arm64 app/ZIP, ad-hoc signing verified; source `77bcf00` |
| `--all-extras python scripts/packaging/smoke.py 'dist/Echo Heist.app' --output-dir output/phase04-presentation/native-app` | PASS: **9/9**, Cocoa, audio ready, startup/resources/settings and source/frozen hashes match |
| `--all-extras python scripts/packaging/smoke.py 'output/phase04-presentation/extracted-final/Echo Heist.app' --output-dir output/phase04-presentation/native-zip` | PASS: fresh `ditto -x -k` ZIP extraction, **9/9**, Cocoa and audio ready |

The 207-test suite includes twelve new cases for typed measured/unknown rewards and immutability, unavailable/mismatched deployment, active actor/spectator boundaries, read-only panels and paused map, policy-preserving retry, confirmed reset/failure, mode-specific Human control/protocol review and once-per-announcement audio. It does not create tests just for each visual helper.

Native Human sweep at presentation checkpoint `b20585f`: 40 captured states, 4010 rendered frames, actual no-sight EMP fuzzy inference (urgency 0.95), physical room review and all four guard-tab pointer selections. Final `77bcf00` adds mode-scoped protocol review and its two regression cases; default Human/simulation/rendering behavior is unchanged. Source timing render/audio/present median 4.84 ms, p95 16.28 ms, max 115.48 ms. Simulation is excluded; screenshot/display changes are included. These are scoped observations, not an FPS guarantee.

Synthetic sweep: 405 rendered frames; median 6.87 ms, p95 7.84 ms, max 14.91 ms under the same timing limitation. Actual displays: 1366×768 (logical 1281×720), OS-clamped 1440×820 (1280×729), fullscreen 1470×923 (1280×804). Reviewed deployment, reset failure/success, actual-ID robot animation/camera, three tabs, stairs, review/retry and fullscreen spacing.

**The synthetic fixture supplies fake search/protocol values for layout testing and ordinary scripted actions to real Simulation.** Its real simulated WIN tests UI flow, not autonomous planning. Every injected capture is visibly stamped `SCRIPTED QA FIXTURE / NOT ALGORITHM EVIDENCE`. The default application ships no fake controller or gateway.

## Hosted and native artifacts

[Runtime CI run 40139741234](https://github.com/khalid999devs/Echo_Heist/actions/runs/40139741234): all three jobs PASS at `77bcf00`: Linux source/headless checks; Windows x64 and macOS arm64 checks/native build/frozen dummy-video smoke. **Physical Windows gameplay/audio is NOT_RUN** for this branch. Optional Linux native packaging is NOT_RUN.

Local `dist/echo-heist-0.1.0a1-macos-arm64.zip`: 112,218,809 bytes; SHA-256 `59cf47f0a211e2a62a52c2ca0dd386ec5fe0c0a2c019f48d6bec529a937db7c0`. Ad-hoc signed, not notarized. Manifest records a clean tree at `77bcf00`; later documentation commits do not change that runtime. Its manifest's original smoke marker is historical; the two separate successful smoke reports above are the actual results.

The package is an interim Human-playable development build with the new unavailable-until-connected Companion UI. It is not full V1 or a completed P04 autonomous build. Source/raw logs/captures stay in ignored `output/phase04-presentation/`; compact hashes, outcomes, metrics and manifest are retained in `EVIDENCE.json`.

## Remaining connected acceptance

Suhita must implement SR1/SR2/SR3, construct/inject the real gateway, and verify genuine autonomous win/capture, belief-only search, minimax parity/physical post travel, evidence-limited tasking and versioned persistence/reset. Then run Khalid's F2/camera/stair/reset visual gate against actual records. Keep both Human routes/capture intact. P06 saved profiles/scoring and P05 object lifecycles are outside this branch. No main merge or phase completion is recorded here.
