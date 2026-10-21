# Grounded facility and crouch handoff

Owner: Khalid, user-directed refinement, 2026-10-22, baseline main `687dbf3`. [Review/screenshots/build evidence](../../../../quality/reports/material_cohesion/REVIEW.md). This supersedes the prior scene handoff's floor/wall materials, shadow projection and complete deferral of under-desk interaction. The owner explicitly brought crouch/creep/under-desk clearance forward now; remaining Phase 5 environment ownership and phase gates are unchanged.

## Run

```sh
uv sync --locked --all-extras
uv run --locked echo-heist
uv run --locked python scripts/checks/run.py
```

Windows x64 uses the same commands in PowerShell after its existing setup prerequisites, or the matching Windows CI ZIP recorded in BUILD.json. Extract the full archive with its support folder. Mac uses the corresponding native ZIP. Fetch main before a new owner branch.

Play Chapter → Human → Launch. WASD moves; **C toggles crouch**; Shift uses the existing three-second sprint/four-second recharge while standing. Q Echo, F EMP, Space stun, E stairs/hold E at Core; Tab map, Esc pause. In Entry, approach the open desk's middle from below, crouch and move under it. C cannot stand beneath the counter: crouch back out first. The other two desk openings are in Instrument Lab and Containment Systems. Open-floor crouching is slower/quieter, not invisible.

Inspect the warm neutral slab floor, cutaway wall faces and structural lights, attached contact shadows, bolted machine bases/service feeds and clear room separation. Desks have one keyboard/chair relationship; the three under-desk openings are chair-free. The interrupted research/plant variety stays in place. Hover and click selected buttons as well as different ones; each deliberate activation now sounds. Separate volumes/mute still apply. Default exploration is ambient, pursuit/lockdown remain tense.

## Consumer changes

- `ActionKind.CROUCH` toggles Simulation-owned `ActorState.crouched`; guards cannot use it. HumanInput queues fresh C presses once. Repeated held keys do not toggle continuously. `OwnStatus.crouched` and the existing `concealed` field expose own state; EntityView carries visible posture only.
- GameRules adds `crouch_speed_percent=55` and `crouch_footstep_interval_ticks=24`. Crouch cannot spend sprint charge. CROUCH footsteps are local one-tile cues; playback gain 0.045, Sentinel salience 0.15. Music/UI playback never creates perception events.
- `StaticMap.crouch_tiles` is an immutable subset of blocked/opaque geometry. `can_walk(tile, crouched=True)` and `body_fits(..., crouched=True)` admit only that clearance, retaining swept collision, body radius and occupancy. Default standing navigation stays blocked. The loader validates UnderDesk → hiding-desk ownership, middle position and front access. Openings: **(3,21), (44,33), (52,15)**.
- A rejected stand emits `ACTION_REJECTED(reason=low_headroom)` without losing posture. Actual cover controls LOS/concealment. A heard blocked-cell cue leads a guard to a reachable edge, not through the desk; last sightings/identity remain observation-based.
- Fingerprint schema is **6** and includes posture, clearance tiles and rules. Do not compare old schema-5 hashes as the same replay.
- `WorldArt.operative_crouch` holds sixteen poses; source props total 48. ActorMotion carries committed posture. Desk-opening depth projection is presentation only. `architecture/materials.py` caches contrast-controlled, graded bitmap floors; `architecture/sections.py` paints cutaway construction/mounts. Existing full-display safe-area and pointer contracts remain unchanged.
- `UiFeedback` emits serial/cue values for actual pointer entries and activations, including already-selected buttons; AudioFrame forwards them. AudioDirector consumes each once on reserved UI channel 0. Stable hover stays quiet. Title/Airy originals replace the default beat-heavy contexts; provenance and 29-file hashes remain packaged.

## Evidence and remaining work

135 focused cases and structure/lint/format/types pass. Both real extraction routes, capture, 48 native scene states, walk/run/creep cycles, under-desk refusal/exit and architectural previews pass. Exact layout, motion and native/hosted package results are retained in the review; no simulated Windows hardware result is substituted for Suhita's machine.

This completes the requested refinement and early crouch subset, not shared P03 or P05. Suhita retains the remaining locker HideSpot lifecycle, glass, doors and canisters. Future Companion navigation must plan posture/clearance explicitly; default standing BFS correctly avoids desk openings. Remaining AI/NEXUS, policies/scoring, release licensing/video/itch.io and physical Windows QA stay in their existing queues.
