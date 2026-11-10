# Robot movement, shadows and service wiring handoff

Khalid, 2026-11-10. User-directed visual refinement on `work/khalid-robot-lighting` from `87302a9`. Fingerprint remains **12**; simulation/AI movement speeds, collisions, observations, tools and scoring are unchanged.

- Added identity-matched robot turnarounds and four directional walk/fast gaits for all three defender types and Companion. Sixteen poses per gait/direction; stable torso, articulated continuous legs, support/swing foot phases, counter-swinging front-view arms, weight/lean and actual-distance timing. Faster actual movement selects longer strides rather than a buzzing walk loop.
- Furniture/actors use room-local light directions, including high ceiling fill and restrained contact shadows. Visible edge fixtures and shadows share source coordinates. Wall-mounted screens/panels keep their exclusions.
- Baked bundled wall wiring, clamps, junction/termination boxes, branches and slack loops. Machine feeds attach to opaque image edges; islands use floor service plates. No invisible obstacle was added.
- [Review/evidence](../../../../quality/reports/robot_lighting/REVIEW.md), [imagegen source/prompt/hash](../../../../quality/reports/robot_lighting/PROMPTS.md). Raw native views/videos remain ignored under `output/robot-lighting`.

```sh
uv run --locked echo-heist
uv run --locked python -m tests.fixtures.visuals.robot_facility --output output/robot-lighting/native --video
uv run --locked python -m tests.fixtures.visuals.robot_facility --output output/robot-lighting/chase --frames 2400 --video
uv run --locked python scripts/quality/profile_desktop.py --output output/robot-lighting/performance-final --complete-mission
```

Normal play: Chapter → Companion → Deploy; F2 hides/shows teaching overlays. Human sees the same defender art. Inspect side/back facing, planted step phases, walk-to-pursuit transition and stunned stop. Research/power/server rooms expose different fixture directions and machine service feeds. The native QA uses diagnostic cameras explicitly; it does not expose hidden actors to gameplay AI or claim ordinary player visibility. `--video` needs ffmpeg only for this developer capture, not to run the game.

Initial full checks **301 PASS / 48.01 s**; final focused presentation **50 PASS / 17.21 s**, strict mypy179/Ruff/format/structure PASS. Final native four-role/chase reviews pass; isolated restart p95 **9.124 ms**, short-run RSS bound PASS; actual Companion WIN2463 and real alarm. A 506.254 ms total display-present outlier remains recorded. Final CI builds/smoke validate the new recursive resource path; physical Windows visual gameplay is still Suhita's check.

All visual implementation claims are released. Suhita should preserve the new art/light/wiring fields when connecting her P06 services; `build_map_surface(..., furnishings=...)` now receives the already-prepared visual furniture for exact socket placement. No UI service port or authoritative gameplay interface changed. Full P06/P07/P08 dependencies and remaining behavior/platform checks remain as previously handed off.
