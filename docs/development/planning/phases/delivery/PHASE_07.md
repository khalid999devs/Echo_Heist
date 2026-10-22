# P07 - Integration, deterministic evidence and usability

Day 4, first block. Integrator: **Khalid**. Remaining effort: Khalid 9, Suhita 6. Status: TODO. Prerequisite: P06. Feature anchors: EH-026 and harness/fixtures portion of EH-027. Source: PDF pp. 15-19.

Ownership revised 2026-10-22: [remaining-work allocation](../../WORKLOAD.md). **KR/SR IDs supersede the original P03-P08 assignments for future work; completed subsets remain credited.** Reuse the [latest consumer baseline](../../../tracking/handoffs/khalid/presentation/CINEMATIC_STARTUP.md). Khalid leads graphics/presentation; Suhita leads gameplay logic. The integration lead closes the phase only after both revised queues and the combined gate pass.

## Inputs

Read P06's complete build/controls/known issues, [test plan](../../../quality/TEST_PLAN.md), [experiments](../../../quality/EXPERIMENTS.md) and R01-R27 in [scope](../../V1_SCOPE.md). Test the combined current commit, not only each developer's individual branch.

## Owner slices

| Slice | Owner / remaining points | Deliverable |
| --- | --- | --- |
| P07-KR1 | Khalid / 5 | Full keyboard/mouse/camera/window/accessibility/navigation review, feedback fixes, real diagnostics and readable algorithm guide presentation |
| P07-KR2 | Khalid / 4 | Render/audio/startup/frame and repeated-session memory profiling, resource/display robustness and integrated candidate engineering review |
| P07-SR1 | Suhita / 4 | Fairness/replay/softlock regressions, path failure fixes, fixed-seed harness and measured simulation/search performance |
| P07-SR2 | Suhita / 2 | 24-scenario registry/policy/reset metadata, backend save/profile recovery, genuine algorithm explanation/trace accuracy and harness trials |

## File boundaries and interfaces

Suhita owns behavioral experiment/check scripts, fairness/replay/search tests, grouped scenario fixtures and backend persistence corrections. Khalid owns render/audio/memory profiling, scene/diagnostic/accessibility corrections and the combined candidate review. Suhita supplies technically accurate algorithm explanations/metrics; Khalid integrates the readable guide. Split shared performance files by responsibility or claim them sequentially.

Both fix their own subsystems and record consumer effects. Tests/fixtures stay under grouped root `tests/`; do not add a generic test framework or duplicate existing tools. Use the current profiling baseline for comparison, then measure the complete AI-enabled game rather than recycling the earlier single-Sentinel results as full-V1 performance evidence.

Implement only high-value regression coverage. Do not spend the integration block building a general testing framework, chasing cosmetic snapshot differences or requiring every preset to win every seed. The headless runner records complete metadata and a finite test-only timeout; there is no in-game deadline.

## Gate and evidence

- T01-T08 and necessary mission/perception/tools/policy/scoring/replay checks pass on the integrated build.
- Actual Human and Companion win/fail/retry flow is demonstrated; no known gameplay-blocking crash, hang, hidden-state leak or mandatory softlock remains.
- Structural limits and established lint/type/test checks pass. Record actual performance on named hardware rather than unsupported FPS guarantees.
- The comparison runner/scenario list is executable; run enough of it now to expose harness failures, with the complete matrix/report finalized in P08.
- Required accessibility/settings controls are usable at target laptop resolutions. Record remaining nonblocking cosmetic issues and candidate commit/lock/map/config identities.

Pass a concrete integrated candidate to P08. Any required functionality still missing means P07 is incomplete, even if optional presentation looks polished.
