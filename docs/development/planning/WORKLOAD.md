# Khalid and Suhita: workload and delivery speed

Target: eight phases over four development days, producing a complete functional V1 initial draft. Phase 1 is entirely Khalid's responsibility. The [phase index](phases/README.md) contains the exact assignments and completion gates.

## Balanced ownership

Khalid leads software architecture, system design, simulation/core logic, strategy algorithms, deterministic experiments and build engineering. He also owns visible input, live algorithm diagnostics and score-presentation work. Suhita leads level/scene architecture, environment composition, game presentation, UI flow and visual/audio feedback. She also owns substantive map importing/validation, NEXUS coordination/protocol persistence and Workshop policy/profile logic.

For this pygame desktop game, frontend means input, scenes, rendering/audio and UI; backend means local simulation, algorithms, data models and persistence. No web server is implied. Both developers own real work on both sides.

## Effort allocation

Points are relative planning estimates, not hours, guaranteed completion times, lines of code or equal difficulty per file. They include implementation, verification, documentation and integration for that slice. Totals deliberately compensate Suhita's later workload for Khalid owning all initial setup.

| Phase | Day | Focus | Khalid points | Suhita points | Integrator |
| --- | --- | --- | --- | --- | --- |
| P01 | 1, opening | Environment, repository, contracts, runtime shell | 12 | 0 | Khalid |
| P02 | 1, remainder | Human heist and five-zone scene | 8 | 12 | Suhita |
| P03 | 2, first block | Fair perception and defender behaviors | 15 | 9 | Khalid |
| P04 | 2, second block | Companion strategy and NEXUS | 14 | 10 | Khalid |
| P05 | 3, first block | Tools, interactive environment and feedback | 7 | 13 | Suhita |
| P06 | 3, second block | Workshop, scoring and complete scene flow | 6 | 14 | Suhita |
| P07 | 4, first block | Full integration, evidence and usability | 9 | 11 | Khalid |
| P08 | 4, second block | Desktop draft delivery and complete-function gate | 9 | 11 | Khalid |
| Total | Four days | Initial functional V1 draft | 80 | 80 | Shared result |

The uneven daily totals are intentional: Khalid's early architecture/AI work is balanced by Suhita's later scene/Workshop/integration work. Equal totals are a planning target; record actual active effort and blockers at each phase gate. If a slice proves much larger, transfer an unstarted, well-bounded task with its points/context rather than silently adding untracked work to one person. Keep the revised cumulative totals visible here.

## Working quickly together

1. Khalid finishes P01 and records one runnable foundation handoff. Suhita can read the source, plan scene composition and collect provenance during that time, but has no required P01 implementation or dependency-repair assignment.
2. Within P02-P08, each person implements the separate files listed in that phase. Start with stable contracts and small working behavior; integrate both slices at the gate. Do not hold independent work while the other developer finishes an unrelated file.
3. The earliest missing required behavior wins priority over optional effects or architecture refinements. Keep P07/P08 for integration and delivery; do not defer the first working MCTS, Workshop or EMP until the last phase.
4. Use one owner per slice, a branch/commit or recorded diff, clear input/output records and a short handoff. Multiple phases may have independent preparation underway, but never claim a phase complete before all prerequisites and its own gate pass.
5. Keep verification proportional. Reuse a small high-value suite and manual playthroughs. The 1,000-line/six-file rules guide responsibility boundaries without creating empty packages or an oversized test framework.

## Phase 8 means functional completion

All R01-R27 gameplay/data/interface functionality must be represented, implemented and verified to the initial-draft standard, including both modes, all required algorithms, tools, Workshop, NEXUS protocols/reset, scores, results/retry, settings, accessibility baseline and ending. Produce Windows/macOS draft archives and evidence; a missing primary build remains incomplete delivery. Publication actions and optional Linux are separately tracked and do not redefine functional completion.

After the complete draft, improve measured balance, AI accuracy, art/animation, sound and other polish. Required mechanics are never moved into that later work. Public release still requires its full license, clean-machine and distribution gates; it may happen on Day 4 if ready.
