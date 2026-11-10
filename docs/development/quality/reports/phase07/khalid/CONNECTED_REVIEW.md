# Connected Mac review — P04/P05, P06 consumers and P07 workload

Khalid, 2026-11-10. User explicitly requested completion of his connected Mac review, P06 consumer work and current-game usability/render/audio/memory checks. Branch `work/khalid-connected-review` from `df7dbdb`. This does not transfer Suhita's scoring/policy/persistence or search/fairness ownership.

Hardware: Apple M4, 16 GiB RAM, model Mac16,12; macOS 26.4.1, Python 3.13.16, pygame-ce 2.5.8 / SDL 2.32.10. Native Cocoa display and mixer enabled. Temporary user-data directories protect the player's settings/protocol memory.

## Presentation findings

The real P04 algorithms were still described as PLANNED in Field Guide. Updated Companion selection/expansion/rollout/backpropagation, A*/utility, physical Interceptor/minimax/alpha-beta and evidence-backed NEXUS descriptions. Removed the stale "coming later" deployment fallback; a failed runtime now directs the player to its actual Workshop notice. No algorithm, scoring, collision, hearing, sprint or melee rule changed.

## Real native interaction acceptance

`uv run --locked --cache-dir .cache/uv python -m tests.fixtures.interactions.acceptance --output output/connected-review/props`

The helper uses production gateway/map/security and ordinary Human keyboard input; no position, prop, guard, result or algorithm state injection. Horizontal cross-link and vertical Core doors close/open, both glass panes shatter once and can be physically crossed, and actual Echo/EMP use and empty/out-of-range rejections are captured. Audio audit records successful production mixer submissions; noise/event IDs remain Simulation-owned. An initial test route was captured by a real guard; the final glass-cell route uses ordinary legitimate emergency tools. An early E press/release-in-one-frame test error was corrected to hold across a simulation step. Neither issue was bypassed by disabling guards.

The prior merged native review already records actual canister roll and locker entry/held-E/exit. Existing automated coverage separately verifies both control modes, collision/LOS revisions, witnessed concealment and once-only sounds. Native mixer submission plus ready audio is functional playback evidence; accelerated QA is not a subjective long listening review.

## P06 consumer readiness

`uv run --locked --cache-dir .cache/uv python -m tests.fixtures.experience.live_capture --output output/connected-review/experience`

Production Companion completes seed 1042 and reaches its real unscored result. All four Workshop blocks change via clicks; Balanced is restored before deployment. Seed cancellation leaves the attempt unchanged; explicit new seed preserves mode/policy and returns through actual protocol review. Paused settings freeze the simulation fingerprint. Remapping/captions/high contrast are working session UI. Four physical window sizes (1280×720, 1440×900, 1366×768, 1024×768) exercise logical coordinates and pointer placement. Real guide, controls, report and accessibility screens are reviewed at native resolution.

**Dependency:** main has no production `ExperienceGateway`, no authoritative detection-encounter score service, named-profile/history service or extra-preference persistence. Their UI reports unavailable, rather than fabricating scores or saves. P06-KR consumer preparation is ready; connected score/profile/history/relaunch acceptance is NOT_RUN until Suhita supplies P06-SR1/SR2/SR3. Existing [experience contract](../../../../architecture/integration/experience/PRESENTATION.md) remains the connection seam.

## Current-game performance method

Updated `scripts/quality/profile_desktop.py` to deploy both modes through real `NexusGateway`, with actual AI, 13 props, reset protocol memory and 64-simulation Companion telemetry. The old profiler constructed a fallback Human-only flow, so its earlier measurements are not evidence for the merged AI build.

Warmup now covers **four** cycles: both modes at both sizes. The initial two-cycle warmup covered only 1280×720; its untraced run returned FAIL at +77.08 MiB RSS after later resolution caches initialized. That diagnostic is retained under `output/connected-review/performance`, not called a memory leak or a pass. Four-cycle warmup measures retained growth after the actual workload variants initialize; it does not raise the existing +64 MiB / +4 MiB thresholds. Untraced Python growth is explicitly unmeasured. Optional tracing is reported separately because it adds overhead. A complete real seed-1042 Companion run additionally samples infiltration/lockdown and verifies alarm playback; short restart samples alone do not cover late-game director work.

Final native untraced run (`--frames-per-cycle 600 --complete-mission`): **12 cycles / 7,200 frames**, 4,800 post-warmup. Update p95 **1.063 ms**, draw **2.577 ms**, total **16.754 ms** (median 7.897); maximum total **255.286 ms**, predominantly display present (253.390 ms). The presentation outlier is recorded, not silently removed or blamed on a particular OS cause. Retained RSS versus four-cycle warmup **+15.52 MiB**, final-six span **13.28 MiB**, bounded criterion PASS. No Python growth claim is made without tracing.

Complete actual Companion run: **WIN at 2463**, **4,830 rendered frames**, real lockdown alarm observed. Infiltration total median/p95/max **16.455/16.729/17.282 ms**; lockdown **16.553/16.777/17.174 ms**. Update/draw p95 **1.034/2.999 ms** infiltration and **1.504/4.067 ms** lockdown. Presentation waits are included; these are observed frame costs, not a guarantee of fixed FPS on other hardware.

Separate tracing/diagnostics run (`--cycles 16 --trace-memory --teaching`): **4,800 frames**, 3,600 post-warmup, both modes and F3. Total median/p95/max **9.301/15.922/41.755 ms** with tracing overhead; retained Python growth **2.193 MiB** (includes profiling/telemetry samples), RSS versus warmup **−73.56 MiB**, final-six RSS span **83.81 MiB**. Existing short-run bounds PASS; RSS variability is not a demonstrated stable plateau. No claim of zero leaks or full long-session acceptance.

Native prop review finishes **22 screenshots**, with four real door mixer submissions, two glass submissions, actual Echo/EMP, successful real-guard melee and recovery rejection. Experience review finishes **21 screenshots**, including real Human remapped movement/high-contrast HUD, actual Companion win/abort, four guide tabs, four window sizes and actual fullscreen at **1470×923**, including the desktop physical-pointer mapper. No synthetic score/profile/history was used. Whole-game P07 acceptance still requires missing P06 services and Suhita's fairness/scenario/recovery work. Physical Windows and final P08 delivery are outside this Mac review.

## Final source checks

`uv run --locked --cache-dir .cache/uv python scripts/checks/run.py`: **PASS**, **301 tests in 44.32 s**, structure/Ruff/format/strict mypy. Cosmetic guide text is verified through native screenshots; no one-test-per-copy-change suite was added. Subsequent report-only and manual-review metadata changes receive structure/link/format checks.

Cocoa warned that leaving fullscreen forced the requested 1280×720 window to 1470×832. The review helper uses the actual returned display size and the desktop pointer mapper, matching responsive application behavior; this warning is recorded rather than presented as an exact requested-size result. Fullscreen itself was 1470×923.
