# P07 - Integration, deterministic evidence and usability

Day 4, first block. Integrator: **Khalid**. Effort: Khalid 9, Suhita 11. Status: TODO. Prerequisite: P06. Feature anchors: EH-026 and harness/fixtures portion of EH-027. Source: PDF pp. 15-19.

## Inputs

Read P06's complete build/controls/known issues, [test plan](../../../quality/TEST_PLAN.md), [experiments](../../../quality/EXPERIMENTS.md) and R01-R27 in [scope](../../V1_SCOPE.md). Test the combined current commit, not only each developer's individual branch.

## Owner slices

| Slice | Owner / points | Deliverable |
| --- | --- | --- |
| P07-K1 | Khalid / 5 | Fairness/replay regressions, critical path/no-path fixes, fixed-seed benchmark harness and measured tick/search performance |
| P07-K2 | Khalid / 2 | Accurate algorithm guide explanations linked to actual implementation and pruning/MCTS/fuzzy evidence |
| P07-K3 | Khalid / 2 | Diagnostics UI readability, live metric correctness and exposure of actionable failure reasons |
| P07-S1 | Suhita / 4 | Backend integration fixtures/scenario registry for the 24-scenario comparison; state/reset/policy-metadata validation |
| P07-S2 | Suhita / 5 | Complete keyboard/camera/window/scaling/accessibility pass, readable scene/feedback corrections and all-mode navigation QA |
| P07-S3 | Suhita / 2 | Save/settings/profile/audio-failure integration fixes, writable-path and no-audio validation |

## File boundaries and interfaces

Khalid owns benchmark/check scripts, fairness/replay tests and AI diagnostic presenters. Suhita owns grouped scenario fixtures, UI/scene corrections and assigned persistence/audio adapters. Fixes to another owner's system are a bounded handoff or explicitly claimed change, not overlapping edits. Shared test fixtures remain under `tests/fixtures/<domain>/` and no test files are added to source packages.

Implement only high-value regression coverage. Do not spend the integration block building a general testing framework, chasing cosmetic snapshot differences or requiring every preset to win every seed. The headless runner records complete metadata and a finite test-only timeout; there is no in-game deadline.

## Gate and evidence

- T01-T08 and necessary mission/perception/tools/policy/scoring/replay checks pass on the integrated build.
- Actual Human and Companion win/fail/retry flow is demonstrated; no known gameplay-blocking crash, hang, hidden-state leak or mandatory softlock remains.
- Structural limits and established lint/type/test checks pass. Record actual performance on named hardware rather than unsupported FPS guarantees.
- The comparison runner/scenario list is executable; run enough of it now to expose harness failures, with the complete matrix/report finalized in P08.
- Required accessibility/settings controls are usable at target laptop resolutions. Record remaining nonblocking cosmetic issues and candidate commit/lock/map/config identities.

Pass a concrete integrated candidate to P08. Any required functionality still missing means P07 is incomplete, even if optional presentation looks polished.
