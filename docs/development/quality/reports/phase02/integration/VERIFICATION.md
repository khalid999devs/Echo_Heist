# Phase 2 combined verification

Date: 2026-10-20, Asia/Dhaka. Candidate: `work/p02-integration`, based on Suhita's `a98548a` (which already includes Khalid's `fd93224`). The user's direction on 2026-10-20 transferred final P02 integration review to Khalid. The source PDF SHA256 remains `64fc08b2725796211931d28550a95557e09ddf3c43f3d66c774e6354e36dedda`.

## Review decision

Suhita's map export, typed importer, geometry/anchor/branch validation, scene composition and map-route tests were kept. Her branch passed 66 local cases before the review. The baseline title and heist were flat greybox screens with no art, weak actor/room readability and no mouse menu path; her branch also had no completed handoff or Windows interactive result. The integrated branch adds original facility/operative art, map-aligned 2.5D drawing, clearer objective/status/minimap, cinematic menus/results, letterboxed pointer input and real scene-flow tests. No gameplay mutation or scoring was moved into UI code.

## P02 functional gate

| Gate | Result | Evidence |
| --- | --- | --- |
| Five named zones, upper/lower branches, cross-link, unique Core/Exit/Spawn and tagged collision/glass/cover | PASS | Packaged `vault-five-zone` loader and invalid-map tests; map is 64×36 at 32 pixels/tile |
| Human input, continuous movement, sprint, collision and legal Core hold | PASS | Real `GameFlow` scene test; core simulation tests |
| One Core theft, immediate lockdown and original-exit extraction; no-core exit cannot win | PASS | Upper, lower and cross-link simulation routes; actual scene win at tick 1204 using seed 1042 |
| Contact capture and result/retry/pause | PASS | Actual scene capture by `guard-service` at tick 169; paused 5000 ms added zero ticks; same-seed retry and result navigation passed |
| Mouse/keyboard menu and resized window pointer mapping | PASS | Scene test covers title/mode mouse action and 1280×1440 letterbox coordinate mapping |
| Stationary guard scope | PASS for P02 | Guard posts are rendered and physical capture works; active sensing/patrol algorithms remain assigned P03 |

The source command `uv run --locked python scripts/checks/run.py` passed structure (1000 lines/6 files), Ruff lint/format, strict mypy across 53 source files, and **69 tests** on macOS arm64/Python 3.13.16. The new integration tests drive the real `HumanInput` and `GameFlow`, rather than calling mission internals to force a result.

## Native and visual evidence

The six screenshots below were captured on a macOS Cocoa display through the same offscreen-canvas path used by `ui/bootstrap.py`. They are scripted input/render inspections; human keyboard feel was not measured.

- [Title](screens/native-five-zone-title.png)
- [Human briefing](screens/native-five-zone-mode.png)
- [Playable heist](screens/native-five-zone-heist.png)
- [Lockdown after Core theft](screens/native-five-zone-lockdown.png)
- [Real win result](screens/native-five-zone-win.png)
- [Real capture result](screens/native-five-zone-capture.png)

`uv run --locked --all-extras python scripts/packaging/build.py` produced an arm64 app/ZIP with the packaged map and both original art resources. `uv run --locked --all-extras python scripts/packaging/smoke.py "dist/Echo Heist.app" --mute --output-dir output/phase02/integration-native-smoke` passed all eight frozen headless/Cocoa/resource/settings/hash assertions. This initial build preceded the final metadata/visual-evidence commit; the clean candidate archive and hosted CI are recorded below after publication.

Clean candidate archive: PENDING clean build after integration commit. Hosted macOS/Windows/Linux CI: PENDING branch push. Interactive Windows x64 desktop: **NOT_RUN** on Suhita's machine. Native macOS keyboard feel/accessibility check: **NOT_RUN**; scripted Cocoa rendering and frozen smoke are PASS. No Windows or public-release claim is inferred from the Mac screenshots.

## Scope boundary

P02 closes the Human mission and map/scene gate. The menu backdrop is an original pre-rendered 2.5D illustration, while actual gameplay uses the validated Tiled geometry and procedural rendering. Guards are stationary contact posts in P02; sight/hearing/patrols belong P03. Autonomous Companion belongs P04; final environment/tool effects, Workshop, approved scoring, audio and broader accessibility belong P05-P07. The result screen reports actual unscored outcomes and does not fabricate a rank.
