# Robot locomotion, local lighting and facility services

Khalid, 2026-11-10. User requested natural bot animation, furniture shadows matching varied lights, and connected wall/machine wiring. Branch `work/khalid-robot-lighting` from `87302a9`. This is a presentation refinement; fingerprint stays 12 and Simulation/AI/scoring rules are unchanged.

## Changes

The previous robot renderer alternated two front-facing drawings from a roster sheet. New matching neutral turnarounds provide north/east/south/west for Sentinel, Tracker, Interceptor and Companion. Runtime prepares sixteen walk and sixteen faster poses per direction with continuous leg skinning, knee articulation, opposite support/swing phases, counter-swinging front-view arms and small chassis weight shifts. High-speed poses increase stride/lift/lean. Committed distance drives phase; actual speed relative to each role's baseline selects the faster gait. Crouching Human animation is retained; disabled/stunned robots stop their gait. No sprite rotation substitutes for directional views, and no gait clock moves actors or creates guard noises.

The preserved RGBA source is [registered](PROMPTS.md). Robot frame dimensions/pivots keep a stable body scale; padding permits foot lift without clipping. Pose tables are prepared at load, not regenerated each frame.

Furniture no longer shares one upper-left sun. Deterministic room fixtures drive both light pools and silhouette direction. Wall lights alternate room edges, clinical ceiling fill reduces directional contrast, and corridors use restrained overhead contact. Shadows project the actual low silhouette, with a separate soft contact region; wall screens/reagent shelving/cable panels retain their existing shadow exclusions. Actors sample the same room light field. Projection caches are bounded (384 silhouettes; room fixture sets 64).

Exposed solid wall runs carry continuous bundled services with clamps, termination/junction boxes, ID stripes, branches and occasional wall-contained slack loops. Nearest-wall equipment feeds terminate on opaque rendered hull/table edges rather than transparent footprint gutters. Central islands use under-bench service plates. The surface is baked once; no new colliders, line-of-sight tags, noises or floor-route blockers are created. Furniture is prepared before map baking so the actual rendered socket locations can be reused.

## Native inspection and verification

Hardware is the same Apple M4 / 16 GiB Mac16,12 / macOS 26.4.1 used in the connected review. Python 3.13.16, pygame-ce 2.5.8 / SDL 2.32.10.

```sh
uv run --locked --cache-dir .cache/uv python -m tests.fixtures.visuals.robot_facility --output output/robot-lighting/native --video
uv run --locked --cache-dir .cache/uv python -m tests.fixtures.visuals.robot_facility --output output/robot-lighting/chase --frames 2400 --video
uv run --locked --cache-dir .cache/uv python scripts/quality/profile_desktop.py --output output/robot-lighting/performance-final --complete-mission
```

The native fixture deploys the production Companion gateway. Each robot camera follows actual committed actor motion, never injected positions or recorded Human paths. Four actor cameras and fourteen room cameras are explicitly diagnostic previews; they do not claim the player's observation or ordinary single-view FPS. Rendering the room previews leaves Simulation's fingerprint unchanged. Raw screens/video/logs stay ignored under `output/robot-lighting`.

Initial full locked checks passed **301 tests in 48.01 s**. Subsequent actual machine-edge service wiring/initialization and faster gait refinements pass the focused presentation suite and lint/format/strict mypy; final source CI repeats the full suite. No visual snapshot test or cosmetic per-file test was added. Final actual native/performance results follow after execution.

The review does not implement Suhita's pending P06 services or claim Windows physical gameplay, full P07 fairness, or P08 release readiness. Existing old asset/phase checkpoints remain historical.

## Final results

- Native Cocoa production review: **480 frames**, actual tick 244, four robot roles with real moving samples; **20 captured states** including all fourteen room previews. The 2,400-frame chase review reaches actual tick **1224**, with fast-gait samples **Companion 832 / Tracker 310 / Interceptor 92 / Sentinel 330**. Source tables contain all sixteen poses per direction/gait; observed pose indices are recorded without inventing missing samples. Both review videos are `real-robots.mp4` in their ignored output folders.
- Inspected directional pose studies, live robot quadrants, machine sockets and research/power/server room wiring. Early leg-cut seams were replaced by continuous leg skinning; an initial diagnostic camera used the intruder's other deck and was corrected to the actual target deck. Those diagnostic mistakes are not recorded as gameplay failures or successful visual acceptance. Final wall edges/feeds use the actual opaque machine image; walking clearances are unchanged.
- Final focused checks: **50 presentation tests in 17.21 s**, Ruff/format/structure PASS; strict mypy **179 source files** PASS. Initial 301-test full checks passed in 48.01 s; final full-source hosted checks follow the pushed commit.
- Isolated final native performance: **12 restarts / 3,600 frames**, 2,400 after four warmup cycles. Update p95 **1.149 ms**, draw **2.781 ms**, total median/p95/max **8.291/9.124/11.685 ms**. Retained RSS versus warmup **+10.81 MiB**, final-six span **7.58 MiB**, existing short-run bound PASS. No Python-growth claim is made in this untraced run.
- Complete actual Companion: **WIN at tick 2463**, 4,830 rendered frames, lockdown alarm observed. Infiltration total median/p95 **8.165/9.200 ms**; lockdown **8.182/9.096 ms**. One infiltration display-present outlier **502.596 ms** produces a **506.254 ms** total maximum; it is retained, with no unsupported attribution or promise of zero lag. An accidentally overlapping diagnostic was interrupted and excluded before this isolated run.

Measurements are specific to this Mac and workload, not a fixed-FPS or zero-leak guarantee. AI behavior, outcomes and geometry are unchanged. Renderer caches/precomputed poses are bounded, and service wiring is baked outside the frame loop.
