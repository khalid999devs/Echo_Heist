# ECHO HEIST

A Python + pygame-ce desktop stealth game with Human and autonomous Companion modes.

Current development: Phase 1 foundation. The full mission and game scenes belong to later phases. Target distribution is free itch.io downloads for Windows x64 and macOS Apple Silicon; Linux is optional after testing.

## Development setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.13. The project requires that minor version; uv can provision it on your development machine when needed.

```sh
uv sync --locked --extra dev --extra build
uv run echo-heist
uv run python scripts/checks/structure.py
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

The first environment checkpoint prints its installed version. Desktop/headless commands and the runnable Phase 1 handoff are added as the foundation is completed.

## Development plan

Start with [AGENTS.md](AGENTS.md), the [development hub](docs/development/README.md), and your owner guide. The eight-phase plan splits work between Khalid and Suhita; Phase 1 belongs to Khalid. All authored files are limited to 1,000 lines, with six maintained direct files per directory and useful tests grouped under root `tests/`.

The blueprint in `docs/idea` is the gameplay authority, with the recorded user-approved schedule, workload and scoring overrides. Dependencies are locked in `uv.lock`; avoid installing the separate `pygame` distribution beside `pygame-ce`.

## License

The project source license is pending the owners' decision before public release. Third-party dependencies retain their own licenses. Do not treat free game downloads or a visible repository as a license grant.
