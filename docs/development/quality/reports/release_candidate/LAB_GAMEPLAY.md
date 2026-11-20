# Lab gameplay recordings and fixes

## Cargo and pursuit revision

Cargo's shortest walk from the Research landing now takes 12 tile transitions, previously six. A bulkhead turns the approach around a patrolling Sentinel. A locker and a desk with crouch clearance give both intruders cover along the route. The simulation maintains a half-second window after continuous confirmed sight. A guard then moves faster than sprint while it keeps that sight. Guards can finish a grab at contact range when their facing changes, with legal sight required to start. Distance, blocked reach, legitimate concealment and stopping the guard still matter. Echo decoys project a translucent, directional copy of the intruder along the recorded path.

The Human Cargo rehearsal completed at tick 1908 on seed 1042 with three distinct cover stops, 64 points and rank B. Human can still extract through Entry on the same seed. Companion's Rush policy extracted through Cargo at tick 1845 on seed 44 with two locker stops and rank B. Rush at seed 18 took the Core, used two lockers and a desk, and was captured at tick 3021. Both bot runs used the same policy with NEXUS memory off. Uncovered Cargo return and direct exposure to the predicted Research gate were reproduced as captures.

The fresh 96-scenario pressure comparison for these rules returned 95 captures and one timeout. All four deployed policies ran 24 scenarios apiece. These probes include changed starts, prior sightings, lock-downs or reduced tool stock. The stock deployment wins above are separate evidence. Reproduce with `uv run --locked python scripts/experiments/comparison.py --output-dir output/lab-gameplay/work/stealth/comparison-final`. The result hash was `3353e3fe6731adce2eeb7042fc5130d77bdb3e0bda94c2c22a172cc0012fe0fb`.

Results use the approved 50 extraction, 40 stealth and 10 pace weights. The three medal cards reflect the achieved results from the service. Clean extraction earns Ghost, Companion extraction earns AI Master, and Speedrunner has its own time requirement.

`uv run --locked python tests/fixtures/autonomy/live_capture.py --output output/lab-gameplay/work/stealth/native-review` exercised the production Cocoa window with audio ready. Seed 44 won and seed 4 was captured. All three live tabs, pause and NEXUS reset passed. Native music now streams directly from bundled files after an SDL music-pause deadlock was reproduced with the recorder.

### Merged build and footage

The gameplay revision merged as `74d8596` in [PR #11](https://github.com/khalid999devs/Echo_Heist/pull/11). `uv run --locked --all-extras python scripts/checks/run.py` passed structure, Ruff, mypy and 348 tests. [Branch CI](https://github.com/khalid999devs/Echo_Heist/actions/runs/44693504577) passed Linux headless checks and the Windows and macOS frozen builds and smoke checks. The Apple Silicon candidate from the same runtime passed codesign and nine Cocoa frozen smoke checks from the extracted archive with audio ready.

Seven clips were captured after merge from `74d8596`. Human takes used the game's ordinary keyboard input with rehearsed timing. Companion ran live with Rush and NEXUS memory off. Both wins scored 64/B with three confirmed encounters. The Human capture at tick 1493 shows three cover stops and deploys Echo at 0:46. The Companion capture at tick 3021 follows two locker hides and an under-desk hide. The Research Tracker's grab completed at 1:46 in the clip. The opening used the production bootstrap with all three launch cues.

Every MP4 decoded through its last frame at 1920 × 1080 and 30 fps with stereo game audio. The ZIP in `output/lab-gameplay` includes all seven clips and `START_HERE.txt` with timestamps. ZIP integrity checks passed. It is 220,204,369 bytes with SHA-256 `5aea093ac512ba4f62e2f95c5bc4c53e3e2cc95e8e11f67d75746f18608dd392`.

## Previous recording revision

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

## Opening clip

`output/lab-gameplay/clips/00 Opening - Logo to Main Menu.mp4` captures 5.77 seconds of the native Cocoa startup, from the first logo frame through the loading progress and crossfade to the animated title menu. The production bootstrap completed with three startup audio cues and no skip input. The 1920 × 1080 MP4 decoded through the final frame with stereo AAC. The verified lab ZIP includes this clip, the six gameplay and monitor clips, and the updated cue sheet.
