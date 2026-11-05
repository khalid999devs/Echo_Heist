# Suhita's agent guide

**2026-11-05:** P04-SR1/SR2/SR3 are implemented on `work/suhita-p04`, merged with current main ([handoff](../../tracking/handoffs/suhita/day_02/P04.md)). Next: PR review/merge and the combined P04 gate with Khalid's connected acceptance. Do not start P05 before that gate.

Identity: **Suhita**, Windows x64. You lead most gameplay logic; Khalid leads complex graphics/scenes. Revised [workload](../../planning/WORKLOAD.md) and KR/SR slices govern remaining work; historical hours are unknown.

## Current baseline and next assignment

Updated **2026-10-31**: PRs #2/#3/#4 are merged into **main**; retired Khalid branches are no longer needed. Read the [main consolidation handoff](../../tracking/handoffs/khalid/day_03/MAIN.md) and [Windows setup/prompt](../setup/WINDOWS_SUHITA.md). Main contains the verified P04/P05/P06 presentation and ports, applied limited melee, current-build performance fixes and delivery preparation. Latest baseline: **246 tests**, **fingerprint 10**, real Human wins/capture and hosted Windows/Mac builds. Physical Windows gameplay/audio remains your own check.

**P01/P02/P03 are complete. Your next queue is P04-SR1/SR2/SR3 only.** Presentation merges do not close P04 or implement its algorithms. Preserve your original contributions, the [P03 combined handoff](../../tracking/handoffs/khalid/day_02/phase03/P03.md) and [guard contract](../../architecture/integration/defenders/GUARD_CONTRACT.md). Older schema-9/7 evidence and branch checkout instructions are historical, not the current baseline.

Read AGENTS, [START_HERE](../START_HERE.md), development hub, Status/claims, [P04](../../planning/phases/intelligence/PHASE_04.md), source PDF pp. 10–14 and 16–18, code rules, architecture/data contracts and approved scoring. Retrieve Khalid's [P04 handoff](../../tracking/handoffs/khalid/day_02/phase04/P04.md) and [autonomy port](../../architecture/integration/autonomy/PRESENTATION.md), plus the [P05 presentation contract](../../architecture/integration/environment/PRESENTATION.md), [limited melee](../../planning/balance/MELEE.md), [P06 handoff](../../tracking/handoffs/khalid/day_03/P06.md) and [experience port](../../architecture/integration/experience/PRESENTATION.md). Later-phase contracts are context to preserve, not permission to skip P04's boundary.

Current playable logic: two BFS/FSM/fuzzy Sentinels, real A* Tracker, sensing-only Core POST, fair evidence/report/hiding/capture, exact geometry and Human mission. Facility: five zones/two decks, 14 rooms, 101 furnishings and three under-desk clearances. Companion/MCTS, Interceptor minimax, NEXUS/protocols, remaining environment lifecycles and saved policies/scoring are unfinished. Do not duplicate the implemented screens or import synthetic UI fixtures into production.

## Preserve the current contracts

- **Fingerprint 10**; retain original evidence_tile/path_revision/FuzzyTrace timestamps and legitimate hearing. Never refresh old evidence by relaying it.
- Simulation owns mutation. Controllers receive filtered immutable observations and return legal actions; renderer snapshots, unseen truth and Workshop profiles are not defender knowledge.
- Conservative route tiles differ from exact fixture bodies; preserve precise collision/LOS/reach, geometry refresh, reciprocal timed stairs and crouch clearance.
- Sprint: three seconds/four-second recharge, louder real noise. Melee: two charges/no refill, four-second recovery; resisted legal strikes spend stock and make noise, invalid actions do neither. Preserve the approved stun/immunity rules and current hashes unless a real logic change requires a documented schema revision.
- Preserve cinematic loading/airlocks, actual-WIN-only extraction, render cache invalidation, remapped input/hints, pause/focus/display mapping, explicit single UI audio serials and listener-permitted captions/effects. New remap/caption/contrast persistence is still P06-SR work; existing audio/display settings already persist.

## Active queue

| Phase | Your slices | Remaining result |
| --- | --- | --- |
| P01–P03 | Complete | Preserve foundation, map and integrated defender work |
| P04 — now | SR1 (9), SR2 (6), SR3 (3) | Companion FSM/utility/A*/MCTS; Interceptor/minimax/NEXUS; protocol persistence/reset/deployment |
| P05 — later | SR1 (4), SR2 (6) | Remaining tool/capture edges and doors/glass/canisters/full hiding; retain applied limited melee |
| P06 — later | SR1 (3), SR2 (4), SR3 (2) | Approved scoring/encounters, policy translation/profiles, history/preferences persistence and atomic deployment/retry |
| P07 — later | SR1 (4), SR2 (2) | Fairness/replay/search performance, scenarios/recovery and accurate explanations |
| P08 — later | SR1 (3), SR2 (2) | Physical Windows full-game QA, complete comparison/experiment report |

Suhita leads P04/P05 integration with Khalid's connected visual acceptance. Khalid leads P06–P08. Do not close shared phases on one owner's slice or label missing mechanics as polish.

## Execute P04 and stop

1. Preserve local edits/unpushed commits; fetch main and create/resume **work/suhita-p04** from it. Merge updated main into existing meaningful work rather than deleting it. Do not merge retired Khalid branches. Verify the locked Windows environment/display/audio and baseline checks before editing.
2. Check/claim P04-SR1/SR2/SR3 and exact shared files. Implement `AutonomyGateway` in `core/contracts/autonomy/` terms and connect `GameFlow(..., autonomy_gateway=gateway)` in startup composition. Narrow Flow/Heist connection claims are released; claim before wiring, preserve layouts and new experience interfaces.
3. Implement real Companion mission FSM, emergency utility, observed-risk A* and bounded deterministic belief-only MCTS with selection/expansion/rollout/backpropagation. No Human recording, prior training, perfect-information rollout or fake visits/rewards.
4. Implement Interceptor graph/minimax/alpha-beta, real travel and legal fallback. Replace the Core POST controller while preserving its registry identity. NEXUS uses legitimate evidence, eligible guards and retained coverage, never unseen truth or a saved player policy.
5. Implement versioned evidence-backed protocols/persistence/reset, at most one justified announced adaptation per attempt, first-launch Companion deployment and real immutable telemetry. Preserve existing Human mode and genuine failure states.
6. Verify actual autonomous completion/capture, all MCTS stages, alpha-beta equivalence/pruning, evidence fairness, baseline reset, pause/retry and unchanged Human/stair/posture behavior. Run meaningful tests and native Windows checks; record actual results and blockers without calling hosted SDL smoke a physical playthrough.
7. Record `docs/development/tracking/handoffs/suhita/day_02/P04.md` and grouped Windows evidence with APIs/events, commit, commands and exact visible review steps. Use your Git identity, short natural commits and push the work branch; open a reviewable PR to main when access permits. **Stop at P04-SR1/SR2/SR3.** Khalid still verifies connected visuals; do not start P05 automatically or self-merge/close the full phase.

Keep authored files ≤1,000 lines and ≤6 direct files per directory; necessary tests under grouped root tests/. Claim shared scene/map changes narrowly; no duplicate engine/importer, scene redesign, scoring-rule changes without approval, sub-agents or external teammate messages. Preserve unmerged branches and never force/reset away work.
