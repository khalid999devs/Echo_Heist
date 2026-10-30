# P05 presentation verification

2026-10-30, macOS 26.4.1 / arm64 / Python 3.13.16. Runtime **`59fffbacb9fad24be8f21369fe9e5e2f37a94626`**, branch `work/khalid-p05-visuals`, [draft PR #3](https://github.com/khalid999devs/Echo_Heist/pull/3). [Runnable handoff](../../../../tracking/handoffs/khalid/day_03/P05.md), [contract](../../../../architecture/integration/environment/PRESENTATION.md), [durable evidence](EVIDENCE.json).

Independent prop/tool/audio presentation is implemented. Real door/glass/canister/locker lifecycle and P04 autonomous behavior are not provided by the diagnostic fixture. Shared P04/P05 gates remain open.

## Actual checks

All commands used `uv run --locked --cache-dir .cache/uv`. Native commands used Cocoa and initialized normal audio; they did not substitute SDL dummy drivers.

| Command suffix | Result |
| --- | --- |
| `python scripts/checks/run.py` | PASS: six-file/1,000-line structure, Ruff, formatting, strict mypy (136 source files), **216 tests in 28.23 s** |
| `python scripts/experiments/p03_evidence.py --output output/phase05-visuals/human-replay.json` | PASS: all five scenarios exactly replay; outcome/ticks/events/tool use/event-chain hash/final fingerprint match the saved P04 report |
| `python scripts/quality/defenders/capture.py --output output/phase05-visuals/human-native` | PASS: real Human upper WIN at 1483 ticks, lower WIN at 1604, careless CAPTURED at 694; both decks, unseen under-desk hiding and read-only diagnostics |
| `python -m tests.fixtures.interactions.capture --output output/phase05-visuals/fixture` | PASS: 240 rendered fixture frames, **16 images** covering closed/open/locked door, glass/shards, canister/impact, locker, both-deck overlays, reduced effects and real Human tool HUD; fixture leaves Simulation unchanged before the real tool captures |
| `python scripts/quality/profile_desktop.py --output output/phase05-visuals/performance` | PASS: 12 mission restarts / 3,600 frames, window-size changes, actual security/audio, bounded short-run memory |
| `--all-extras python scripts/packaging/build.py` | PASS: clean-source arm64 app/ZIP at `59fffba`; ad-hoc signing verified |
| `--all-extras python scripts/packaging/smoke.py 'dist/Echo Heist.app' --output-dir output/phase05-visuals/native-app` | PASS: **9/9**, frozen/source fixture hashes match, Cocoa, 33 audio assets loaded and audio ready |
| `--all-extras python scripts/packaging/smoke.py 'output/phase05-visuals/extracted-final/Echo Heist.app' --output-dir output/phase05-visuals/native-zip` | PASS: fresh `ditto -x -k` extraction, **9/9**, Cocoa and audio ready |

Nine added regression cases cover resisted/rejected actual tools, hidden-target/foreign-feedback boundaries, immutable/validated prop state, bounded/deduplicated/expiring events, interaction hints, hearing-based stereo, mix/pause/reset/exit, authoritative concealment/deck filtering and actual scene pause/retry timing. Cosmetic helpers do not each get a separate test file.

Native screenshots were inspected for prop states, reduced effects, both-floor camera placement, actual tool counters/rejections, and the existing Human scene. The fixture camera was corrected to the current 96-pixel map scale; its props remain labeled diagnostic overlays. Default gameplay receives an empty environment view until SR2 supplies real objects. The reviewed tool HUD retains remaining charges while showing USED/EMPTY/MISS/RESISTED feedback.

The first screenshot helper wrote directly from a native display surface and stalled during PNG encoding. It was stopped; the fixture now exports the project's explicit opaque RGB canvas. The final fixture run completed normally. Earlier fixture failures were not counted as successful evidence.

## Performance scope

A separate source export of baseline **`1d24b4b`** ran the same desktop profiler on the same machine, sharing unchanged world/character resources. The final run uses committed runtime `59fffba`, including reuse of one snapshot per event batch. An earlier profile is retained separately under ignored output; it is not the final measurement.

| Measured workload | P04 baseline | P05 presentation |
| --- | --- | --- |
| Update median / p95 | 1.641 / 2.175 ms | 1.770 / 2.305 ms |
| Draw median / p95 | 6.246 / 19.392 ms | 6.499 / 19.643 ms |
| Total p95 | 22.318 ms | 22.674 ms |
| Python growth after warmup | 1.045 MB | 1.056 MB |
| Final six RSS samples, span | 74.85 MB | 9.95 MB |
| Final RSS versus warmup | -55.94 MB | -99.44 MB |

CPU draw cost and total p95 are close in these samples; compositor scheduling makes total medians unsuitable as a speedup claim. Python tracing adds overhead, so this does not promise 60 fps on every device. Both reports pass the existing budget of under 4 MB Python growth and final-six RSS below warmup +64 MB. RSS can fall through OS compression; this short run does not prove absence of every long-session leak. The real Human sweep separately measured draw/audio/present median 7.88 ms, p95 8.66 ms; its cold/resize maximum was 526.1 ms and it excludes simulation.

The new presentation bounds are 32 effects, 128 pending environment audio cues, 1,024 remembered presentation IDs, 4,096 remembered audio IDs and 12 mixer channels. Door material/shadows, canister angles, shard layouts and effect rings use bounded caches. Camera/deck culling and read-only state keep presentation separate from gameplay. Full whole-game, low-end and long-session acceptance remains P07.

## Builds and limits

The local Mac app and fresh ZIP both pass 9/9 native checks with audio ready. Archive: `dist/echo-heist-0.1.0a1-macos-arm64.zip`, 112,442,571 bytes, SHA-256 `48e8d5a0a5e1c7bf6179ddd7c72b4a8d78ba5c059fbb30179d29d16dfa6c499a`. The build manifest records clean source `59fffba`; its original smoke marker is historical and the separate successful reports are authoritative.

[Runtime CI run 41041860894](https://github.com/khalid999devs/Echo_Heist/actions/runs/41041860894) passes all three jobs: Linux source/headless checks and Windows x64/macOS arm64 checks, primary builds and frozen dummy-video smoke. Detailed results are in EVIDENCE.json. Hosted native packaging/dummy-video smoke is distinct from physical Windows gameplay/audio. Linux source/headless checks do not establish a Linux desktop release. Primary clean-machine and release gates remain P08.

Four original mono PCM cues are reproduced by `scripts/authoring/interaction_audio.py` without external samples, licensed under the project MIT license. Exact asset hashes/bytes and original recording licenses remain in the packaged manifest/CREDITS. The existing locker image is reused at runtime; no new third-party graphics or dependency is introduced.
