# Start or resume developer work

2026-10-31 independent follow-up: [P06 UI/settings and delivery-preparation handoff](../tracking/handoffs/khalid/day_03/P06.md) on `work/khalid-p06-ui`, stacked on P05. Read its typed experience port before SR scoring/profile/history/preferences wiring. Session remaps/captions/contrast work; persistence/scoring and shared P04–P08 gates remain pending.

Ownership updated **2026-10-22**: Khalid leads complex graphics/scenes; Suhita leads most gameplay logic. Read the [revised workload](../planning/WORKLOAD.md). **KR/SR** are the active remaining-work slice IDs; original P03-P08 assignments in dated handoffs are historical. P01/P02/P03 are complete; P04 is IN_PROGRESS. Khalid's [P04 presentation handoff](../tracking/handoffs/khalid/day_02/phase04/P04.md) is on `work/khalid-p04`, separate from main. Its real-runtime acceptance awaits Suhita's SR implementation. P05 has early crouch plus [independent presentation](../tracking/handoffs/khalid/day_03/P05.md) on `work/khalid-p05-visuals`; connected P05 acceptance and P06-P08 remain open. Do not repeat completed work or count synthetic presentation checks as finished AI behavior.

Latest P05 branch follow-up: [applied limited melee](../tracking/handoffs/khalid/day_03/MELEE.md), runtime `68d0c69`, **fingerprint 10**, actual two-charge stock/four-second recovery, 226 tests. This directly authorized SR1 subset is implemented; Suhita preserves it while retaining other P04/P05 logic. Main/P03 and the older P04 handoff still use schema 9.

Latest actual consumer baseline: [P03 handoff](../tracking/handoffs/khalid/day_02/phase03/P03.md), [combined gate](../quality/reports/phase03/integration/VERIFICATION.md), [guard contract](../architecture/integration/defenders/GUARD_CONTRACT.md). Retrieve **fingerprint 9**, original evidence tiles, retained fuzzy traces, geometry revisions and the real Sentinel/Tracker registry. P03 is complete; do not resume its old queues.

Historical physical/desktop baseline: [cinematic opening, airlocks and physical fixtures](../tracking/handoffs/khalid/presentation/CINEMATIC_STARTUP.md), [actual review](../quality/reports/cinematic_startup/REVIEW.md). Retrieve **fingerprint-7**, precise obstacle bounds versus conservative route tiles, 0.2-tile actor body, two-deck stairs, posture/clearance, full-display pointer mapping, startup thread ownership and explicit audio serials before changing consumers. Earlier fingerprint-3/6 contracts and counts are superseded where noted.

This is the operational entry point for either developer's separately invoked agent. The eight-phase/four-development-day functional target remains; [Status](../tracking/STATUS.md) records actual progress rather than a calendar guarantee. The [accepted P02 handoff](../tracking/handoffs/khalid/day_01/P02_INTEGRATION.md) preserves the original contributions.

## Resolve the developer once

- If the user/context identifies Khalid, or explicitly points to his guide, use [Khalid's queue](owners/KHALID.md).
- If the user/context identifies Suhita, or explicitly points to her guide, use [Suhita's queue](owners/SUHITA.md).
- Suhita's Windows x64 machine uses the [Windows setup/handoff](setup/WINDOWS_SUHITA.md); it includes current clone/bootstrap commands, the P04-SR1/SR2/SR3 boundary and a complete starting prompt.
- Keep that identity for later messages such as "start", "continue" or "finish my part" in the same conversation. Do not ask repeatedly.
- If no identity is available, read the plan/state without mutations and ask one concise identity question. Do not guess or claim the other developer's slice.

## Retrieve full context before editing

1. Read [AGENTS.md](../../../AGENTS.md), the [development hub](../README.md), [Status](../tracking/STATUS.md), [Handoffs](../tracking/HANDOFFS.md) and the appropriate owner guide.
2. Read the [eight-phase index](../planning/phases/README.md), [workload table](../planning/WORKLOAD.md) and the next ready assigned phase. Read its prerequisites' actual handoff, not only their plan text.
3. Read [code rules](CODE_RULES.md), [codebase](../architecture/CODEBASE.md), [contracts](../architecture/DATA_CONTRACTS.md), [approved scoring](../planning/SCORING.md) and relevant source PDF pages. The user overrides the blueprint's schedule/score defaults; preserve all other required functionality.
   The owner's [full gameplay/environment/UI brief](../planning/references/IMPLEMENTATION_BRIEF.md) and [repository audit/first milestone](../planning/references/REPOSITORY_AUDIT.md) guide the 2026-10-21 incremental revision. Also retrieve the [two-floor/stair/sprint geometry](../architecture/integration/TWO_FLOOR_LAB.md) and [latest scene/timed-stair/lockdown contract](../architecture/integration/SCENE_PRESENTATION.md) and the [closer-camera consumer handoff](../tracking/handoffs/khalid/day_02/CLOSE_CAMERA.md) before changing coordinates, map rendering, routes or menu focus; concept screenshots are inspiration, never runtime gameplay or evidence of missing systems.
4. Inspect existing code, available launch/check commands, working changes, dependency lock and relevant tests. Planned paths are a starting design; follow the P01 actual contract map and update docs if a justified implementation layout differs.
5. Check your task slices/feature anchors, readiness, active claims and file boundaries. Choose the earliest ready slice for your identity. Use revised KR/SR IDs for P03-P08. Do not resume old P02 branches, original future K/S assignments or the retired M0-M5 milestones.

## Execute and guide the developer

Explain the current phase, your assigned slice and expected visible behavior briefly, then implement it through verification. Provide exact working launch commands, controls, seed/profile and what to inspect whenever a scene or gameplay check matters. Use available local inspection tools to verify what you can; request developer assistance only for genuinely unavailable hardware/manual actions or missing required information.

Do not stop at a plan or ask permission to perform already assigned reversible work. Keep the revised visual/logic file seams, structural limits and proportional test policy. Suhita may change previously Khalid-authored core/AI logic; shared scene roots/map files require narrow single-writer claims. If a dependency is missing, finish useful independent preparation within your assignment and record the exact blocker rather than implementing someone else's system or faking its result.

When your slice passes, record commands/evidence, changed APIs/map/events, branch/commit/diff and next integration action in the handoff. Update your slice status; complete shared EH feature anchors only when every listed owner slice and feature acceptance pass. The phase integrator checks the combined build before recording phase completion. Continue the next ready slice only within the user's requested scope.

## Minimal start prompts

Khalid:

```text
I'm Khalid. Read AGENTS.md and docs/development/workflow/owners/KHALID.md.
Start my next ready phase slice, retrieve its full context, implement and verify
it, then record the handoff and guide me through the working result.
```

Suhita:

```text
I'm Suhita. Read AGENTS.md and docs/development/workflow/owners/SUHITA.md.
Start my next ready phase slice, retrieve its full context, implement and verify
it, then record the handoff and guide me through the working result.
```

Once that owner context is established, "start" or "continue my part" should resume the next ready assigned slice with no need to paste the project idea again.
