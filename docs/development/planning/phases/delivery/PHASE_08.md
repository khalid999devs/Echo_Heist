# P08 - Complete functional V1 draft and desktop delivery

Day 4, second block. Integrator: **Khalid**. Remaining effort: Khalid 9, Suhita 5. Status: TODO. Prerequisite: P07. Feature anchors: completion of EH-027, EH-028 and EH-030. Source: PDF pp. 18-19 plus the user's complete-draft requirement.

Ownership revised 2026-10-22: [remaining-work allocation](../../WORKLOAD.md). **KR/SR IDs supersede the original P03-P08 assignments for future work; completed subsets remain credited.** Reuse the [latest consumer baseline](../../../tracking/handoffs/khalid/presentation/CINEMATIC_STARTUP.md). Khalid leads graphics/presentation; Suhita leads gameplay logic. The integration lead closes the phase only after both revised queues and the combined gate pass.

## Inputs

Read P07's candidate handoff, [full scope](../../V1_SCOPE.md), [experiment protocol](../../../quality/EXPERIMENTS.md), [release plan](../../../release/RELEASE_PLAN.md) and [asset register](../../../assets/ASSETS.md). Preserve the approved score rules; calibrate pace only as allowed by its specification.

## Owner slices

| Slice | Owner / remaining points | Deliverable |
| --- | --- | --- |
| P08-KR1 | Khalid / 5 | Locked Windows/macOS candidate builds, resource/save checks, exact archive manifests/hashes, Mac native gameplay/download QA and packaging instructions |
| P08-KR2 | Khalid / 4 | Complete source/run/test/build handoff and shared traceability audit; gameplay demonstration, representative screenshots, credits and draft distribution media |
| P08-SR1 | Suhita / 3 | Physical Windows Human/Companion launch-to-results/retry/controls/audio/save/download QA and owned logic fixes |
| P08-SR2 | Suhita / 2 | Execute/analyze complete 24-scenario/four-policy comparison, failure/policy-change evidence and reproducibility notes for the final handoff |

## File boundaries and interfaces

Khalid owns packaging/specs/manifests, Mac platform and visual QA, technical delivery instructions and demonstration/media/credits. Suhita owns native Windows gameplay evidence, complete experiment/report outputs and related logic fixes. Both reconcile R01-R27 against the exact candidate; a teammate's build is not a substitute for that platform's physical playthrough.

Store compact reports under grouped quality/release folders and large logs/builds/video outside source control, with durable artifact/hash references. Existing development archives are useful baselines, not the final complete-V1 artifacts; rebuild after remaining gameplay ships. Publishing remains subject to the separate actual release gates/account context.

## Complete-function acceptance checklist

- All five zones, both branches/cross-link, collision, interacting/hiding/props and readable objective routing work.
- Human and autonomous Companion are available on first launch and share the same core theft, mandatory lockdown, extraction and fair capture/retry rules.
- BFS, A*, fuzzy inference, minimax/alpha-beta and MCTS actually execute with evidence; Companion has no hidden-state or recording shortcut.
- Echo, EMP, melee/immunity, all guard types, NEXUS dispatch/protocol/reset, four Workshop blocks/presets/profiles and deployment seed options are functional.
- Menu/mode/Workshop/HUD/Lab View/guide/results/epilogue, approved scores/grades/achievements, pause/restart, configurable controls and accessibility/audio/window settings are connected.
- Settings, profiles, run history/telemetry and NEXUS memory persist/recover in writable paths; deterministic comparison metadata and algorithm evidence can be regenerated.
- T01-T08, necessary regressions, structural limits and actual Human/Companion completion/capture checks pass; no known blocker prevents full play.
- Both primary draft archives exist from the candidate commit, with hashes and separate native-test status. No missing archive or unrun platform test is disguised as complete delivery.
- Setup/controls/known issues, comparison summary, short demonstration and source handoff identify the same candidate/version. Both owner queues and shared feature anchors are reconciled.

All required functionality must be implemented at this point. Simple art, measured balance/AI refinements and nonblocking cosmetic issues may improve later; missing mechanics or broken primary flows cannot be labeled future polish. If a mandatory checklist item fails, leave P08 IN_PROGRESS/BLOCKED with the exact cause and repair it rather than declaring the draft complete.

Public GitHub/itch.io publication and academic submission use EH-031 after the independent [release gates](../../../release/RELEASE_PLAN.md) pass and account context is available; that can occur on Day 4. Optional Linux and postlaunch polish are outside these eight functional phases. Record any remaining public-release checks separately from functional implementation and actual desktop delivery.
