# Lab gameplay recordings and fixes

2026-11-20, Khalid. Runtime `2c1cdc7`, Apple Silicon macOS 26.4.1. See the [presentation runbook](../../../release/draft/DEMO.md) for the live sequence and monitor controls.

## Runtime corrections

- The lockdown state stays in the top-right HUD. The repeating centered alarm caption, redundant Core banner and NEXUS toast were removed. Top-left extraction guidance, the audible alarm, normal sound captions and the detailed NEXUS message in its monitor are available.
- A blocked stair landing now triggers a brief retry delay and route reconsideration from the Companion's own observations. A first retreat remains available. If the Companion makes a rapid round trip, A* tries another path before immediately crossing a third time. The stair overlay only shows completed travel when the actor reaches the destination.
- Companion spectator mode displays active Core recovery and capture progress. Keyboard interaction prompts apply to Human mode.

The earlier Balanced seed 1042 loop included eight Companion crossings. The revised run made three and ended in capture by the Security Sentinel. Seed 23 supplies the new paired demo with NEXUS memory off. Balanced reaches Cargo at tick 2052 with 76/A. Rush is captured by the Core Interceptor at tick 1133 with 0/F.

## Checks

- `uv run --locked --all-extras --cache-dir .cache/uv python scripts/checks/run.py` passed structure, Ruff, mypy and 343 tests.
- The native Cocoa recheck through the real gateway confirmed a Balanced win at seed 23 and capture at seed 4. It also exercised the three decision tabs, freeze-on-pause and persisted NEXUS reset.
- `uv run --locked python scripts/experiments/comparison.py --output-dir output/lab-gameplay/work/comparison-final` ran 24 scenarios per policy. Ghost won 2, Balanced 4, Rush 6 and Custom 3. There were 15 wins, 81 captures and zero timeouts.
- Windows x64 and macOS arm64 builds and frozen checks passed, as did the Linux headless job. [Runtime CI](https://github.com/khalid999devs/Echo_Heist/actions/runs/44685365155)
- The freshly extracted Mac ZIP passed codesign verification and all nine frozen smoke checks with Cocoa and audio ready. It is 114,118,216 bytes with SHA-256 `952da46726f59f4a3458c3543a25ddad3ea5cc08f0c12b3cfd52d563db1b5b78`.

## Footage provenance

The Human capture uses manually directed movement, interaction and equipment inputs. The Human win uses the proven route's timed keyboard rehearsal through the same input adapter. The Companion is controlled by the game's live AI. The four mission clips start with ordinary deployment and continue to the actual result. The monitor clips are continuous excerpts of another Balanced attempt with the relevant in-game tabs open. The recorder captured the game surface and final SDL audio mix. MP4 export scales the 1280 × 720 game surface to 1920 × 1080 at 30 fps and uses H.264 and stereo AAC.

- **Human success, seed 1042.** Security stairs to the Core, Research stairs to Cargo. Extraction at tick 1221, 76/A.
- **Human capture, seed 1042.** EMP clears the Service approach. After stealing the Core, the operative heads for Cargo and stuns the Tracker. The Core Interceptor catches the operative at tick 1063, 0/F.
- **Companion success and capture, seed 23.** Same facility and baseline memory with Balanced and Rush respectively.
- **Companion monitoring.** The live panel shows sampled MCTS actions, the latest decision and risk-weighted A* as the bot approaches and steals the Core.
- **Enemy monitoring.** NEXUS dispatch is followed by the Interceptor's minimax/alpha-beta search and the Vault Sentinel and Research Tracker tabs.
