# Core security and stun review

2026-11-20, Khalid. The runtime revision is `ec55029`, with the doorway regression fixture corrected in `c3e2c74`. This replaces the balance and replay baseline in the [two-exit verification](REVIEW.md).

## Gameplay

- Five defenders now patrol the facility. A BFS Sentinel sweeps the east side of the Core chamber, while the existing Interceptor covers the lower approaches and can man either return gate.
- The view cone widens from 100° to 112° across. Opaque geometry still clips it with the same ray test shown by the renderer. Amber indicates patrol/identification and red highlights confirmed pursuit. Guards keep their rear blind spots. The F3 panel can select all five defenders by mouse or number key.
- Intruder-to-guard body clearance grows from 0.40 to 0.52 tile between centers. A stunned body still occupies space. A stun buys time to go around it. Movement, stair landings and locker entry use the same check. The fingerprint schema is 15.
- Both a stun and resisted impact play one clang from the same committed noise event that guards hear. A rejected strike plays the unavailable cue and emits no impact. Reception depends on acoustic distance and blockers. A responding guard receives the impact's original tile and tick.
- Companion recovery holds its route through routine risk changes. A new goal, changed geometry or blocked movement can still trigger replanning. The former Ghost stair loop in `s16-service-corridor-late` now reaches the Core and is captured at tick 3380.

## Playthroughs

Seed 1042, production map and props, scripted keyboard inputs through the native Cocoa scene. CoreAudio was ready and all 33 audio assets loaded. Clips in `output/core-security/` use actual gameplay frames. Their audio uses shipped samples placed at the corresponding gameplay events.

| Attempt | Outcome | Tick |
| --- | --- | ---: |
| Security approach, sprint-only Research return | Core Sentinel captures the operative after lockdown | 738 |
| Research approach, Security return with tools | Entry Airlock win | 1520 |
| Security approach with a 45-tick delay, Research return with tools | Cargo Airlock win | 1221 |

On the Cargo run, the Security Sentinel heard the tick-560 strike near the approach and moved to investigate its origin at tick 561. The Core Sentinel started a grab at tick 705. A valid stun canceled it at tick 706. The operative took the Core at tick 799 and the Sentinel resumed pursuit at tick 808. The geometry and tool tests cover physical body blocking while stunned, and the audio tests cover single playback, resisted impacts and rejection. Listening tests cover a near guard hearing around cover, a far guard and a guard behind a sealed wall for both intruder types.

The Service Sentinel confirmed a sighting at tick 197. The operative broke the line of sight and entered the Service locker at tick 213 with the sprint on recharge. The guard searched and returned to patrol at tick 290. The operative stayed hidden through tick 463. The locked witnessed-cover tests confirm that Sentinels and Trackers can inspect cover they saw the operative enter.

A controlled open lane exercised sustained sprint independently of map corners. The Tracker confirmed sight at tick 18, the burst entered recharge at tick 108, and the Tracker captured at tick 386 despite uninterrupted sprint input. The slower Sentinel remained behind in that deliberately unobstructed lane through tick 500. On the production route, the Core pair caught the sprint-only operative after lockdown.

## Companion comparison

`uv run --locked python scripts/experiments/comparison.py --output-dir output/core-security/verified-comparison` ran the 24 authored starts under all four presets on the revised runtime. The first repeated case matched. Counts are controlled AI outcomes.

| Preset | Wins | Captures | Runner caps |
| --- | ---: | ---: | ---: |
| Ghost | 2 | 22 | 0 |
| Balanced | 3 | 21 | 0 |
| Rush | 6 | 18 | 0 |
| Custom | 3 | 21 | 0 |

The earlier candidate scored 35 wins from the same 96 starts. This candidate scores 14 wins. Both production Human exits succeed on seed 1042. Balanced Companion wins at tick 2826 with grade B on seed 1042 and at tick 2052 with grade A on seed 23. The approved score weights and melee limits are retained.

## Package and verification

- `uv run --locked --all-extras python scripts/checks/run.py` passed structure, lint, format, strict mypy and all 336 tests on the clean candidate.
- `uv run --locked --all-extras python scripts/packaging/build.py` built the Apple Silicon ZIP from clean `c3e2c74`. The archive is 114,108,348 bytes. SHA-256 `398cbcb8557cff94a4dd1b8a4b335b335c8f2c5864ee356e14d266580b7dd336`. Fresh extraction passed codesign verification and all nine checks with native Cocoa and audio ready. The app is ad-hoc signed.
- Eight native restart/resize cycles covered both modes and 720 frames. Memory stayed bounded in this sample. A full Balanced run finished at tick 2826 with the alarm active during lockdown. In the isolated repeat, total frame p95 was 16.66 ms in infiltration and 16.77 ms in lockdown. Draw p95 was 3.83 ms and 4.93 ms. A single lockdown presentation outlier brought one total frame to 1.12 s. Raw results are in `output/core-security/performance-isolated/PERFORMANCE.json`.
- Hosted Linux headless checks and Windows x64 and macOS arm64 builds/frozen smoke passed on `c3e2c74`. [Candidate CI](https://github.com/khalid999devs/Echo_Heist/actions/runs/44619233603).
- Physical Windows gameplay, sound, download and pace measurements remain part of P08.
