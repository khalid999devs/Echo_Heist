# Runnable scene presentation handoff

Khalid, user-directed continuation of the two-floor draft, 2026-10-21. Branch `work/complete-visual-scenes`, baseline main `1d34f3b`. [Contract](../../../../architecture/integration/SCENE_PRESENTATION.md), [native review](../../../../quality/reports/scene_presentation/REVIEW.md) and [actual build record](../../../../quality/reports/scene_presentation/BUILD.json). P03 remains partial; P04-P08 remain open. This is a presentation handoff, not completion of those shared phases.

## Run and inspect

```sh
uv sync --locked --all-extras
uv run --locked echo-heist
uv run --locked python scripts/checks/run.py
```

Windows PowerShell uses the same three commands from the checkout; close an older running app before updating. Keep any local work on its branch. Use the new native Windows CI archive only after its build record says PASS; Mac ZIPs cannot run on Windows.

1. Click anywhere on Chapter 01 → briefing → Launch. WASD move; Shift uses the approved three-second louder sprint/four-second recharge; E climbs/recovers Core; Q Echo, F EMP, Space stun; Tab pauses on both floor plans. The seed remains 1042, two original routes/cross-link and all 14 rooms/63 furnishings remain.
2. E on either landing starts an 0.8-second architectural climbing animation. Move to cancel. Pause/map freeze it; blocked landings cannot overlap actors. Following Core recovery, hear the continuous siren and see smooth red fixture pulses; guards move 20% faster and search longer. Reduced Flashing makes lights steady.
3. Esc opens mouse/keyboard pause buttons. Open Settings, drag volumes, go Back and resume the same frozen run. Tab map has a working Close button. Abort requires its own confirmation. Retry resets the mission.
4. Choose Companion in the briefing → edit Workshop presets/four choices → preview either floor and drag the detailed map. Deployment is intentionally unavailable until P04; no fake decisions run. The draft stays only in memory. Field Guide is available from the title and separates current behavior from planned AI.
5. Complete a real extraction → Encrypted Transmission opens the source's replication-seed epilogue. Success uses separate exterior dawn art; capture/abort show the interrupted facility. Results are still unscored until P06.

## Consumer changes

`core/contracts` adds own stair progress, presentation-only StairView, STAIR_STARTED/CANCELED and required GameRules stair/lockdown fields. Fingerprint schema **5** supersedes old hashes. Read the contract for ordering and occupancy rules. Controllers must use own progress/filtered observations, wait while climbing and never consume UI snapshots. HumanInput and the QA driver already follow that rule.

`ui/scenes/design` holds local presentation drafts/layouts; it does not implement Suhita's policy validation/persistence. Presets match blueprint p. 14. Wire real profiles/Companion observations in the assigned later slices and remove preview labels only when actually working. Do not use this local draft as a second policy source. `navigation/controls.py` shares draw/hit geometry. New scene names are WORKSHOP/LAB/GUIDE/EPILOGUE; `HeistRequest.SETTINGS` returns to the paused run. Audio channel 2 is reserved for continuous siren; ordinary SFX start at 3.

WorldArt now supplies 16 directional Human frames, 12 defender frames grouped by type and four Companion poses. Props retain aspect ratio within authoritative footprints. Resources are original PNGs with exact prompts/hashes recorded; no source PDF or inspiration screenshot changed. Environment render, root render, character assets and architecture integration directories are at six direct files; regroup before adding files. Scene designs are grouped under `ui/scenes/design/`. Tests remain under root tests; core unit directory is also full.

## Actual evidence and remaining work

Implementation commits: `e8e73a9` (stair/lockdown), `407be30` (scene/art/navigation) and final runtime `19b454b` (SDL focus click). Later commits record verification only. The clean runtime Mac ZIP is **55,313,813 bytes**, SHA256 `d2696bb0c916166645afc9ea5b8777f6ffc3aa30be09cb9fa0c32175875f66c6`; app and fresh extraction each pass eight native Cocoa checks with audio. [Hosted source CI](https://github.com/khalid999devs/Echo_Heist/actions/runs/39634968086) passes all three platform jobs including native Windows/Mac builds and frozen dummy smoke. Use BUILD.json for exact source/artifact scope. This replaces the older Mac download at the same filename.

Matching Windows archive: `dist/echo-heist-0.1.0a1-windows-x64.zip`, **56,619,251 bytes**, SHA256 `2008d37b35e552202f8c03526bc0b2f9cf01ff375d2b10aa1aeb042c5dae156a`. Downloaded from the passing source CI, hash verified, eight frozen dummy checks PASS. Extract on Windows and run `EchoHeist/EchoHeist.exe`; it is unsigned. Interactive Windows QA remains open. Source development uses `uv` commands above; never run the Mac bundle on Windows.

117 tests / strict types / lint / formatting / structure PASS. Native 48-state review, both route wins, capture/abort and audio context/lifecycle PASS; exact commands/results/screens are linked above. Local app/ZIP and hosted platform status belong in BUILD.json, distinguishing native display smoke from dummy CI. Interactive Windows, subjective sound mix, minimum hardware and quarantined download acceptance are not claimed. Development hours are not invented.

Remaining backend queues and approved scoring are unchanged. Glass breaking, doors, hiding and canister mechanics remain P05 by explicit instruction. No advanced AI, persisted Workshop profile or scoring system is represented as complete. Run the relevant P03/P04/P06 gates when those consumers connect.
