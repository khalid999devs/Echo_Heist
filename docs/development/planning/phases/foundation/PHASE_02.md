# P02 - Complete Human loop and five-zone game scene

Day 1, remainder. Integrator: **Suhita**. Effort: Khalid 8, Suhita 12. Status: TODO. Prerequisite: P01 foundation handoff. Feature anchors: EH-006, EH-007, EH-008, EH-011, EH-012 and initial EH-019. Source: PDF pp. 2-7, 15-17.

## Inputs

Read the P01 handoff for actual package paths/commands. Read the [map/data contracts](../../../architecture/DATA_CONTRACTS.md), [code boundaries](../../../architecture/CODEBASE.md) and R01-R05/R09/R17-R20 in [scope](../../V1_SCOPE.md). Both people use the same map, actions and simulation.

## Owner slices

| Slice | Owner / points | Deliverable |
| --- | --- | --- |
| P02-K1 | Khalid / 6 | Continuous movement/collision/sprint, interaction legality, atomic theft/lockdown/extraction, capture timing and initial functional tool actions |
| P02-K2 | Khalid / 2 | Human input-to-action adapter and objective/interaction prompt presenter; no rules in widgets |
| P02-S1 | Suhita / 8 | Five-zone Tiled greybox, two branches/cross-link, readable scene/camera, basic menu/mode/heist/results/pause screens and actor/object presentation |
| P02-S2 | Suhita / 4 | Typed Tiled importer, object/property validation, anchor uniqueness, geometry flags and branch/lockdown reachability checks |

## File boundaries and coordination

Khalid writes `core/simulation/`, initial `core/abilities/`, `ui/input/` and objective prompt presentation. Suhita writes `level/io/`, map resources and `ui/scenes/` / `ui/render/`. Map model types come from the agreed contract; Suhita's loader supplies values, and Khalid's Simulation owns mutations. Agree exact prompt-widget filenames before either edits a shared scene file.

Suhita builds Entry/Extraction -> Service Wing -> upper Security Control/lower Research Floor -> Core Chamber, with the cross-link. Include stable Spawn/Exit/Core IDs, cover/hide markers, explicit movement/vision/sound tags and patrol/chokepoint data. A minimal stationary guard can exercise contact/capture at this gate; P03 supplies the complete active defender behavior. Do not label the minimal guard as finished patrol AI.

Initial Echo/EMP/melee legality must be executable so P04 can plan legal tool choices; refine effects/edge cases in P05. Basic result screens can show outcome before final scoring arrives in P06. Companion mode stays visibly in development until P04.

## Gate and evidence

- Human starts, moves/interacts, takes core exactly once, enters mandatory lockdown and extracts at the original exit; no-core exit never wins.
- Capture can end a run and be interrupted under legal conditions; result/retry/pause work. Record a Human win and capture.
- Both branches/cross-link and lockdown return connectivity validate; collision tags match scene boundaries.
- Invalid maps and unreachable anchors fail clearly. Test collision/mission rules and importer validation with small fixtures, not cosmetic screen snapshots.
- Suhita records map IDs/screens/loader schema; Khalid records legal actions/mission events. Integrate these on the same build and update both slice statuses before closing the phase.
