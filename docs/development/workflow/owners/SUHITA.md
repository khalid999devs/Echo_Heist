# Suhita's agent guide

Identity: **Suhita**, Windows x64. Khalid explicitly reassigned the remaining work on **2026-10-22**: you lead most gameplay logic; he leads complex visual graphics, scenes and presentation. This supersedes your original scene-heavy queue and his original exclusive core ownership. Read the [remaining workload and transfer map](../../planning/WORKLOAD.md). Remaining estimates are 60 points for you / 48 for Khalid, accounting provisionally for his completed foundation and large refinement pass; actual effort is reviewed at every gate.

P01 belonged entirely to Khalid and is complete. Your original P02 map/loader/scene contribution is accepted and preserved. **Do not redo P02 or resume its deleted branch. P03-SR1/SR2/SR3 are next.** Use the [current Windows setup](../setup/WINDOWS_SUHITA.md) and start a fresh `work/suhita-p03` from current main, or safely resume that branch after inspecting its changes.

## Retrieve the baseline before editing

Follow [START_HERE](../START_HERE.md): [Status](../../tracking/STATUS.md), [claims](../../tracking/HANDOFFS.md), [P03](../../planning/phases/intelligence/PHASE_03.md), source PDF pp. 6-11 and 16-18, code rules, architecture/data contracts and approved scoring. Read the accepted [P02 integration](../../tracking/handoffs/khalid/day_01/P02_INTEGRATION.md) and [first Sentinel contract](../../architecture/integration/STEALTH_SLICE.md) as history, then the **latest** [cinematic/physical-fixture handoff](../../tracking/handoffs/khalid/presentation/CINEMATIC_STARTUP.md) and [scene integration contract](../../architecture/integration/SCENE_PRESENTATION.md).

Current main contains `ec8ca48` plus the ownership update. Current runtime has one active Sentinel, real Human wins/capture, 14 rooms/five zones across two decks, 101 furnishings, four existing guard posts and validated patrol/chokepoint data. Three posts still have only P02 contact behavior; Tracker, Interceptor and NEXUS are not implemented controllers. Companion/Workshop designs are previews, not running AI or saved policy functionality.

Critical current contracts:

- Fingerprint **7**; immutable explicit obstacle bounds share physics/LOS/reach. `StaticMap.can_walk` is a conservative tile grid, not every sub-tile passage. Do not restore invisible tile-sized fixture barriers.
- Reciprocal stair traversal is an actual Simulation action. Keep deck topology, legal body clearance, crouch/under-desk rules and stable map IDs when adding navigation.
- Approved sprint is three seconds plus four-second recharge; walking is quieter. Hearing yields cue locations, never hidden actor positions. Chase speed and lockdown precedence already exist; reuse them.
- Simulation owns all mutation; controllers use filtered immutable observations/reports. Renderer snapshots are privileged display data and forbidden as AI inputs.
- Full-display coordinates/pointer translation, explicit UI-audio serials, loading worker lifecycle and actual-WIN-only extraction are working consumer contracts.

## Active queue — revised IDs

`SR` means Suhita's revised remaining slice. Original P03-P08 K/S IDs are historical. A new slice covers unfinished acceptance only, not a rewrite of already verified logic.

| Phase | Your slices / points | Remaining result | Integration lead |
| --- | --- | --- | --- |
| P01/P02 | Complete; no new claim | Retain original foundation/map contribution | Complete |
| [P03](../../planning/phases/intelligence/PHASE_03.md) | P03-SR1 4; SR2 5; SR3 3 | Fair sensing/report/capture gaps; Tracker A* and defender rules; registry/geometry revision/replay integration | You |
| [P04](../../planning/phases/intelligence/PHASE_04.md) | P04-SR1 9; SR2 6; SR3 3 | Companion FSM/utility/A*/MCTS; Interceptor/minimax + NEXUS dispatch; protocol persistence/reset and functional deployment | You |
| [P05](../../planning/phases/experience/PHASE_05.md) | P05-SR1 4; SR2 6 | Complete shared tools/capture rules; doors/glass/canister/hiding lifecycles and their integration tests | You |
| [P06](../../planning/phases/experience/PHASE_06.md) | P06-SR1 3; SR2 4; SR3 2 | Approved scores/encounters; policies/profiles; history/settings/deployment/retry behavior | Khalid |
| [P07](../../planning/phases/delivery/PHASE_07.md) | P07-SR1 4; SR2 2 | Fairness/replay/search performance; scenario/persistence evidence and accurate algorithm explanations | Khalid |
| [P08](../../planning/phases/delivery/PHASE_08.md) | P08-SR1 3; SR2 2 | Physical Windows full-game QA; complete comparison and honest experiment report | Khalid |

## Start now and stop boundary

1. Reproduce the locked Windows environment; read current claims and inspect local changes. The latest recorded suite has **149 tests**; use the actual count on your fetched commit. Launch Human mode and report actual display/audio behavior, including failures.
2. Claim **P03-SR1/SR2/SR3 only** and exact files. Audit existing sensing, Sentinel and crouch implementation before changing it. Write the typed guard/registry/revision/event contract with consumer notes early.
3. Finish perception/report provenance and capture fairness gaps, implement real Tracker A* with legitimate last-seen search/expiry, complete registry and deterministic replay evidence. Reuse the existing Sentinel BFS/FSM/fuzzy implementation. Integrate through current Simulation; do not build a second engine or importer.
4. Replace the temporary nearest-Sentinel selection in `ui/scenes/heist.py` with your validated registry through a **narrow functional wiring claim**. Enable Sentinel/Tracker behavior required by P03; Interceptor minimax remains P04. Let Khalid own complex rendering/art/camera/layout changes. Expose typed guard/event metrics for his P03-KR1/KR2 work.
5. Run relevant checks and real default-security win/capture routes, including both decks and stair links. Record behavior changes and deterministic seed/action/config metadata. Do not use `security_enabled=False` to pass gameplay acceptance or feed privileged view state into controllers.
6. Write `tracking/handoffs/suhita/day_02/P03.md` under `docs/development`, plus grouped Windows evidence as needed. Record actual commands, tests, files, contracts, remaining visual dependencies and what Khalid should inspect. Guide Suhita through the visible result using exact controls/routes.
7. Commit naturally with Suhita's own Git identity; push `work/suhita-p03` when access permits. Keep main for integration. **Stop after your P03 slices. Do not start P04 or mark full P03 DONE until Khalid's required visual slices and the combined gate pass.**

Your logic authority includes `core/`, `ai/`, typed level registry/import validation, persistence and behavioral tests. Shared map JSON and scene/composition roots require a precise claim; current screen structure/art and routes must be preserved. A new schema must have its consumer migration in the handoff. Do not create broad abstractions or regenerate art to solve a logic task.

Tests stay under grouped root `tests/`, only for meaningful risks. All authored files <=1,000 lines and directories <=six maintained direct files. Do not change approved scoring rules without a chat proposal and approval. No external teammate messages or spawned agents without explicit authorization. Native hosted Windows dummy-video success is not physical Windows gameplay/audio QA; record them separately.
