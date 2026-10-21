# Cinematic interface and first stealth slice review

2026-10-21, Khalid. Branch: `work/stealth-vertical-slice`; starting main: `9ea201f`. This supersedes the previous P02 presentation captures. P02 remains complete; this starts a **partial P03 Sentinel/perception slice**, not full V1 completion. The [runtime contract](../../../../architecture/integration/STEALTH_SLICE.md) and [runnable handoff](../../../../tracking/handoffs/khalid/day_02/STEALTH_SLICE.md) describe the boundary.

## Implemented and visibly exercised

- Owner-approved cinematic 3D-rendered chamber with subtle pan/dust/light animation; continuous gradient behind futuristic type and shared translucent controls. Gameplay remains a genuine 2D top-down mission.
- Six-item main menu, honest unavailable Companion/Workshop states, real last-session report navigation, independent persisted music/SFX sliders, reduced flashing and fullscreen.
- Compact objective/waypoint, elapsed time, actual guard alert state, tool stocks and small minimap. Base HUD panels occupy about 10.5% of the logical canvas; transient notices/progress keep total below 20%. Explicit Tab/F3 dialogs are optional overlays.
- Nine Entry/Service furnishings with matching map-owned physical/opaque/acoustic footprints, room-appropriate sprites, clear route lanes, contact shadows, darker closed roofs and cover art fitted to actual cover cells. This is the first furnished cluster; the entire facility is not yet a finished interior.
- One live Sentinel: real BFS patrol, sight cone, progressive identification, heard-only investigation, chase, last-seen search/expiry and return. Actual movement drives gait/facing. F3 shows real BFS, memory, identification and fuzzy values. Other three posts retain P02 contact behavior.
- Real Core hold/theft, changed lockdown objective/music/emergency lights, empty socket, extraction, capture and interruptible EMP/melee. A disabled robot remains a solid body. HUD labels disruption rather than suggesting immediate active pursuit.
- Five CC0 context tracks and eleven event cues, licensed and hashed in the [audio record](../../../../assets/AUDIO.md). Playback follows committed events and cannot alter guard knowledge.

## Native screens inspected

The screenshot driver uses Cocoa, actual GameFlow/HumanInput actions and asserted scene/outcome transitions. It exports explicit RGB because unused Cocoa display alpha produced blank previews in some viewers. All **31** current images are opaque. The source sweep asserts a genuine upper-route win using EMP, a live Sentinel capture and voluntary abort; it never forces an outcome. This is scripted inspection, not a human playtest.

| Group | Screens | Review |
| --- | --- | --- |
| Main menu | [Human focus](screens/menus/01-title.png), [Quit focus](screens/menus/02-title-quit-selected.png) | Stable focus and continuous cinematic blend |
| Briefing | [Human](screens/menus/03-human-briefing.png), [Companion unavailable](screens/menus/04-companion-unavailable.png) | Clear launch/disabled choices and explanation |
| Settings | [Default](screens/menus/05-settings.png), [Adjusted](screens/menus/06-settings-adjusted.png) | Visible slider values, selection and back controls |
| Honest missing screens | [Workshop](screens/unavailable/workshop.png), [No report yet](screens/unavailable/empty-report.png) | Plain explanation; no fake configuration or report |
| Normal mission | [Entry](screens/gameplay/01-entry.png), [Core hold](screens/gameplay/05-core-link.png), [Lockdown](screens/gameplay/06-lockdown.png) | Open view, real progress/return objective and removed Core marker |
| Dialogs | [Route](screens/gameplay/02-route-guide.png), [Pause](screens/gameplay/03-paused.png), [Abort confirmation](screens/gameplay/04-confirm-abort.png) | Background blur and clear input/consequence text |
| Sentinel | [Patrol](screens/stealth/patrol.png), [Suspicious](screens/stealth/spotted.png), [Chase](screens/stealth/chase.png), [Disabled](screens/stealth/disabled.png), [Search](screens/stealth/search.png), [Return](screens/stealth/return.png) | Sensor-clipped cones and labels follow committed behavior |
| Feedback | [Echo](screens/feedback/echo.png), [EMP](screens/feedback/emp.png), [Melee out of range](screens/feedback/melee.png), [Live Lab](screens/feedback/live-ai-lab.png) | Actual inventory/response; diagnostics clearly optional |
| Outcomes | [Win](screens/outcomes/01-win.png), [Capture](screens/outcomes/02-captured.png), [Abort](screens/outcomes/03-aborted.png), [Retry hover](screens/outcomes/04-retry-hover.png), [Menu hover](screens/outcomes/05-menu-hover.png) | Factual unscored results and stable action focus |
| Window sizes | [960×540](screens/display/01-small-window.png), [1024×800](screens/display/02-tall-window-letterbox.png) | Preserved aspect and visible controls |

The earlier [seven-second cinematic clip](cinematic-preview.mp4) remains a title/gait sample from before the active Sentinel and compact HUD. It is not current gameplay/AI evidence.

## Actual verification

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/checks/run.py
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/quality/capture_ui.py --output output/vertical-slice/final-evidence
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked --all-extras python scripts/packaging/build.py
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked --all-extras python scripts/packaging/smoke.py "dist/Echo Heist.app" --output-dir output/vertical-slice/frozen-app
```

PASS: **89 cases**, Ruff lint/format, strict mypy over **72 source files**, 1,000-line/6-file structure rules. Meaningful new cases cover sight/glass/corners/acoustics, shortest BFS, bounded fuzzy output, anonymous cues, hidden-position invariance, report expiry, capture interruption, active-guard replay, furniture errors/layer order and an actual lower-route extraction with the live Sentinel.

An accelerated native audio-enabled playthrough at `8fd87db` completed WIN in 1,287 rendered frames, exercised all five music contexts from actual states, loaded all 16 audio assets and emitted 108 cues. Update/audio/draw averaged **7.77 ms**, p95 **8.43 ms**, excluding display/encoding. [Machine-readable result](NATIVE_PLAYTHROUGH.json). This is one local source measurement, not a complete FPS, minimum-hardware, subjective mix or final AI benchmark.

A clean `8fd87db` macOS arm64 app and freshly extracted ZIP each passed all eight Cocoa frozen-smoke checks with audio ready and 16 assets loaded. Final small label refinements are being rebuilt; the exact latest archive/commit and hosted CI result are recorded in the handoff when complete. No Windows interactive or Linux native release claim is made.

## Remaining work

The owner's full brief is still open: extend purposeful interiors and route pacing, finish Tracker A*, Interceptor minimax/alpha-beta, NEXUS, autonomous Companion/MCTS, Workshop/profile behavior, approved scoring and remaining production animation/cues. Glass breaking, doors, hiding and canisters remain P05 by explicit owner choice. Wider human play-feel, Windows speakers/input and clean-machine release QA remain NOT_RUN. Do not replace these with fake UI metrics or declare the full game polished.
