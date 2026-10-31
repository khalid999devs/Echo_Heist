# Independent experience/UI verification

2026-10-31, Khalid. Branch `work/khalid-p06-ui`; stacked P05 base `f50b08a`. [Consumer contract](../../../../architecture/integration/experience/PRESENTATION.md), [runnable handoff](../../../../tracking/handoffs/khalid/day_03/P06.md), [machine-readable evidence](EVIDENCE.json). Runtime and final hosted/build evidence are recorded below after those commands complete; no planned run is counted as PASS.

## Actual checks

All commands use `uv run --locked --cache-dir .cache/uv` locally. `python -m pytest` is required rather than the bare pytest executable for imports under the root tests namespace. An initial bare invocation failed collection and was corrected; it was not counted as a passing run.

| Command | Actual result |
| --- | --- |
| `python scripts/checks/run.py` | PASS: structure, Ruff, formatting, strict mypy (149 source modules), 243 tests; 17 new meaningful regression cases at this checkpoint. Final added history-mouse case is recorded separately below. |
| `python -m tests.fixtures.experience.capture --output output/phase06-ui/native` | PASS after correcting fixture teardown/background; native Cocoa/audio ready, 32 saved UI views, four authored display sizes, real Human abort/navigation/remap and explicitly labeled synthetic profiles/scores/history. |
| `python scripts/quality/defenders/capture.py --output output/phase06-ui/human-native` | PASS: real Human upper WIN 1483 ticks, lower WIN 1604, exposed CAPTURED 694; both decks, actual fuzzy hearing urgency 0.95, unseen under-desk concealment and read-only diagnostics. 4,010 frames, 40 screenshot states. |
| `python scripts/experiments/p03_evidence.py --output output/phase06-ui/replay.json` | PASS: five schema-10 replays; upper/lower/cross WIN 1513/1581/1603; untooled upper/lower CAPTURED 1174/349. All event-chain/state hashes exactly match the prior limited-melee evidence. |
| `python scripts/quality/profile_desktop.py --output output/phase06-ui/performance` | Completed 12 restarts, 3,600 frames with audio/security, alternating 1280×720 / 1440×900. Short-run memory threshold PASS; timing investigation below. |

## Visual and functional review

Inspected the 32 new screen states as contact sheets and full-size briefing, Workshop, controls/accessibility, results and HUD views. Checked actual native WIN/capture layouts. Results use extraction-specific art only on genuine wins; current failures retain the blurred actual facility context. Menu/seed/profile control rectangles are shared by drawing and pointer activation. Text fits the authored safe area; settings notices no longer collide with Back, and history has mouse Previous/Next as well as arrows. Canceled modals do not leak a second event into a new mission; a stale score cannot attach to a new seed/mode/attempt/tool-count tuple.

The UI fixture requested 1366×768, 1440×900, 1920×1080 and 1024×768 for safe-area/pointer coverage. The actual Human native driver additionally recorded 1366×768 logical 1281×720, OS-clamped 1440×820 logical 1280×729, and fullscreen 1470×923 logical 1280×804, with four working guard tabs each. The OS resize warnings are retained in output, not silently described as requested window dimensions. Source rendering is exercised on this Mac only.

Test-only fixed S/A/F reports and profile/history storage verify consumer layout/errors, not scoring examples, rank reachability, saves/relaunch or functioning AI. Current default game has no ExperienceGateway and says unavailable. The terminal-result fallback consumes only an actual backend result if supplied; it never computes one.

## Performance limits

The real Human native driver measured render/audio/present median **10.04 ms**, p95 **13.73 ms**, max **765.75 ms** across 4,010 accelerated frames; this excludes simulation and includes screenshot/native presentation outliers. It does not prove a constant 60 FPS.

The first traced restart audit measured total median **23.089 ms**, p95 **59.317 ms**, max **1132.924 ms**; draw p95 **51.341 ms**. This ran with concurrent checks/replay and is slower than the historical P05 traced p95 **22.674 ms**. It must not be advertised as a performance improvement. Retained Python growth was **1.057 MiB**, RSS warmup-to-final **−75.19 MiB**; final-six RSS span **108.15 MiB**. The script's bounded criterion passed (all final-six samples below warmup +64 MiB, Python growth below 4 MiB), but the large RSS variability is not a stable plateau or proof of no leaks. The isolated repeat confirmed slow traced costs: median 22.758 ms, p95 59.393 ms, max 141.163 ms; retained Python 1.056 MiB, final-six RSS span 11.81 MiB. A cProfile/tracemalloc diagnostic identified minimap rasterization, vision rays and repeated snapshot/observation work. The UI now reuses one immutable observation per draw/event batch and caches floor rasters per map/deck, with actual-map replacement invalidation. Conservative off-screen cone bounds skip only ray fans whose entire cone/meter extent cannot contribute pixels. Guard sensing and on-screen clipping remain unchanged. Final measured timings follow below.

Cache/input preference snapshots are bounded to 32; captions retain at most 256 event IDs; profiles/history accept at most 32/100 records. Gateway report retrieval is once per actual terminal attempt, history/profile IO is explicit, and no service reads/writes occur while drawing. These scope controls do not replace future full-game AI/search/resource profiling. Any full performance acceptance stays open until the combined game runs both modes on primary hardware.

## Remaining acceptance

Suhita's actual scores/encounter lifetime, policy/preset translation, history/profile/preferences recovery and relaunch tests, missing P04/P05 AI/environment lifecycles, full-scenario comparison and whole-game P07/P08 gates are pending. Current native Mac checks cannot claim physical Windows or Linux gameplay. Clean-machine download/security behavior, final video/credits/notices and source/original-asset license remain release work.
