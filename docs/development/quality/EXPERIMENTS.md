# Reproducible AI and academic evidence

Blueprint basis: pp. 9-14, 18. Status: experiment design only; no results exist.

Eight-phase schedule: P03/P04 introduce real telemetry/algorithm evidence; P06 verifies saved policy-sensitive choices; P07 supplies Khalid's harness and Suhita's scenario/metadata fixtures; P08 assigns Suhita the full matrix execution/analysis and Khalid the technical reproducibility review. Preserve the full denominator under time pressure and report incomplete runs explicitly.

## Experiment protocol

Use a versioned suite of 24 deterministic scenarios as an initial choice within the PDF's 20-30 range. Cover initial patrol timing, upper/lower routes, junction decisions, partial vision, heard-only cues, stale sightings, nearby capture threats, scarce tools, core theft and lockdown return. Scenarios share the canonical rules/map or clearly identified reduced algorithm fixtures; do not confuse a fixture result with full-mission performance.

Evaluate Ghost, Balanced, Rush and one saved user-tuned policy on identical scenario seeds, with NEXUS memory reset and the same map/balance version. That yields 96 initial policy-scenario runs. Set a generous tick cap only for the test runner: a cap hit is `TIMEOUT/STALLED` evidence, not a new in-game mission deadline. Report success/failure/timeouts separately. Keep the original tuning suite and a small held-out set distinct when iterating policies.

Do not cherry-pick only successful seeds. Preserve the full denominator and failure causes. These are controlled scenario comparisons, not proof that a preset is universally superior. If measuring robustness with additional seeds, report how those seeds were selected and keep policy comparisons paired.

## Required output

| Category | Metrics |
| --- | --- |
| Outcome | Mode, win/capture/abort/timeout, simulation duration, capture guard/sector, decisive events |
| Behavior | Raw confirmed sightings, shared detection encounters, time waiting/stalled, route choice, gadgets spent, approved score/grade and completion/stealth/pace subtotals |
| Navigation | Algorithm calls, nodes expanded, path cost/length, no-path/replan counts |
| Sentinel | Fuzzy input memberships, firing rules, urgency and FSM transitions |
| Interceptor | Search depth, evaluated/pruned nodes, candidate post values, selected post, physical arrival |
| Companion | MCTS iterations, per-action visits/mean reward, chosen action, utility override and reason |
| Performance | Tick/search elapsed distributions, frame data where relevant, hardware/runtime metadata |

Store full run headers as specified in [data contracts](../architecture/DATA_CONTRACTS.md), including initial NEXUS memory, policy/map/config hashes, RNG scheme, commit and lock. Separate deterministic decision telemetry from nondeterministic profiling durations so timing does not spoil replay comparison.

Record the [approved scoring version](../planning/SCORING.md) and pace-reference ticks too. Compare policies against the same reference; changing calibration must not silently change scores within a comparison. Tool usage is an analytical metric, not a direct score penalty.

Compare ordinary minimax against alpha-beta on the same small tactical trees with identical move ordering/depth. Require equivalent evaluation/selected value and demonstrate fewer evaluated nodes on trees that permit pruning. Ties may select different equal-valued legal posts unless the implementation fixes a common tie order; record that rule. An alpha-beta label alone proves nothing.

For MCTS, show actual alternative visit/reward statistics, all four search stages and legal-action filters. Display at least three alternatives in Lab View when three are legally available; never fabricate extra alternatives in constrained states. For fairness, preserve an observation snapshot that explains the choice without privileged world state.

## Analysis and evidence package

Generate a per-run CSV/JSON and human-readable summary with per-policy win rate, time for completed runs, detections/tools and timeout counts. Pair differences by scenario; list important failure cases, not only averages. Include a same-seed policy-change example and a reset-memory reproducibility check. Report protocol-on adaptation tests separately from the memory-reset baseline.

Keep reports under `docs/development/quality/experiments/` when results exist; retain large raw logs as linked build/release artifacts with hashes. The public source must include the seed list, runner and command needed to regenerate the report. Record a command only after that CLI actually exists and has been run.

## Demonstration video outline

1. Show version and first-launch access to Human and Companion modes.
2. Demonstrate core theft, mandatory lockdown, successful extraction and a fair capture/escape case.
3. Show Companion autonomy without a recording or training prerequisite.
4. Open actual algorithm evidence: BFS/A*, fuzzy rules, Interceptor alpha-beta and MCTS alternatives.
5. Change Workshop settings, retry the same seed with memory reset, and explain a real behavior change and the result report.
6. Show reproducible experiment summary, GitHub source/test instructions and itch.io downloads.

Use the final candidate, label any edited/time-compressed footage, and keep logs backing the decisions shown. Match academic rubric requirements when supplied; video duration and submission deadline are currently unspecified.
