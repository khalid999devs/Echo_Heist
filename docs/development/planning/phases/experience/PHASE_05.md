# P05 - Complete tools, interactive environment and feedback

Day 3, first block. Integrator: **Suhita**. Remaining effort: Khalid 9, Suhita 10. Status: IN_PROGRESS (early crouch and independent presentation implemented; connected lifecycle acceptance pending). Prerequisite for the full phase: P04. Feature anchors: completion of EH-019, EH-020 and environment part of EH-025. Source: PDF pp. 4-8, 15, 17, 19.

Ownership revised 2026-10-22: [remaining-work allocation](../../WORKLOAD.md). **KR/SR IDs supersede the original P03-P08 assignments for future work; completed subsets remain credited.** Reuse the [latest consumer baseline](../../../tracking/handoffs/khalid/presentation/CINEMATIC_STARTUP.md). Khalid leads graphics/presentation; Suhita leads gameplay logic. The integration lead closes the phase only after both revised queues and the combined gate pass.

## Inputs

2026-10-25: Khalid explicitly authorized independent P05-KR1/KR2 presentation ahead of the unfinished P04 gate, in this order: interactive prop/animation components, existing tool feedback, spatial sound/reduced flash, then scoped rendering performance. Work on `work/khalid-p05-visuals` builds on the P04 presentation branch. This does not authorize SR lifecycle implementation or close either phase. New environment state is supplied through a typed presentation contract; diagnostic fixture transitions are labeled and cannot change the shipped mission's mechanics.

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

## Actual independent checkpoint — 2026-10-30

Khalid's authorized KR1/KR2 presentation is implemented on `work/khalid-p05-visuals`, runtime `59fffba`: prop/effect consumers, truthful existing tool feedback, listener-filtered audio/reduced effects, 216 tests, unchanged Human replays and native review. [Handoff](../../../tracking/handoffs/khalid/day_03/P05.md), [verification](../../../quality/reports/phase05/khalid/VERIFICATION.md). The default environment view remains empty until SR2 provides real committed lifecycle state and placements. Both KR connected acceptance and the shared gate remain pending P04/SR1/SR2; the labeled fixture does not close them.

## Applied user-requested melee subset — 2026-10-30

Khalid directly implemented the approved two-charge/four-second melee update, including actual stock/timer/validation, truthful HUD and legitimate existing clang/investigation behavior. [Rules](../../balance/MELEE.md), [handoff](../../../tracking/handoffs/khalid/day_03/MELEE.md), [verification](../../../quality/reports/phase05/khalid/MELEE.md). Runtime `68d0c69` uses fingerprint 10; 226 tests pass. This is an explicitly authorized narrow subset of SR1, not completion of Suhita's SR1 or the phase. Preserve it while finishing remaining tools, P04 autonomy and SR2 lifecycles.

## Gate and evidence

- All tools work in both modes, with shared stock/range/collision rules; T05 and capture-boundary regressions pass.
- No infinite melee stunlock, duplicate glass break, door cache error or decoy extraction is possible.
- Observe each interaction/ability in the actual scene; displayed stock, telegraphs and sound reach agree with simulation.
- Original/licensed assets have provenance. Basic reduced-flash behavior is present for ability/lockdown effects.
- Hand off exact event IDs, object schemas, cue mapping, stock display and relevant test evidence to P06.
