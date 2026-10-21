# ECHO HEIST development hub

Created: 2026-10-18. Stage: P01 and complete Human P02 integrated; first P03 stealth slice in progress; P04-P08 pending. Day 1 implementation started on 2026-10-18; P02 was accepted on 2026-10-20.

Current target: a complete working initial draft in **eight phases over four development days**. Khalid owns Phase 1; later work is split by strengths with 80 estimated points each. All defined functionality must work after Phase 8; later work improves accuracy and polish. Public distribution retains its platform/release checks.

Agents start at the root [AGENTS.md](../../AGENTS.md) and [START_HERE](workflow/START_HERE.md), then use [Khalid's guide](workflow/owners/KHALID.md) or [Suhita's guide](workflow/owners/SUHITA.md). Follow the authored-file limit of 1,000 lines, six maintained direct files per directory and grouped master tests tree in [code rules](workflow/CODE_RULES.md).

This folder holds development plans, engineering decisions, task tracking, verification records, and release preparation. Keep future development documents in the appropriate group here. Player-facing installation instructions will also belong in the repository README and release archive.

## Source of truth

The [19-page V1.2 blueprint](../idea/ECHO_HEIST_Complete_V1_Game_Development_Blueprint.pdf) governs the game. The user's release clarification requires Windows x64 and macOS Apple Silicon as primary V1 targets, Linux x64 only after proper testing, and free downloadable distribution on itch.io. Browser and Steam releases are outside V1.

PDF SHA-256: `64fc08b2725796211931d28550a95557e09ddf3c43f3d66c774e6354e36dedda`.

The [existing text export](../idea/ECHO_HEIST_Blueprint_Text.txt) is a reading aid. Resolve discrepancies against the PDF. Page numbers below mean PDF pages, including its cover. The document's V1.2 reference revision describes the game's V1 release; these are different version labels.

Preserve approved gameplay requirements. The blueprint explicitly identifies controls, coordinates, timings, weights, and numerical budgets as tunable defaults. Record changes to those defaults with evidence. The user approved the [replacement scoring rules](planning/SCORING.md) in chat on 2026-10-18; they supersede the PDF's scoring defaults. Further scoring-rule changes must be proposed in chat and approved first. Record proposed changes to required scope before implementation; only the project owner can authorize those scope changes.

## Read and work in this order

| Group | Document | Purpose |
| --- | --- | --- |
| Planning | [Master plan](planning/MASTER_PLAN.md) | Dependency order, milestones, owners, gates, delivery strategy |
| Planning | [Eight phases](planning/phases/README.md) | Detailed owner slices, context, dependencies and gates for P01-P08 |
| Planning | [Workload and speed](planning/WORKLOAD.md) | Named responsibilities, 80/80 effort allocation and parallel handoffs |
| Planning | [V1 scope](planning/V1_SCOPE.md) | Requirements traced to PDF pages and verification |
| Planning | [Approved scoring](planning/SCORING.md) | Completion/stealth/pace formula, ranks, encounter counting and calibration |
| Architecture | [Codebase](architecture/CODEBASE.md) | Package structure, dependency boundaries, runtime rules |
| Architecture | [Data contracts](architecture/DATA_CONTRACTS.md) | Actions, observations, events, persistence, tuning defaults |
| Workflow | [Initial setup](workflow/INITIAL_SETUP.md) | Concrete first implementation batch and its acceptance checks |
| Workflow | [AI development workflow](workflow/AI_WORKFLOW.md) | Model effort, bounded tasks, reusable handoff prompt |
| Workflow | [Startup and code rules](workflow/START_HERE.md) | Owner-aware startup; linked structural and testing instructions |
| Quality | [Test plan](quality/TEST_PLAN.md) | Blueprint T01-T08, additional risk tests, manual QA |
| Quality | [Experiments](quality/EXPERIMENTS.md) | Seeded comparisons, AI proof, academic evidence |
| Assets | [Asset register](assets/ASSETS.md) | Minimum production assets, origin, licenses, credits |
| Release | [Release plan](release/RELEASE_PLAN.md) | Native builds, clean-machine testing, itch.io, submission |
| Tracking | [Status](tracking/STATUS.md) | Current milestone, next task, actual evidence |
| Tracking | [Backlog](tracking/BACKLOG.md) | Ordered work items with dependencies and acceptance |
| Tracking | [Risks and decisions](tracking/RISKS_AND_DECISIONS.md) | Open risks, mitigations, proposed implementation decisions |
| Tracking | [Changelog](tracking/CHANGELOG.md) | Dated development handoffs and verification |
| Tracking | [Claims and handoffs](tracking/HANDOFFS.md) | Owner/file coordination, runnable integration evidence and shared-task completion |

Current runnable baseline: [P02 integrated handoff](tracking/handoffs/khalid/day_01/P02_INTEGRATION.md) and [verification/screenshots](quality/reports/phase02/integration/VERIFICATION.md). The standard desktop app now runs the five-zone Human mission. The [public GitHub repository](https://github.com/khalid999devs/Echo_Heist) holds the incremental owner history. Follow [Status](tracking/STATUS.md) for current hosted CI evidence; Suhita's interactive Windows desktop QA is still pending.

Suhita's workstation entry: [Windows x64 setup and P02 handoff](workflow/setup/WINDOWS_SUHITA.md), including PowerShell clone/run/check/native-build commands and the P02-S1/S2 boundary.

Historical core baseline: [Khalid's P02 owner handoff](tracking/handoffs/khalid/day_01/P02.md), with fixed-point/mission/input contracts and the original diagnostic-room evidence. The subsequent P02 integration accepted both owners' work. Current map/movement consumers should retrieve the [two-floor/stair/sprint handoff](tracking/handoffs/khalid/day_02/TWO_FLOOR_LAB.md), which records the changed coordinates and actual current checks.

## Tracking rules

Use `TODO`, `IN_PROGRESS`, `BLOCKED`, and `DONE`. A task becomes DONE only when its acceptance condition is met and evidence is recorded. A plan or a compiled executable does not prove gameplay acceptance or platform support.

At the end of each implementation batch, update your owner slice/handoff and relevant Backlog/Status/Changelog records without overwriting the other developer's changes. The phase integrator closes the shared gate only after combined verification. Store future QA reports under grouped `quality/reports/`, experiment summaries under `quality/experiments/`, and manifests under `release/manifests/`; create them only for real evidence and group before adding a seventh direct file. Keep large generated logs, captures/builds and experiment output outside version control, with durable artifact references in reports.

Current revision: [first stealth runtime contracts](architecture/integration/STEALTH_SLICE.md), [two-floor contract](architecture/integration/TWO_FLOOR_LAB.md), [audio integration](assets/AUDIO.md), and [38-state native review](quality/reports/two_floor_lab/REVIEW.md). The owner brief is being implemented in playable milestones; full V1 acceptance remains open.
