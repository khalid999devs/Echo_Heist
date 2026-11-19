# Two-exit desktop candidate verification

2026-11-19, Khalid. The clean source build used `65160e99406aef8c7b1e12018521abc8f309f307`. Main merge `876c7bdc28d75a90a117dc81821f461c86f6e3e0` has the same tree. Game 0.1.0a1, fingerprint 14, Python 3.13.16, pygame-ce 2.5.8, SDL 2.32.10. Local Mac is Apple M4, 16 GiB, macOS 26.4.1 arm64.

Suhita's approved score, profile/history/preferences service and experiment runner were accepted from [PR #9](https://github.com/khalid999devs/Echo_Heist/pull/9). The exact PR head passed 328 local locked tests before the second exit work. [PR #10](https://github.com/khalid999devs/Echo_Heist/pull/10) adds Cargo Airlock, stronger pursuit, recovery from AI retreat loops, title history access, the Workshop NEXUS memory switch and real decision notes in terminal reports.

## Balance and behavior

- The cargo route adds a loop through the southern service wing on the existing 64 × 40 tile atlas. The two stairs and Security/Research cross-link remain. Entry is `(3,24)` and Cargo is `(25,37)`. The core carrier can use either after lockdown. Capture keeps same-tick precedence. The map, HUD, both extraction pads and the win report identify the routes.
- Confirmed chase uses **140%** of each guard's normal speed as soon as identification completes. Lockdown routines use **120%**. Simulation takes the larger multiplier, preserving identification, occlusion, last-seen search and tool timing. The player walks at 2.4 tiles/s and sprints at 4.0 tiles/s for three seconds with four seconds of recharge. Tracker chase is 3.36 tiles/s and Interceptor chase is 3.92 tiles/s. Sustained timed sprint averages about 3.09 tiles/s. Breaking sight and using cover or a tool buys time.
- Kept two Sentinels, one Tracker and one Interceptor. The faster-chase trial at 145% failed the witnessed Tracker hide regression. The 140% candidate passed it and both Human escape paths. Extra guards were unnecessary for this difficulty pass.
- Interceptor hypotheses include both escape goals under lockdown, using only original evidence and public geometry. The Companion chooses from the two exits by observed-risk path cost and has a bounded recovery trigger after 900 ticks without moving closer to an objective. Recovery still uses legal actions and visible threats, and real grabs and tool limits apply.
- Approved score weights and grade thresholds are unchanged. For the current 900 s draft pace reference, all sampled successful runs reached 10 pace points. The score calibration still needs real Human timings. This release candidate records actual MCTS and Interceptor decisions without changing score math or the Simulation's replay event stream.

## Playthroughs and traces

Native Cocoa with mixer ready. The Human attempts used scripted keyboard input on the same live production map, guards and props. A fresh data directory and reset NEXUS memory were used for the baseline. The video is an edited 35.6 s excerpt with shipped gameplay music. Playthrough times are simulation ticks.

| Mode and route | Seed | Outcome | Tick | Score / rank | Encounters |
| --- | --- | --- | ---: | --- | ---: |
| Human, Security return → Entry | 1042 | WIN | 1452 | 60 / B | 4 |
| Human, Research return → Cargo | 1042 | WIN | 1172 | 64 / B | 3 |
| Companion, Balanced → Cargo | 1042 | WIN | 2063 | 64 / B | 3 |
| Human, exposed unassisted Service approach | 1042 | CAPTURED | 679 | 0 / F | 2 |
| Companion, Balanced | 4 | CAPTURED in locked integration test | 662 | 0 / F | — |

Same-seed Human retry returned to briefing and relaunched at tick zero. Title Report after relaunch loaded four real scored attempts. Saved reports retained actual MCTS visits and alpha-beta post/node evidence. The Workshop memory switch round-tripped, and the connected tests covered saved policies, remap and accessibility persistence. Native views include the two-exit map, Cargo escape, both results, Workshop, live MCTS and saved report. The previous prop walkthrough reached the cross-link door on this candidate. Its fixed north-door approach can now be intercepted or reopened by a guard. A separate native run used controlled adjacent starts with real keyboard inputs, full security and the shipped prop engine. It confirmed all 13 props (three doors, two panes, three canisters, five lockers), once-only shatter cues and 36 mixer submissions. Controlled starts are interaction QA.

## Locked checks and 96-run comparison

```sh
uv run --locked python scripts/checks/run.py
uv run --locked python scripts/experiments/comparison.py --output-dir output/release-candidate/comparison-delivery
uv run --locked python scripts/quality/profile_desktop.py --output output/release-candidate/performance --complete-mission
```

