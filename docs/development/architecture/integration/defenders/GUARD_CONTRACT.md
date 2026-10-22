# P03 guard registry, evidence and geometry-revision contract

Owner: **Suhita**, P03-SR1/SR2/SR3 on `work/suhita-p03` (from main `a700359`). Consumers: Khalid's P03-KR1/KR2 cue and diagnostic presentation, later P04 Interceptor/NEXUS and Companion work. Status: **published at claim time; the "Actual" notes are filled in only after verification** in the [P03 handoff](../../../tracking/handoffs/suhita/day_02/P03.md).

The fingerprint-7 baseline in the [cinematic/fixture handoff](../../../tracking/handoffs/khalid/presentation/CINEMATIC_STARTUP.md) still governs physical bounds, posture, stairs and sprint. This contract adds only defender logic values. Simulation remains the only mutation authority; controllers receive one filtered `Observation` and return a `GuardDecision`.

## Registry: `level/security.py`

- `build_security_registry(level: LevelData) -> SecurityRegistry` validates the existing map posts, routes and chokepoints and raises `SecurityRegistryError` listing every problem. It never edits the map or infers values from art.
- `GuardAssignment(guard_id, kind, role, route_id, patrol, zone_id, chokepoint_ids)`; `patrol` is the closed route without its repeated first point. Role is derived from the authored `guard_kind`:
  - `SENTINEL` → `GuardRole.SENTINEL` (BFS/FSM/fuzzy, existing controller);
  - `TRACKER` → `GuardRole.TRACKER` (A* + last-seen memory, new controller);
  - `INTERCEPTOR` → `GuardRole.POST` until P04. A POST has real sensing and faces its route but issues only WAIT; it may capture only an intruder it currently sees. Minimax/alpha-beta is **not** implemented in P03.
- Validation: unique guard/route/chokepoint IDs; known kind; route exists and is used by exactly one guard; guard starts on the first waypoint; every waypoint body-fits; consecutive waypoints connect through legal map connections (stairs included); chokepoints are walkable and join two known zones; every POST has at least one chokepoint of its zone.
- `SecurityRegistry.revision` is a SHA-256 over the assignment values; replay headers record it. `registry.spec(rules)` returns the `SecuritySpec` used by Simulation.

## Evidence and provenance

- `GuardMemory` records the provenance of its current goal: `evidence_kind` (`SIGHT`, `NOISE`, `MOTION`, `REPORT`, `HIDE_ENTRY`), `evidence_id` (heard event, cue, report or sighting ID) and `evidence_tick` (original observation tick, never the delivery tick). Simulation rejects a decision whose new evidence does not appear in the guard's own Observation.
- Visual identity remains authoritative: only a guard's own identification meter reaches CHASE. Hearing yields a cue tile; a radio `SecurityReport` yields an investigation lead with the reporter's original tick. Re-delivering the same report cannot refresh its age or create contact. Leads, cues and sightings expire from their original tick (`memory_ticks`, ~5 s).
- Tracker uses legitimate SIGHTING reports from other guards. Sentinels keep their original patrol/investigation role; NEXUS dispatch is P04.

## Hiding and capture fairness

- An intruder is concealed when crouched inside an authored under-desk clearance. Concealed actors are excluded from every guard's sight.
- If an active guard saw the intruder on the previous tick and the intruder becomes concealed, Simulation gives that guard a `VisualCue(kind="HIDE_ENTRY")` at the cover tile. Only that guard may then reveal the actor by inspecting from capture range with clear reach while the cue is unexpired. An unseen entry gives no cue, so an adjacent guard cannot see or capture the hidden actor.
- Capture still needs CHASE plus current sight for active controllers; POST guards need current sight. Tools still resolve before capture.

## Geometry revisions

- `Observation.geometry_revision` (default 0) is public facility knowledge. `Simulation.request_geometry_revision(map, reason)` validates a same-size replacement map (same stairs; every actor still fits), applies it at the start of the next tick and emits `GEOMETRY_REVISED`. P05 doors/glass will use this adapter; P03 adds no door state.
- Guards store `path_revision` and replan whenever it differs. Physical bounds/LOS use the replacement map directly; no invisible tile-sized barriers are created.

## Presentation values for KR1/KR2

`GuardView` gains `role`, `algorithm` (`BFS`, `A*` or `NONE`), `evidence_kind`, `evidence_tick`, `path_cost` and `search_tiles`, appended with defaults so current drawing keeps working. `POLICY_DECISION` details add `algorithm`, `path_cost`, `evidence_kind` and `evidence_tick`. These are privileged display values, never controller inputs.

## Replay

`core/simulation/replay.py` records a header (game/fingerprint schema, map/rules/sensor hashes, registry revision, seed, rate) plus per-tick intruder actions, and verifies a re-run tick by tick against event and fingerprint hashes. Fingerprint schema becomes **8** because guard memory/evidence/witness state and geometry revision enter the canonical state; schema-7 hashes are not comparable.
