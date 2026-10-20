# Phase 2 combined verification

Dates: 2026-10-20 through 2026-10-21, Asia/Dhaka. Candidate: `work/p02-integration`, based on Suhita's `a98548a` (which already includes Khalid's `fd93224`). The user's direction on 2026-10-20 transferred final P02 integration review to Khalid. The source PDF SHA256 remains `64fc08b2725796211931d28550a95557e09ddf3c43f3d66c774e6354e36dedda`.

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

The final illustrated candidate was built from clean commit `4b9cc49db768fdea2b2c2928e1c6ff17a9d93a24` using `UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked --all-extras python scripts/packaging/build.py`. The [build manifest](build-manifest.json) records `working_tree_dirty=false`. Local archive: `dist/echo-heist-0.1.0a1-macos-arm64.zip`; 29,198,546 bytes; SHA256 `1679740607d557d8e81472abf9ebee3635f8fa2806e7134e7835aaf66946477d`. Signing is ad-hoc, not notarized. The manifest's build-time `native_smoke=NOT_RUN` is superseded by the separate smoke evidence below.

`uv run --locked --all-extras python scripts/packaging/smoke.py "dist/Echo Heist.app" --mute --output-dir output/phase02/final-native-smoke` passed all eight assertions on real Cocoa. The ZIP was then extracted to a fresh `/private/tmp/echo-heist-p02-final.FBRPZv` directory and its app passed the same check with output at `output/phase02/final-extracted-smoke`. The [committed extracted-app summary](native-smoke.json) records all eight checks, isolated settings, system-only PATH and native Cocoa rendering. Source scene interaction tests and screenshots cover actual heist flow; frozen smoke covers startup/resource loading and deterministic diagnostic hashes.

[Hosted run 39503129521](https://github.com/khalid999devs/Echo_Heist/actions/runs/39503129521) passed on the same code commit: Linux headless checks, macOS arm64 checks/build/frozen dummy-video smoke and Windows x64 checks/build/frozen dummy-video smoke. Both native job artifacts were uploaded successfully. These are hosted automated checks; interactive Windows x64 desktop remains **NOT_RUN** on Suhita's machine. Native macOS human keyboard feel/accessibility check remains **NOT_RUN**; scripted Cocoa rendering and frozen smoke are PASS. No public-release claim is inferred from these checks.

## Scope boundary

P02 closes the Human mission and map/scene gate. The menu backdrop is an original pre-rendered 2.5D illustration with subtle motion, while actual gameplay uses illustrated tiles and characters over validated Tiled geometry. This is not a 3D renderer or a completed production art pass. Guards are stationary contact posts in P02; sight/hearing/patrols belong P03. Autonomous Companion belongs P04. The owner chose to keep glass breaking, doors, hiding and canisters in Suhita's P05 work; these are not shown as working interactions now. Final environment/tool effects, Workshop, approved scoring, audio and broader accessibility belong P05-P07. The result screen reports actual unscored outcomes and does not fabricate a rank.
