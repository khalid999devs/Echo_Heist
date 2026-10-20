# Phase 2 combined verification

Date: 2026-10-20, Asia/Dhaka. Candidate: `work/p02-integration`, based on Suhita's `a98548a` (which already includes Khalid's `fd93224`). The user's direction on 2026-10-20 transferred final P02 integration review to Khalid. The source PDF SHA256 remains `64fc08b2725796211931d28550a95557e09ddf3c43f3d66c774e6354e36dedda`.

## Review decision

Suhita's map export, typed importer, geometry/anchor/branch validation, scene composition and map-route tests were kept. Her branch passed 66 local cases before the review. The baseline title and heist were flat greybox screens with no art, weak actor/room readability and no mouse menu path; her branch also had no completed handoff or Windows interactive result. The integrated branch adds original facility/operative art, map-aligned textured floor/bulkhead/room furnishings, four-frame operative and guard strips, clearer objective/status/minimap, sci-fi font, cinematic menus/results, letterboxed pointer input and real scene-flow tests. No gameplay mutation or scoring was moved into UI code.

## P02 functional gate

| Gate | Result | Evidence |
| --- | --- | --- |
| Five named zones, upper/lower branches, cross-link, unique Core/Exit/Spawn and tagged collision/glass/cover | PASS | Packaged `vault-five-zone` loader and invalid-map tests; map is 64×36 at 32 pixels/tile |
| Human input, continuous movement, sprint, collision and legal Core hold | PASS | Real `GameFlow` scene test; core simulation tests |
| One Core theft, immediate lockdown and original-exit extraction; no-core exit cannot win | PASS | Upper, lower and cross-link simulation routes; actual scene win at tick 1204 using seed 1042 |
| Contact capture and result/retry/pause | PASS | Actual scene capture by `guard-service` at tick 169; paused 5000 ms added zero ticks; same-seed retry and result navigation passed |
| Mouse/keyboard menu and resized window pointer mapping | PASS | Scene test covers title/mode mouse action and 1280×1440 letterbox coordinate mapping |
| Stationary guard scope | PASS for P02 | Guard posts are rendered and physical capture works; active sensing/patrol algorithms remain assigned P03 |
| Walking/sprinting presentation stays outside game rules | PASS | Real input changes committed position and presentation gait; frame-strip difference and draw-without-simulation-step checked |

The source command `UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/checks/run.py` passed structure (1000 lines/6 files), Ruff lint/format, strict mypy across 53 source files, and **70 tests** on macOS arm64/Python 3.13.16. The integration tests drive the real `HumanInput` and `GameFlow`, rather than calling mission internals to force a result.

## Native and visual evidence

The six screenshots below were captured on a macOS Cocoa display through the same offscreen-canvas path used by `ui/bootstrap.py`. They are scripted input/render inspections; human keyboard feel was not measured.

- [Title](screens/native-five-zone-title.png)
- [Human briefing](screens/native-five-zone-mode.png)
- [Playable heist](screens/native-five-zone-heist.png)
- [Lockdown after Core theft](screens/native-five-zone-lockdown.png)
- [Real win result](screens/native-five-zone-win.png)
- [Real capture result](screens/native-five-zone-capture.png)

The [2.4-second gameplay clip](movement-preview.mp4) is a 72-frame capture from the real scene with walk, sprint and direction changes. It confirms sprite frames and camera motion on the Cocoa display; it is not a human playtest. The screenshots and clip include the new packaged tiles, props, actor art and Oxanium UI font. Asset origin, hashes and font license are recorded in the [asset register](../../../../assets/ASSETS.md).

An earlier arm64 app/ZIP passed all eight frozen smoke assertions before the final visual assets were integrated. A clean candidate rebuild with the illustrated gameplay resources is required below before this report can claim those assets passed frozen smoke.

Clean candidate archive: PENDING clean build after integration commit. Hosted macOS/Windows/Linux CI: PENDING branch push. Interactive Windows x64 desktop: **NOT_RUN** on Suhita's machine. Native macOS keyboard feel/accessibility check: **NOT_RUN**; scripted Cocoa rendering and frozen smoke are PASS. No Windows or public-release claim is inferred from the Mac screenshots.

## Scope boundary

P02 closes the Human mission and map/scene gate. The menu backdrop is an original pre-rendered 2.5D illustration with subtle motion, while actual gameplay uses illustrated tiles and characters over validated Tiled geometry. This is not a 3D renderer or a completed production art pass. Guards are stationary contact posts in P02; sight/hearing/patrols belong P03. Autonomous Companion belongs P04. The owner chose to keep glass breaking, doors, hiding and canisters in Suhita's P05 work; these are not shown as working interactions now. Final environment/tool effects, Workshop, approved scoring, audio and broader accessibility belong P05-P07. The result screen reports actual unscored outcomes and does not fabricate a rank.
