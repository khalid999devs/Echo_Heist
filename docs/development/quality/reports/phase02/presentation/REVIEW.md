# Phase 2 screen composition review

Date: 2026-10-21, Asia/Dhaka. Owner: Khalid, under the user's requested visual follow-up. Branch: `work/p02-ui-polish`; starting main: `9ea201f`. This review supersedes the earlier integration screenshots for current presentation. P02 gameplay scope and approved scoring are unchanged; P03 is not started.

## Result and visual decisions

The owner selected a **cinematic 3D-rendered facility scene with animation**, rather than a live real-time 3D diorama. The new perspective artwork shows the operative and Companion overlooking the reactor. Runtime camera drift, dust and a restrained light pulse animate that artwork. The gameplay environment remains the authoritative 2D Tiled mission.

- Replaced the title's top-down image and hard vertical divider with a perspective chamber and continuous dark-to-scene fade. Kept the reactor and characters visible while leaving quiet space for controls.
- Unified menus, HUD, notices and dialogs with rounded translucent glass, consistent light edges and soft fills. Removed the abrupt portrait card and the result screen's solid wall of color.
- Blurred the underlying mission for pause, route and abort dialogs; kept the heading, body and input hints clear. Disabled Companion selection has visible focus and a plain explanation.
- Removed phase numbers, simulation ticks, internal guard IDs and seed jargon from player-facing copy. Actual outcome/time/Core extraction status remain factual; no score is fabricated.
- Cropped props from explicit atlas regions to remove neighboring fragments, toned them to the environment, added contact shadows, reduced extra floor grid lines and softened actor/lockdown outlines.

## Screens inspected

All captures use the actual `GameFlow`, bundled assets and native macOS Cocoa display. Routes use real HumanInput actions; win, capture and abort are asserted against committed outcomes. These are scripted visual inspections, not a substitute for human playtesting or Windows desktop QA.

| Screen/state | Evidence | Visual inspection |
| --- | --- | --- |
| Title / begin selected | [Screenshot](screens/menus/01-title.png) | Clear title/action hierarchy, perspective scene and continuous blend |
| Title / quit selected | [Screenshot](screens/menus/02-title-quit-selected.png) | Selection moves without shifting controls |
| Human briefing | [Screenshot](screens/menus/03-human-briefing.png) | Launch and mode choices remain clear over scene |
| Companion unavailable | [Screenshot](screens/menus/04-companion-unavailable.png) | Focus/disabled state and explanation visible; launch unavailable |
| Mission entry | [Screenshot](screens/gameplay/01-entry.png) | Objective, inventory, route and quick controls readable |
| Route guide | [Screenshot](screens/gameplay/02-route-guide.png) | Dialog fits, underlying world is blurred, close key visible |
| Pause | [Screenshot](screens/gameplay/03-paused.png) | Resume/restart/abort instructions and layout explanation fit |
| Confirm abort | [Screenshot](screens/gameplay/04-confirm-abort.png) | Consequence and confirm/cancel keys clear |
| Core hold | [Screenshot](screens/gameplay/05-core-link.png) | Progress bar, objective and actor visible |
| Lockdown | [Screenshot](screens/gameplay/06-lockdown.png) | Return objective and non-color alert text clear; soft perimeter |
| Echo feedback | [Screenshot](screens/feedback/echo.png) | Tool notice fits and inventory updates |
| EMP feedback | [Screenshot](screens/feedback/emp.png) | Notice fits and stock reaches zero |
| Melee out of range | [Screenshot](screens/feedback/melee.png) | Failure guidance fits without hiding controls |
| Tactical telemetry unavailable | [Screenshot](screens/feedback/lab-unavailable.png) | Plain notice and close key fit |
| Win | [Screenshot](screens/outcomes/01-win.png) | Factual outcome, time and Core status; scene blends behind text |
| Capture | [Screenshot](screens/outcomes/02-captured.png) | Red accent has no hard cutoff; outcome/time readable |
| Abort | [Screenshot](screens/outcomes/03-aborted.png) | Amber outcome has same layout and controls |
| Result retry hover | [Screenshot](screens/outcomes/04-retry-hover.png) | Hover feedback stays inside the action |
| Result menu hover | [Screenshot](screens/outcomes/05-menu-hover.png) | Secondary action has visible focus |
| 960×540 window | [Screenshot](screens/display/01-small-window.png) | Full composition and controls retained at smaller scale |
| 1024×800 window | [Screenshot](screens/display/02-tall-window-letterbox.png) | Correct letterboxing; no stretched artwork or clipped controls |

The [seven-second clip](cinematic-preview.mp4) captures title drift/dust, menu selection and real walk/sprint input. It contains 210 frames at 30 fps. Source update/draw averaged 3.96 ms, p95 6.34 ms on this local run, excluding display/encoding. This is a presentation sample, not a full-game AI performance claim.

## Commands and actual checks

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/checks/run.py
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/quality/capture_ui.py --output docs/development/quality/reports/phase02/presentation/screens
```

PASS: 70 existing tests; Ruff lint/format; strict mypy across 56 source files; 1,000-line/6-file structure checks. No cosmetic unit tests were added. The native capture sweep asserts real win/capture/abort outcomes and saved 21 screenshots. A first requested 1024×900 window was constrained by macOS to 1024×820; the final capture explicitly requests 1024×800 and completes without that warning.

Final clean native build and hosted CI evidence: PENDING until the candidate is committed and rebuilt. The earlier integration archive predates this visual follow-up and must not be used as evidence for the new background.

## Reproduce and continue

Run `uv run --locked echo-heist`. Use arrows/mouse and Enter in menus, WASD/arrows to move, Shift to sprint, E at the Core, Tab for the guide, Escape to pause. The source and frozen app must use the same visual resource paths and logical 1280×720 canvas.

Windows interactive visual inspection and subjective human play-feel remain NOT_RUN. P03 guard AI and the owner's deferred P05 glass/door/hiding/canister mechanics remain assigned future work. Asset provenance and the exact adopted prompt are in [PROMPTS](PROMPTS.md) and the [asset register](../../../../assets/ASSETS.md).
