# ECHO HEIST

A Python + pygame-ce desktop stealth game with Human and autonomous Companion modes.

Current development: **P01 complete; Khalid's P02 core/input slices complete** (`0.1.0a1`, work/khalid-p02). The full five-zone map and scenes await Suhita's integration. Target distribution is free itch.io downloads for Windows x64 and macOS Apple Silicon; Linux is optional after testing.

## Development setup

Suhita on Windows: use the [Windows setup and Phase 2 handoff](docs/development/workflow/setup/WINDOWS_SUHITA.md) for PowerShell commands, your work branch and assigned implementation boundaries.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.13. The project requires that minor version; uv can provision it on your development machine when needed.

```sh
uv sync --locked --extra dev --extra build
uv run --locked echo-heist
uv run --locked echo-heist --headless --seed 1042
uv run --locked python scripts/checks/run.py
```

The standard desktop entry still opens the foundation shell until the scenes are integrated. It loads packaged resources, preserves aspect ratio on resize and closes with Escape/window close. `--mute` skips audio initialization; unavailable audio devices fall back silently. `--headless` repeats a small seeded continuous MOVE/WAIT diagnostic without importing pygame.

Try Khalid's real input/mission rules in the explicitly diagnostic contact room:

```sh
uv run --locked python -m echo_heist.diagnostics.human_preview
```

WASD/arrows move, Shift sprints, hold E near the yellow Core then return to the green Entry marker. Q deploys Echo, F uses EMP, Space melees one reachable guard; Escape pauses and R retries. The guard is stationary for capture testing. See the [P02 owner handoff](docs/development/tracking/handoffs/khalid/day_01/P02.md) for exact contracts, tests and Suhita's integration steps. This room is separate from her five-zone scene.

For an isolated window check:

```sh
uv run --locked echo-heist --smoke-frames 12 --mute --data-dir .local/profile --report output/smoke.json
```

Settings normally live in the OS user application-data folder (`Echo Heist`), never beside the executable. `--data-dir` overrides that location for checks. Invalid files are backed up before recovery; settings from a newer schema stay untouched. Test data/logs/builds are ignored by Git. Use `uv run --locked pytest` for the focused behavior suite; the combined check command also runs structure/lint/format/type checks.

## Native foundation build

On Apple Silicon macOS or Windows x64:

```sh
uv run --locked --all-extras python scripts/packaging/build.py
```

On macOS this produces `dist/Echo Heist.app` and a platform ZIP. On Windows it produces `dist/EchoHeist/EchoHeist.exe` with its support folder and a platform ZIP. Keep the whole bundle/folder. The local macOS build is ad-hoc signed, not notarized. It is a foundation smoke artifact, not the finished game.

```sh
uv run --locked --all-extras python scripts/packaging/smoke.py "dist/Echo Heist.app" --mute
```

Use `dist/EchoHeist/EchoHeist.exe` on Windows. The smoke helper runs the frozen app from an unrelated directory, compares headless hashes and checks resources/settings. `--dummy-video` is available for CI and does not verify a real desktop. See [current Status](docs/development/tracking/STATUS.md) for hosted CI evidence. Windows wheel availability is verified; native Windows desktop QA remains pending.

See the [P01 verification](docs/development/quality/reports/phase01/VERIFICATION.md) and [Suhita's runnable handoff](docs/development/tracking/handoffs/khalid/day_01/P01.md). Both can begin their assigned P02 slices after reading those interfaces.

## Development plan

Start with [AGENTS.md](AGENTS.md), the [development hub](docs/development/README.md), and your owner guide. The eight-phase plan splits work between Khalid and Suhita; Phase 1 belongs to Khalid. All authored files are limited to 1,000 lines, with six maintained direct files per directory and useful tests grouped under root `tests/`.

The blueprint in `docs/idea` is the gameplay authority, with the recorded user-approved schedule, workload and scoring overrides. Dependencies are locked in `uv.lock`; avoid installing the separate `pygame` distribution beside `pygame-ce`.

## License

The project source license is pending the owners' decision before public release. Third-party dependencies retain their own licenses. Do not treat free game downloads or a visible repository as a license grant.
