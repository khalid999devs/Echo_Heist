# Suhita's agent guide

Identity: **Suhita**, Windows x64. You lead most gameplay logic; Khalid leads complex graphics/scenes. [Workload](../../planning/WORKLOAD.md): after P03, estimated remaining effort is 48 points for you / 43 for Khalid, provisionally balancing his completed foundation/refinements. Actual historical hours are unknown.

**P01/P02/P03 are complete. Your next queue is P04-SR1/SR2/SR3.** Do not redo Tracker, guard registry or P03. Preserve your original commits and [P03 handoff](../../tracking/handoffs/suhita/day_02/P03.md), then retrieve the superseding [combined schema-9 handoff](../../tracking/handoffs/khalid/day_02/phase03/P03.md) and [actual acceptance](../../quality/reports/phase03/integration/VERIFICATION.md). Main must contain this integration before dependent work begins. Use the [Windows setup and prompt](../setup/WINDOWS_SUHITA.md).

## Retrieve the current baseline

Read [START_HERE](../START_HERE.md), Status/claims, [P04](../../planning/phases/intelligence/PHASE_04.md), source PDF pp. 10-14 and 16-18, code rules, architecture/data contracts and approved scoring. Read the [guard contract](../../architecture/integration/defenders/GUARD_CONTRACT.md) and the earlier [physical fixture handoff](../../tracking/handoffs/khalid/presentation/CINEMATIC_STARTUP.md) for geometry/input/startup details.

Current main runtime: two BFS/FSM/fuzzy Sentinels, a real A* Tracker and a sensing-only Core POST; fair reports/hiding/capture, geometry revisions, exact replay and live F3 teaching traces. Both Human routes win. The facility has five zones/two decks, 14 rooms, 101 furnishings and three real under-desk clearances. Interceptor minimax, Companion/MCTS, NEXUS/protocols and saved policies/scoring are unfinished. Khalid's `work/khalid-p04` adds the [presentation handoff](../../tracking/handoffs/khalid/day_02/phase04/P04.md) and [typed integration port](../../architecture/integration/autonomy/PRESENTATION.md). Retrieve that branch before wiring; do not duplicate its UI or mistake its synthetic QA fixture for a controller.

Preserve these contracts:

- **Fingerprint 9**, original `evidence_tile`, `path_revision` and immutable retained `FuzzyTrace`; schema-8/7 hashes are historical. Never invent new evaluation times for old evidence.
- Exact fixture bodies share physics/LOS/reach. `can_walk` is conservative navigation data; do not restore invisible tile-sized barriers. Geometry changes refresh current sensing before controller decisions.
- Reciprocal stairs, body clearance and crouch/under-desk rules stay authoritative in Simulation. Timed sprint is 3 seconds with 4-second recharge; actual sprint noise is louder.
- Controllers receive filtered immutable Observations and return legal actions. Renderer snapshots, debug paths, true unseen actor positions, Workshop policies and retained display values are not NEXUS/guard knowledge.
- Full-display input mapping, explicit UI-audio serials, resource worker ownership and actual-WIN-only extraction remain regression constraints.

## Active queue

| Phase | Your slices | Remaining result |
| --- | --- | --- |
| P01-P03 | Complete | Preserve foundation, map and integrated defender work |
| P04 | SR1 (9), SR2 (6), SR3 (3) | Companion FSM/utility/A*/MCTS; Interceptor/minimax/NEXUS; protocol persistence/reset/deployment |
| P05 | SR1 (4), SR2 (6) | Complete tools/capture and doors/glass/canisters/full hiding |
| P06 | SR1 (3), SR2 (4), SR3 (2) | Approved scoring, policies/profiles, history/settings/deployment/retry |
| P07 | SR1 (4), SR2 (2) | Fairness/replay/search performance, scenarios/recovery and accurate explanations |
| P08 | SR1 (3), SR2 (2) | Physical Windows full-game QA, complete comparison and experiment report |

You normally lead P04/P05 integration with Khalid's visual acceptance; Khalid leads P06-P08. Do not close a shared phase on an owner slice alone.

## Start P04 and stop boundary

1. Preserve local changes, fetch synchronized main and create/resume **work/suhita-p04**. Retrieve and normally merge `origin/work/khalid-p04` into your work branch after inspecting its handoff; main remains the P03 baseline until combined integration. Recorded suites are **195 tests on main / 207 on Khalid's presentation branch**. Verify your actual locked Windows environment, display/audio and any existing startup timeout.
2. Check claims; claim **P04-SR1/SR2/SR3** and exact files. Use `core/contracts/autonomy/` and implement `AutonomyGateway`; supply it at `GameFlow(..., autonomy_gateway=gateway)` through the startup composition. Read the port's timestamp, active-actor, reset and pause semantics. The shared scene implementation claim is released for a narrow backend connection; claim it before editing. Do not rewrite the screens.
3. Implement real Companion mission FSM, emergency utility, observed-risk A* and bounded belief-only MCTS (selection, expansion, rollout, backpropagation). No human recording, training prerequisite or hidden-state rollout. Human and Companion use the same simulation rules.
4. Implement Interceptor graph/minimax/alpha-beta with physical travel and legal fallback. NEXUS uses legitimate evidence, retains coverage and never reads unseen truth or saved Workshop policy. Preserve the Core registry identity while replacing POST with the real controller.
5. Implement versioned evidence-backed protocol persistence/reset, at most one announced adaptation per attempt and functional first-launch deployment. P06 owns the complete editable Workshop/profile/score flow; P05 owns deferred object lifecycles.
6. Run meaningful search/fairness/replay/persistence checks and prove actual autonomous completion and capture. Record genuine visit/reward and evaluated/pruned-node evidence. Preserve current Human wins/capture, stairs/posture and exact geometry behavior. Request Khalid's connected F2/NEXUS/Interceptor/reset visual acceptance through the repository handoff; the scripted presentation fixture is explicitly not algorithm evidence.
7. Write `docs/development/tracking/handoffs/suhita/day_02/P04.md` and grouped Windows evidence. Give Khalid actual APIs/events, a runnable branch/commit and exact visible inspection steps. Commit with your Git identity, push when access permits, then **stop at P04 SR1/SR2/SR3**. Full P04 still requires KR1/KR2 and its combined gate; do not start P05 automatically.

You own core/AI, typed registry/import adapters, persistence and necessary behavioral tests. Khalid owns complex render/art/camera/layout. Shared scene roots/map JSON need a narrow single-writer claim. Do not rewrite scenes or duplicate an engine/importer to bypass ownership. Keep authored files at most 1,000 lines, six direct files per directory, and meaningful tests under root tests/. Scoring changes require chat approval. No teammate messages or spawned agents without explicit authorization. Hosted Windows dummy-video smoke is separate from physical gameplay/audio QA.
