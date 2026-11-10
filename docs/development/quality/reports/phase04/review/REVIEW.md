# PR #5 — P04 runtime review

Khalid, 2026-11-10. Reviewed Suhita's `c99984e` and preserved her commits, algorithms and contracts. PR #6 is a descendant and must include these review fixes before integration. This record covers review/integration, not finished V1 scoring or release acceptance.

## Findings and fixes

- The failing Windows/Mac CI jobs had passed source checks, native builds and frozen smoke; only artifact upload failed with `Artifact storage quota has been hit`. Inventory: 163 stored archives, about 13,086 MiB. Existing archives were not deleted. Uploads now run for main/manual builds only, retain seven days and report archive failure explicitly in annotations/job summary. Tests, compilation and smoke remain required failure-producing steps. A green validation job does not assert a downloadable archive exists.
- The live MCTS panel displayed the first four enum actions, so a chosen action later in the list could disappear. It now prioritizes the chosen action and measured visit counts. No visits/rewards or gameplay decisions are modified. A regression renders a chosen EMP beyond the original four rows and checks its real count/reward remain visible.
- Added `tests.fixtures.autonomy.live_capture`, a production-gateway native review driver. It uses ordinary deployment/input, actual AI and real outcomes; no actor position, score, telemetry or terminal state is injected.

## Actual evidence

- Original branch `python scripts/checks/run.py`: **277 tests**, structure/Ruff/format/mypy PASS on this Mac. The added panel regression: **3/3** focused contract tests PASS. Final updated branch checks and hosted results are verified before merge.
- `python scripts/experiments/p04_evidence.py --output output/pr-review/p04-evidence.json --seeds 2`: real Balanced **2/2 wins**, Ghost **0/2**, Rush **0/2** (actual captures); repeated seed matches. All four tested Interceptor positions have alpha-beta/minimax value/post parity, with 6–7 pruned branches. Memory adaptation changes the run and reset reproduces baseline. Human upper/upper, lower/upper and cross/upper win; blind lower/lower is captured as recorded by Suhita.
- `python -m tests.fixtures.autonomy.live_capture --output output/pr-review/p04-native`: native **Cocoa/audio ready**, real Companion **1042 WIN at 2463**, **4 CAPTURED at 1180**. Fourteen screenshots cover Workshop, actual F2 decisions/Interceptor search, NEXUS, lockdown, outcomes, pause and confirmed UI memory reset. Pause leaves the fingerprint unchanged. Actual Verify Echo protocol appears after evidence-bearing attempts; confirmation clears it.
- Inspected the actual Companion, Interceptor and protocol screens. Interceptor native capture reports its actual depth 3 / 13 evaluated / 4 pruned result; no missing trace is zero-filled. Raw screenshots/JSON/logs stay ignored under `output/pr-review`.

## Boundaries

Preserve schema **11** for this P04 checkpoint; P05 introduces **12**. No score, melee, map, AI policy or simulation rule is changed by these fixes. P04 connected presentation has now been exercised against actual runtime data. Ghost/Rush tuning and the previously recorded rare narrow-corridor body-block remain P07 hardening work; this review does not promise every policy/seed wins or complete that whole-game gate. P05 lifecycle tests/native review are separate. Physical Windows gameplay and final primary-download/credits/media acceptance remain separately recorded.

Follow-up runner failure: GitHub cancelled both Mac jobs before execution with `The configuration 'macos-14-arm64-us-default' is not supported`. [GitHub's runner-images reference](https://github.com/actions/runner-images/blob/main/README.md) records macOS 14 retirement on 2026-11-02 and supports `macos-15` for arm64. Updated the pinned Mac label to `macos-15`; architecture verification remains mandatory. Updated P04 full source checks pass **278 tests in 38.66 s**. The canceled infrastructure job is not recorded as a successful Mac test.
