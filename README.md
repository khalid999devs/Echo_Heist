# ECHO HEIST

Infiltrate Nexus Research, steal the experimental Core, and escape the lockdown. Play as the Human operative or configure Echo in the AI Workshop and watch it take on the same security team. Choose the Entry Airlock or the Cargo Airlock on your way out.

**Desktop release candidate · Windows x64 and macOS Apple Silicon.** Follow the [player guide](docs/development/release/draft/PLAYER_GUIDE.md) and [current QA and delivery status](docs/development/tracking/STATUS.md).

## Run from source

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and use Python 3.13.

```sh
uv sync --locked --all-extras
uv run --locked echo-heist
uv run --locked python scripts/checks/run.py
```

| Default binding | Action |
| --- | --- |
| WASD or arrows | Move |
| C | Crouch or stand |
| Left Shift | Sprint for up to 3 seconds, then recharge for 4 seconds |
| E | Interact with stairs, doors and lockers. Hold beside the Core |
| Q / F / Space | Deploy Echo / use EMP / stun |
| Tab / Esc | Facility map / pause |
| F2 / F3 | Companion decisions / guard diagnostics |

Use corners and cover to break sight during pursuit. Sprint footsteps attract guards. The Tracker and Interceptor close distance over repeated sprint bursts if you stay in view. Settings provides key bindings, sound captions, contrast, reduced flashing and fullscreen. Use `--mute` to start silently or `--data-dir` to isolate local saves for testing.

## AI and experiments

- Sentinels use BFS, a finite-state machine and fuzzy investigation. The Tracker uses A* and follows the last confirmed sighting.
- The Interceptor uses bounded minimax with alpha-beta pruning to predict a chokepoint and travels there physically. NEXUS coordinates using observed reports and sounds.
- Companion uses a mission state machine, emergency utility, observed-risk A* and bounded MCTS. The four Workshop settings change tactical choices. Open F2 in Companion mode to see its real search evidence.
- Reproduce the 24-scenario, four-policy experiment with `uv run --locked python scripts/experiments/comparison.py --output-dir output/comparison`.

## Native package

On the target operating system, run `uv run --locked --all-extras python scripts/packaging/build.py`. It produces a Windows x64 or macOS arm64 ZIP and a manifest in `dist/`. Keep the whole extracted folder or bundle together. The macOS development package is ad-hoc signed. See the [release plan](docs/development/release/RELEASE_PLAN.md) for download and platform checks.

## Development and credits

Start with [AGENTS.md](AGENTS.md) and the [development hub](docs/development/README.md). The blueprint under `docs/idea` governs the game with the recorded owner decisions. Tests are grouped under `tests/`.

Developed by Khalid and Suhita. See the [asset credits and license inventory](docs/development/release/draft/CREDITS.md). The project source license awaits the owners' release decision. Third-party assets and dependencies retain their own terms.
