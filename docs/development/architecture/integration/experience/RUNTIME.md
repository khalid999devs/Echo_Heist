# P06–P08 SR runtime: scoring, experience service and experiments

2026-11-11, Suhita, branch `work/suhita-p06-p08` (stacked on `work/suhita-p05`). The consumer side is Khalid's [experience presentation contract](PRESENTATION.md); nothing here changes his screens' contracts.

## Approved scoring (P06-SR1)

- Rules: `resources/data/gameplay/scoring.json` → `ScoringRules` (scoring version 1). The 50/40/12/10 weights and S/A/B/C/F bands are the [approved rules](../../../planning/SCORING.md); `ScoringRules` refuses other weights. `pace_reference_ticks` stays at the marked draft **27,000 ticks (900 s)** and `speedrunner_ticks` at a draft **9,000 ticks (300 s)** until Suhita's physical Human playtest (see the [comparison report](../../../quality/experiments/POLICY_COMPARISON.md) for measured durations).
- `core/scoring/score.py`: `score_run` (one integer function for both modes), `pace_points`, `grade`, `achievements` (Ghost = no encounter, AI Master = Companion win, Speedrunner = win within the threshold; labels only).
- `core/scoring/encounters.py` + Simulation: after guard decisions, every guard in CHASE whose `last_seen_tick` is this observation tick is one confirmation at its original tick; a grab start is also a confirmation. A team encounter starts on the first confirmation while none is active and counts once; it stays active while the newest confirmation is within `SensorRules.memory_ticks` (150) or any grab is in progress. Relayed reports, other guards, repeated sight, stun/EMP, hearing, partial suspicion, Echo motion and unwitnessed cover never add a count.
- `Simulation(..., scoring=ScoringRules)`; `StepResult.terminal` is the authoritative `RunResult` on and after the ending tick (including abort); `Simulation.terminal_result()` and `detection_encounters()` are privileged reads. `decisive_events` keeps encounter starts, Core taken, lockdown, capture and the mission end (at most 24).
- `AutonomousMission` fills `policy_id` for Companion attempts, counts its own `TOOL_USED` events (`tools`) and calls the optional result listener once when the attempt ends.
- Fingerprint schema **13** (scoring rules, encounter state, decisive events, optional scenario start).

## Experience service (P06-SR2/SR3)

`autonomy/experience.py` `ExperienceService` implements `ExperienceGateway`; `autonomy/gateway.connect_experience(gateway, data_dir)` wires it to the NEXUS gateway; `ui/startup/loader.py` passes it to `GameFlow(experience_gateway=...)` beside the autonomy gateway.

| Port | Behavior |
| --- | --- |
| `report` | Returns the finished attempt's own `RunResult` when map, seed, mode, outcome and elapsed ticks match; tools are the runtime's own count; one report per run key; prepends it to history. Unknown attempt → `None` |
| `history` | Newest first, at most 100, unique run keys |
| `profiles` / `save_profile` / `delete_profile` | At most 32; names 1–24 printable characters; saving an existing name (case-insensitive) updates that profile and keeps its ID; IDs `profile-<n>` never reused; deleting an unknown ID fails |
| `preferences` / `save_preferences` | Controls, captions and contrast; the UI still validates bindings and falls back to defaults with a notice |

Files beside settings and NEXUS memory: `policy-profiles.json`, `run-history.json`, `desktop-preferences.json`, each `{"schema": 1, ...}` written atomically. Missing → empty/default. Damaged → moved to `<name>.corrupt-<ns>.json`, reported once with `ExperienceUnavailable`, then a fresh store. Newer schema → left untouched; reads and writes refuse with a clear reason. A failed history write never hides the run's score.

Report labels: `Human`; `Ghost`/`Balanced`/`Rush` for an unmodified preset; otherwise the saved profile name, or `Custom policy`. Backend presets: `core/contracts/autonomy/policy.PRESETS` (a test keeps the Workshop's preset buttons identical).

NEXUS switch: `NexusGateway.set_protocols_enabled(bool)` persists the choice; disabling clears the selected protocol so the next attempt is the baseline. It is a backend method only; a Workshop toggle is Khalid's UI work.

Deployment: the gateway applies seed, policy and the current protocol memory together at `deploy`; reset, retry (same seed/policy) and new-seed choices stay in Khalid's Flow and are unchanged.

## Experiments (P07-SR1/SR2, P08-SR2)

- Registry `resources/data/experiments/scenarios.json` (`experiments/scenarios.py`): suite `vault-five-zone/v1`, 24 scenarios in 11 categories, four policies (Ghost, Balanced, Rush, Custom = Safest/Retreat/EMP-if-trapped/Balanced), runner tick cap 9,000.
- Scenario starts are explicit test inputs: `IntruderStart` (`core/contracts/config/scenario.py`: start tile, reduced tool stock, Core already held → lockdown) plus a Companion deployment hold. They are part of the fingerprint; normal play never uses them.
- Harness `experiments/harness.py` records outcome, score/grade/encounters/subtotals, raw confirmed sightings, tools, capture guard/zone, route zones, stairs, longest still streak, MCTS decisions/visits/chosen actions/overrides, A* expansions/no-path plans, Sentinel fuzzy evaluations, Interceptor searches/evaluated/pruned/posts, decisive events and fingerprint; wall-clock tick timing is kept apart.
- Runner `scripts/experiments/comparison.py --output-dir <dir> [--only ...] [--policies ...]` writes `runs.json` and `runs.csv`; its deterministic hash excludes timing and normalizes the lock file's line endings.

## Behavior fix (P07-SR1)

`ai/guards/steering.give_way`: a guard whose next step pushes into another guard's body within half a tile (from its own observation) tries the other axis toward its waypoint, then a perpendicular step. Intruders are never treated as blockers. This removed a permanent two-guard deadlock in the core corridor (scenario s06 timed out at 9,000 ticks before; now it resolves).
