# Phase 1 setup: Khalid's implementation batch

Status: TODO. This is the concrete setup specification; no game source, dependency environment, Git repository or build has been created by the planning pass.

Schedule/owner: [P01](../planning/phases/foundation/PHASE_01.md), opening of Day 1, belongs entirely to Khalid. Suhita has no required setup implementation. Record a runnable contract/command handoff so both developers can start P02 that day. A minimal window alone is not the entire Day 1 outcome.

## Proposed toolchain

Use Python 3.13 as an initial compatibility candidate, pygame-ce as the runtime, Tiled JSON for maps, uv for dependency locking/install, pytest for behavior tests, Ruff for formatting/lint, and mypy for typed core/controller contracts. Use PyInstaller as an optional build dependency. Exact package versions must be resolved and locked after verifying compatible wheels on Windows x64 and macOS arm64; these documents do not claim compatibility has been tested.

The inspected local host is arm64 with Python 3.14.4 and no installed pygame/pytest. Do not silently use that interpreter as the project baseline. Either provision the proposed interpreter locally, or record evidence for adopting another supported minor version consistently across development and builds. The first setup task owns this decision.

The official [pygame-ce repository](https://github.com/pygame-community/pygame-ce) documents installation and its `pygame` import namespace. Install `pygame-ce`, avoiding the separate `pygame` distribution in the same environment. The [PyInstaller manual](https://pyinstaller.org/en/stable/index.html) requires native OS builds; a local Mac build cannot validate Windows packaging.

## Ordered implementation

1. Initialize local Git if still absent, preserve the existing AGENTS instructions, add ignore rules and preserve `docs/idea`. Ignore environments, caches, saves/logs, coverage, build/dist and OS metadata. Prepare a clear README linking to this hub. Follow the six-file root budget in CODE_RULES; select/record a source-license decision before public open-source claims, without inventing copyright ownership.
2. Create `pyproject.toml` with the `src/echo_heist` package, project version, Python constraint, resource inclusion, `echo-heist` entry point, runtime dependencies and optional `dev`/`build` groups. Resolve `uv.lock`; verify both target dependency sets instead of hand-writing lock contents.
3. Implement minimal `__main__`/app bootstrap, a pygame window with graceful quit and optional-audio fallback, and a tiny package-owned resource. Source launch, installed launch and frozen launch must use the same resource service.
4. Implement initial action/observation/event records and a small pure headless Simulation. A scripted fixture only needs movement/wait, fixed ticks, stable RNG, legal-action rejection and ordered events at this stage. It is a foundation check, not a completed heist.
5. Separate the controller API from authoritative state and implement the first deep-immutability/information-boundary checks. Add deterministic action replay on the fixture. Keep UI/audio imports out of the headless path.
6. Implement platform-specific writable paths and settings persistence with atomic JSON save and recovery. Tests inject temporary paths; running setup/tests must not overwrite a real user profile.
7. Add a PyInstaller spec/entry wrapper that includes package resources, produces a Windows one-folder executable or macOS arm64 `.app`, and keeps saved data outside the bundle. Exclude tests and source PDFs from runtime packages.
8. Add CI jobs to install the locked environment, lint/format/type-check, run headless tests, and create native smoke artifacts on Windows x64 and macOS arm64 runners. Verify actual runner/Python architecture explicitly rather than assuming a label. A Linux headless job is useful without claiming Linux release support.
9. Execute the available native build, run it outside the repository, and record the result. Leave unavailable target QA visibly pending. Update the tracking documents with actual command output/evidence.
10. Add the lightweight structure checker under `scripts/checks/`, enforce authored-file limits and six direct maintained files per directory, and keep every test under grouped root `tests/`. Record the actual API/import map, launch/check commands, dependencies, resource/map/event conventions and next consumer work in Khalid's P01 handoff.

## Planned developer commands

These become valid only after the package/tool configuration above is implemented. The uv bootstrap itself is a separate machine prerequisite; document its official installation method in the repository README during setup.

```sh
uv sync --locked --extra dev --extra build
uv run python -m echo_heist
uv run ruff check .
uv run ruff format --check .
uv run mypy src/echo_heist
uv run pytest
uv run pyinstaller --clean --noconfirm packaging/echo_heist.spec
```

Use the same locked commands in CI. The packaging script must choose native settings or platform-specific specs explicitly. The headless seed CLI and replay CLI are later deliverables, not assumed existing commands.

## Setup acceptance

- Fresh locked install works with the agreed Python minor and native architecture.
- App opens, displays a package-owned resource, tolerates unavailable audio, and exits cleanly.
- The pure simulation runs without SDL/display initialization and repeats its canonical event/state hashes for identical fixture/actions/seed.
- Hidden authoritative state never appears in controller inputs; mutable nested observation data is rejected.
- Settings save/load/recovery works under injected writable directories.
- Installed and frozen resources resolve when the working directory is unrelated to the project.
- Actual local checks pass; CI configuration is distinguished from executed hosted CI.
- The native artifact starts without a separately installed Python. Windows/macOS acceptance are recorded independently.
- Structure checks pass and Suhita receives a runnable foundation with actual commands/contracts, not a responsibility to repair or recreate setup.

Once the foundation passes, close Khalid's P01 slices and record the runnable handoff. Both owners then take their ready P02 slices; Suhita integrates the first complete Human scene/mission. An explicitly setup-only assignment ends at the P01 acceptance boundary. Avoid generating unfinished classes for the whole game during setup.
