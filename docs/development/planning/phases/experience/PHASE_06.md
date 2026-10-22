# P06 - Workshop, approved scoring and complete game flow

Day 3, second block. Integrator: **Khalid**. Remaining effort: Khalid 9, Suhita 9. Status: TODO. Prerequisite: P05. Feature anchors: EH-023, EH-024, EH-033 and remaining scene/settings/narrative EH-025. Source: PDF pp. 2, 5, 14-18 plus user-approved scoring.

Ownership revised 2026-10-22: [remaining-work allocation](../../WORKLOAD.md). **KR/SR IDs supersede the original P03-P08 assignments for future work; completed subsets remain credited.** Reuse the [latest consumer baseline](../../../tracking/handoffs/khalid/presentation/CINEMATIC_STARTUP.md). Khalid leads graphics/presentation; Suhita leads gameplay logic. The integration lead closes the phase only after both revised queues and the combined gate pass.

## Inputs

Read the [approved scoring specification](../../SCORING.md), policy/persistence [contracts](../../../architecture/DATA_CONTRACTS.md), P04 protocol/policy handoff and P05 tool events. Read the source scene flow and result/retry requirements before building screens. Further scoring-rule changes require proposal in chat and explicit approval first.

## Owner slices

| Slice | Owner / remaining points | Deliverable |
| --- | --- | --- |
| P06-KR1 | Khalid / 3 | Actual result/score breakdown, encounter explanation, statistics and achievement presentation |
| P06-KR2 | Khalid / 4 | Connect/refine existing Workshop, modes, HUD/Lab/guide/results/epilogue screens and complete retry/edit/new-seed navigation |
| P06-KR3 | Khalid / 2 | Settings/remapping/accessibility UI, volume/window/reduced-flash/subtitle controls and invalid-profile recovery presentation |
| P06-SR1 | Suhita / 3 | Approved 50/40/10 score, team detection encounter lifetime, integer pace, ranks/achievements and immutable result data |
| P06-SR2 | Suhita / 4 | Validated four-block policy/weight translation, Ghost/Balanced/Rush presets and versioned named-profile save/load/recovery |
| P06-SR3 | Suhita / 2 | Apply seed/policy/reset atomically at deployment, retry semantics, history/telemetry and settings/remapping persistence; functional scene wiring |

## File boundaries and interfaces

Suhita owns `core/scoring/`, `workshop/`, policy/profile/history persistence, encounter state and behavior/data integration. Khalid owns result/Workshop/settings screens, scene layout/navigation presentation, input binding UI and genuine diagnostics display. Publish immutable result/policy/deployment contracts before connecting screens. Existing `ui/scenes/design/` previews are presentation assets, not validated policy or saved profile implementations.

Shared `flow.py`, `heist.py`, settings and resources glue use narrow single-writer claims. Suhita can connect real commands/data without taking over layout; Khalid can build complete interaction affordances without duplicating backend rules. Preserve actual result/airlock semantics and never display a calculated grade before its authoritative result exists.

Use only enum/bounded data profiles, never arbitrary executable code. Policies affect legal tactical preferences and weights, not map/physics/defenders. Apply profile/seed/memory settings together at deployment. Results retain the actual seed/policy/score metadata; retries must not silently choose a new challenge or retain memory after reset.

## Gate and evidence

- T01/T02/T08 and full menu-to-run-to-result-to-retry flows work for both modes. Show the brief ending after a real win.
- All four blocks/presets are editable and saved; same-seed comparisons show an actual policy-sensitive decision change.
- Approved score examples/rank boundaries/encounter counting pass; all success grades are reachable and tool use has no direct point penalty.
- Required algorithm guide/Lab View display real data. Subtitles/icons/volume/window/pause controls exist and are usable.
- Corrupt policy/settings data recovers safely. Hand off exact controls, full scene graph, policy schema, score breakdown and known issues to P07.

Every required gameplay/UI feature must now be connected. P07/P08 validate and fix the complete game rather than introducing the first working Workshop, scoring or ending.
