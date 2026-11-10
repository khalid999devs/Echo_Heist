# Start or resume developer work

Updated **2026-11-10**: PRs **#5/#6 are merged into main**, preserving Suhita's original commits, after review fixes and successful CI. Read the [merged runtime handoff](../quality/reports/phase05/review/INTEGRATION.md). Current baseline: **fingerprint 12 / 301 tests**. Old work branches and earlier schema/count/checkout instructions are historical.

**P01/P02/P03 are DONE.** P04/P05 runtime now includes real Companion/MCTS, Interceptor/minimax, NEXUS/protocol persistence/reset and doors/glass/canisters/lockers. Production Companion deployment is available; native actual-data review is recorded. Full P04/P05 gate sign-off remains conservative; remaining P05 native door/glass/ability and physical Windows review must be recorded. Do not rebuild these implemented systems.

Authoritative scoring/encounters, editable saved policies/profiles, history and additional preferences persistence remain P06 work. P06 consumers already exist; retrieve their [handoff](../tracking/handoffs/khalid/day_03/P06.md). P07 balance/fairness/performance and P08 delivery remain open. A future request to implement the next slice must check current gates and claims first; this PR review does not authorize automatic later-phase implementation.

Preserve the [P03 combined behavior/guard contract](../architecture/integration/defenders/GUARD_CONTRACT.md): original evidence timestamps/tiles, geometry revisions and retained actual fuzzy traces. Schema-9 P03, schema-7 [physical fixture/input/startup](../tracking/handoffs/khalid/presentation/CINEMATIC_STARTUP.md) and earlier source hashes are historical subsets. Current rules include exact obstacle bodies, reciprocal timed stairs, crouch/clearance, three-second sprint/four-second recharge, two-charge melee/four-second recovery and legitimate noise consequences. Do not downgrade to an old replay schema or unlimited melee.

This is the operational entry point for either developer's separately invoked agent. Read the owner guide after resolving identity. Preserve existing local/unpushed work; never delete a teammate's unmerged branch. A phase is complete only after both owner slices and its combined gate pass.

## Resolve the developer once

- If the user/context identifies Khalid, or explicitly points to his guide, use [Khalid's queue](owners/KHALID.md).
- If the user/context identifies Suhita, or explicitly points to her guide, use [Suhita's queue](owners/SUHITA.md).
- Suhita's Windows x64 machine uses the [Windows setup/handoff](setup/WINDOWS_SUHITA.md); it includes current clone/bootstrap commands, the merged-runtime baseline and current review boundary.
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
