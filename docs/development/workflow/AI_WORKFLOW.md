# AI-assisted development workflow

Recommendation date: 2026-10-18. This is a workload-based recommendation, not a benchmark of this project or a guarantee that an effort setting produces correct code.

## GPT-6.1 Sol effort recommendation

| Work | Recommended effort | Why |
| --- | --- | --- |
| Full PDF synthesis, requirement audit, architecture and milestone planning | Extra high (`xhigh`) | Many connected constraints and decisions with expensive downstream consequences |
| Initial package/simulation setup and normal gameplay implementation | High (`high`) | Substantial code reasoning with a bounded, reviewable outcome |
| Fairness, determinism, MCTS/minimax design or cross-platform packaging diagnosis | Extra high (`xhigh`) when needed | Interacting correctness constraints and difficult failure analysis |
| Small UI copy, documentation updates, straightforward fixes | Medium (`medium`) | Clear local changes with limited dependencies |
| A persistent difficult blocker | Consider Max (`max`) after narrowing/reproducing it | Extra effort is useful only when it improves the actual result enough to justify added latency/cost |

If selecting one setting for the combined planning-and-foundation assignment, choose **Extra high**. For ongoing development, use **High** as the default and increase effort for difficult decisions. The game itself needs no OpenAI API, model inference, API key or online connection; these settings apply to the coding assistant.

Official documentation confirms GPT-6.1 Sol supports `low`, `medium` (default), `high`, `xhigh`, and `max`: [model documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol). The official [model-selection guide](https://developers.openai.com/api/docs/guides/model-selection) associates Extra high with demanding polished deliverables and recommends comparing results on real tasks. The assignment-to-effort mapping above is our recommendation.

## Working discipline

Give each developer's agent one owner-specific phase slice with explicit acceptance conditions. Resolve identity using [START_HERE](START_HERE.md), then read that owner's guide, phase, source pages and actual prerequisite handoff. Let it implement and verify routine reversible work without repeated planning pauses. Keep required scope anchored to the PDF and user overrides.

The active plan has eight phases: P01/P02 on Day 1, P03/P04 on Day 2, P05/P06 on Day 3 and P07/P08 on Day 4. Khalid owns P01 entirely; remaining work follows the revised graphics/logic split in [Workload](../planning/WORKLOAD.md): Khalid leads visuals/scenes, Suhita most logic. KR/SR IDs supersede old future assignments; estimates and actual effort are reviewed at each gate. Both retain frontend/backend contributions. P08 must finish the functional game; later accuracy/polish does not absorb missing features. Approved scoring remains unchanged; propose any further scoring-rule change in chat and wait for approval.

Treat claims as evidence-dependent: writing a test is not passing it; configuring CI is not a successful hosted run; generating a package is not testing it on hardware; a policy label is not proof of meaningful AI behavior. Inspect each result and update tracking honestly.

Implement one shared simulation. Reject shortcuts such as hidden-state access, prerecorded Companion routes, fake search metrics, renderer-owned game rules, policy buffs to physics or fixed success outcomes. A shallow but real bounded search is better evidence than a complex-looking placeholder.

## Reusable owner-specific prompt

```text
I'm [Khalid or Suhita]. Read AGENTS.md and my matching guide under
docs/development/workflow/owners/. Retrieve full source/phase/contract context,
the current Status/Backlog, claims and actual prerequisite handoff.

Start my earliest ready assigned phase slice. Implement it through proportionate
verification, preserve the other developer's files, obey the 1000-line/six-file
limits and keep necessary tests under grouped root tests/. Guide me through the
working behavior with exact commands, controls and a seed/profile where useful.

Record my slice evidence and the next integration action. Do not close a shared
feature/phase while the other owner's required work is unfinished. Phase 1 is
Khalid-only. After all eight phases the complete functional V1 draft must work.
Do not change approved scoring rules without proposing in chat and receiving
approval first; do not claim unrun platform tests or publish externally here.
```

Use the shorter identity-specific prompts in START_HERE when preferred. Once identity is established, "start"/"continue my part" resumes the next ready slice. Include logs/commit/reproduction for debugging. Increase effort after identifying what remains uncertain; do not substitute a larger setting for missing tests or requirements.