Structure, lint, formatting, strict mypy and **330 tests passed**. T01–T08 and related regressions cover first launch, real Core theft, acoustics, evidence expiry, EMP capture ordering, physical interception, deterministic policies/replay and carrier-only extraction. [Hosted checks on the runtime](https://github.com/khalid999devs/Echo_Heist/actions/runs/44552230940) passed Linux headless, Windows x64 build/frozen smoke and Mac arm64 build/frozen smoke.

| Policy | Wins / 24 | Captures | Runner caps |
| --- | ---: | ---: | ---: |
| Ghost | 3 | 21 | 0 |
| Balanced | 10 | 14 | 0 |
| Rush | 10 | 14 | 0 |
| Custom | 12 | 12 | 0 |

The pre-recovery candidate reached the runner cap six times. All 96 final cases resolved and the first case's repeated fingerprint matched. All 35 wins in this suite chose Cargo. An extra controlled near-Entry start with the Core verified an actual Companion entry extraction at tick 12. Ghost remains the lowest-win policy in this fixed suite. This is a comparative experiment, with some scenario starts near the objective, so the proportions are distinct from a human playtest win rate.

The run recorded 1,796 MCTS decisions, 288,908 A* expansions and 1,369 Interceptor searches pruning 11,858 branches. Median across per-run p95 simulation time was 1.64 ms, maximum per-run p95 was 4.31 ms. Deterministic hash is `1c8d6f4d86df1ced4e8b484156f9436d340b7b0f721a6343ac60308dbaa66ba5`. [Per-run CSV](COMPARISON.csv). Suhita's [original comparison](../../experiments/POLICY_COMPARISON.md) remains attributable to its earlier map and source.

## Native performance and packaging

Twelve Cocoa restart/resize cycles measured 3,600 frames across Human and Companion. The warm sample had 16.804 ms p95 total frame time, 5.323 ms p95 draw and 26.177 ms maximum total. Final RSS was 5.25 MiB above warmup with a 27.29 MiB span in the last six samples. Memory stayed bounded over this run. The full Balanced win had 16.72 ms infiltration and 16.734 ms lockdown p95 frame time and the alarm played. The run used no Python allocation tracing.

The clean Mac package was built with PyInstaller 6.22.3. The extracted ZIP passed codesign verification and all nine frozen smoke checks with Cocoa video and audio ready. On that run, the first logo appeared at 333 ms and the opening reached the menu in 8.54 s. The app is ad-hoc signed. Clean-machine download/quarantine handling remains a release check.

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `dist/echo-heist-0.1.0a1-macos-arm64.zip` | 114,107,999 bytes | `9be7dad1a0546e3a41caa599175ac9d0bd7bf49a1b1de7748a2103d56c22d09f` |

[Windows CI on the matching main tree](https://github.com/khalid999devs/Echo_Heist/actions/runs/44553112638/job/135661834459) built the unsigned x64 ZIP (112,604,922 bytes, SHA-256 `64fc32f35a152744ee8d8202a6b9ed2b4c44f7f466c4bed2030bbe5a4abc107f`) and passed the dummy-video frozen smoke. GitHub reported its artifact quota was full, so that ZIP is unavailable to download. A native Windows rerun can produce a new archive from the same source.

## Scope and delivery gates

- **R01–R09, R27.** Both Human routes, autonomous outcome, Core/lockdown/ending, stealth, shared tools, hiding/prop lifecycle and sound/visual feedback. The exact suite covers each lifecycle. Earlier connected native audio/prop evidence remains recorded. [Connected review](../../../tracking/handoffs/khalid/day_04/CONNECTED_REVIEW.md).
- **R10–R16, R20, R23.** Real BFS/FSM/fuzzy, A*, minimax/alpha-beta, NEXUS, MCTS, editable Workshop and filtered controller boundaries. Verified with live traces and the repeated suite.
- **R17–R19, R21–R22.** Menus, seed/retry, settings/accessibility, profiles, history and score/decision evidence. Native review is supplemented by locked navigation, corruption recovery and audio tests.
- **R24–R26.** Mac candidate archive verified. Physical Windows Human/props, exact download acceptance and player pace calibration remain. The older Windows result is linked below. Public GitHub visibility, owner licensing, itch.io publication and academic submission are open. The Mac build/source/demo are a desktop candidate.

[Earlier Windows checklist](../phase08/suhita/WINDOWS_QA.md) · [Current player guide](../../../release/draft/PLAYER_GUIDE.md) · [Release plan](../../../release/RELEASE_PLAN.md)
