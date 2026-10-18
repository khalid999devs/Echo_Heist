# Eight-phase, four-day functional V1 draft plan

Status: implementation pending. Owners: Khalid and Suhita. The user requires the complete working initial draft after Phase 8, with all defined functionality; later work improves accuracy, balance and polish.

## Authority and boundaries

The source PDF defines the game. User overrides define four development days, eight phases, named workload ownership, repository limits and approved scoring. The [scope matrix](V1_SCOPE.md) remains the feature checklist and [approved scoring](SCORING.md) remains unchanged. The old M0-M5 implementation labels are retired; use P01-P08 and preserve EH feature IDs for traceability.

Khalid owns Phase 1 completely. For P02-P08, both developers have real frontend and backend responsibilities, weighted toward their strengths. [Workload allocation](WORKLOAD.md) totals 80 estimated points each; points include implementation, verification and handoff, not just code. Start/end dates are recorded when implementation begins.

## Phase and day map

| Day | Phase | Focus | Khalid / Suhita points | Integrator |
| --- | --- | --- | --- | --- |
| 1, opening | [P01](phases/foundation/PHASE_01.md) | Environment, filesystem, contracts, runnable shell and smoke package | 12 / 0 | Khalid |
| 1, remainder | [P02](phases/foundation/PHASE_02.md) | Five-zone scene, Human core/lockdown/extract/capture/retry loop | 8 / 12 | Suhita |
| 2, first block | [P03](phases/intelligence/PHASE_03.md) | Fair sensing, BFS/A*/fuzzy, active defenders and replay | 15 / 9 | Khalid |
| 2, second block | [P04](phases/intelligence/PHASE_04.md) | Autonomous Companion/MCTS, Interceptor/minimax, NEXUS | 14 / 10 | Khalid |
| 3, first block | [P05](phases/experience/PHASE_05.md) | Complete tools/props, scene/audio feedback and rule edge cases | 7 / 13 | Suhita |
| 3, second block | [P06](phases/experience/PHASE_06.md) | Workshop/profiles, scoring, settings, complete UI and ending | 6 / 14 | Suhita |
| 4, first block | [P07](phases/delivery/PHASE_07.md) | Full integration, fairness/evidence, performance and usability | 9 / 11 | Khalid |
| 4, second block | [P08](phases/delivery/PHASE_08.md) | Native draft archives, full comparison, functional audit and handoff | 9 / 11 | Khalid |

The [phase index](phases/README.md) links detailed source pages, owner slices, planned file boundaries, interfaces, necessary checks and completion gates. Daily totals differ intentionally; overall estimated workload is equal. Record actual effort and transfer bounded unstarted tasks when evidence calls for rebalancing.

## Developer responsibilities

Khalid leads software architecture, system design, simulation/AI strategy, determinism and build engineering. His frontend work includes input adapters, objective/tool presenters, live diagnostics and result scoring presentation. Suhita leads scene/level architecture, world composition, screens, feedback and game usability. Her backend work includes map importing/validation, patrol registries, NEXUS task/protocol logic, environment object lifecycles and Workshop policy/profile persistence.

One primary writer owns each slice/file. Shared systems are connected through explicit contracts, with consumer-impact notes in the handoff. No general engine framework, speculative abstractions, unnecessary tests or empty module forest is needed for this draft.

## Execution and startup

1. Read the root AGENTS entry point and [START_HERE](../workflow/START_HERE.md).
2. Use [Khalid's guide](../workflow/owners/KHALID.md) or [Suhita's guide](../workflow/owners/SUHITA.md), current [Status](../tracking/STATUS.md), [Backlog](../tracking/BACKLOG.md) and [claims/handoffs](../tracking/HANDOFFS.md).
3. Read the next ready phase and its actual prerequisite handoff. Implement only the assigned slices, with the full source/contract context.
4. Run proportionate checks and give the developer exact instructions for observing the working result. Record actual results and remaining platform/manual gaps.
5. Integrate both slices, check the phase gate and update tracking before calling the phase DONE.

Suhita can prepare scene plans/provenance while Khalid sets up P01, but she has no required setup implementation. Once the foundation handoff is runnable, owners work independently within the same phase. Respect prerequisites without idling on unrelated blocked external checks.

## Completion after Phase 8

P08 requires the entire functional identity: one complete five-zone heist, both first-launch modes, core/lockdown/extraction and fair capture, all required algorithms actually used, Echo/EMP/melee, environment interactions, autonomous Companion, NEXUS protocols/reset, editable Workshop/profiles, scores/results/retry, persistence, controls/accessibility baseline, algorithm evidence and short ending.

Both primary draft archives must exist with recorded hashes and honest native QA status. The complete comparison suite, source/run instructions, known issues and short demonstration accompany the draft. T01-T08 and relevant high-value regressions must pass. Missing mechanics, fake searches, hidden-state shortcuts, broken saves, mandatory softlocks or missing primary artifacts prevent completion.

Simple coherent art and documented nonblocking cosmetic issues are acceptable for this initial draft. Later iterations improve measured balance/AI accuracy, art/audio and polish on top of the complete game; they do not contain deferred required functionality.

## Public release and scope pressure

Windows x64 and macOS Apple Silicon remain the primary free itch.io targets. Public GitHub/itch.io publication and academic submission use EH-031 after the [release gates](../release/RELEASE_PLAN.md) pass; this can happen on Day 4 if ready. It does not add a ninth functional implementation phase. Linux is optional and outside the four-day critical path; browser and Steam remain outside V1.

Reserve P07/P08 for integrated fixes/evidence/delivery. Cut optional effects, advanced lighting, extra media editing and untested Linux first. A missed gate is reported with its exact incomplete behavior and repaired, never renamed as a complete draft. Keep actual platform tests distinct from source launch, configured CI or a successful build.
