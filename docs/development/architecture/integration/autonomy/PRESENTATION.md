# P04 presentation and runtime integration port

2026-10-25. Khalid claims KR1/KR2 on `work/khalid-p04` from main `65df8b5`. No P04 logic branch or PR was published at startup. This document defines the presentation seam for Suhita's SR1/SR2/SR3; it does not claim that her controllers, protocols or autonomous outcomes exist.

## Implemented shared types

`core/contracts/autonomy/` contains data-only deployment selections, immutable measured telemetry and structural runtime ports. They import no pygame, UI, Simulation implementation or persistence. Existing Simulation satisfies `MissionRuntime`; Suhita's orchestration wrapper selects AI actions from filtered observations and forwards every mutation to Simulation.

- `AutonomyGateway.availability()` returns supported `ControlMode`s, protocol-service availability and an honest unavailable reason. Human's existing built-in runtime remains available without a gateway. Companion never falls back to the Human runtime.
- A protocol summary/review applies only to modes actually handled by the gateway. A Companion-only service does not relabel the built-in Human attempt as adapted. The complete SR integration should advertise both modes so Human-vs-AI and AI-vs-AI share real defenders/NEXUS; forward Human actions unchanged through its runtime.
- `protocols()` returns actual `ProtocolState`; `reset_protocols()` performs the backend-owned persistent reset and returns its resulting state. Reset requires explicit UI confirmation, is available only between attempts, and is never inferred from a visual toggle.
- `deploy(DeploymentRequest(mode, seed, map_id, policy))` returns a new `AutonomousRun` with `actor_id`, `mode`, `runtime` and `telemetry()`. Failure raises `DeploymentUnavailable`, leaves the current scene/attempt untouched and starts no hidden simulation.
- A new runtime starts at tick 0, uses the same simulation rate and authored map as the presented mission, and exposes an actual OPERATIVE for Human or COMPANION for AI. The UI follows `actor_id`; it never assumes the Human spawn ID is the robot.
- `MissionRuntime` exposes tick/rate, filtered `observe`, privileged `presentation_snapshot`, validated `step(..., abort=...)`, and canonical `fingerprint`. In Companion mode the UI supplies no movement/tool actions; the backend chooses them. Pause/map/settings/entrance stop calls to step. Abort is forwarded to the same runtime. Companion retry returns to Workshop with the original policy/seed for a fresh protocol review, rather than silently launching another attempt. Human retry also returns to its briefing when a protocol service is available.

## Telemetry semantics

`CompanionTrace` is the last actual decision: original tick, FSM state, chosen action/reason, completed simulation count, alternatives with visits and normalized mean rewards, actual A* path/cost/expanded nodes, and optional actual utility override/reason. Unknown rewards are None; unvisited alternatives are not shown as measured zero rewards. Visits cannot exceed completed simulations. Drawing never runs MCTS, A*, utility or an inference function.

`NexusTrace` carries actual evaluation/announcement ticks, current legitimate-evidence task assignments and optional measured Interceptor depth/value/evaluated/pruned-node trace. `LearnedProtocol` includes a stable ID, label, rationale and observed evidence summary. `ProtocolState` describes the real backend revision/memory setting/active protocol/reset capability. Absence of a trace or service is shown honestly, not as fabricated baseline statistics.

`AutonomyTelemetry` is privileged read-only display data. It must never be fed to Companion, guards, NEXUS, beliefs or rollouts. Original observation/evidence timestamps remain authoritative. Backend persistence, eligibility, one-announced-protocol rules, legal actions and information fairness remain Suhita's responsibilities.

Telemetry is sampled after committed runtime steps and cached by the session. Rendering/paused panels never reevaluate an algorithm or read disk. `announcement_tick` plus text identifies an announcement: repeated delivery does not replay its notice/audio. The UI does not enforce the one-adaptation rule by hiding backend events. Every actual mutation, protocol selection and persistence/reset guarantee must be implemented and verified by SR3.

The active actor ID drives camera, interpolation, observation, map, own-tool audio, guard-cue filtering and stair art. Companion spectator input never forwards Human movement/tool actions. F2 toggles three diagnostic tabs; F3 retains the existing independent guard view. Stair cinematics overlay teaching panels and suppress their pointer targets. All tabs reuse the existing explicit UI-audio serial and full-display event mapping.

Variable explanations are fitted/wrapped and cached with bounded label/surface caches. Missing metrics remain unavailable; a normalized reward of zero is distinct from an unvisited `None`. The backend supplies original decision times, finite normalized values and coherent visit budgets; invalid data fails at the typed boundary instead of being silently corrected into apparent evidence.

## Composition and ownership

Suhita supplies `AutonomyGateway` to `GameFlow(..., autonomy_gateway=gateway)` in the existing app composition. One keyword argument is the intended composition hook; there is no dynamic plugin discovery, import-time service, test AI fallback or second game engine. Prepare/read services explicitly during startup ownership transfer; never advance gameplay while resources/entrance obscure it.

Khalid owns the new presentation modules, camera/active-actor wiring and narrow deployment/event/audio consumers in `flow.py` / `heist.py`. Suhita implements the gateway and orchestration under her logic/application boundaries. Claim any conflicting shared methods before editing. Adapters may translate existing backend DTOs into these immutable records; do not duplicate algorithms in presentation.

The four policy selections match the existing Workshop design (navigation, guard reaction, emergency, risk). P04 carries them in an immutable deployment request; P06 still owns full saved profiles/history/editor semantics. Global physics/scoring/sensor rules are never policy fields.

Implementation checkpoint: `77bcf00`. Read [Khalid's runnable handoff](../../../tracking/handoffs/khalid/day_02/phase04/P04.md) for retrieval, real-runtime acceptance and native/CI results. Default app composition deliberately has no nonexistent gateway. SR3 owns its construction and injection; do not merely advertise Companion availability without connecting a real runtime. Merge `origin/work/khalid-p04` into the SR work branch normally, claim the narrow startup hook, then keep the tested screens intact.

## Completion boundary

Independent camera/layout/control/port checks and explicitly labeled synthetic QA fixtures can prove presentation behavior. They do not prove autonomous planning, justified NEXUS adaptation or a completed P04 phase. KR live acceptance remains open until Suhita's actual runtime demonstrates real autonomous win/capture, actual search traces and protocol reset on the combined game. Main's working Human path and fingerprint-9 behavior must remain intact.
