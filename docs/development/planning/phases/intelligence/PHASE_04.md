# P04 - Autonomous Companion, Interceptor and NEXUS

Day 2, second block. Integrator: **Khalid**. Effort: Khalid 14, Suhita 10. Status: TODO. Prerequisite: P03; tool-action legality from P02. Feature anchors: EH-015, EH-016, EH-017, EH-018, EH-022. Source: PDF pp. 10-14, 16-18.

## Inputs

Read P03 reports/navigation/telemetry, the [approved observation boundary](../../../architecture/CODEBASE.md), [policy defaults](../../../architecture/DATA_CONTRACTS.md) and [algorithm evidence plan](../../../quality/EXPERIMENTS.md). The Companion gets no hidden guard state, pretrained recording or human completion prerequisite.

## Owner slices

| Slice | Owner / points | Deliverable |
| --- | --- | --- |
| P04-K1 | Khalid / 9 | Companion mission FSM, emergency utility, observed-risk A*, real bounded belief-only MCTS selection/expansion/rollout/backpropagation |
| P04-K2 | Khalid / 3 | Interceptor tactical graph, minimax/alpha-beta, plausible hypotheses and actual physical route to selected post |
| P04-K3 | Khalid / 2 | Visible Companion decision/alternative presenter using genuine search metrics |
| P04-S1 | Suhita / 5 | Backend NEXUS evidence-based task scores/dispatch, guard eligibility, coverage limits and core-lockdown task reassignment |
| P04-S2 | Suhita / 2 | Backend versioned evidence-backed protocol state/persistence/reset, at most one announced adaptation per attempt |
| P04-S3 | Suhita / 3 | First-launch Companion deployment path, follow camera and clear NEXUS protocol/alert presentation |

## File boundaries and interfaces

Khalid writes `ai/companion/`, `ai/planning/`, Interceptor behavior and `ui/diagnostics/` decision presenters. Suhita writes `ai/director/`, protocol persistence through infrastructure, and Companion/NEXUS scene widgets. Both use immutable reports, typed task orders and validated legal actions; Simulation resolves those actions. NEXUS never reads the saved Workshop policy or true unseen intruder position.

Keep the initial search small: fixed iterations (starting at 64), shallow abstract rollouts, deterministic ties and event-based triggers. An illegal/stale choice has a legal wait/retreat/replan fallback. Announce the protocol before deployment; memory reset clears every persistent adaptation input. Basic programmatic policy variants are sufficient here; P06 exposes the four user-editable blocks.

## Gate and evidence

- Companion can win and genuinely lose on the actual mission without human recordings or training. Both modes use the same movement/tools/mission rules.
- T06/T07 pass at their current integration scope. Interceptor moves to its post; alpha-beta agrees with unpruned values on controlled trees.
- Actual MCTS alternatives have real visits/rewards; all four search stages and permitted-belief rollouts are verified.
- NEXUS reacts only to legitimate evidence, retains coverage, starts mandatory lockdown and exposes at most one justified protocol.
- Reset memory reproduces baseline behavior; protocol UI matches saved state. Record an autonomous completion/capture and algorithm traces for P05/P06.
