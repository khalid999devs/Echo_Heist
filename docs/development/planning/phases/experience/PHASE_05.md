# P05 - Complete tools, interactive environment and feedback

Day 3, first block. Integrator: **Suhita**. Effort: Khalid 7, Suhita 13. Status: TODO. Prerequisite: P04. Feature anchors: completion of EH-019, EH-020 and environment part of EH-025. Source: PDF pp. 4-8, 15, 17, 19.

## Inputs

Read P04's actual run, action legality and event handoff, the [ability defaults](../../../architecture/DATA_CONTRACTS.md), [asset register](../../../assets/ASSETS.md) and T05 in the [test plan](../../../quality/TEST_PLAN.md). Keep real event/noise semantics tied to visible effects.

## Owner slices

| Slice | Owner / points | Deliverable |
| --- | --- | --- |
| P05-K1 | Khalid / 5 | Complete Echo backward path replay, EMP/stun/capture ordering, melee adjacency/immunity and controller stale-action handling |
| P05-K2 | Khalid / 2 | Tool input/HUD presenter, stock/cooldown/illegal-action feedback and actual action explanation |
| P05-S1 | Suhita / 5 | Backend glass/canister/door/hide object lifecycle, stable interactions, once-only noise and occupancy/vision revision updates |
| P05-S2 | Suhita / 5 | Scene composition, tool/environment effects, distinct gameplay SFX, core/lockdown look and sound, baseline actor animation |
| P05-S3 | Suhita / 3 | Necessary object/door/tool integration fixtures, audio-event mapping checks and asset provenance records |

## File boundaries and interfaces

Khalid owns `core/abilities/`, capture ordering and `ui/input/` / tool-HUD presenters. Suhita owns environment system modules under `core/environment/`, map object lifecycle adapters, assets and `ui/render/` / `ui/audio/`. These backend systems are called by Simulation; they do not mutate authoritative state independently through UI callbacks. Keep each directory at six direct files or fewer.

Use stable event/object IDs and deterministic interaction priority. Glass breaks once; the canister emits its final collision cue once; door changes affect collision/LOS/navigation consistently. Echo is nonphysical, cannot carry core/extract and does not erase legitimate reports. EMP is single-charge; melee never destroys guards. Audio playback consumes the committed event and cannot create duplicate simulation noises.

## Gate and evidence

- All tools work in both modes, with shared stock/range/collision rules; T05 and capture-boundary regressions pass.
- No infinite melee stunlock, duplicate glass break, door cache error or decoy extraction is possible.
- Observe each interaction/ability in the actual scene; displayed stock, telegraphs and sound reach agree with simulation.
- Original/licensed assets have provenance. Basic reduced-flash behavior is present for ability/lockdown effects.
- Hand off exact event IDs, object schemas, cue mapping, stock display and relevant test evidence to P06.
