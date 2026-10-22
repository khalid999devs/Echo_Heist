# P05 - Complete tools, interactive environment and feedback

Day 3, first block. Integrator: **Suhita**. Remaining effort: Khalid 9, Suhita 10. Status: IN_PROGRESS (early owner-requested crouch subset only). Prerequisite for the full phase: P04. Feature anchors: completion of EH-019, EH-020 and environment part of EH-025. Source: PDF pp. 4-8, 15, 17, 19.

Ownership revised 2026-10-22: [remaining-work allocation](../../WORKLOAD.md). **KR/SR IDs supersede the original P03-P08 assignments for future work; completed subsets remain credited.** Reuse the [latest consumer baseline](../../../tracking/handoffs/khalid/presentation/CINEMATIC_STARTUP.md). Khalid leads graphics/presentation; Suhita leads gameplay logic. The integration lead closes the phase only after both revised queues and the combined gate pass.

## Inputs

User-directed early subset, 2026-10-22: Khalid implemented crouch/creep and three physical under-desk clearances during the presentation refinement. [Actual handoff](../../../tracking/handoffs/khalid/presentation/MATERIALS_AND_CROUCH.md). This does not close the full phase gate. Suhita owns remaining locker HideSpot entry/exit, glass, doors and canister rules under SR2; Khalid owns their visible/audio effects under KR2. Reuse the authoritative posture/clearance contract rather than duplicating it; approved scoring remains unchanged.

Read P04's actual run, action legality and event handoff, the [ability defaults](../../../architecture/DATA_CONTRACTS.md), [asset register](../../../assets/ASSETS.md) and T05 in the [test plan](../../../quality/TEST_PLAN.md). Keep real event/noise semantics tied to visible effects.

## Owner slices

| Slice | Owner / remaining points | Deliverable |
| --- | --- | --- |
| P05-KR1 | Khalid / 3 | Tool input/HUD, stock/cooldown/rejection feedback and readable animations driven by actual actions/events |
| P05-KR2 | Khalid / 6 | Integrate interactive props with existing scene art, hiding/door/glass/canister effects, spatial SFX/VFX/actor feedback, reduced flash and provenance |
| P05-SR1 | Suhita / 4 | Finish Echo backward replay, EMP/stun/capture ordering, melee adjacency/immunity and stale-action handling for both controllers |
| P05-SR2 | Suhita / 6 | Authoritative door/glass/canister/hide lifecycle, stable interactions, once-only noise, occupancy/vision/navigation revisions and focused integration tests |

## File boundaries and interfaces

Suhita owns `core/abilities/`, capture ordering, environment modules and map object lifecycle adapters invoked by Simulation. She reuses existing under-desk/posture rules and adds the remaining interactions. Khalid owns tool input/display, assets, render/scene animation and `ui/audio/`; he connects events rather than creating world mutations from callbacks. Shared map object schemas and scene roots require a narrow single-writer claim.

The existing cinematic pressure doors are presentation only and do not satisfy physical door locks/lifecycles. Already working locomotion, alarm, tools and basic sound mappings must be reused and extended only for the remaining rules. Keep directories at six direct files or fewer.

Use stable event/object IDs and deterministic interaction priority. Glass breaks once; the canister emits its final collision cue once; door changes affect collision/LOS/navigation consistently. Echo is nonphysical, cannot carry core/extract and does not erase legitimate reports. EMP is single-charge; melee never destroys guards. Audio playback consumes the committed event and cannot create duplicate simulation noises.

## Gate and evidence

- All tools work in both modes, with shared stock/range/collision rules; T05 and capture-boundary regressions pass.
- No infinite melee stunlock, duplicate glass break, door cache error or decoy extraction is possible.
- Observe each interaction/ability in the actual scene; displayed stock, telegraphs and sound reach agree with simulation.
- Original/licensed assets have provenance. Basic reduced-flash behavior is present for ability/lockdown effects.
- Hand off exact event IDs, object schemas, cue mapping, stock display and relevant test evidence to P06.
