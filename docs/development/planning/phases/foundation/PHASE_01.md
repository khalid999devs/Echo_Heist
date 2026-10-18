# P01 - Environment, repository and runnable foundation

Day 1, opening block. Owner/integrator: **Khalid only**. Effort: Khalid 12, Suhita 0. Status: DONE on 2026-10-18. P01-K1/K2/K3: DONE. Feature anchors: EH-001 through EH-005. Source: PDF pp. 16-17, 19; user explicitly assigns initial setup to Khalid.

## Required context

Read [initial setup](../../../workflow/INITIAL_SETUP.md), [codebase](../../../architecture/CODEBASE.md), [contracts](../../../architecture/DATA_CONTRACTS.md), [code rules](../../../workflow/CODE_RULES.md) and [handoff protocol](../../../tracking/HANDOFFS.md). Respect the six-file root budget and grouped master tests tree.

## Khalid's slices

| Slice | Points | Deliverable |
| --- | --- | --- |
| P01-K1 | 5 | Verify interpreter/native build access; initialize Git/ignore; installable package, real dependency lock, grouped filesystem, developer commands and structure checker |
| P01-K2 | 4 | Typed immutable action/observation/event/result contracts, pure fixed-tick simulation shell, stable RNG and a small deterministic fixture |
| P01-K3 | 3 | Pygame bootstrap/input shell, resource lookup, writable settings, graceful audio/quit, first available native smoke package and basic CI/check recipe |

Implement one runnable package, not empty files for every future feature. Keep the source license choice/status truthful. Reserve source packages and public interfaces for Suhita before she starts P02. Structure checker and CI are useful tooling, not grounds for a large test framework.

## Files and handoff interfaces

Khalid writes root configuration, package bootstrap, `core/contracts/`, initial `core/simulation/`, `infrastructure/`, `scripts/checks/`, `packaging/` and CI. Only create relevant tests under `tests/unit/` or `tests/integration/`. At handoff record actual import paths, runtime types, launch/check/build commands, interpreter/lock details and a runnable minimal resource.

The initial Simulation API accepts typed actions, advances one committed tick and returns events/observations without initializing pygame. Presentation consumes a read-only snapshot. Define map/object interfaces for the upcoming loader and event IDs needed by scene/audio consumers. Document any contract deviation before P02 uses it.

## Gate and evidence

- Fresh locked environment opens/exits the app and headless fixture runs without a display.
- Fixture repeats canonical state/events; invalid actions are rejected; nested observation data cannot mutate authoritative state.
- Resources work outside the repository working directory; settings save/recover under temporary/writable paths.
- File/directory rules pass. Record actual checks and distinguish configured CI from an executed hosted run.
- Build/launch the available native smoke artifact; verify access/status for the other primary OS. Record missing platform evidence explicitly.
- Record the P01 foundation handoff and close all three slices before marking P01 DONE.

Suhita has no required implementation or setup-repair work in this phase. She may read the source and prepare scene ideas/provenance while waiting. P02 can begin once the runnable foundation and its contract handoff exist; native external access gaps stay tracked rather than causing idle local work.

Completion evidence: [P01 handoff](../../../tracking/handoffs/khalid/day_01/P01.md), [verification report](../../../quality/reports/phase01/VERIFICATION.md). Local checks/21 tests pass; actual extracted macOS arm64 app smoke passes; Windows locked-wheel resolution passes. Windows native execution and hosted CI remain NOT_RUN, and source licensing remains a pre-publication decision. P02 remains unstarted.
