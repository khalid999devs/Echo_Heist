# P06–P08 SR verification (Suhita)

2026-11-11. Branch `work/suhita-p06-p08`, runtime **`765a164`** (stacked on `work/suhita-p05` a6ddbee). [Handoff](../../../../tracking/handoffs/suhita/day_04/P06_P08.md), [runtime contract](../../../../architecture/integration/experience/RUNTIME.md), [policy comparison](../../../experiments/POLICY_COMPARISON.md), [Windows QA checklist](../../phase08/suhita/WINDOWS_QA.md).

## Where each check ran

| Environment | What ran | Result |
| --- | --- | --- |
| Locked `uv` environment on the Linux shell of Suhita's computer (CPython 3.13.16, pygame-ce 2.5.8, SDL dummy video/audio) on `E:\Echo_Heist` at `765a164` | structure, `ruff check`, `ruff format --check`, `mypy` (185 files) | PASS |
| same | full `pytest` in two parts (unit + audio/persistence/replay/perception/experiments/smoke: 249; mission + presentation: 78) | **327 passed** |
| same | 96-run comparison in two 12-scenario halves | all 96 records identical to the container run |
| Agent container (CPython 3.13.17, non-locked tools) | full 96-run comparison; 4-scenario hash check | hash `279ce530…8f82e40`; 4-scenario hash `2eb0c8e5…23673c0` also matched on Suhita's computer |
| Physical Windows desktop, 2026-11-16, at `59ed6ff` (merged with main) | native locked checks, 4-scenario comparison, build, frozen smoke, 8 checklist steps in the packaged game | structure/Ruff/format/mypy PASS; **327 passed, 1 failed** (bootstrap smoke 30 s timeout, slow startup on this machine for every commit); 16/16 runs identical; build PASS; smoke 9/9 PASS with real video/audio; [checklist](../../phase08/suhita/WINDOWS_QA.md) |
| Hosted CI / packaged builds | on push / Khalid's P08-KR1 | NOT_RUN here |

## After merging main (2026-11-16)

`59ed6ff` merges main `34d68cf` (P04/P05 merged, Khalid's connected review and robot lighting). No simulation, AI, level or data file changed. Linux shell, locked environment: structure, Ruff, format, mypy (189 files) PASS; **328 tests pass** (run in four parts because of the shell's time limit: unit+smoke 188, integration excluding mission/experiments 95, mission 42, experiments 3). The four-scenario comparison is run-for-run identical to the recorded CSV; its hash is `2eb0c8e5…` when the old commit ID is substituted (the commit is part of the hash).

## Evidence by slice

**P06-SR1 scoring** — `tests/unit/core/scoring/`: the published example table (0–4+ encounters at 1× and 2× reference), grade boundaries 59/60, 74/75, 89/90, scores clamped to 50–100 over many inputs, every success grade reachable, pace bounds (10 at/below reference, 5 at twice, 0 for huge times, zero duration safe, never increasing), failures 0/F with no subtotals or achievements, identical function for both modes, achievements never change points, packaged rules equal the approved version and other weights are refused. Encounter state machine: two guards on one tick and continuous sight count once, a short break inside the TTL keeps it, a grab keeps it open, expiry then a new sighting counts again, a stale relayed timestamp cannot reopen it. In a live sentinel fixture (both controller kinds) an EMP does not reset the encounter and the abort report is 0/F with one encounter; hearing sprinting through a wall plus an unseen Echo give zero. The real Human mission win is now 100/S.

**P06-SR2/SR3 services** — `tests/integration/persistence/test_experience.py`: a Human abort and a Companion win (seed 1) through the real gateway give matched 0/F and scored reports (50 + 40 − 12·encounters + pace, AI Master, label "Balanced", policy ID, decisive events), one report per run key, unknown attempts get none, history survives a new process newest-first; profiles save/overwrite-by-name/32-limit/name validation/delete/unknown delete/restart, custom profile name used as report label; each of the three files is quarantined once when damaged and never overwritten when newer; preferences round-trip; the NEXUS switch persists. `tests/integration/presentation/experience/test_real_services.py`: Khalid's Flow with both real gateways shows the service's report (not the runtime's), history and profiles, and loads saved preferences. Workshop preset buttons equal the backend presets.

**P07-SR1/SR2** — `tests/integration/experiments/test_harness.py`: 24 scenarios across all 11 categories construct valid starts (tile, stock, lockdown); records repeat exactly; the same seed with Ghost vs Rush changes fingerprint and decisions; regression for the guard deadlock (s06 no longer times out). The in-game algorithm guide now describes what runs (Interceptor alpha-beta, 64-simulation MCTS, NEXUS dispatch and protocols, lockers/doors/noisy props) instead of "planned" features.

**P08-SR2** — the full matrix and analysis are in the [comparison report](../../../experiments/POLICY_COMPARISON.md): 96 runs, no timeouts, per-policy and per-category results, failure locations, a same-seed policy-change example, algorithm totals and tick timing.

## Changed expectations

- Fingerprint schema 13; replay test updated.
- `tests/integration/mission/test_human_loop.py`: a real win now has an approved score (100/S) instead of none.
- `tests/integration/presentation/experience/test_controls.py`: an abort without the history service now shows the Simulation's own 0/F report instead of "unscored".

## Not verified

Human-play checklist steps on Windows (wins, capture/retry, props, calibration), hosted CI, packaged builds, Khalid's KR visual acceptance of the real reports/profiles/preferences and of the guide text, and the Human side of pace calibration.
