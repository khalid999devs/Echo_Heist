# Runnable scene and facility handoff

Owner: Khalid. Scope: user-authorized fullscreen/layout/audio/facility follow-up, completed scene presentation on the integrated P02/partial-P03 baseline. Original Suhita commits and ownership remain preserved. [Review and evidence](../../../../quality/reports/facility_finish/REVIEW.md); [consumer contract](../../../../architecture/integration/SCENE_PRESENTATION.md). Exact runtime/build commit is in the review's BUILD.json.

## Run and inspect

```sh
uv sync --locked --all-extras
uv run --locked echo-heist
uv run --locked python scripts/checks/run.py
```

Windows x64 uses these commands from PowerShell after the documented Windows prerequisites; keep the entire PyInstaller folder beside its EXE. Mac uses the new native ZIP recorded in BUILD.json. Fetch main before starting a fresh owner branch; do not resume one of the retired integration branches.

Play Chapter → Human → Launch. WASD walks; hold Shift for the approved three-second louder sprint, then four-second recharge. Q Echo, F EMP, Space emergency stun, hold E at the core, E at stairs; Tab pauses on the two-deck map, Esc pauses. Quiet walking remains responsive. Move to interrupt a climb. Recover the core and return downstairs to the green extraction marker.

In Settings, test fullscreen on your display, both volume sliders and reduced flashing. The picture must reach all display edges; labels, controls and hit rectangles must agree. Check pause → Settings → Back → Resume retains the exact mission. The title keeps the original chamber illustration; a successful extraction uses its separate exterior scene. Report is available after an actual result. Workshop/Companion/Guide are navigable designs with availability stated; they do not fabricate AI results.

Inspect the laboratories and service rooms for distinct fitted equipment, correct one-seat/two-monitor desk logic, softer grounding shadows, interrupted work, displaced chairs and varied plant health. Cover is physical. Five dark maintenance recesses are prepared for P05; actual concealment is deliberately not active yet.

## Consumer details

- Use `logical_size_for`, `interface_canvas` and `interface_events` in `ui/render/layout/viewport.py`; fixed interface rectangles stay in the centred design space. Full backgrounds and mission rendering use the full canvas. `GameFlow.resize` preserves the live session and resizes its camera.
- Keep the 96px tile conversion data-driven. Furniture `appearance`/`condition` are optional validated metadata; physical flags are separate. Displaced chairs block bodies but not sight/sound. Story marks and utility pipes have no simulation effects.
- Hide IDs stay stable: hide-1 (20,18), hide-2 (29,26), hide-3 (35,15), hide-4 (44,29), hide-5 (50,24). Five existing cover blockers retain their original coordinates. Read the generated map for footprints; never hard-code art bounds into collision.
- `FurnitureVisual.depth` keeps recess art behind the operative until a future authoritative concealment state exists. Cached art now includes 47 source props; 101 physical furnishings plus five covers/five recess visuals are separately sorted.
- AudioFrame now carries listener ID, permitted heard-event IDs, room style, own sprint recharge, settings values and visible suspicion. Presentation never publishes noise or mutates guard knowledge. Mixer channels: UI0, critical1, siren2, ventilation3, ordinary4–11.
- Audio provenance is packaged in `resources/assets/audio/manifest.json` and CREDITS.md. Raw art is preserved, with prompts/hashes in the review. Only walking WAVs are processed derivatives.

## Verification and boundary

127 behavior checks, strict types over 97 source files, lint/format/structure pass. Both default-security Human routes, capture, 48 scene states, 30 responsive native states, all four movement facings and 19 architectural previews pass. The real bootstrap fullscreen check reports audio ready and settings saved. Exact native app/fresh-ZIP and hosted results are recorded separately in BUILD.json, without treating CI configuration as execution.

Clean runtime `28aff88` produces the current 106,402,812-byte Mac ZIP; its native app and fresh extraction each pass all eight Cocoa frozen checks with audio ready. Hosted run [39679169548](https://github.com/khalid999devs/Echo_Heist/actions/runs/39679169548) passes Linux checks and native Windows/Mac builds with frozen dummy-video smoke. Exact SHA256 and environment are in BUILD.json. CI artifacts are downloadable from that run; a dummy-video runner is not Suhita's interactive Windows test.

Interactive Windows display/audio/download checks still need Suhita's hardware. Full P03, P04-P08, final scoring/policies and P05 environment interactions remain pending. Source license/public-release gates are unchanged. Continue the assigned phase queue from the updated contract; do not mark the whole game complete from this presentation pass.
