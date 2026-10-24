# P03 combined acceptance

Khalid, 2026-10-24. The user explicitly requested completion of KR1/KR2, combined acceptance and merge of [PR #1](https://github.com/khalid999devs/Echo_Heist/pull/1). Suhita's SR1/SR2/SR3 and original authorship are preserved. This gate combines her reviewed logic (`acaa461`, including fixes `c562fff`) with Khalid's visual integration **11cee9b19feb55b863096f41cea5b11eb146d5ef**. P04 was not started.

## Gate results

| P03 requirement | Actual evidence |
| --- | --- |
| Fair Sentinel/Tracker sensing, memory, reports and hiding | 195 passing cases include T03's hearing/occlusion contract, T04 last-seen search/noninterference, report provenance/expiry, seen/unseen hiding for both controllers, physical inspection barriers and sight-gated capture. Actual glass lifecycle remains P05. |
| BFS/A*/fuzzy execute in gameplay | Both real default-security native routes run all four registered guards; real EMP hearing at (22,20) produces Sentinel urgency **0.95**, firing weight **0.25** on Loud+Near, visibility **0**, identification **0/18**, and no last sighting. The panel displays the stored evaluation, not a recomputation or sample. |
| Genuine diagnostics and cue alignment | F3 selects each guard by 1-4 or mouse. Live filtered sensor counts, identification, last-plan cost/expanded nodes/revision, evidence age, original cue, last sighting, path and legal search candidates are shown. Original cue and reachable approach are separate values. |
| Readable state/capture feedback | Distinct CHECKING/IDENTIFYING/PURSUIT/SEARCHING/RETURNING badges and cone colors; real wind-up countdown/progress and interrupt feedback; transient rings at committed cue origins. Color is accompanied by text. |
| Both-deck map/art/route review | Native upper WIN **1483** ticks, lower WIN **1604**, careless CAPTURED **694**; both floor IDs recorded. Fourteen room/physical-collider overlays inspected. Fixture profiles, authored map, routes, collision dimensions and movement rules are unchanged. Cones share the authoritative sight ray and current map; debug paths split at stair/deck transitions. |
| Reproducibility and geometry | All five seeded headless route replays match; outcomes/ticks/event chains match the reviewed schema-8 baseline. Schema-9 fingerprints intentionally differ because retained trace/evidence fields enter canonical memory. First-tick geometry revision/path/visibility and distinct pending-map hashes remain tested. |
| Responsive controls / read-only drawing | F3 tabs clicked at native 1366×768, OS-clamped 1440×820, and **1470×923 fullscreen**. All 12 selections pass through normal window/logical/safe-area mapping. Fingerprints remain unchanged by F3 selection/drawing. Tall 1280×1440 mapping is also covered in integration tests. |

The source sweep captures **40 states**, 4,010 rendered frames, both Human wins, real capture, unseen under-desk entry/exit, active guard states and actual fuzzy reasoning. It is accelerated ordinary Human input, not autonomous Companion gameplay. Room inspection uses a separate diagnostic camera and physical bounds; it does not move actors or alter collision.

## Commands actually run

From the isolated checkout with the locked Python 3.13.16 arm64 environment:

```sh
uv run --locked --cache-dir /tmp/echo-heist-review-uv python scripts/checks/run.py
uv run --locked --cache-dir /tmp/echo-heist-review-uv python scripts/experiments/p03_evidence.py --output output/phase03-integration/evidence.json
uv run --locked --cache-dir /tmp/echo-heist-review-uv python scripts/quality/defenders/capture.py --output output/phase03-integration/final
uv run --locked --cache-dir /tmp/echo-heist-review-uv python scripts/quality/profile_desktop.py --teaching --output output/phase03-integration/performance
uv run --locked --cache-dir /tmp/echo-heist-review-uv python scripts/packaging/build.py
uv run --locked --cache-dir /tmp/echo-heist-review-uv python scripts/packaging/smoke.py "dist/Echo Heist.app" --output-dir output/phase03-integration/native-app
ditto -x -k dist/echo-heist-0.1.0a1-macos-arm64.zip output/phase03-integration/extracted
uv run --locked --cache-dir /tmp/echo-heist-review-uv python scripts/packaging/smoke.py "output/phase03-integration/extracted/Echo Heist.app" --output-dir output/phase03-integration/native-zip
```

- Full checks PASS: structure (1,000 lines / six direct files), Ruff, formatting **250 files**, strict mypy **118 source files**, **195 tests in 23.41 s**. The existing tall-window test additionally verifies live F3 selection/drawing; the new behavioral case verifies genuine trace values, original cue versus approach, and retained evidence time. No cosmetic snapshot tests were added.
- Headless evidence PASS: upper/lower/cross with tools WIN at 1514/1581/1603; careless upper/lower CAPTURED at 1174/349. All five exact replays match.
- Native source PASS on Cocoa with audio. The first focused sweep exposed a diagnostic label clipping at the viewport edge; marker labels now stay within the viewport. A preliminary fuzzy demonstration sampled after sight had resumed; the final harness explicitly samples the sound-investigation tick and records true values. No AI rule was changed to make a demonstration pass.
- Twelve restart/resize cycles, 3,000 measured frames with F3 and Python tracing: update p95 **2.479 ms**, total p95 **21.655 ms**; retained Python growth **1.048 MiB**, last-six RSS span **27.61 MiB**, bounded criterion PASS. The run includes a **1.153 s** maximum dominated by native presentation (**1.137 s**); it is not evidence of steady 60 FPS. The separate untraced playthrough render/audio/present p95 is **8.76 ms**, excluding simulation. Full performance acceptance remains P07; this short audit is not proof against every leak.
- Native Mac app and fresh ZIP: clean source **11cee9b**, both **9/9 PASS**, Cocoa and audio ready. Archive, lock, startup and check evidence is recorded in [EVIDENCE.json](EVIDENCE.json).
- Hosted Windows x64/macOS arm64 builds and frozen dummy smoke, plus Linux headless checks, are verified on the integrated source before merge; exact run identities are recorded in the evidence. Physical Windows gameplay on the combined build is **NOT_RUN**; Suhita's earlier [Windows source record](../windows/VERIFICATION.md) is preserved, and current Windows retest commands remain in her setup guide.

## Boundary and handoff

P03-KR1/KR2 and the combined P03 gate are complete under the user's integration request. Suhita remains the normal integration lead for P04/P05. P03-only EH-009/010/014/021 and the capture telegraph portion EH-011 close; cross-phase replay/comparison, full Lab/Workshop and tool/environment items remain open for their later owner slices.

Fingerprint **9** is the current consumer contract. `GuardMemory` / `GuardView` append immutable `FuzzyTrace`, original `evidence_tile`, and view `path_revision`; no scoring, AI decision thresholds, map/art, dependency lock or player rules changed. [Guard contract](../../../../architecture/integration/defenders/GUARD_CONTRACT.md), [Khalid handoff](../../../../tracking/handoffs/khalid/day_02/phase03/P03.md).

Next: Suhita starts P04-SR1/SR2/SR3 from merged main on a new branch, preserving the real Sentinel/Tracker and typed telemetry. Companion/MCTS, Interceptor/minimax, NEXUS/protocols and deployment are still unfinished. P05 doors/glass/canisters/full hiding, P06 policies/scoring/history, and P07/P08 whole-game QA/delivery remain open. Successful build/merge does not imply full V1 or public release.

Generated logs/screens/profile/builds live under ignored `output/phase03-integration/` and `dist/` in the integration checkout; compact hashes/results are committed here. Estimated KR effort was five points; actual active hours were not logged. No new art/audio assets or licenses were introduced.
