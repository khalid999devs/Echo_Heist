# Contract targets and implemented foundation

Blueprint basis: pp. 5-17. P01 has implemented the immutable DTOs and diagnostic Simulation subset; its [actual interfaces and limitations](../tracking/handoffs/khalid/day_01/P01.md) are the integration baseline. The table below describes full-game targets, not a claim that mission/sensing/scoring systems are already implemented. Suhita and Khalid use the actual handoff from P02 onward.

## Simulation interfaces

| Record | Required data and constraints |
| --- | --- |
| WorldState | Tick, mission phase, actors, grid/door revision, core owner, inventories, noises, guard/NEXUS memory, seed. Private authoritative mutable state. |
| Observation | Schema version, agent ID, tick, permitted static map, known door changes, visible entity snapshots, heard cues, legitimate reports, own status/inventory, mission phase. Deeply immutable and serializable. |
| Action | Actor ID, kind, issue tick, direction or target ID/tile, movement intent including sprint where legal. No arbitrary callback or executable payload. |
| StepResult | Committed tick, new permitted observations, ordered events, optional terminal result; presentation state is separate. |
| SecurityReport | Source ID, kind, observed tile/sector, observation tick, confidence, provenance/event ID and optional expiry. A sound report never becomes confirmed sighting without visual evidence. |
| NoiseEvent | Stable ID, kind, source tile, radius/attenuation context, tick, optional legitimately visible source. Heard data excludes hidden actor identity/location. |
| RunResult | Run ID, mode, seed, outcome, simulation duration, detections, gadget use, policy ID/hash, capture guard/sector, grade, decisive events, version metadata. |

RunResult also records distinct detection encounters, completion/stealth/pace subtotals, final score, scoring version and pace-reference ticks, following the [approved scoring specification](../planning/SCORING.md). Raw per-guard confirmations remain diagnostic events; scoring uses the shared encounter count. The Simulation owns encounter lifetime and scoring; UI and controllers cannot emit extra point awards.

Action kinds follow the PDF: MOVE, WAIT, INTERACT, ECHO, EMP, MELEE, HIDE. Human E resolves to a stable interaction request for doors/core/hiding. Controller requests are validated centrally; illegal/expired requests consume no resource and produce a rejection reason for diagnostics. Define a bounded tick-validity window and deterministic priority for simultaneous requests during P01.

Implemented P01 rule: an action must match its latest Observation.tick; multiple intents for one actor all reject, and actors resolve in stable ID order. The diagnostic accepts cardinal tile MOVE/WAIT only, increments a committed tick and emits typed events. Sprint, interactions/tools, continuous speed, sensing and terminal scoring remain assigned later behavior. Only individual Observation values go to controllers; StepResult/presentation snapshots stay with orchestration/UI.

The mission is INFILTRATE -> CORE_HELD/LOCKDOWN -> WIN, CAPTURED or ABORTED. Capture can also end infiltration. Aborted attempts are unsuccessful but labeled distinctly. Core theft assigns ownership, raises lockdown, emits CORE_TAKEN and changes objective atomically, exactly once. Only the actual carrier may extract. An Echo is a decoy entity with no inventory or mission authority.

## Replay and telemetry

Each run header records schema/game version, commit, Python/dependency-lock version or hash, map hash, balance hash, seed, initial NEXUS memory/protocol, policy version/hash and simulation rate. A seed alone does not reproduce a changed build or a human run; record human action ticks too.

Use separate deterministic RNG streams for world setup, AI decisions and cosmetic effects, derived with a stable documented seed function rather than process-randomized language hashing. Stable ordering resolves equal-cost path nodes, equal utilities and equal-visit MCTS actions. Capture decisions at their issue ticks, and store canonical state/event hashes for regression comparison.

Canonical gameplay events include MOVE/INTERACTION outcomes as needed for replay, CORE_TAKEN, NOISE_CREATED, SIGHTING_CONFIRMED, REPORT_SENT, CAPTURE_STARTED/CANCELED/COMPLETED, GUARD_DISABLED/STUNNED, TOOL_USED, LOCKDOWN_STARTED, MISSION_ENDED and POLICY_DECISION. Algorithm diagnostics carry agent ID, tick, algorithm, inputs from its permitted view, selected option and metrics.

Keep privileged debug telemetry separate from what controllers consume. Bound event buffers and disk growth. Do not log full per-frame state indefinitely; use configurable diagnostics and a retained run-history limit. Disk-write failure must not change simulation decisions or stop a playable run.

## Policies and persistence

Policies contain ID, base preset, policy version, label, navigation, guard reaction, emergency priority, risk tolerance and bounded search settings. Run seed and memory-reset options are deployment settings; support reading the blueprint's combined example by separating these fields during load. Validate enums, numeric bounds, length and unknown/unsupported versions before applying. No eval, executable config or arbitrary imports.

Presets:

| Preset | Navigation | Guard reaction | Emergency | Risk |
| --- | --- | --- | --- | --- |
| Ghost | Safest | Hide | Escape-first | Cautious |
| Balanced | Balanced | Retreat/replan | EMP if trapped | Balanced |
| Rush | Shortest | Consider Echo | Melee if adjacent | Bold |

Persist versioned settings, policies, run history, JSONL telemetry and NEXUS memory under an OS-appropriate user application data directory, never beside the installed executable. Memory reset must clear every adaptation input, not just the displayed protocol. Use atomic replacement for JSON, bounded history, sensible defaults for missing fields, and a recoverable backup/quarantine path for corrupt files. Unknown future schema versions must not be silently overwritten. Test migration and unwritable directories.

## Map validation

Require unique stable IDs for Spawn, Exit and Core; five named zones; four-neighbor occupancy; patrol paths; hide spots; doors; props; tactical chokepoint graph; and explicit movement/vision/sound tags. Ground/decor are render-only. Glass partitions and breakable racks have distinct properties. Dynamic door updates must revise both relevant geometry and navigation caches.

Reject duplicate/missing objective anchors, invalid patrol coordinates, unknown object types without a declared cosmetic allowance, broken external resource references, and unreachable goals. Validate both branches, cross-link and lockdown return connectivity. Automated reachability does not prove that patrol timing and capture balance are fair; add real playtests.

## Initial tunable values

| Parameter | Blueprint starting point |
| --- | --- |
| Simulation / rendering | 30 Hz / target 60 FPS |
| Logical tile / example map | 32 px / approximately 80 x 56 cells |
| Walk / sprint | 2.2 / 3.6 tiles per second |
| Guards | Roughly 5-6: 2-3 Sentinels, 1-2 Trackers, one Interceptor |
| Capture telegraph | Approximately 0.4 s, represented as ticks |
| Echo | Three charges, previous 2.5 s path replayed backward |
| EMP | One charge, approximately 2.5 tiles radius / 3 s disable |
| Melee | One adjacent reachable target / 1.5 s stun / 2 s recovery immunity |
| Tracker sighting TTL | Approximately 5 s, refreshed only by fresh evidence |
| Core interaction | Approximately 0.8 s continuous valid interaction |
| Sound radii in tiles | Walk 0-1; sprint 3; canister 4; glass 6; melee 6; EMP 5 |
| Interceptor search | Depth 2-3, event driven |
| Companion MCTS | 64 simulations, rollout depth 4, deterministic iteration budget |
| Presentation reference | 1280 x 720, preserve aspect at 1366 x 768 and 1920 x 1080 |

Keep these in a versioned configuration resource with units and bounds. Log tuning changes with before/after values and evidence. Avoid storing the same numerical constant separately in AI, UI and simulation code.
