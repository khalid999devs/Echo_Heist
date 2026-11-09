# P05 environment runtime (SR1/SR2)

2026-11-09, Suhita, branch `work/suhita-p05` (from `work/suhita-p04` c99984e). This is the authoritative side of the [presentation seam](PRESENTATION.md): Simulation owns every prop; presentation only reads `PresentationSnapshot.environment`.

## Inputs

- Map data: `markers` point objects `Door` (optional int `span` 1-3), `Glass` (optional bool `horizontal`, `span`), `Canister`, and every existing `HideSpot` (a locker). `level/environment.py` turns them into `EnvironmentSpec(props, rules)`. A door's axis is derived from the walls around it: exactly one orientation must close a real wall passage, or the map fails validation. Props may not sit on stairs, anchors or each other; glass may not block a patrol route.
- Rules: `resources/data/gameplay/environment.json` → `EnvironmentRules` (door cycle 12 ticks, door noise 2, glass 6, canister 4 tiles, canister 5 ticks/tile up to 4 tiles, locker hatch 9 ticks, cue lifetime 60 ticks).
- `Simulation(..., environment=EnvironmentSpec | None)`. `None` keeps the previous behavior exactly (all older fixtures/tests). `NexusGateway` builds the spec once and passes it to every Human and Companion attempt; the built-in fallback `HeistSession` does the same.

## Geometry, routing and sight

`StaticMap.door_tiles` marks controlled passages. The **physical** map is the authored map plus closed doors (blocked and opaque) and intact glass (blocked, transparent). `can_walk` still accepts a closed door tile, so BFS/A* for guards, the Companion and the Human driver plan through it; the body is stopped by collision until someone pushes into the door, which starts opening it. Changes are committed as one combined geometry revision applied at the start of the next tick (`GEOMETRY_REVISED`, `Observation.geometry_revision`), so collision, line of sight, reach and planning always agree. Sound is unchanged by doors (gaps leak sound).

`Simulation.presentation_snapshot().world_map` is the physical map. The Workshop runtime check (`ui/scenes/companion/deployment.py`) now accepts it when identity, stairs and objects match and no authored wall is missing.

## Lifecycles (order within one tick)

1. **Push**, before movement: a MOVE whose step points into a closed or closing door starts opening it; a MOVE with available sprint into intact glass shatters it.
2. Movement. A hidden intruder who moves leaves its locker first.
3. **Interact/Hide**, after all movement (reach revalidated): offered interactions are sorted by distance, then ID; a Core hold in progress stays first; a stair landing offers only its stair; a hidden intruder is only offered `LeaveHide`. `INTERACT` may name any offered target; `HIDE` enters the named or nearest free locker.
4. Tools (unchanged), then **bump**: an intruder whose step lands on a resting canister kicks it along that step.
5. **Advance**: door travel; canister rolling (one tile per 5 ticks, up to 4); cue expiry. Then core theft, stairs, sensors, captures, extraction.

| Prop | States | Rules |
| --- | --- | --- |
| Door | OPEN → CLOSING → CLOSED → OPENING → OPEN | Intruder E toggles; any actor pushing opens. Closing is refused (`door_obstructed`) or bounces open (`REOPENING`) if a body or canister is in the doorway. Never locks, so the exit graph always stays valid in lockdown. Intruder-caused motion: one `DOOR` NoiseEvent (2 tiles); a guard's own door is silent, like guard footsteps |
| Glass | INTACT → SHATTERED (once) | E or sprint into it. Exactly one `GLASS` NoiseEvent (6 tiles); the tile becomes walkable next tick; never offered or heard again |
| Canister | REST → ROLLING → IMPACT → REST | Not a collider. Kick by E (away from the kicker) or bump. Stops before blocked tiles, stairs, bodies or another canister; exactly one `METAL` NoiseEvent (4 tiles) at the final tile per roll |
| Locker | EMPTY ↔ OCCUPIED | E/HIDE within interaction reach moves the intruder to the locker centre and stands it up; one occupant. Concealed exactly like under-desk cover: unseen entry hides it from sight and capture; a guard that saw the entry gets the existing `HIDE_ENTRY` cue and may inspect from an adjacent tile. Exit by E or any MOVE. Tools still work inside; crouch is refused (`hidden`). Cosmetic hatch, no NoiseEvent |

## Values given to controllers

Own only: `OwnStatus.concealed`, new `OwnStatus.hidden_in`, `interactions` (kinds `Door`, `Glass`, `Canister`, `HideSpot`, `LeaveHide`, plus existing `Core`/`Stair`), the physical map and its revision. Prop state, other actors' lockers and cues are privileged presentation data.

## Events and presentation

`EventKind.PROP_CHANGED` (`object_id` with `state` or `cue`, and `noise_event_id`). Each `EnvironmentCue` uses that event's ID and original tick, references the real NoiseEvent when there is one, and is `visible` only if it is the mission intruder's own cue or within its sight range and line of sight. `PropView` geometry: door/glass footprint = span × quarter tile along the leaf; canister current/previous positions and roll; locker at the back of its recess tile with `occupant_id` and cover 1.0 while occupied. The static HideSpot cabinet is no longer baked into furniture; the locker prop draws it.

Fingerprint schema **12**: the physical and authored maps (including `door_tiles`), the environment spec and all prop state are hashed.

## SR1 edge rules confirmed or changed

- Melee reach is now symmetric with capture: an intruder revealed inside desk clearance can strike the guard that can grab it there (previously always `no_reachable_guard`).
- Tools resolve before capture on the same tick in both modes (T05), Echo neither cancels a grab nor erases reports, a closed door blocks melee reach, stale tool intents spend nothing, and tools work from inside a locker.
- Human input: only a multi-tick hint (the Core) repeats while E is held; doors, lockers, glass, canisters and stairs need a fresh press.
- Companion: may enter an offered locker only under a recent threat and when no guard is in view; Simulation decides legality.
