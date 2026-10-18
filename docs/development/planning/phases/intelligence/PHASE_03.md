# P03 - Fair perception, navigation and active defenders

Day 2, first block. Integrator: **Khalid**. Effort: Khalid 15, Suhita 9. Status: TODO. Prerequisite: P02. Feature anchors: EH-009, EH-010, EH-013, EH-014, EH-021. Source: PDF pp. 6-11, 16-18.

## Inputs

Read the P02 map/mission handoff, permitted [observations/reports](../../../architecture/DATA_CONTRACTS.md), and the [test plan](../../../quality/TEST_PLAN.md). Keep guard presentation state distinct from authoritative behavior and from controller inputs.

## Owner slices

| Slice | Owner / points | Deliverable |
| --- | --- | --- |
| P03-K1 | Khalid / 7 | Sight/occlusion, acoustic reach, confirmed identity vs suspicion, report provenance/expiry, seen/unseen hiding and fair capture integration |
| P03-K2 | Khalid / 6 | BFS patrol/FSM, Tracker A*/last-seen search, Sentinel fuzzy memberships/rules and headless deterministic replay/decision events |
| P03-K3 | Khalid / 2 | Frontend sensor/algorithm diagnostics presenter with actual values and clear teaching/debug labels |
| P03-S1 | Suhita / 4 | Backend patrol-path/chokepoint registry, map-to-guard assignment validation and dynamic geometry revision adapter |
| P03-S2 | Suhita / 3 | Guard silhouettes/states, suspicion/contact/capture telegraph, visible/heard cue presentation from committed events |
| P03-S3 | Suhita / 2 | Minimal patrol/perception integration fixtures and documented visual checks showing scene data drives real behavior |

## File boundaries and interfaces

Khalid writes `core/perception/`, guard/nav/fuzzy modules, replay infrastructure and `ui/diagnostics/`. Suhita writes `level/model/` registry adapters, guard/cue rendering, and the integration fixtures assigned above. Agree registry IDs and the read-only display-state schema before implementing both ends. Dynamic door revision must invalidate path/LOS data without either person patching the other's module concurrently.

Hearing reveals a cue location, never hidden actor coordinates. A guard's evidence has its original observation tick. Fresh sight refreshes memory; radio duplication does not fabricate new contact. Fuzzy urgency affects investigation, while true visual identification remains authoritative for detection. Chase loss leads to last-seen search/expiry, not automatic tracking or failure.

## Gate and evidence

- Active Sentinel and Tracker move legally, sense through the correct rules, investigate and recover to routine behavior.
- T03/T04 pass; witnessed hiding differs from unseen entry. Capture remains readable and interruptible.
- Logs prove BFS/A*/fuzzy execute in gameplay. A* small-fixture cost agrees with a reference; fuzzy output/rule activations stay bounded.
- Same action/seed/config fixture repeats; modifying unseen authoritative positions cannot affect an unchanged observation/controller decision.
- Suhita demonstrates patrol map data, guard states and world cue locations align. Commit/map/config identities and diagnostics are handed to P04.
