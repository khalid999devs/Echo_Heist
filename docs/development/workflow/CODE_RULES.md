# Repository and implementation rules

Required by the user on 2026-10-18. Applies to both developers and their agents. [AGENTS.md](../../../AGENTS.md) is the automatic-discovery entry point; this document holds the detailed rules.

## File and directory limits

1. Every authored source, script, test, configuration, instruction and development document must be **at most 1,000 physical lines**, including comments and blank lines. Aim for cohesive modules substantially smaller than the cap. Split by domain responsibility, not arbitrary numbered fragments.
2. Every maintained directory may contain **at most six direct files**. Subdirectories are not files and are checked independently. Count `__init__.py`, dotfiles and documentation. Before adding a seventh file, move related files into a meaningful subdirectory and repair imports/resource references/links.
3. Do not evade limits with minified code, several statements per line, huge embedded strings, extension tricks, duplicate modules or a catch-all utility directory. Avoid both oversized modules and excessive tiny modules.
4. Preserve the original `docs/idea` references unchanged; its long text export is source material, not new authored code. Generated lockfile contents, external/vendor code, binary media, build output, local environments and caches are outside the authored-line rule. Never manually truncate a lock or modify third-party code to satisfy it.
5. The six-file count applies to maintained project files, including generated locks checked into the repository; local OS metadata/cache contents and generated artifact trees do not consume the maintained-directory budget. Ignore those trees in Git and in the structure checker.

Reserve the root's six maintained-file slots for `AGENTS.md`, `README.md`, `pyproject.toml`, `uv.lock`, `.gitignore`, and `LICENSE`. Put tool settings in `pyproject.toml`, CI under `.github/workflows`, packaging under `packaging/`, and scripts under grouped `scripts/` subdirectories. Avoid an extra root `.python-version` or convenience script; configure/document interpreter selection in the existing project configuration. If a genuinely necessary tool requires another root file, first redesign the root grouping within the rule instead of silently making an exception.

Phase 1 must implement a small structure-check script under `scripts/checks/` and wire it into the existing check command/CI. Report offending path and line/file counts. The checker is a useful repository check, not a reason to add a large test suite about file counting.

## Package and design hygiene

- Use the [codebase boundaries](../architecture/CODEBASE.md) and [contracts](../architecture/DATA_CONTRACTS.md). Create modules only as implemented responsibilities require them.
- Keep authoritative gameplay in pure simulation, input/render/audio in presentation, and disk IO in infrastructure. Use typed values and explicit dependencies; avoid mutable globals, circular imports and import-time initialization.
- Configuration values have units, bounds and one source. Do not copy constants between UI, AI and core.
- Prefer small composable functions/classes over a custom engine framework or a general ECS. Validate external JSON and map input at boundaries, with useful error messages.
- Define interfaces before parallel work touches both ends. An implementation change that affects another owner's consumer needs an updated contract and handoff note in the same change.
- Leave no runtime placeholder, fake metric or forced success in a completed phase. Debug fixtures belong in tests or clearly marked diagnostic tools, not the shipped default path.
- Keep resource paths independent of current working directory. Settings/profiles/history use writable application data, never the installed application bundle.

## Tests belong in one master tree

```text
tests/
  conftest.py
  unit/
    core/                     # mission, scoring, capture, tools
    navigation/               # BFS/A* and geometry
    intelligence/             # fuzzy, minimax, MCTS and beliefs
    policies/                 # validation and protocol rules
  integration/
    mission/                  # full mission/action/capture flow
    perception/               # sight, hearing, reports and fairness
    persistence/              # profile/settings recovery and reset
    replay/                   # determinism and policy comparison
  smoke/
    desktop/                  # only useful automated launch/resource checks
  fixtures/
    maps/
    tactics/
    profiles/
```

Create these directories only when they contain necessary work; use the same six-file limit recursively. Keep a shared fixture local to its tests unless several subsystems actually use it. Do not place `test_*.py`, `*_test.py`, `tests.py` or test-only fixtures beside application modules. Manual platform/UI reports belong under `docs/development/quality/reports/`; generated logs/builds stay outside version control.

Add or change an automated test when a failure would materially affect mission rules, fairness, deterministic replay, required algorithm correctness, score/rank rules, config/persistence recovery, or a bug likely to recur. Use focused unit tests for pure logic and integration tests for cross-system behavior. Avoid one test per function, class-existence assertions, private-method mirroring, broad screenshot suites and tests for routine copy/layout changes. Test feel, visual readability and native download behavior through documented manual checks when that is the meaningful evidence.

## Collaboration and completion

Use the [startup protocol](START_HERE.md), [workload plan](../planning/WORKLOAD.md), assigned phase and [handoff records](../tracking/HANDOFFS.md). Keep one primary writer per task/file while parallel work is active. Read existing diffs before edits; never discard someone else's changes. Coordinate shared contracts through narrow explicit diffs.

A completed slice has working behavior, proportionate verification, no structural-rule violation and a recorded handoff. Completing a slice does not complete the entire phase or shared task. The phase integrator checks both slices together and records the gate evidence. Peer feedback is useful; routine implementation does not require a new approval pause. Scoring-rule changes remain the explicit exception requiring prior chat approval.
