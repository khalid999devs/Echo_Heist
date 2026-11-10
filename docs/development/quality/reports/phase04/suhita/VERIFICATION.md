# P04-SR1/SR2/SR3 verification (Suhita)

**2026-11-05 (Asia/Dhaka).** Branch `work/suhita-p04`, verified runtime **`61c29a5`**: the 2026-10-25 SR runtime merged normally with current main `1136788` (merge `cd69baf`) plus limited-melee adaptation, liveness fixes and fingerprint schema 11. [Handoff](../../../../tracking/handoffs/suhita/day_02/P04.md), [runtime contract](../../../../architecture/integration/autonomy/RUNTIME.md), [Windows evidence](EVIDENCE.json). The 2026-10-25 container-only record (184 non-pygame tests, Balanced 11/24 with unlimited melee) is superseded.

## Where each check actually ran

| Environment | Command | Result |
| --- | --- | --- |
| Suhita's Windows 11 x64 laptop (10.0.26300, i5-1235U, Intel UHD, Realtek HD Audio), CPython 3.13.16, uv 0.13.1 | `uv sync --locked --all-extras --python 3.13`; `uv run --locked python scripts/checks/run.py` | **PASS**: structure, Ruff, 353 formatted files, strict mypy 169 modules, **277 tests in 85.3 s** |
| same | `uv run --locked python scripts/experiments/p04_evidence.py --output output/windows-p04/evidence.json --seeds 24` | PASS, 111 s; deterministic hash `88ba3ab7…8f3cd2`; numbers below |
| same | `uv run --locked --all-extras python scripts/packaging/build.py` | PASS: `dist/EchoHeist/EchoHeist.exe` 3,506,890 bytes, SHA256 `6a9894e0…249ca2`; ZIP 111,152,129 bytes, SHA256 `91761b48…ab193a`; PyInstaller 6.22.3, unsigned. Manifest marks `working_tree_dirty: true` (one uncommitted Markdown contract file; runtime source equals `61c29a5`) |
| same | `uv run --locked --all-extras python scripts/packaging/smoke.py dist/EchoHeist/EchoHeist.exe --output-dir output/windows-p04/native-smoke` | **PASS 9/9**, `video_driver: windows`, audio `ready`, 33 audio assets, startup 6.16 s (resource load 5.55 s, frame gap p95 25 ms). The earlier 35–46 s laptop startup did not recur |
| same | `uv run --locked echo-heist --data-dir .local/p04-inspect-20261105-221806` (fresh profile) | Launched by the script; Suhita's observations of physical play/display/audio were **not reported back**, so they remain **NOT_CONFIRMED** here |
| Agent Linux VM (locked env, CPython 3.13.16, dummy SDL) | Full suite in chunks, static checks, preset sweeps | 277 passed; static checks PASS; Balanced 30/48 over seeds 0–47 |
| Hosted CI | Runs on push | Pending the push |

## Algorithm evidence (Windows run, packaged map, 24 seeds per preset, runner cap 9,000 ticks)

| Preset | WIN | CAPTURED | Runner cap | Median win | Mean confirmed sightings | Mean tool uses |
| --- | --- | --- | --- | --- | --- | --- |
| Ghost (Safest/Hide/Escape/Cautious) | 1 | 22 | 1 | 4,978 ticks | 4.25 | 4.33 |
| Balanced (default) | **16** | 8 | 0 | 2,058 ticks | 5.29 | 5.75 |
| Rush (Shortest/Echo/Melee-first/Bold) | 5 | 18 | 1 | 2,090 ticks | 6.67 | 5.92 |

- Each run starts from the briefing and the Companion's own observations; no recording, Human path or QA fixture. Per-seed outcomes on Windows are identical to the Linux VM sweep, and a repeat of Balanced seed 0 reproduces its fingerprint.
- Real MCTS: 1,627 decisions, each exactly 64 simulations (104,128 backpropagations = 1,627 × 64), 204,948 selections, 86,700 expansions, 107,091 rollout steps. Balanced seed 0 (a win at tick 2,025): 21 decisions, mean 3.5 visited alternatives, mean best child 38.9 / 64 visits.
- Captures across all 72 runs: Research 27, Security 13, Core/Interceptor 4, Service 4.
- Interceptor alpha-beta vs minimax on the real lockdown problem from four guard tiles: identical value and post every time; 9–17 leaves vs 23, 6–7 pruned branches; the post flips between Research Return and the Security gate with guard position.
- NEXUS dispatches: CHECK SOUND 55, INTERCEPT 36, SUPPORT PURSUIT 34, PROTECT EXIT 18.
- Protocol reset: two attempts of security-sector contacts select `REINFORCE_ROUTE:security-control`; the adapted attempt differs; after reset the fingerprint equals the baseline.
- Human routes with the full P04 defenders and two melee charges: upper/upper, lower→upper and cross→upper **WIN**; blind lower→lower is **CAPTURED** at the Research Return gate the Interceptor searched and physically holds.
- Default seed 1042 (Linux VM): Balanced takes the Core at tick 1,000 and **wins** at tick 2,463; Ghost and Rush are genuinely captured.

## Merge-specific findings and fixes

- After the merge the old Companion won **0/24** Balanced seeds: its wins had depended on unlimited melee (5–13 strikes per run). It now plans strikes only with its own charge and finished recovery (utility, MCTS root and rollouts).
- Measured fixes: consistent MCTS leaf exposure; non-cautious press-on/sprint while infiltrating; three liveness fixes (gate-holding Interceptor, grab/escape alternation, ALTERNATE commitment). Two candidate changes were measured and **rejected** (EMP reservation, escape-cycle counting) because they lowered win rates.
- Remaining runner-cap cases: one Rush seed where two guards body-block each other in a gate (pre-existing shared P03 steering), one slow cautious Ghost run.

## New or changed tests

`tests/unit/intelligence/test_companion_tools.py` (own melee stock/recovery in utility; rollout spend/recovery), `tests/integration/presentation/test_companion_runtime.py` (real gateway through Workshop on a fresh profile), `tests/integration/mission/test_companion.py` (re-pinned win/capture seeds; formerly stalled seeds 1042 and 34 must win), `tests/integration/replay/test_guard_replay.py` (schema 11; Interceptor's searched/held gate).

## Still open

Khalid's connected KR1/KR2 visual acceptance, the combined P04 gate, Suhita's physical play/audio confirmation and hosted CI on the pushed branch.
