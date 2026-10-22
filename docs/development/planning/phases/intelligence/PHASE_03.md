# P03 - Fair perception, navigation and active defenders

Day 2, first block. Integrator: **Suhita**. Remaining effort: Khalid 5, Suhita 12. Status: IN_PROGRESS. Suhita's SR1/SR2/SR3 are DONE on `work/suhita-p03` ([handoff](../../../tracking/handoffs/suhita/day_02/P03.md)); KR1/KR2 and the shared gate remain open. Prerequisite: P02. Feature anchors: EH-009, EH-010, EH-013, EH-014, EH-021. Source: PDF pp. 6-11, 16-18.

Ownership revised 2026-10-22: [remaining-work allocation](../../WORKLOAD.md). **KR/SR IDs supersede the original P03-P08 assignments for future work; completed subsets remain credited.** Reuse the [latest consumer baseline](../../../tracking/handoffs/khalid/presentation/CINEMATIC_STARTUP.md). Khalid leads graphics/presentation; Suhita leads gameplay logic. The integration lead closes the phase only after both revised queues and the combined gate pass.

## Inputs

Read the P02 map/mission handoff, permitted [observations/reports](../../../architecture/DATA_CONTRACTS.md), and the [test plan](../../../quality/TEST_PLAN.md). Keep guard presentation state distinct from authoritative behavior and from controller inputs.

## Owner slices

| Slice | Owner / remaining points | Deliverable |
| --- | --- | --- |
| P03-KR1 | Khalid / 3 | Distinct guard state/capture/heard-cue feedback and genuine sensor/search/fuzzy diagnostics; reuse current art and Sentinel display |
| P03-KR2 | Khalid / 2 | Map/art collision and route readability review; connect new guard views, inspect both decks and verify visible behavior at the shared gate |
| P03-SR1 | Suhita / 4 | Finish remaining sight/acoustic/report provenance/expiry and seen-versus-unseen hiding/capture rules around the existing Sentinel/posture implementation |
| P03-SR2 | Suhita / 5 | Real Tracker A*/last-seen search, legal stair/geometry handling; audit/reuse Sentinel BFS/FSM/fuzzy and finish required defender behavior gaps |
| P03-SR3 | Suhita / 3 | Typed patrol/chokepoint registry, assignment validation, geometry revision adapter, deterministic replay/decision evidence and narrow live runtime wiring |

## File boundaries and interfaces

Suhita writes `core/perception/`, `core/simulation/` security integration, guard/navigation modules under `ai/`, the typed level registry/import adapter and necessary behavioral tests. Existing level data lives in `level/model.py` and `level/io/`; split only when responsibility/limits require it. Future paths in older plans are not pre-existing APIs. She may replace the temporary nearest-Sentinel selection in `ui/scenes/heist.py` with the validated registry through a recorded narrow claim.

Khalid owns guard/cue drawing, camera/layout, real diagnostics presentation and map/art geometry review. Agree immutable guard views, registry IDs, event names and geometry revision semantics before parallel changes. Shared scene roots/map JSON have one named writer at a time. Reuse fingerprint-7 explicit obstacle bounds, posture and reciprocal stair actions; dynamic geometry invalidates paths/LOS without recreating invisible fixture barriers.

P03 completes Sentinel/Tracker behavior; Interceptor minimax and coordinated NEXUS remain P04. P03 validates witnessed versus unwitnessed use of the existing posture/clearance contract and prepares hiding evidence interfaces; full locker/object lifecycle stays P05. This avoids advancing deferred mechanics merely to close P03.

Hearing reveals a cue location, never hidden actor coordinates. A guard's evidence has its original observation tick. Fresh sight refreshes memory; radio duplication does not fabricate new contact. Fuzzy urgency affects investigation, while true visual identification remains authoritative for detection. Chase loss leads to last-seen search/expiry, not automatic tracking or failure.

## Gate and evidence

- Active Sentinel and Tracker move legally, sense through the correct rules, investigate and recover to routine behavior.
- T03/T04 pass; witnessed hiding differs from unseen entry. Capture remains readable and interruptible.
- Logs prove BFS/A*/fuzzy execute in gameplay. A* small-fixture cost agrees with a reference; fuzzy output/rule activations stay bounded.
- Same action/seed/config fixture repeats; modifying unseen authoritative positions cannot affect an unchanged observation/controller decision.
- Suhita proves patrol/registry behavior; Khalid verifies that guard states and world cue locations align. Commit/map/config identities and diagnostics are handed to P04.
