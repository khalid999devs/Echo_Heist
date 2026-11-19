# Four-policy comparison on 24 scenarios (P08-SR2)

2026-11-11, Suhita. Candidate commit **`765a164`** on `work/suhita-p06-p08`. Suite `vault-five-zone/v1` ([registry](../../../../src/echo_heist/resources/data/experiments/scenarios.json)), 24 scenarios × Ghost, Balanced, Rush, Custom = **96 real Companion attempts**, all with props, scoring, NEXUS memory at its reset baseline, runner tick cap 9,000. Compact data: [summary JSON](policy-comparison-summary.json), [per-run CSV](policy-comparison-runs.csv).

Regenerate:

```sh
uv run --locked python scripts/experiments/comparison.py --output-dir output/p08/comparison
```

## Reproducibility

- Deterministic hash `279ce5309092a7bf0e1ae2ade1c229e54788cad44d9387b819a27108e8f82e40` (agent container, CPython 3.13.17, 210.5 s).
- The same 96 records were produced again in the **locked environment on the Linux shell of Suhita's computer** (CPython 3.13.16), run in two halves of 12 scenarios: every record identical, metadata identical.
- Repeating the first run gives the same fingerprint (`repeat_first_run_matches: true`). An earlier full run at `dc9023b` (before test/doc-only commits) produced exactly the same 96 records.
- Metadata recorded: commit, `uv.lock` hash (line endings normalized), map/rules/sensor/prop/scoring hashes, scoring version 1, pace reference 27,000 ticks, registry revision, RNG stream.

## Results

| Policy | Wins | Captured | Timeout | Median win (ticks) | Grades (A/B/F) | Mean encounters | Mean Echo/EMP/melee used |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ghost | 3 / 24 | 21 | 0 | 2,921 | 0 / 3 / 21 | 2.08 | 1.88 / 0.83 / 1.79 |
| Balanced | 8 / 24 | 16 | 0 | 1,700 | 4 / 4 / 16 | 2.08 | 2.58 / 0.92 / 1.38 |
| Rush | 13 / 24 | 11 | 0 | 1,460 | 10 / 3 / 11 | 2.00 | 2.71 / 0.83 / 1.42 |
| Custom | 11 / 24 | 13 | 0 | 1,898 | 6 / 5 / 13 | 2.38 | 2.54 / 0.92 / 1.42 |

Wins per category (paired: same scenario seed/start for every policy):

| Category | Ghost | Balanced | Rush | Custom |
| --- | --- | --- | --- | --- |
| patrol-timing | 1/4 | 1/4 | 0/4 | 2/4 |
| route-upper | 1/2 | 1/2 | 1/2 | 0/2 |
| route-lower | 0/2 | 0/2 | 1/2 | 1/2 |
| junction | 0/2 | 1/2 | 2/2 | 1/2 |
| partial-vision | 0/2 | 2/2 | 2/2 | 2/2 |
| heard-only | 0/2 | 0/2 | 2/2 | 0/2 |
| stale-sighting | 0/2 | 0/2 | 0/2 | 0/2 |
| capture-threat | 0/2 | 0/2 | 2/2 | 1/2 |
| scarce-tools | 0/2 | 0/2 | 0/2 | 0/2 |
| core-theft | 0/2 | 1/2 | 2/2 | 2/2 |
| lockdown-return | 1/2 | 2/2 | 1/2 | 2/2 |

- No run hit the runner cap. Before the P07 guard give-way fix, `s06-upper-stairs-late` timed out because two guards deadlocked in the core corridor.
- All four policies lose `s02`, `s06`, `s15`, `s16`, `s19` and `s20`; only `s23` (starting in lockdown beside the Core) is won by all four.
- Captures by guard and place (61 total): service Sentinel in the Service Wing 13 (plus 1 at the entry); research Tracker in the Service Wing 10, in corridors 6, in the core chamber 5, on its floor 4, at the entry 4, in Security 2; Interceptor in the core chamber 8 (plus 2 elsewhere); security Sentinel 6.
- 819 raw confirmed sightings collapse into 205 team detection encounters. No successful run had zero encounters, so no run reached S or earned Ghost, and none fell to C.

## Policy-sensitive behavior (same seed, same start)

`s05-upper-stairs`: Ghost WIN in 5,252 ticks (B, 6 encounters) after 28 Advance / 9 Hide / 10 Wait decisions and 15 zone changes; Balanced WIN in 1,401 (A, 2 encounters; 15/2/1); Rush WIN in 1,529 (A, 1 encounter; 20 Advance / 1 Wait); Custom CAPTURED at 1,992 (3 encounters). The Workshop blocks change real MCTS rewards and A* risk costs, which shows up as different routes, waiting and outcomes.

## Algorithm evidence across the 96 runs

- MCTS: 1,753 Companion decisions, mean 3.65 alternatives with visits per decision.
- A*: 181,597 nodes expanded by the Companion's observed-risk planner; 46 plans found no path (the controller then waits and replans).
- Interceptor alpha-beta: 1,781 searches, 21,561 evaluated nodes, 12,833 pruned branches (minimax parity is in the P04 evidence).
- Sentinel fuzzy inference: 17,177 decisions carried a Sugeno urgency.

## Performance (wall clock, excluded from the hash)

Per-tick time including all AI: median per-run p95 **3.07 ms** in the container, **2.93 / 2.37 ms** for the two halves on Suhita's computer (worst per-run p95 11.0 ms). One tick is 33.3 ms at 30 Hz. Rendering is not included; frame-time profiling belongs to Khalid's P07-KR2.

## Pace calibration input (not applied)

Successful runs took 878–5,252 ticks (median 1,582 ≈ 53 s); Balanced wins 901–3,788. The scripted P04/P05 Human routes take about 1,450–1,600 ticks. With the draft reference of 27,000 ticks every win scores the full 10 pace points. SCORING.md asks for one shared reference from successful Human **and** Balanced runs; the Human side needs real playtest times (P08-SR1 step 15), so the draft value stays until then. Any new reference must be recorded with the scoring version.

## Limits of this evidence

These are controlled scenario comparisons on one map, not proof that a preset is generally better. Win rates are low in several categories; balance tuning is outside the functional phases. Physical Windows play, frame timing and packaged builds are reported separately.
