# Eight-phase, four-day functional V1 draft plan

Status: P01/P02 DONE; P03 IN_PROGRESS; P05 early crouch subset only; remaining gates open. Ownership revised 2026-10-22. Owners: Khalid and Suhita. The user requires the complete working initial draft after Phase 8, with all defined functionality; later work improves accuracy, balance and polish.

## Authority and boundaries

The source PDF defines the game. User overrides define four development days, eight phases, named workload ownership, repository limits and approved scoring. The [scope matrix](V1_SCOPE.md) remains the feature checklist and [approved scoring](SCORING.md) remains unchanged. The old M0-M5 implementation labels are retired; use P01-P08 and preserve EH feature IDs for traceability.

Khalid owns Phase 1 completely. Completed P02 and refinement contributions stay credited. For remaining P03-P08, Khalid leads complex visuals/scenes and Suhita leads most logic, with both retaining real frontend/backend work. [Workload allocation](WORKLOAD.md) replaces the original 80/80 estimate with **48/60 remaining points**, provisionally offsetting Khalid's completed foundation/visual work. Points include verification/handoff, are not hours, and are reviewed against actual effort at every gate. New KR/SR slice IDs prevent old assignments from being mistaken for current ownership.

## Phase and day map

| Original block | Phase | Focus | Remaining Khalid / Suhita | Integration lead |
| --- | --- | --- | --- | --- |
| Day 1 | P01/P02 | Foundation and Human heist | 0 / 0 — DONE | Complete combined work |
| Day 2, first | [P03](phases/intelligence/PHASE_03.md) | Fair sensing, BFS/A*/fuzzy, defenders and replay | 5 / 12 | Suhita |
| Day 2, second | [P04](phases/intelligence/PHASE_04.md) | Companion/MCTS, Interceptor/minimax, NEXUS | 7 / 18 | Suhita |
| Day 3, first | [P05](phases/experience/PHASE_05.md) | Tools/environment rules and visible/audio feedback | 9 / 10 | Suhita |
| Day 3, second | [P06](phases/experience/PHASE_06.md) | Workshop/profiles/scoring, full UI/settings/ending | 9 / 9 | Khalid |
| Day 4, first | [P07](phases/delivery/PHASE_07.md) | Integrated correctness, evidence, performance and UX | 9 / 6 | Khalid |
| Day 4, second | [P08](phases/delivery/PHASE_08.md) | Candidate builds, complete comparison/audit/demo | 9 / 5 | Khalid |

The [phase index](phases/README.md) links detailed source pages, owner slices, planned file boundaries, interfaces, necessary checks and completion gates. Completed hours were not logged, so exact lifetime equality cannot be claimed. Review actual active effort and transfer bounded unstarted work when evidence calls for rebalancing. Work began 2026-10-18 and P03 is still open on 2026-10-22 after user-requested refinements; the four-day target is retained, not reported as achieved or restarted.

## Developer responsibilities

Khalid leads environment/art, character animation, lighting/materials, camera, scene/UI/audio presentation, rendering performance, resource/display integration and desktop packaging. Suhita leads core/AI/perception/navigation, tools and environment lifecycle, NEXUS, Workshop policy/profile/history persistence, approved scoring and deterministic evidence. She also wires real backend data/actions into existing scenes and performs Windows gameplay QA. Khalid continues architecture/contract review and build engineering; both test their own changes.

Shared scene roots and map JSON require narrow single-writer claims. Publish typed display/event/deployment contracts before connecting graphics. Suhita is authorized to implement unfinished logic in modules previously authored by Khalid; Khalid preserves her runtime changes while completing the visual consumers.

One primary writer owns each slice/file. Shared systems are connected through explicit contracts, with consumer-impact notes in the handoff. No general engine framework, speculative abstractions, unnecessary tests or empty module forest is needed for this draft.

## Execution and startup

1. Read the root AGENTS entry point and [START_HERE](../workflow/START_HERE.md).
2. Use [Khalid's guide](../workflow/owners/KHALID.md) or [Suhita's guide](../workflow/owners/SUHITA.md), current [Status](../tracking/STATUS.md), [Backlog](../tracking/BACKLOG.md) and [claims/handoffs](../tracking/HANDOFFS.md).
3. Read the next ready phase and its actual prerequisite handoff. Implement only the assigned slices, with the full source/contract context.
4. Run proportionate checks and give the developer exact instructions for observing the working result. Record actual results and remaining platform/manual gaps.
5. Integrate both slices, check the phase gate and update tracking before calling the phase DONE.

P01/P02 are complete. Start Suhita at P03-SR1/SR2/SR3 and Khalid at P03-KR1/KR2. Owners can progress independently on agreed interfaces within the phase. Respect shared gates and the requested stop boundary; a preview scene does not satisfy a future logic prerequisite.

## Completion after Phase 8

P08 requires the entire functional identity: one complete five-zone heist, both first-launch modes, core/lockdown/extraction and fair capture, all required algorithms actually used, Echo/EMP/melee, environment interactions, autonomous Companion, NEXUS protocols/reset, editable Workshop/profiles, scores/results/retry, persistence, controls/accessibility baseline, algorithm evidence and short ending.

Both primary draft archives must exist with recorded hashes and honest native QA status. The complete comparison suite, source/run instructions, known issues and short demonstration accompany the draft. T01-T08 and relevant high-value regressions must pass. Missing mechanics, fake searches, hidden-state shortcuts, broken saves, mandatory softlocks or missing primary artifacts prevent completion.

Simple coherent art and documented nonblocking cosmetic issues are acceptable for this initial draft. Later iterations improve measured balance/AI accuracy, art/audio and polish on top of the complete game; they do not contain deferred required functionality.

## Public release and scope pressure

Windows x64 and macOS Apple Silicon remain the primary free itch.io targets. Public GitHub/itch.io publication and academic submission use EH-031 after the [release gates](../release/RELEASE_PLAN.md) pass; this can happen on Day 4 if ready. It does not add a ninth functional implementation phase. Linux is optional and outside the four-day critical path; browser and Steam remain outside V1.

Reserve P07/P08 for integrated fixes/evidence/delivery. Cut optional effects, advanced lighting, extra media editing and untested Linux first. A missed gate is reported with its exact incomplete behavior and repaired, never renamed as a complete draft. Keep actual platform tests distinct from source launch, configured CI or a successful build.
