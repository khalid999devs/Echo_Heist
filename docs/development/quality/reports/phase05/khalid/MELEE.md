# Limited-melee verification

2026-10-30. Branch `work/khalid-p05-visuals`, runtime **`68d0c69`**, [approved rules](../../../../planning/balance/MELEE.md), [runnable handoff](../../../../tracking/handoffs/khalid/day_03/MELEE.md), [exact evidence](MELEE_EVIDENCE.json). This user-authorized balance update supersedes the unlimited melee and fingerprint-9 details in the earlier presentation checkpoint; those older measurements remain historical.

## Applied rules and boundaries

Two charges per attempt, no refill; 120-tick/four-second recovery; existing 45-tick stun, 60-tick post-stun immunity and one six-tile impact noise per valid strike. A resisted strike still spends a charge/recovery and makes noise. Invalid requests spend nothing, start no recovery and make no gameplay noise. Both intruder actor kinds use identical rules. The HUD displays actual charges/recovery and distinct rejection messages.

Existing acoustic sensing/fuzzy investigation/original-time evidence expiry provides the consequence. The integration check demonstrates a nearby guard hearing the impact around a wall, investigating its original tile while the intruder moves away, and a distant guard hearing nothing. At default 30 Hz, evidence remains fresh through 150 ticks and expires afterwards. No moving-location reveal, universal alert, confirmed-sighting event from sound alone or scoring change is added.

The new inventory, ready-at timer and rule enter **fingerprint schema 10** and the replay header. Changed hashes are expected. Old schema-9 replay logs must not be passed off as current matches. Controller deployment/startup and other P04/SR lifecycles are unchanged.

## Commands and actual results

All commands used `uv run --locked --cache-dir .cache/uv`. Native commands used Cocoa and normal audio initialization.

| Command suffix | Actual result |
| --- | --- |
| `python scripts/checks/run.py` | PASS: structure, Ruff, 291 formatted Python/config files, strict mypy (136 source modules), **226 tests in 28.14 s** |
| `pytest -q tests/unit/core/abilities tests/integration/perception/test_melee_consequences.py tests/unit/core/test_tools.py tests/unit/presentation/test_interactions.py` | PASS: 20 focused checks in 0.46 s |
| `python scripts/experiments/p03_evidence.py --output output/melee-balance/replay.json` | PASS: three successful routes (1513 / 1581 / 1603 ticks), two careless captures (1174 / 349), all five replay exactly under schema 10 |
| `python -m tests.fixtures.interactions.melee_capture --output output/melee-balance/hud` | PASS: eight native states; actual 2→1→0 stock, 120→119→0 recovery, rejection/pause/retry; 33 audio assets, 13 cues played |
| `python scripts/quality/defenders/capture.py --output output/melee-balance/human-native` | PASS: real Human upper WIN 1483, lower WIN 1604, careless CAPTURED 694; both decks, actual four-guard behavior, hiding and read-only diagnostics |
| `--all-extras python scripts/packaging/build.py` | PASS: clean-tree Mac arm64 app/ZIP at `68d0c69`, ad-hoc signing verified |
| `--all-extras python scripts/packaging/smoke.py 'dist/Echo Heist.app' --output-dir output/melee-balance/native-app` | PASS: **9/9**, Cocoa, normal audio ready, source/frozen deterministic hashes match |
| `--all-extras python scripts/packaging/smoke.py 'output/melee-balance/extracted-final/Echo Heist.app' --output-dir output/melee-balance/native-zip` | PASS: fresh `ditto -x -k` ZIP extraction, **9/9**, Cocoa/audio ready |

Ten added regression cases cover exact commit-tick recovery, no refill, Human/Companion parity, illegal/stale/multiple/malformed actions, valid resisted cost without stun extension, capture interruption and legitimate/expired hearing evidence. Existing immunity/presentation isolation tests explicitly use a short diagnostic cooldown to exercise resistance independently; the new normal-configuration tests verify the shipped four-second rule.

Native screenshots were inspected for readable charge/countdown labels, recovering/empty messages and unchanged layout. The practice fixture disables guard AI only; it does not prove a Companion planner. The separate native mission sweep and replay scenarios use normal defenders. No new cosmetic per-file test suites or image assets were added.

[Runtime CI run 41048163778](https://github.com/khalid999devs/Echo_Heist/actions/runs/41048163778) passes all three jobs: Linux source/headless and Windows x64/macOS arm64 checks, native builds and frozen dummy-video smoke. The local app/fresh ZIP both pass 9/9 real-display checks with audio ready.

The current Mac ZIP is 112,443,582 bytes; SHA-256 `d046610d18de1b81c2fd6514a05dd5c1d652624aa3bc52c27250d628c7058fbc`, clean runtime `68d0c69`. The build manifest's initial smoke marker is historical; the separate successful smoke reports are authoritative. The earlier `59fffba` archive record remains historical, and the local `dist` path now contains this melee update. Detailed results/digests are in MELEE_EVIDENCE.json. Hosted Windows/Mac package smoke is separate from physical Windows play/audio; Linux desktop packaging and P08 release gates remain unverified. This change does not complete shared P04/P05 or V1.
