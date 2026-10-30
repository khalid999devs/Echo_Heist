# Khalid's agent guide

Identity: **Khalid**. The owner explicitly changed the remaining split on **2026-10-22**: lead complex visual graphics, scene design, animation, camera, UI/audio presentation, rendering performance and desktop delivery. Suhita now leads most gameplay logic, including core systems previously authored by you. The [remaining workload](../../planning/WORKLOAD.md) now estimates 43 points for you and 48 for Suhita after P03 to offset completed foundation/refinement work; equal lifetime effort is a target, not a measured fact.

Read [START_HERE](../START_HERE.md), [Status](../../tracking/STATUS.md), [claims](../../tracking/HANDOFFS.md), [code rules](../CODE_RULES.md), the assigned phase and its source/contracts. P01/P02/P03 are DONE; **P04 is the earliest open phase**. P05 has early crouch and an independently verified presentation implementation; its connected gate remains open. Preview scenes do not complete their future behavior gates.

## Actual baseline

Start from synchronized main containing the [P03 handoff](../../tracking/handoffs/khalid/day_02/phase03/P03.md) and [combined gate](../../quality/reports/phase03/integration/VERIFICATION.md). Current fingerprint is **9**, with original evidence locations, retained actual fuzzy traces, two Sentinels, Tracker A* and a sensing-only Core POST. All P03 slices are complete; P04 is next. Physical contracts below remain valid; their old schema-7 hashes are historical. Retrieve [cinematic/physical-fixture handoff](../../tracking/handoffs/khalid/presentation/CINEMATIC_STARTUP.md), [scene contract](../../architecture/integration/SCENE_PRESENTATION.md) and [actual evidence](../../quality/reports/cinematic_startup/REVIEW.md). The physical baseline used fingerprint **7**; current P03 uses **9**, explicit physical obstacle bounds versus conservative route tiles, 0.2-tile body, two decks/stairs, posture/under-desk clearance, full-display input mapping, explicit UI audio serials and loading/airlock lifecycles. Older fingerprint-3/6 handoffs are historical subsets.

The existing game already has cinematic title/loading/airlocks, room art and material variety, character walk/run/crouch, quiet steps/louder sprint, lockdown presentation, real Human wins/capture and first Sentinel behavior. Preserve these and adapt to real new logic; do not restart the visual foundation.

## Active queue — revised IDs

`KR` means Khalid's revised remaining slice. Original P03-P08 K/S IDs are historical; completed contributions keep their credit.

| Phase | Your slices / points | Remaining result | Integration lead |
| --- | --- | --- | --- |
| P01/P02 | Complete; no new claim | Foundation/core/integrated Human scene retained | Complete |
| [P03](../../planning/phases/intelligence/PHASE_03.md) | DONE | Real guard feedback/diagnostics and both-deck combined gate | User-directed integration complete |
| [P04](../../planning/phases/intelligence/PHASE_04.md) | P04-KR1 4; KR2 3 | Implemented on work/khalid-p04; actual Companion/Lab/protocol visual acceptance awaits SR runtime | Suhita |
| [P05](../../planning/phases/experience/PHASE_05.md) | P05-KR1 3; KR2 6 | Tool HUD/input, physical interaction animation, props/VFX/SFX and provenance | Suhita |
| [P06](../../planning/phases/experience/PHASE_06.md) | P06-KR1 3; KR2 4; KR3 2 | Actual score/results, Workshop/full scene flow, settings/accessibility presentation | You |
| [P07](../../planning/phases/delivery/PHASE_07.md) | P07-KR1 5; KR2 4 | Whole-game usability/accessibility and diagnostic clarity; render/audio/memory profiling | You |
| [P08](../../planning/phases/delivery/PHASE_08.md) | P08-KR1 5; KR2 4 | Primary builds/Mac QA, technical handoff, final traceability, demonstration/media/credits | You |

## Start next

2026-10-30: the authorized independent P05 presentation is implemented; retrieve the [P05 handoff](../../tracking/handoffs/khalid/day_03/P05.md) and [actual evidence](../../quality/reports/phase05/khalid/VERIFICATION.md). Its narrow scene-hook claim is released for integration. Next connected work is visual acceptance against Suhita's P04 runtime, then P05 lifecycle state/placements. Do not count the component fixture as gameplay or close those gates.

User override, 2026-10-25: proceed with independent P05-KR1/KR2 presentation on `work/khalid-p05-visuals` while Suhita owns P04 logic. Order: props/animation, tool feedback, spatial sound/reduced flash, then scoped performance. Preserve the P04 branch and Suhita's controller/deployment/startup connection. Claim only narrow event/draw/audio consumer hooks; no SR world lifecycle or scoring changes. Full P04/P05 gates still require combined behavior. This supersedes the wait-only instruction below for this explicitly authorized subset.

Current queue: **P04-KR1/KR2** presentation is implemented and independently verified on `work/khalid-p04`; read its [runnable handoff](../../tracking/handoffs/khalid/day_02/phase04/P04.md) and [typed runtime port](../../architecture/integration/autonomy/PRESENTATION.md). No SR backend was published at the 2026-10-25 handoff. Next action is visual acceptance against Suhita's actual runtime after she connects it. Do not rebuild the screens, implement her AI, close P04 on synthetic data or advance to P05 before the shared gate. The `heist.py`/`flow.py` implementation claim is released for her narrow adapter/composition connection; preserve the new graphics and input contracts.

You own complex drawing/layout under `ui/render/`, visual scene files, startup/audio presentation and assets. Suhita may make narrow functional controller/deployment/result wiring in `ui/scenes/heist.py` / `flow.py`; designate one writer before either edits those shared files. Preserve her core/AI/persistence changes. You retain real nonvisual work in geometry/art calibration, display/input/resource integration, performance and build engineering.

Provide actual typed display/event requirements before asset/UI implementation. Rendering must not mutate Simulation, infer detections or fabricate search metrics. The full-display pointer mapping, startup worker ownership, actual-WIN extraction animation and independent audio volumes remain regression constraints.

## Verification and handoff

Run the checks relevant to changed behavior and inspect actual scenes at supported laptop sizes. Use screenshot/motion/performance tools only where needed; do not rerun every historical audit for a copy change. Save exact commands/results and asset provenance under `docs/development`.

Give Suhita a runnable branch/commit, actual interfaces and the exact next connection. Integrate both owner slices before closing a shared phase. P03/P04/P05 are led by Suhita with your visual acceptance; P06-P08 by you with her behavior/platform evidence. Neither build success nor a polished preview proves missing AI or mechanics.

Keep natural short commits without assistant attribution. Preserve user changes and teammate authorship. No external teammate messages or spawned agents without explicit authorization. Stop at the requested slice boundary. Further scoring-rule changes still require chat approval.
