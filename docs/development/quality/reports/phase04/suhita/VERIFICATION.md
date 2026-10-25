# P04-SR1/SR2/SR3 verification (Suhita)

2026-10-25. Branch `work/suhita-p04`, logic runtime **`e57562b`** (main `65df8b5` + Khalid's `work/khalid-p04` `1d24b4b`, merged as a fast-forward). [Handoff](../../../tracking/handoffs/suhita/day_02/P04.md), [runtime contract](../../../architecture/integration/autonomy/RUNTIME.md), [exact evidence](EVIDENCE.json).

## Where each check actually ran

| Environment | What ran | Result |
| --- | --- | --- |
| Agent Linux container, CPython 3.13.17 | Every test that does not import pygame (unit, mission, perception, persistence, replay): `pytest tests/unit tests/integration/{mission/test_five_zone_mission,mission/test_human_loop,mission/test_companion,perception,persistence,replay}.py` minus the two pygame unit files | **184 passed** |
| same | `scripts/checks/structure.py`, `ruff check .`, `ruff format --check .` (Ruff 0.16.9, not the locked 0.17.1), `mypy --strict` over `ai/ core/ level/ autonomy/ infrastructure/` (mypy 2.3.1, not the locked 1.20.2) | PASS |
| same | `python scripts/experiments/p04_evidence.py --output output/p04/evidence.json --seeds 24` (207 s) | PASS; numbers below |
| Locked `uv sync` environment | Not reproducible in the container: PyPI is blocked by the session proxy (403), so pygame-ce and the locked tool versions were unavailable | **NOT_RUN here** |
| Suhita's physical Windows x64 | Locked checks, full pygame suite (scene/audio/startup/presentation), desktop launch and inspection | **NOT_RUN at handoff** — commands in the handoff; record results below when run |
| Hosted CI (Windows/macOS/Linux) | Runs automatically on push | NOT_RUN until the branch is pushed from Suhita's account |

The pygame-dependent test files (38 test functions before parametrization: scene flow, audio, startup, presentation, input, observation boundary, desktop smoke) were **not executed** by the agent. Two of them were edited only in their expected values: the Core guard's algorithm label (`NONE` -> `ALPHA-BETA`) and the default-security lower-route scene now returns through the Security corridor.

## Algorithm evidence (actual runs, packaged map, tick cap 9,000 for the runner only)

Companion, 24 seeds per preset, Workshop presets as the blueprint defines them:

| Preset | WIN | CAPTURED | TIMEOUT (runner cap) | Median win | Mean confirmed sightings | Mean tool uses |
| --- | --- | --- | --- | --- | --- | --- |
| Ghost | 2 | 18 | 4 | 5,512 ticks | 7.5 | 7.5 |
| Balanced | 11 | 12 | 1 | 5,141 ticks | 14.4 | 11.8 |
| Rush | 8 | 15 | 1 | 2,794 ticks | 9.6 | 8.5 |

- No recording, scripted path or training: each run starts from the briefing and the Companion's own observations. Same seed twice gives the same fingerprint (`repeat_balanced_seed_6_matches: true`).
- Balanced seed 6 (a win): 54 MCTS decisions, mean 3.4 visited alternatives, mean best-child 38.6 of 64 visits; stage totals selections 7,433 / expansions 2,690 / rollout steps 2,995 / backpropagations 3,456 (= 54 x 64).
- Interceptor alpha-beta vs plain minimax on the real lockdown problem from four guard tiles: identical value and post every time; leaves 9-17 vs 23, 6-7 pruned branches. Posts flip between Research Return and Security gate with guard position.
- NEXUS dispatches over the 72 runs: SUPPORT PURSUIT 80, CHECK SOUND 43, INTERCEPT 32, PROTECT EXIT 25.
- Protocol reset: two attempts of security-sector contacts select `REINFORCE_ROUTE:security-control`; the adapted attempt differs; after reset the fingerprint equals the baseline (`reset_matches_baseline: true`).
- Human routes with the full P04 defenders: upper/upper, lower->upper and cross->upper **WIN**; blind lower->lower is **CAPTURED** by the Interceptor holding Research Return.

The raw script output hash is `a492cd19...c2b224`; the committed EVIDENCE.json stores the same data with per-run fingerprints shortened to 16 characters and the run list moved to `companion_runs`.

## Windows results

Pending Suhita's run of the commands in the handoff. Until recorded here, physical Windows display/audio and the locked suite remain NOT_RUN for this branch.
