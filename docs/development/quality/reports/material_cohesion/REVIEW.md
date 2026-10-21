# Material, perspective and crouch review

Khalid, 2026-10-22. User-requested follow-up to the [responsive facility revision](../facility_finish/REVIEW.md), baseline main `687dbf3`. The owner explicitly requested crouching/crouch-walking and under-desk hiding now, bringing this subset forward from the previous Phase 5 deferral. The remaining shared P03/P05 and later phase gates stay open; approved scoring is unchanged.

## Visible changes

- Warm neutral mineral/epoxy slabs replace the blue technical floor grid. A new material-only bitmap is contrast-controlled, room-graded and given aligned restrained seams once at map load. Service/server materials stay darker; research has a cooler neutral balance. The original PNG is preserved.
- Cutaway walls now have a defined cap, shaded front elevation, skirting and restrained panel detail. Existing rendered bulkhead skin is toned to this palette; sealed roof space remains darker. Wall lights are mounted on structural walls instead of standing inside floor cells. Room washes use the floor mask; the obsolete unmasked zone glow no longer illuminates sealed roof space.
- Shared room grading, bolted machine plinths, short service feeds and fitted footprints ground the instruments. High ceiling lights produce short cast shadows with soft base contact. The earlier long projection made narrow feet and broad equipment bodies appear detached; this is corrected for furniture and actors.
- Three analysis desks have a single keyboard/mouse, paired monitors, real open knee space and no chair inside that opening. Displaced chairs and interrupted work elsewhere remain. The camera and 14-room/two-floor route topology are preserved.
- C toggles crouching. A four-facing authored crouch/creep atlas uses a lower foot-anchored pose; creep phase follows actual travel. Standing under low headroom is refused with visible feedback. A shallow presentation socket aligns the operative with the desk opening without changing its authoritative position.
- Default title/infiltration music is quieter ambient SRG774 Title/Airy; pursuit/lockdown retain their higher tension tracks. Menu hover uses a short Kenney selection cue. Explicit pointer-entry/activation serials make hovering and clicking audible even when selection does not change. Stable hovering does not repeatedly retrigger, and music/SFX preferences and mute remain respected.

## Authoritative crouch behavior

Crouching is 55% of walking speed. It cannot spend sprint charge; normal walk/sprint timing remains unchanged. Crouched footsteps use the one-tile local hearing radius, occur every 24 ticks instead of 12 and play at gain 0.045 (walk 0.09, sprint 0.42). Sentinel salience for CROUCH is lower than FOOTSTEP.

UnderDesk objects validate ownership of a three-tile-wide single-depth hiding desk and its middle opening. Standing collision/LOS remain solid; only crouched bodies can enter the clearance tile. Concealment follows actual posture plus physical cover; open-floor crouching never grants invisibility. Nearby guards can still hear movement and investigate a reachable desk edge. A guard retains legitimate sightings and receives no hidden visual identity/position. Locker HideSpot enter/exit, doors, breaking glass and canisters remain later work.

The three opening tiles are (3,21), (44,33), (52,15). Existing standing collision, opaque geometry, room/stair access and both mission branches are preserved. A candidate north-wall desk move blocked the Instrument Lab entrance; validation caught it and the rear service aisle was retained. Presentation contact, mounts and material treatment provide the new integration without sacrificing circulation.

## Actual checks

- `uv run --locked python scripts/checks/run.py`: **135 tests**, strict mypy over **101 source files**, Ruff lint/format and the 1,000-line/six-direct-file structure guards pass.
- Focused regressions cover crouch speed/cadence/sprint stock, under-desk entry/exit and low headroom, open-floor visibility, retained guard memory, audible hidden movement/reachable investigation, guard action restrictions, deterministic replay, corrupt desk ownership/clearance and repeated selection-independent UI feedback.
- `capture_scenes.py --output output/materials-and-crouch/delivery-scenes`: native Cocoa, 48 states / 3,862 frames; actual default-security upper WIN at tick 1,505, lower WIN at 1,620 and capture at 759. All six Sentinel states, five music contexts, six stair stages and 1,560 siren frames pass. Render/audio/display median 6.04ms, p95 8.03ms, cold-load maximum 312.05ms; excludes Simulation cost and is not a minimum-hardware benchmark.
- `capture_motion.py --output output/materials-and-crouch/delivery-motion`: native input-driven walk/run/crouch review, all eight walk/run slots and four creep slots, four facings, real desk entry, refused standing and legal exit. Every reviewed draw preserves the Simulation fingerprint. Fourteen room/five prepared-recess previews use camera-only architectural inspection; they are not claimed as player visits. Security is disabled in this visual fixture; the separate route sweep uses default security.
- `capture_layouts.py --output output/materials-and-crouch/layouts`: native full-display/resized navigation review. Exact sizes/outcomes are retained in verification/LAYOUTS.json. Events exercise the actual pointer mapping, not hand-operated OS clicks.
- Audio source hashes/decoding/lifecycle and UI cue gain are checked. ffmpeg measured source hover mean −17.3dBFS / peak −1.1, confirmation −24.0 / −5.3 and title −21.9 / −0.9 before playback gains; this quantifies cue headroom, not subjective speaker approval. All 29 packaged audio manifest hashes match.

Raw captures/video/logs remain under ignored `output/materials-and-crouch/`. Kept contact sheets and full-size crouch/material views are under `screens/`. [Build evidence](verification/BUILD.json) distinguishes clean source, native package smoke and hosted checks; Windows physical display/audio QA remains unrun.

## References and provenance

The [Godot lighting explanation](https://docs.godotengine.org/en/stable/tutorials/2d/2d_lights_and_shadows.html) supports separating ambient material treatment, receiving surfaces and shadow/occluder placement; this pygame implementation adapts those principles with cached 2.5D art, not a claim of a live 3D/PBR renderer. [SRG774's ambient pack](https://opengameart.org/content/dark-sci-fi-audio-pack) provides CC0 original OGGs; [Kenney Interface Sounds](https://kenney.nl/assets/interface-sounds) supplies the short hover cue. Exact bitmap [prompts/modes](PROMPTS.md), hashes and audio levels are preserved in verification/. Licensing/notices are packaged.

Companion deployment, remaining advanced defenders/NEXUS, policy persistence, final scoring and the rest of P05-P08 are not claimed complete by this refinement.
