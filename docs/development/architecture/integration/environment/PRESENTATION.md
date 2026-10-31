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

## Implemented consumer checkpoint — 2026-10-30

Runtime `59fffba` supplies `ui/presenters/interactions.py`, `ui/render/interactions/`, and `ui/audio/spatial.py`; see the [runnable handoff](../../../tracking/handoffs/khalid/day_03/P05.md). The map currently uses **96 render pixels/tile**; consumers read that scale rather than assuming the historical 48-pixel base.

The new effect clock interpolates simulation progress and freezes on pause. State is reconstructed from each snapshot; transient effects are deduplicated/expired from original ticks, with a new presenter for each attempt. Foreign tool feedback cannot overwrite the active actor's status, and hit graphics require an actually visible target. Perception and geometry remain backend-owned.

Recognized `InteractionHint.kind` strings are `Core`, `Stair`, `Door`, `HideSpot`, `LeaveHide`, and `Canister`; unknown kinds display generic `Interact`. Required ticks above one enable a hold/progress prompt. Existing E input returns `INTERACT` with the supplied target ID. SR2 must connect legal dispatch and stable priority; the prompt itself does not create an interaction. At the original `59fffba` checkpoint no tool cooldown existed. The later [approved melee follow-up](../../../tracking/handoffs/khalid/day_03/MELEE.md) adds actual two-charge stock and four-second recovery in Simulation/own observations and displays it in the HUD. Actual stock and sprint timing remain authoritative.

The environment frame carries original cue IDs, committed tick/rate, own position and actual `HeardCue` values. Four mono PCM sounds are spatialized only after listener filtering. Repeated IDs do not replay; scene exit/restart stops transient world channels. Panning survives SFX volume/pause changes. The mixer uses ordinary mono gain for centered/muted channels because pygame's channel volume getter excludes stereo separation; [upstream documentation](https://pyga.me/docs/ref/mixer.html#pygame.mixer.Channel.get_volume) describes that distinction.
