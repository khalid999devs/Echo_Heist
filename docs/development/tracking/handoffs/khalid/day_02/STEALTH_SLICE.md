# Khalid — first stealth slice handoff

2026-10-21. **Milestone implemented; full P03 remains IN_PROGRESS.** Starting main `9ea201f`; work branch `work/stealth-vertical-slice`. Commits `6727dfe` (cinematic/UI), `4e3fce0` (CC0 audio/Settings), `8fd87db` (live Sentinel/room cluster), followed by the current native review/label refinement. P01/P02 remain complete. Approved scoring is unchanged and still awaits P06 implementation.

## Run and inspect

```sh
uv sync --locked --extra dev --extra build
uv run --locked echo-heist
uv run --locked python scripts/checks/run.py
```

Windows PowerShell uses the same uv commands; inspect the [Windows environment guide](../../../../workflow/setup/WINDOWS_SUHITA.md) first. Pull the current integration commit into an owner branch while preserving local changes. Do not resume the already-completed P02 queue.

Select Human Infiltration, then Launch Mission. Seed is 1042 by default. WASD/arrows move; Shift sprints; Q Echo; F EMP; Space melee; hold E at the Core; Tab guide; F3 actual Sentinel diagnostics; Escape pause. Settings changes independent music/SFX levels, fullscreen and reduced flashing, saved on clean exit.

Entry/Service contain physical consoles, storage, cargo and greenery with matching collision/sight/sound footprints. The nearby Sentinel patrols, hears sprinting, investigates, identifies visible intruders, chases, searches the last seen location, then returns. Its amber/red cone and identity bar follow actual geometry/state. Escape, EMP or melee can interrupt a wind-up. A disabled robot remains solid, so pass around it. Core theft removes the minimap target, changes the objective and music, lights the emergency route and leaves an empty socket. Return to the Entry lift to win.

The native scripted lower route wins with the live Sentinel. The upper route needs guard timing or tools; the capture sweep uses a real EMP in range and a real input detour around the disabled body. Running blindly north along the old P02 route can now produce an actual capture. This is expected active-guard behavior, not a forced failure.

## Consumer contracts and boundaries

Read [STEALTH_SLICE runtime contracts](../../../../architecture/integration/STEALTH_SLICE.md), the [owner brief](../../../../planning/references/IMPLEMENTATION_BRIEF.md) and [current review](../../../../quality/reports/phase02/presentation/REVIEW.md). Additive observations provide filtered visible entities, heard cue origins and anonymous motion; GuardMemory remains Simulation-owned. PresentationSnapshot.guards is privileged UI data, never a controller input. Fingerprint schema is 3; reproduce with the same code/map/security/GameRules values.

Current composition activates only `guard-service` using the existing validated route. Three other posts retain P02 physical contact behavior. Suhita's P03-S1 registry/geometry revision adapter remains open; replace the temporary single-Sentinel selection through a narrow shared contract when that work is ready. No second importer or hidden-world controller access is needed. Furniture is a rectangular Tiled marker with exact whole-tile dimensions/style and explicit physical/vision/sound flags.

Khalid's full P03-K1/K2/K3 slices are not declared DONE: Tracker A*, complete replay headers, shared registry integration, roster/cues and hiding-related acceptance remain. Companion/MCTS, Interceptor minimax, NEXUS, Workshop, approved score/rank and full P05 interactions remain pending. The user explicitly kept actual glass breaking, doors, hiding and canisters in P05. Do not build fake screens or claim full V1 completion.

## Actual evidence

- Structure, Ruff lint/format, strict mypy (72 source files) and **89 tests PASS**.
- Focused tests cover shortest BFS, filtered sight/hearing, transparent glass/opaque corners, cue-only knowledge, report provenance/expiry, capture interruption, paired hidden-position fairness, deterministic active security, furniture footprints/errors/layer order and a real live-guard lower-route win.
- **31 native Cocoa screenshots**, with asserted scene/outcome navigation and explicit opaque RGB export, were visually inspected. [Review and all screenshots](../../../../quality/reports/phase02/presentation/REVIEW.md).
- Accelerated native source playthrough: 1,287 frames, actual WIN, all five context tracks selected from real states, 16 decoded assets, 108 cues; update/audio/draw mean 7.77 ms, p95 8.43 ms, excluding display/encoding. This is one local source measurement, not final hardware/FPS or subjective mix acceptance.
- Clean `8fd87db` app and extracted ZIP each passed all eight native frozen checks with Cocoa, audio ready and 16 assets loaded. Final label refinements are being rebuilt; final exact archive/hash/source and hosted CI status will be appended after those checks finish.
- Windows interactive scene/audio/download QA and Linux native packaging remain NOT_RUN. Human play-feel and the full reference-image quality target remain open.

No scoring-rule or original source-PDF changes. All authored files remain below 1,001 lines; maintained directories have at most six direct files; tests remain under the root tests tree. This follow-up was explicitly requested by the owner; no teammate agent or external teammate messages were used. Estimated/actual hours were not tracked, so no invented workload total is recorded.

## Continue next

Finish the rest of P03 against these actual APIs, then extend purposeful interiors and route pacing before the later Companion/Workshop and P05 mechanics milestones. Keep Suhita's separately invoked owner queue and shared feature status intact. The four-day/eight-phase plan remains the target, not evidence that unfinished functionality already exists.
