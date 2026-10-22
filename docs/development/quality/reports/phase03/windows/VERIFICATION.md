# P03-SR1/SR2/SR3 Windows verification

Tester: Suhita's agent on Suhita's own machine, 2026-10-22 (Asia/Dhaka). Branch `work/suhita-p03`; runtime commits through `6e9148b`, built from main `a700359`. Handoff: [P03 owner handoff](../../../../tracking/handoffs/suhita/day_02/P03.md). Results are PASS, FAIL or NOT_RUN exactly as observed.

## Machine and environment

| Item | Actual |
| --- | --- |
| OS | Microsoft Windows 11 Pro 10.0.26300, 64-bit (`Windows-11-10.0.26300-SP0`) |
| Hardware | 12th Gen Intel Core i5-1235U, Intel UHD Graphics, 1920×1080 display (window reported 1536×793 at system scaling) |
| Audio | Realtek High Definition Audio plus Intel Smart Sound devices, status OK |
| Tools | Git 2.51.0.windows.2, uv 0.13.1, CPython 3.13.16 AMD64 from `uv python install 3.13` |
| Locked sync | `uv sync --locked --all-extras --python 3.13`: PASS (22 resolved, 21 checked, lock unchanged) |
| Git identity | `suhitaAurthi <aurthi2020@gmail.com>`; `core.autocrlf=true` (Git for Windows system config) |

The checkout's local "modifications" seen from a Linux shell were CRLF-only; with `core.autocrlf=true` the tree was clean on `main...origin/main` at `a700359` before branching.

Execution note: commands ran natively in Windows from `.cmd` wrappers in the ignored `output/agent-transfer/` folder, logging to `output/windows-p03/`. Logic changes were also iterated on a Linux x86_64 / CPython 3.13.16 workspace; that is recorded only as cross-OS comparison data, not as a Windows result.

## Results

| Check | Command | Result |
| --- | --- | --- |
| Baseline platform | `uv run --locked python -c "import platform; ..."` | PASS: `3.13.16 AMD64` |
| Baseline headless | `uv run --locked echo-heist --headless --seed 1042 --report ...` | PASS, repeatable; schema-7 state hash `d22114eb…` |
| Baseline full checks (main `a700359`) | `uv run --locked python scripts/checks/run.py` | Structure, Ruff, format, mypy PASS; pytest **148 passed, 1 failed** (158 s) |
| Branch full checks (`e2bc229`, same runtime as `6e9148b`) | same | Structure, Ruff, format (239 files), strict mypy (115 files) PASS; pytest **188 passed, 1 failed** (384 s) |
| P03 subset (`6e9148b`) | `uv run --locked python -m pytest -q --durations=15 tests/integration/perception tests/integration/replay tests/unit/navigation tests/unit/intelligence tests/unit/level` | PASS: **89 passed** in 20.5 s |
| Branch headless | `uv run --locked echo-heist --headless --seed 1042 --report ...` | PASS; schema-8 state hash `f4d8bc18…` (event hash unchanged `15a5126f…`) |
| Default-security evidence | `uv run --locked python scripts/experiments/p03_evidence.py --output output/windows-p03/branch/evidence.json` | PASS, exit 0; [EVIDENCE.json](EVIDENCE.json) |
| Interactive desktop | `uv run --locked echo-heist --data-dir .local\suhita-profile` | PASS for launch/menus/heist/capture/retry/audio; see below |
| Native package build/smoke | `scripts/packaging/build.py`, `smoke.py` | NOT_RUN: no packaging/resource/entry-point change in this slice |

The single failing test on both baseline and branch is the pre-existing `tests/smoke/desktop/test_bootstrap.py` subprocess timeout (30 s). A timed rerun of the same command (`--smoke-frames 2`, dummy video, unavailable audio) completed successfully in **37.6 s and 47.7 s**: first logo paint 22–29 ms, but `resource_load_ms` **35,379 and 45,997**. It is a startup resource-preparation duration on this laptop, not a hang and not caused by P03 (it fails identically on untouched main). Owner: Khalid's startup/resource performance (KR). The interactive run measured the same 35.9 s load.

## Default-security scenarios (real four-guard registry, seed 1042)

| Scenario | Outcome / ticks | Decisions by algorithm | Max nodes | Windows wall time |
| --- | --- | --- | --- | --- |
| Upper route, tools | WIN 1514 | A* 47, BFS 95 | A* 41, BFS 68 | 3.09 s |
| Lower route, tools | WIN 1581 | A* 67, BFS 89 | A* 35, BFS 68 | 3.42 s |
| Cross-link route, tools | WIN 1603 | A* 46, BFS 87 | A* 49, BFS 101 | 4.44 s |
| Upper route, no tools | CAPTURED 1174 by `guard-service` | A* 41, BFS 68 | A* 82, BFS 68 | 2.58 s |
| Lower route, no tools | CAPTURED 349 by `guard-research` (Tracker) | A* 18, BFS 28 | A* 35, BFS 68 | 0.82 s |

Every scenario's recorded log replayed exactly (`replay_matched: true`). Decision evidence kinds include SIGHT, radio REPORT leads and fuzzy-graded NOISE cues. Wall times include the scripted driver, replay recording and hashing: about 2 ms per 30 Hz tick on this CPU.

**Cross-OS determinism data point.** The same commit on Linux x86_64 / CPython 3.13.16 produced identical outcomes, tick counts, per-tick event-chain hashes and final schema-8 fingerprints for all five scenarios (for example upper-tools `e26af4a1…` / `2125873e…`, lower-no-tools `6061ff5d…` / `cf4130b9…`). This is one Windows/Linux comparison, not a macOS or general cross-platform claim.

## Interactive Windows session

Real `windows` video driver, windowed, audio **ready** (29 assets loaded, 159 cues played), saved profile `.local\suhita-profile`. Title → settings/back → Play Chapter → Human → Launch Mission all worked with keyboard and mouse. In the heist, F3 showed all four registry guards on one line each (`core PATROL NONE`, `research PATROL A*`, `security/service PATROL BFS`) inside the existing panel. Walking into the Service Wing, the service Sentinel's identification meter rose (`SPOTTED`, 17/18, HUD SUSPICIOUS), then CHASE; while chasing, the Tracker independently showed `INVESTIGATE A*` on the radio report. Standing in sight produced CAPTURED at 00:33; R retried into a fresh run twice (CAPTURED at 00:10 and 00:11 after walking straight into the Sentinel's patrol loop). The game exited with code 0 and reported `outcomes: {"CAPTURED": 3}`, `runs_started: 3`.

These blind keyboard attempts are evidence that sensing, pursuit, capture, results and retry work on this hardware, not a balance judgment. The scripted keyboard-driver scene test `test_default_live_guard_allows_actual_lower_route_core_and_extraction` passed natively with every guard active, and the scenario table above shows each branch is winnable. An interactive Windows **win**, under-desk hiding at the desktop, and fullscreen/resize were NOT_RUN in this session.
