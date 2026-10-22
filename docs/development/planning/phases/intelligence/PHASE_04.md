# P04 - Autonomous Companion, Interceptor and NEXUS

Day 2, second block. Integrator: **Suhita**. Remaining effort: Khalid 7, Suhita 18. Status: TODO. Prerequisite: P03; tool-action legality from P02. Feature anchors: EH-015, EH-016, EH-017, EH-018, EH-022. Source: PDF pp. 10-14, 16-18.

Ownership revised 2026-10-22: [remaining-work allocation](../../WORKLOAD.md). **KR/SR IDs supersede the original P03-P08 assignments for future work; completed subsets remain credited.** Reuse the [latest consumer baseline](../../../tracking/handoffs/khalid/presentation/CINEMATIC_STARTUP.md). Khalid leads graphics/presentation; Suhita leads gameplay logic. The integration lead closes the phase only after both revised queues and the combined gate pass.

## Inputs

Read P03 reports/navigation/telemetry, the [approved observation boundary](../../../architecture/CODEBASE.md), [policy defaults](../../../architecture/DATA_CONTRACTS.md) and [algorithm evidence plan](../../../quality/EXPERIMENTS.md). The Companion gets no hidden guard state, pretrained recording or human completion prerequisite.

## Owner slices

| Slice | Owner / remaining points | Deliverable |
| --- | --- | --- |
| P04-KR1 | Khalid / 4 | Connect and refine Companion decision/alternatives and Lab View using real search metrics; animation/readability appropriate to actual controller state |
| P04-KR2 | Khalid / 3 | Companion follow camera, first-launch deploy flow, NEXUS protocol/alert/reset presentation and visual acceptance |
| P04-SR1 | Suhita / 9 | Companion mission FSM, emergency utility, observed-risk A* and real bounded belief-only MCTS with all four stages |
| P04-SR2 | Suhita / 6 | Interceptor graph/minimax/alpha-beta and physical post travel; evidence-based NEXUS dispatch, guard eligibility, retained coverage and lockdown reassignment |
| P04-SR3 | Suhita / 3 | Versioned evidence-backed protocols/persistence/reset, one announced adaptation per attempt, functional deployment/controller wiring and actual run evidence |

## File boundaries and interfaces

Suhita owns `ai/companion/`, planning/Interceptor/director logic, protocol persistence, Simulation/controller connections and behavioral evidence. Create those packages only as real implementation needs them. Khalid owns Companion/NEXUS screen design, rendering/camera and diagnostic presentation. Suhita may wire typed deployment commands and snapshots into existing scenes under a narrow shared-file claim; she does not redesign their graphics.

Agree immutable task/protocol/decision records first. Both use reports and validated legal actions; Simulation resolves all mutations. NEXUS never reads saved Workshop policy or true unseen intruder position. Preserve the current actual-WIN-only ending, pause/stair/input and explicit-audio contracts.

Keep the initial search small: fixed iterations (starting at 64), shallow abstract rollouts, deterministic ties and event-based triggers. An illegal/stale choice has a legal wait/retreat/replan fallback. Announce the protocol before deployment; memory reset clears every persistent adaptation input. Basic programmatic policy variants are sufficient here; P06 exposes the four user-editable blocks.

## Gate and evidence

- Companion can win and genuinely lose on the actual mission without human recordings or training. Both modes use the same movement/tools/mission rules.
- T06/T07 pass at their current integration scope. Interceptor moves to its post; alpha-beta agrees with unpruned values on controlled trees.
- Actual MCTS alternatives have real visits/rewards; all four search stages and permitted-belief rollouts are verified.
- NEXUS reacts only to legitimate evidence, retains coverage, starts mandatory lockdown and exposes at most one justified protocol.
- Reset memory reproduces baseline behavior; protocol UI matches saved state. Record an autonomous completion/capture and algorithm traces for P05/P06.
