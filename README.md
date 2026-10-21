# ECHO HEIST

A Python + pygame-ce desktop stealth game with Human and autonomous Companion modes.

Current development: **Phase 2 Human mission complete** (`0.1.0a1`). The five-zone facility, title/briefing/game/results flow, Core theft, lockdown, extraction, capture and basic tools are playable. The first P03 stealth slice adds one active Sentinel with fair sight/hearing, BFS patrol, investigation/chase/search, compact HUD, event audio and Settings. Companion, the remaining advanced defenders, Workshop and scoring are pending. Target distribution is free itch.io downloads for Windows x64 and macOS Apple Silicon; Linux is optional after testing.

## Development setup

Suhita on Windows: use the [Windows setup and Phase 2 handoff](docs/development/workflow/setup/WINDOWS_SUHITA.md) for PowerShell commands, your work branch and assigned implementation boundaries.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.13. The project requires that minor version; uv can provision it on your development machine when needed.

```sh
uv sync --locked --extra dev --extra build
uv run --locked echo-heist
uv run --locked echo-heist --headless --seed 1042
uv run --locked python scripts/checks/run.py
```

The desktop entry opens the cinematic title, then a Human mission briefing and the actual five-zone heist. Select with mouse or arrows/Enter. In the mission, move with WASD/arrows, sprint with Shift, hold E near the Core, and return to the original Exit after lockdown. Q deploys Echo, F uses EMP, Space melees, Tab opens the paused facility map, and Escape pauses. Pause offers resume, same-seed retry and confirmed abort. Companion remains visibly unavailable until Phase 4.

The window preserves aspect ratio on resize and maps mouse input through its letterbox. `--mute` skips audio initialization; unavailable audio devices fall back silently. `--headless` repeats the small seeded foundation diagnostic without importing pygame.

The older diagnostic contact room is still available for focused core-rule inspection:

```sh
uv run --locked python -m echo_heist.diagnostics.human_preview
```

The facility now has 23 smaller rooms, 104 physical furnishings, narrow corridors, two railed stair gangways and slower movement. Three other posts retain P02 contact behavior while the remaining P03/P04 algorithms are developed. F3 opens real Sentinel telemetry; Tab shows the room map and controls with mission time paused. Music and sound volumes are adjustable in Settings. See the [current facility review](docs/development/quality/reports/facility_density/REVIEW.md) for actual checks and screenshots.

For an isolated window check:

```sh
uv run --locked echo-heist --smoke-frames 12 --mute --data-dir .local/profile --report output/smoke.json
```

Settings normally live in the OS user application-data folder (`Echo Heist`), never beside the executable. `--data-dir` overrides that location for checks. Invalid files are backed up before recovery; settings from a newer schema stay untouched. Test data/logs/builds are ignored by Git. Use `uv run --locked pytest` for the focused behavior suite; the combined check command also runs structure/lint/format/type checks.

## Native draft build

On Apple Silicon macOS or Windows x64:

```sh
uv run --locked --all-extras python scripts/packaging/build.py
```

On macOS this produces `dist/Echo Heist.app` and a platform ZIP. On Windows it produces `dist/EchoHeist/EchoHeist.exe` with its support folder and a platform ZIP. Keep the whole bundle/folder. The local macOS build is ad-hoc signed, not notarized. It contains the current Human stealth slice; the full V1 remains in development.

```sh
uv run --locked --all-extras python scripts/packaging/smoke.py "dist/Echo Heist.app" --mute
```

Use `dist/EchoHeist/EchoHeist.exe` on Windows. The smoke helper runs the frozen app from an unrelated directory, compares headless hashes and checks resources/settings. `--dummy-video` is available for CI and does not verify a real desktop. See [current Status](docs/development/tracking/STATUS.md) for hosted CI evidence. Windows wheel availability is verified; native Windows desktop QA remains pending.

See the [P01 handoff](docs/development/tracking/handoffs/khalid/day_01/P01.md) and [Phase 2 evidence](docs/development/quality/reports/phase02/integration/VERIFICATION.md). P03 is in progress; P04-P08 remain in the development plan.

## Development plan

Start with [AGENTS.md](AGENTS.md), the [development hub](docs/development/README.md), and your owner guide. The eight-phase plan splits work between Khalid and Suhita; Phase 1 belongs to Khalid. All authored files are limited to 1,000 lines, with six maintained direct files per directory and useful tests grouped under root `tests/`.

The blueprint in `docs/idea` is the gameplay authority, with the recorded user-approved schedule, workload and scoring overrides. Dependencies are locked in `uv.lock`; avoid installing the separate `pygame` distribution beside `pygame-ce`.

## License

The project source license is pending the owners' decision before public release. Third-party dependencies retain their own licenses. Do not treat free game downloads or a visible repository as a license grant.
