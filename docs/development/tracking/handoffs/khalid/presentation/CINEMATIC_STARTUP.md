# Cinematic startup, airlocks and physical fixture handoff

Owner: Khalid, 2026-10-22. User-directed refinement of main `da1358c`, on `work/cinematic-startup`. Shared P03-P08 gates remain open. [Review and actual evidence](../../../../quality/reports/cinematic_startup/REVIEW.md), [asset prompts](../../../../quality/reports/cinematic_startup/PROMPTS.md). This supersedes fingerprint-6 and tile-only physical fixture collision in the preceding material/crouch handoff.

## Run and inspect

```sh
uv sync --locked --all-extras
uv run --locked echo-heist
```

The window immediately paints a signal mark, then shows the core emblem, actual resource progress and a quiet sound sequence. The warmed title fades in; a key/click queues a skip until loading finishes. Closing during loading cancels and joins the resource worker. Mute, saved SFX volume, reduced flashing and resize/fullscreen remain supported. No startup input is forwarded into a mission.

Play Chapter → Human → Launch. Pressure doors part over the real Entry scene in 1.25 seconds. Simulation is frozen while Entry is obscured. A deliberate key/click skips into normal controls without losing the first movement press. Only a committed WIN starts the 1.95-second closing/sealing/reopening extraction transition into the distinct dawn result artwork. Capture and abort have their own existing results. These transitions do not implement Phase 5 door locks or change outcomes.

WASD moves, **C toggles crouch/creep**, Shift uses the approved three-second sprint/four-second recharge, E stairs/hold E at Core, Q Echo, F EMP, Space stun, Tab map, Esc pause. There is no separate seated pose/action. The three desk clearances remain (3,21), (44,33), (52,15); crouch into their central knee openings and back out before standing.

Inspect visible side gaps around narrow equipment, including server racks and long placement footprints. The operative must stop at equipment bodies, never at their empty reserved floor. Walls remain solid. White lab light, warm service/office lights, cool server light and cyan reactor light now complement different mineral/epoxy/antistatic/grip floor patterns. Existing contextual aftermath, wear and plant conditions stay deterministic across retries. Wall panels/recesses no longer receive duplicate projected floor shadows; the operative retains its grounded contact shadow.

## Contracts to retrieve before continuing

- `StaticMap.obstacles` contains immutable `ObstacleBounds` in integer simulation units. It builds an immutable spatial index once. `hard_blocked`/`hard_opaque` retain wall tiles; explicit fixture bodies replace only their reserved tile flags for continuous collision/LOS/reach. Body radius is **6,000 units / 0.2 tiles**, matching visible feet/shoulders more closely.
- The original blocked tile grid is preserved for conservative standing route/placement validation. `can_walk` still describes that grid, **not every sub-tile floor gap**. Future Companion navigation must use body clearance/posture if it plans those gaps. Existing Sentinel reachable-edge handling remains in place. Sound blocking retains its authored acoustic flags.
- Furniture exports four integer permille bounds `collision_left/top/right/bottom`, relative to its reserved footprint. Cover markers additionally reference `collision_tile_x/y`: the marker is the adjacent standing approach, not the cover body. Loader validation rejects partial/out-of-range/empty geometry. Runtime never infers Simulation state from bitmap pixels.
- Offline `scripts/level/calibrate_colliders.py` measures the authored art, clips bodies to their reserved footprint and exports **106** profiles: 101 furniture, five cover. Pots use physical bases rather than leaves; hiding desks retain full body bounds with explicit knee clearances. Re-run after changing fixture art/placement, then run both routes and crouch checks. `author_facility.py` preserves profiles only for unchanged footprints.
- Fingerprint schema is **7**, including physical obstacle geometry, posture and rules. Old hashes are incompatible. Physics, LOS and reach share these bounds; AI/controllers still receive immutable filtered observations.
- `UiFeedback` supplies explicit interaction serials. `AudioFrame.explicit_ui_feedback=True` disables legacy selection-change hover inference. Chapter card and nested Play are one hover region. `transition_serial/cue` are presentation-only pressure-door audio; repeated delivery cannot replay a stage.
- Music preference multiplies title 0.40, exploration 0.34, pursuit 0.38, lockdown 0.40, result 0.34. Exploration remains ambient. Existing quiet walk/loud sprint, actual hearing, siren, pause and independent volumes are unchanged. Airlocks reuse licensed Kenney open/close cues; 29 recordings still ship.
- `ui/startup/` owns opening drawing, one resource worker, staged preparation and ownership transfer. Main owns display/events; worker owns off-screen resources until its Future completes. All opening text is rendered before the worker starts, avoiding concurrent pygame font rendering. Worker joins on cancellation/failure before pygame shutdown.
- Tile/room-local lighting/shadow buffers avoid full-map temporary alpha surfaces. Mineral decoding is cached once. Resident prop crops detach from full source atlases, with a 512px maximum dimension before final fixture fitting. Runtime preserves original bitmap bytes. Native ICNS/ICO package the selected original core icon.

## Verification and delivery

149 meaningful tests plus structure, Ruff, formatting and strict types pass. Native Cocoa route checks pass upper WIN at 1,488 ticks and lower WIN at 1,566; capture at 758. The 56-state scene sweep includes both airlock sequences, both stair directions, six Sentinel states and all five music contexts. The measured 200–300 ms music-switch stalls are removed: gain ramps across frames, initial streaming is primed under the opening. Final native scene max is 32.24 ms; separate native performance p95 is 16.889 ms across 3,000 measured frames, with no sustained memory growth in 12 restarts. Startup variants, 780 motion frames and exact package manifests are recorded in the linked review; a source check is not an artifact or platform test.

Exact commands:

```sh
uv run --locked python scripts/checks/run.py
uv run --locked python scripts/quality/capture_startup.py --output output/cinematic-startup/final-normal
uv run --locked python scripts/quality/capture_scenes.py --output output/cinematic-startup/scenes-final
uv run --locked python scripts/quality/capture_motion.py --output output/cinematic-startup/motion
uv run --locked python scripts/quality/profile_desktop.py
uv run --locked --all-extras python scripts/packaging/build.py
uv run --locked python scripts/packaging/smoke.py 'dist/Echo Heist.app'
```

The full codebase remains a playable development revision. Physical Windows gameplay/audio QA, remaining AI/NEXUS, policy/scoring integration, later environment lifecycles and public itch.io release gates are still pending. Suhita should fetch main, read this consumer handoff, then create her next assigned branch. Do not restore the old invisible tile-sized fixture barriers.
