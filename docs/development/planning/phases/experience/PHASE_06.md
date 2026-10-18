# P06 - Workshop, approved scoring and complete game flow

Day 3, second block. Integrator: **Suhita**. Effort: Khalid 6, Suhita 14. Status: TODO. Prerequisite: P05. Feature anchors: EH-023, EH-024, EH-033 and remaining scene/settings/narrative EH-025. Source: PDF pp. 2, 5, 14-18 plus user-approved scoring.

## Inputs

Read the [approved scoring specification](../../SCORING.md), policy/persistence [contracts](../../../architecture/DATA_CONTRACTS.md), P04 protocol/policy handoff and P05 tool events. Read the source scene flow and result/retry requirements before building screens. Further scoring-rule changes require proposal in chat and explicit approval first.

## Owner slices

| Slice | Owner / points | Deliverable |
| --- | --- | --- |
| P06-K1 | Khalid / 4 | Approved 50/40/10 scoring, shared detection encounters, integer pace, rank/achievement semantics and immutable result breakdown |
| P06-K2 | Khalid / 2 | Score-breakdown widget/presenter, clear per-encounter explanation and real result statistics |
| P06-S1 | Suhita / 5 | Backend validated policy fields/weight translation, Ghost/Balanced/Rush presets, named profile save/load and seed/reset deployment settings |
| P06-S2 | Suhita / 7 | Complete main/menu/mode/Workshop/heist/results/epilogue flow, retry/edit/new-seed actions, readable HUD/Lab View and narrative presentation |
| P06-S3 | Suhita / 2 | Settings persistence connection, remapping/volumes/window/reduced-flash/subtitle controls and invalid-profile recovery UI |

## File boundaries and interfaces

Khalid writes `core/scoring/` and a score presenter under the result scene's agreed subdirectory. Suhita writes `workshop/`, profile persistence adapters, settings UI and scene navigation. Agree the immutable result/policy schema first; neither developer should edit the other's scoring/profile implementation to simplify a widget.

Use only enum/bounded data profiles, never arbitrary executable code. Policies affect legal tactical preferences and weights, not map/physics/defenders. Apply profile/seed/memory settings together at deployment. Results retain the actual seed/policy/score metadata; retries must not silently choose a new challenge or retain memory after reset.

## Gate and evidence

- T01/T02/T08 and full menu-to-run-to-result-to-retry flows work for both modes. Show the brief ending after a real win.
- All four blocks/presets are editable and saved; same-seed comparisons show an actual policy-sensitive decision change.
- Approved score examples/rank boundaries/encounter counting pass; all success grades are reachable and tool use has no direct point penalty.
- Required algorithm guide/Lab View display real data. Subtitles/icons/volume/window/pause controls exist and are usable.
- Corrupt policy/settings data recovers safely. Hand off exact controls, full scene graph, policy schema, score breakdown and known issues to P07.

Every required gameplay/UI feature must now be connected. P07/P08 validate and fix the complete game rather than introducing the first working Workshop, scoring or ending.
