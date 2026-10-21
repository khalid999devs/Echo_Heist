# Two-floor lab, movement and visual review

Khalid, 2026-10-21; baseline main `2be5f61`, branch `work/two-floor-atmosphere`. Owner-requested refinement, with the three-second sprint/four-second recharge explicitly approved in chat. [Actual consumer contract](../../../architecture/integration/TWO_FLOOR_LAB.md). Remaining shared phases stay open.

## Result

- Two real decks without expanding the 64×40 atlas: Entry/Service downstairs, Security/Research/Core upstairs, two reciprocal stair pairs, original branch alternatives and cross-link preserved. E uses a landing; held E does not bounce between floors. Guards navigate the same edges. Occupied destinations reject travel; walls separate sight and physical reach, while hearing follows the connected stairs.
- 14 purposeful rooms, 63 physical furnishings, closer 48-pixel presentation scale. Clinical lab floor/wall light, warmer service accents, planted desks, pumps, benches, test cells and server fittings. Screen indicators, tank bubbles and fans animate; actor idle/walk/run/facing follows committed movement. No visual change controls collision or AI sensing.
- Responsive 2.5 tiles/s walking and 3.7 sprint. A burst lasts up to 90 ticks; exhaustion or release starts 120-tick recharge at 30 Hz. Holding Shift while unavailable walks and later resumes. Only effective sprint emits louder sprint steps. Blocked attempts do not consume charge; pause/map freeze timers. Readiness is visible beside the tools.
- Less repeated menu copy, smaller chapter card, one Launch, short settings/pause, clear floor labels and paused two-floor map. Mission arrows point toward a stair when the objective is on the other floor. Feedback banners no longer collide with sprint readiness.
- Existing title art preserved. Successful extraction has a new original exterior dawn scene showing the secured core; failure/abort show the actual interrupted mission. No invented scores, ranks, achievements or Companion metrics. [Generation prompt/provenance](PROMPTS.md).
- Fixed a native Mac alpha-compositing defect, not just the shadow shape: default render surfaces inherited an alpha mask despite being opaque. Layered effects could clear destination alpha, producing dark sprite/prop rectangles. Explicit RGB targets fix the map, desktop canvas and screenshot path. Feathered contact shadows retain transparent corners. Native probes and a layered-alpha regression verify the correction.

## Actual verification

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/checks/run.py
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/quality/capture_ui.py --output output/two-floor-lab/alpha-verified
UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python output/two-floor-lab/check_audio.py
```

PASS: **111 behavior cases**, strict mypy over **80 source files**, Ruff lint/format and the 1,000-line/six-direct-file rules. New risk coverage exercises legal/occupied stair transfer, reciprocal import/deck validation, sound versus sight across floors, autonomous guard traversal/replay, exact burst/recharge/noise timing, blocked requests, one stair transfer per E press, pause freezing and the native alpha failure. Existing capture, tools, mission and fairness assertions remain.

Seed 1042, actual native Cocoa input sweep: **Security WIN tick 1507**, **Research WIN 1568**, **deliberate contact CAPTURED 698**, real abort/retry/report/pause. All seven Sentinel states observed. [Actual results](PLAYTHROUGH.json). These optimized QA inputs use real stock tools and are not novice completion-time or full-game balance evidence.

All **38 screen states** were captured and visually reviewed through contact sheets and individual full-size checks; after native alpha correction, the affected entry/lab/actor/ending views were checked again. Full files are under ignored `output/two-floor-lab/alpha-verified/`. Representative final native screenshots:

| Menus | Facility | Outcomes |
| --- | --- | --- |
| [Chapter](screens/ui/chapter.png) | [Entry](screens/facility/entry.png) | [Extraction](screens/ending/extraction.png) |
| [Briefing](screens/ui/briefing.png) | [Both floors](screens/facility/map.png) | [Capture](screens/ending/capture.png) |
| [Settings](screens/ui/settings.png) | [Stair landing](screens/facility/stairs.png) | [Abort](screens/ending/abort.png) |
| [Pause](screens/ui/pause.png) | [Research](screens/facility/research.png), [Core](screens/facility/core.png) | Actual mission facts only |

The review used a general-player usability checklist: one clear opening action, visible objective and next interaction, reachable controls, consistent focus/click regions, honest unavailable modes, floor awareness, meaningful feedback and a visible movement recharge. This is an engineering usability review, not an external gamer study. Polished global reception cannot be established by screenshots or scripted checks.

Native source audio run: **1,511 rendered frames**, WIN, all five music contexts from actual game states, 16 decoded assets and 134 cues. Paused map freezes mission time and ducks audio. [Actual audio/render timing](AUDIO_PLAYTHROUGH.json). Timings cover render/audio/display only on this Mac, excluding simulation updates; first-use audio work can cause a startup outlier. They are not minimum-hardware or cross-platform performance claims. No new audio download/license was introduced.

## Packaging and remaining boundary

Clean implementation **`123225bfda7698f505705436521cc09023118d02`** built successfully. Native Mac app and fresh ZIP extraction each PASS all eight Cocoa frozen smoke checks, audio ready. Archive **46,287,058 bytes**, SHA256 **`2a91cced913430b643e3dfc540f44ed3c53a69a3f41bffe90c08d64cc32ebbc6`**; Python 3.13.16 / PyInstaller 6.22.3 / macOS 26.4.1 arm64, ad-hoc signed/not notarized. [Actual build/smoke results](BUILD.json). The build manifest's smoke reminder is separate from these executed smoke results. [Runnable handoff](../../../tracking/handoffs/khalid/day_02/TWO_FLOOR_LAB.md) records exact commands and compatibility. Hosted CI [39608091170](https://github.com/khalid999devs/Echo_Heist/actions/runs/39608091170) has passing Linux/Windows jobs; the hosted Mac runner has not reported steps at integration. Local native Mac checks/build/smoke passed. BUILD.json keeps hosted startup separate from those results.

P03 remains partial: one autonomous Sentinel and three contact posts. Remaining defenders, registry, Companion/MCTS, Interceptor/minimax, NEXUS, Workshop and approved final scoring remain assigned work. Glass breaking, doors, hiding and canisters remain P05 by owner instruction. Interactive Windows hardware/audio/download, Linux native distribution, clean-download quarantine and full frozen mission playthrough remain separate checks.
