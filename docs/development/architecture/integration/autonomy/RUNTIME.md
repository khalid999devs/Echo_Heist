# P04 runtime, defender and protocol contract (SR side)

2026-10-25, Suhita, `work/suhita-p04` (merged `origin/work/khalid-p04` at `1d24b4b`). This is the logic side of the [presentation port](PRESENTATION.md). It accepts Khalid's immutable `core/contracts/autonomy/` records unchanged and adds only the internal records below. Nothing here changes the Human controls, geometry, stairs, crouch, sprint or audio contracts.

## Agreed external interface (unchanged from KR)

- `AutonomyGateway` / `AutonomousRun` / `MissionRuntime`, `DeploymentRequest`, `PolicySelection`, `ProtocolState`, `LearnedProtocol`, `CompanionTrace`, `NexusTrace`, `GuardTask`, `InterceptorTrace`.
- The gateway advertises **HUMAN and COMPANION** with protocols available, so both modes share the same defenders and NEXUS. Human actions are forwarded unchanged; in Companion mode the UI supplies an empty action tuple and the runtime asks the Companion controller.
- Telemetry is built once after each committed step and cached; `telemetry()` never runs a search.

## New internal records

| Record | Location | Meaning |
| --- | --- | --- |
| `GuardRole.INTERCEPTOR` | `core/contracts/security/model.py` | Registry role for INTERCEPTOR actors; algorithm label `ALPHA-BETA`. `POST` stays for tests/legacy sensing-only posts. |
| `InterceptPlan` | same | Interceptor's own last actual search: tick, post ID/tile, depth, evaluated leaves, pruned branches, value, hypotheses. Stored in its `GuardMemory.intercept`. |
| `SecurityReport.recipient` | `core/contracts/events.py` | Empty for broadcast radio. A NEXUS dispatch is `report_kind="DISPATCH"`, `source_guard="nexus"`, addressed to one guard, carrying the **original** evidence tick. |
| `RouteGraph`, `ZoneArea`, `RouteNode` | `core/contracts/security/director.py` | Public static zone/chokepoint graph built by the validated registry; core/exit zones and chokepoint-to-chokepoint walking distances. |
| `DirectorRules`, `ProtocolId`, `ActiveProtocol` | same | NEXUS caps/coverage and the at-most-one protocol applied to this attempt. |
| `NexusEvidence`, `NexusStatus` | same | What NEXUS legitimately observed this attempt (for persistence) and its current tasks/announcement (privileged display). |

`SecuritySpec` gains optional `graph` and `director`. Without them the P03 behavior is used; the packaged registry supplies both, so the shipped game always has NEXUS.

## Information boundary

- **NEXUS view**: the union of its guards' own filtered observations (heard cues, visual cues, radio reports), the public mission phase/core alarm and its own robots' status. It never reads intruder actors, the Companion's policy or controller memory.
- **Interceptor**: its own observation plus radio reports and NEXUS dispatches. Route hypotheses come from report/last-seen tiles and the static graph, never from the intruder's true position or future action.
- **Companion**: its own `Observation` plus a public `MissionBriefing` (map, zones, chokepoints, cover, core/exit and the guard roster with type and home zone). Beliefs come only from what it saw; unseen guards are sampled from briefing hypotheses.

## Persistence

`infrastructure/persistence/protocols.py` stores schema-1 `nexus-memory.json` beside settings in the user data directory. Missing → baseline; corrupt → quarantined copy and baseline; future schema → refused without overwrite. Reset clears every adaptation input (evidence totals, attempts, active protocol) and bumps the revision. At most one protocol is selected between attempts, announced through `ProtocolState.active` before deployment, applied unchanged for that attempt, and its evidence is recorded once when the attempt ends.

## Fingerprint and replay

NEXUS memory is part of `WorldState`, so the canonical fingerprint schema becomes **10**. Replacing the sensing-only POST with the Interceptor changes recorded defender traces; P03 hashes are historical. The replay header records the director/protocol configuration through the registry revision and fingerprint.

## Shared-file claims

Narrow startup composition only: `ui/bootstrap.py` passes the data directory, `ui/startup/sequence.py` forwards it, `ui/startup/loader.py` constructs the gateway and injects `GameFlow(..., autonomy_gateway=gateway)`. No render/camera/layout/art/map JSON edits. UI test expectations that name the Core guard's algorithm are updated from `NONE` to `ALPHA-BETA` only.
