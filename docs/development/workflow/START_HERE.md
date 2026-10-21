# Start or resume developer work

This is the operational entry point for either developer's coding agent. The goal is a complete working initial V1 draft in eight phases over four development days. P01 and P02 are implemented; retrieve the [actual P02 integrated handoff](../tracking/handoffs/khalid/day_01/P02_INTEGRATION.md). P03 has a first verified Sentinel subset; P04-P08 are pending; inspect current tracking/code before assuming later modules exist.

## Resolve the developer once

- If the user/context identifies Khalid, or explicitly points to his guide, use [Khalid's queue](owners/KHALID.md).
- If the user/context identifies Suhita, or explicitly points to her guide, use [Suhita's queue](owners/SUHITA.md).
- Suhita's Windows x64 machine uses the [Windows setup/handoff](setup/WINDOWS_SUHITA.md); it includes clone/bootstrap commands and the P02 owner boundary.
- Keep that identity for later messages such as "start", "continue" or "finish my part" in the same conversation. Do not ask repeatedly.
- If no identity is available, read the plan/state without mutations and ask one concise identity question. Do not guess or claim the other developer's slice.

## Retrieve full context before editing

1. Read [AGENTS.md](../../../AGENTS.md), the [development hub](../README.md), [Status](../tracking/STATUS.md), [Handoffs](../tracking/HANDOFFS.md) and the appropriate owner guide.
2. Read the [eight-phase index](../planning/phases/README.md), [workload table](../planning/WORKLOAD.md) and the next ready assigned phase. Read its prerequisites' actual handoff, not only their plan text.
3. Read [code rules](CODE_RULES.md), [codebase](../architecture/CODEBASE.md), [contracts](../architecture/DATA_CONTRACTS.md), [approved scoring](../planning/SCORING.md) and relevant source PDF pages. The user overrides the blueprint's schedule/score defaults; preserve all other required functionality.
   The owner's [full gameplay/environment/UI brief](../planning/references/IMPLEMENTATION_BRIEF.md) and [repository audit/first milestone](../planning/references/REPOSITORY_AUDIT.md) guide the 2026-10-21 incremental revision. Also retrieve the [two-floor/stair/sprint geometry](../architecture/integration/TWO_FLOOR_LAB.md) and [latest scene/timed-stair/lockdown contract](../architecture/integration/SCENE_PRESENTATION.md) before changing coordinates, routes or menu focus; concept screenshots are inspiration, never runtime gameplay or evidence of missing systems.
4. Inspect existing code, available launch/check commands, working changes, dependency lock and relevant tests. Planned paths are a starting design; follow the P01 actual contract map and update docs if a justified implementation layout differs.
5. Check your task slices/feature anchors, readiness, active claims and file boundaries. Choose the earliest ready slice for your identity. Do not use a generic A/B role assignment or the retired M0-M5 milestones.

## Execute and guide the developer

Explain the current phase, your assigned slice and expected visible behavior briefly, then implement it through verification. Provide exact working launch commands, controls, seed/profile and what to inspect whenever a scene or gameplay check matters. Use available local inspection tools to verify what you can; request developer assistance only for genuinely unavailable hardware/manual actions or missing required information.

Do not stop at a plan or ask permission to perform already assigned reversible work. Keep frontend/backend boundaries, structural limits and the proportional test policy. If a dependency is missing, finish useful independent preparation within your assignment and record the exact blocker rather than implementing someone else's system or faking its result.

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
