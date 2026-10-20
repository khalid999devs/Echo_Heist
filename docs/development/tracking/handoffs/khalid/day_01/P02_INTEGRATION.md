# P02 integrated Human mission handoff

Date: 2026-10-20. Integration reviewer: Khalid, by the user's explicit request. Source owners remain Khalid (P02-K1/K2) and Suhita (P02-S1/S2). Baseline: Suhita's `a98548a` includes Khalid's `fd93224`; reviewed on `work/p02-integration` without overwriting either owner branch. Status: **P02 DONE**; P03-P08 not started by this handoff. [Combined verification and screenshots](../../../../quality/reports/phase02/integration/VERIFICATION.md).

## Run and inspect

```sh
uv sync --locked --all-extras --python 3.13
uv run --locked python scripts/checks/run.py
uv run --locked echo-heist
```

On Windows x64 use the PowerShell equivalents in [Windows setup](../../../../workflow/setup/WINDOWS_SUHITA.md). The title uses mouse or arrows/Enter. Choose Human and launch. WASD/arrows move, Shift sprints, hold E near the Core, Q Echo, F EMP, Space melee, Tab route summary, Escape pause. Pause offers resume, R same-seed restart and X confirmed abort. The result offers retry or main menu. Companion is visibly unavailable until P04.

Map ID: `vault-five-zone`; Tiled JSON schema `echo-heist-map/1`; 64×36 orthogonal tiles, 32 pixels/tile. Anchors: `entry-spawn=(5,17)`, `entry-exit=(2,17)`, `vault-core=(58,17)`. Zones: entry, service-wing, security-control, research-floor, core-chamber. Upper route: entry → service → security → core. Lower route: entry → service → research → core. Chokepoint `choke-cross-link=(36,17)` joins both branches. The importer validates the geometry flags, unique typed IDs, anchor placement, patrol routes and return reachability. Four guard posts remain stationary until P03 drives patrol AI.

Source composition: `level/io/tiled.py:load_tiled_map` and `level/model.py:LevelData` produce immutable static map/spawn/mission values. `ui/scenes/flow.py:GameFlow` loads rules and map once, then constructs `ui/scenes/heist.py:HeistSession`. The session feeds Khalid's `ui/input/human.py:HumanInput` from the operative's filtered observation to `core/simulation/engine.py:Simulation.step`. Rendering consumes the separate `PresentationSnapshot`; `ui/bootstrap.py` owns the real display, aspect-ratio scaling and pointer translation. Generated menu art and `ui/render/motifs.py` are presentation only. No AI controller receives privileged snapshot data.

Verification: combined structure/Ruff/mypy and 69 cases PASS; map validator covers malformed layers/anchors and both branches; real scene win/capture/pause/retry and native Cocoa screenshots PASS. A frozen macOS arm64 app with packaged map/art passed all eight native smoke assertions. Exact archive and hosted CI details live in the linked report. Suhita's own interactive Windows x64 playthrough remains **NOT_RUN**; do not substitute hosted dummy-video smoke for that claim. Her branch had no separate final handoff, so this document records the integration acceptance without attributing unperformed checks to her.

Next consumer: P03 can use `LevelData.guards`, `routes`, `chokepoints`, static vision/sound flags and the authoritative Simulation action/observation interface. Keep real guard state/perception in Simulation, implement BFS/A*/fuzzy/replay as assigned, and preserve the P02 map and event IDs. The source license, active AI, Companion, final tools/environment, Workshop, score and public desktop release remain future gates.
