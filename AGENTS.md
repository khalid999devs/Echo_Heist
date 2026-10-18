# ECHO HEIST agent entry point

Read [START_HERE](docs/development/workflow/START_HERE.md) before implementing. Identify the developer from the user's context, then read that developer's owner guide. If the developer is already known, do not ask again. If identity is absent, inspect context/read-only state and ask once which developer's queue to use; never guess task ownership.

## Required project rules

- The source PDF in `docs/idea` governs gameplay, with explicit user overrides: four development days, eight phases, named ownership, and approved scoring. Read the development hub and assigned phase for context.
- Phase 1 belongs entirely to Khalid. Do not claim it for Suhita or start dependent implementation before its foundation handoff is ready.
- Preserve all required functionality through Phase 8. Simple presentation is acceptable for the initial draft; missing mechanics, fake AI, hidden-state cheats and untested platform claims are not.
- Follow [CODE_RULES](docs/development/workflow/CODE_RULES.md): at most **1,000 lines per authored file**, at most **six maintained direct files per directory**, including package initializers and dotfiles. Group by responsibility before exceeding either limit. These are limits, not target sizes.
- Keep automated test files under the root `tests/` tree, grouped by type and subsystem. Add tests for meaningful rules/risks; do not create tests merely for every file, trivial wrappers or cosmetic edits.
- Keep simulation, observations and AI independent of pygame presentation. Controllers receive filtered immutable observations and return actions. All gameplay mutation belongs to Simulation.
- Use the approved `docs/development/planning/SCORING.md`. Propose further scoring-rule changes in chat and wait for explicit approval before adopting them.
- Check owner/phase prerequisites and existing task claims before editing. Use the handoff protocol, preserve the other developer's changes, and update only the task records you actually worked on. Never mark a shared EH item complete while its other owner's slices remain unfinished.
- Update development records under `docs/development`. Record actual commands/results; distinguish planned APIs, configured CI, successful runs, built artifacts and tested platforms.
- Implement the assigned phase slice through verification and a usable handoff. Do not pause for routine reversible work, spawn other agents without explicit authorization, or send messages to teammates through external services.

The preserved idea documents are read-only source references. Generated dependency locks, third-party tools, caches and binary assets are not authored code; do not corrupt or split them to satisfy a source-line check. Directory hygiene still applies to maintained project files. See CODE_RULES for exact scope and root-file budget.
