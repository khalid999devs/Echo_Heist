# P05 environment presentation seam

2026-10-25, Khalid's explicitly authorized independent P05-KR1/KR2 work on `work/khalid-p05-visuals`, based on P04 presentation `1d24b4b`. P04 is not complete. Suhita retains all SR lifecycle, AI, tool-rule and persistence ownership.

## State and coordinates

`core/contracts/environment/presentation.py` defines immutable `PropView`, `EnvironmentCue` and `EnvironmentView`. `PresentationSnapshot.environment` defaults to an empty view. No Simulation or map lifecycle is added by these contracts; default Human gameplay and fingerprint 9 remain intact.

Every prop uses its stable authored object ID, `PropKind` and ground-footprint centre/size in existing fixed-point world units (30,000 per tile). Presentation uses the current tile-pixel scale and camera. Doors/glass can span either axis according to their footprint. Footprints describe visible placement, not new collisions. Keep future dynamic doors out of the permanently baked wall art; SR2 must update authoritative geometry, LOS and navigation revision together.

Door/locker `openness` is an actual committed fraction, not a UI timer which opens a collider. Glass `broken` persists after transient shards finish. Canister current/previous positions and `roll_degrees` come from physical travel; the renderer may interpolate those two committed samples. A locker may supply `occupant_id`/`occupant_cover`, but rendering applies cover only to an already-concealed ordinary actor snapshot. A visual may never hide an unconcealed actor or erase observed memory.

State must be present even when no recent cue exists so loading/retry/recovery can draw the correct current prop. The backend controls which mutable prop values may be presented; these privileged values never return to controllers.

## Events, visibility and sound

`EnvironmentCue` carries a stable event ID, original simulation tick, kind/object/actor IDs and world position. Kinds: door movement, glass break, final canister impact, hide entry and hide exit. `visible` must reflect actual observation; audible-only events cannot reveal an exact visual explosion behind a wall. Repeated delivery must not restart particles or sound. New attempts reset presentation buffers.

Gameplay-relevant sounds reference the real committed `noise_event_id`. Foreign audio is allowed only when that ID appears in the active listener's `Observation.heard_events`; panning uses the heard tile, not a hidden moving actor position. Own cosmetic servo/locker sound may be heard without creating a NoiseEvent. Playback never creates, changes or duplicates a simulation sound. The backend owns once-only glass/final-impact emission and any actual noise radii.

## Integration boundaries

Khalid owns the new prop/effect drawing and bounded presentation state, tool HUD feedback and audio consumers. The narrow shared changes are the snapshot DTO field, HeistSession event/draw integration and GameFlow audio fields. P04 controller/deployment/startup methods are left for Suhita. Existing assets, crouch/desk clearance, map IDs and core rules are retained.

SR2 later populates the environment view from authoritative objects and emits these cues after successful state changes. It implements door collision/LOS, canister travel, one-time glass, legal locker entry/exit and guard investigation. SR1 supplies actual tool results, stock and immunity/invalid-action reasons. The UI consumes them without optimistic world mutation or invented cooldowns.

Independent visual fixtures belong under `tests/fixtures/` and are visibly labeled. They can demonstrate animation, sound filtering, pause/reset and layout, but cannot satisfy P05's actual lifecycle or both-mode gate. Full connected acceptance still requires P04 and Suhita's P05 behavior handoff.
