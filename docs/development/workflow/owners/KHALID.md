# Khalid's agent guide

Identity: **Khalid**. The owner explicitly changed the remaining split on **2026-10-22**: lead complex visual graphics, scene design, animation, camera, UI/audio presentation, rendering performance and desktop delivery. Suhita now leads most gameplay logic, including core systems previously authored by you. The [remaining workload](../../planning/WORKLOAD.md) estimates 48 points for you and 60 for Suhita to offset completed foundation/refinement work; equal lifetime effort is a target, not a measured fact.

Read [START_HERE](../START_HERE.md), [Status](../../tracking/STATUS.md), [claims](../../tracking/HANDOFFS.md), [code rules](../CODE_RULES.md), the assigned phase and its source/contracts. P01/P02 are DONE; **P03 is the earliest open phase**. P05 has only an early crouch subset. Preview scenes do not complete their future behavior gates.

## Actual baseline

Start from current main containing `ec8ca48` and this ownership revision. Retrieve [cinematic/physical-fixture handoff](../../tracking/handoffs/khalid/presentation/CINEMATIC_STARTUP.md), [scene contract](../../architecture/integration/SCENE_PRESENTATION.md) and [actual evidence](../../quality/reports/cinematic_startup/REVIEW.md). Latest contracts are fingerprint **7**, explicit physical obstacle bounds versus conservative route tiles, 0.2-tile body, two decks/stairs, posture/under-desk clearance, full-display input mapping, explicit UI audio serials and loading/airlock lifecycles. Older fingerprint-3/6 handoffs are historical subsets.

The existing game already has cinematic title/loading/airlocks, room art and material variety, character walk/run/crouch, quiet steps/louder sprint, lockdown presentation, real Human wins/capture and first Sentinel behavior. Preserve these and adapt to real new logic; do not restart the visual foundation.

## Active queue — revised IDs

`KR` means Khalid's revised remaining slice. Original P03-P08 K/S IDs are historical; completed contributions keep their credit.

| Phase | Your slices / points | Remaining result | Integration lead |
| --- | --- | --- | --- |
| P01/P02 | Complete; no new claim | Foundation/core/integrated Human scene retained | Complete |
| [P03](../../planning/phases/intelligence/PHASE_03.md) | P03-KR1 3; KR2 2 | Guard states/cues and genuine diagnostics; geometry/scene integration review | Suhita |
| [P04](../../planning/phases/intelligence/PHASE_04.md) | P04-KR1 4; KR2 3 | Companion/Lab decision presentation, follow camera, NEXUS/deploy/protocol UI | Suhita |
| [P05](../../planning/phases/experience/PHASE_05.md) | P05-KR1 3; KR2 6 | Tool HUD/input, physical interaction animation, props/VFX/SFX and provenance | Suhita |
| [P06](../../planning/phases/experience/PHASE_06.md) | P06-KR1 3; KR2 4; KR3 2 | Actual score/results, Workshop/full scene flow, settings/accessibility presentation | You |
| [P07](../../planning/phases/delivery/PHASE_07.md) | P07-KR1 5; KR2 4 | Whole-game usability/accessibility and diagnostic clarity; render/audio/memory profiling | You |
| [P08](../../planning/phases/delivery/PHASE_08.md) | P08-KR1 5; KR2 4 | Primary builds/Mac QA, technical handoff, final traceability, demonstration/media/credits | You |

## Start next

Claim **P03-KR1/KR2** on `work/khalid-p03` from synchronized main. Read Suhita's P03 claims/contract first. Use the current real Sentinel to review cue readability now; connect Tracker telemetry after her handoff. Your queue does not include implementing her remaining AI to avoid waiting. Complete independent visual work and record exact consumer dependencies.

You own complex drawing/layout under `ui/render/`, visual scene files, startup/audio presentation and assets. Suhita may make narrow functional controller/deployment/result wiring in `ui/scenes/heist.py` / `flow.py`; designate one writer before either edits those shared files. Preserve her core/AI/persistence changes. You retain real nonvisual work in geometry/art calibration, display/input/resource integration, performance and build engineering.

Provide actual typed display/event requirements before asset/UI implementation. Rendering must not mutate Simulation, infer detections or fabricate search metrics. The full-display pointer mapping, startup worker ownership, actual-WIN extraction animation and independent audio volumes remain regression constraints.

## Verification and handoff

Run the checks relevant to changed behavior and inspect actual scenes at supported laptop sizes. Use screenshot/motion/performance tools only where needed; do not rerun every historical audit for a copy change. Save exact commands/results and asset provenance under `docs/development`.

Give Suhita a runnable branch/commit, actual interfaces and the exact next connection. Integrate both owner slices before closing a shared phase. P03/P04/P05 are led by Suhita with your visual acceptance; P06-P08 by you with her behavior/platform evidence. Neither build success nor a polished preview proves missing AI or mechanics.

Keep natural short commits without assistant attribution. Preserve user changes and teammate authorship. No external teammate messages or spawned agents without explicit authorization. Stop at the requested slice boundary. Further scoring-rule changes still require chat approval.
