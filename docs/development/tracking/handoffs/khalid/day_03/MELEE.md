# Applied limited-melee handoff

**2026-10-30 / Khalid / user-directed P05-SR1 balance subset and KR1 HUD.** Branch `work/khalid-p05-visuals`, runtime **`68d0c69bc6833a73262653602cd075fe8314b86a`**, after presentation handoff `4709833`. [Approved override](../../../../planning/balance/MELEE.md), [actual verification](../../../../quality/reports/phase05/khalid/MELEE.md), [evidence](../../../../quality/reports/phase05/khalid/MELEE_EVIDENCE.json). Main and the P04 branch are unchanged.

The approved melee subset is implemented and verified. Suhita retains all other P04/P05 logic and connected phase gates. This direct user request supersedes the prior presentation-only boundary for these named fields/rules only.

## Player-visible behavior

Space makes a single-target emergency stun: **two charges per attempt**, no refill, **four-second recovery**. The existing 1.5-second stun and two-second guard immunity remain. A valid resisted hit spends a charge, starts recovery and makes noise. Invalid/out-of-range/empty/recovering attempts spend nothing and emit no gameplay impact noise. The ordinary unavailable UI sound is cosmetic.

The STUN HUD now shows actual charges and recovery, such as `1 / 4.0s`; empty and recovering requests have distinct notices. Pause freezes Simulation and its countdown. Retry creates fresh inventory/timers. Human and Companion actors use the same authoritative tool validator/effect; the real autonomous P04 controller remains Suhita's separate prerequisite.

Each valid impact produces exactly one existing six-tile MELEE NoiseEvent, with normal acoustic occlusion. Nearby guards can investigate its original tile using existing fuzzy urgency and roughly five-second evidence memory. Guards beyond acoustic reach hear nothing. That memory never supplies a moving player's current location or creates confirmed sighting without actual vision. Scoring is unchanged.

## Changed contracts

- `Inventory.melee_charges = 2` is appended after existing fields, preserving their positional arguments. This is the initial stock source, like existing Echo/EMP defaults.
- `GameRules.melee_cooldown_ticks = 120` is configured in the locked gameplay JSON at 30 Hz. Four seconds is simulation time. No clock or rendering callback replenishes stock or advances recovery.
- Private `ActorState.melee_ready_at` holds the committed deadline. `OwnStatus.melee_cooldown_remaining` exposes only that actor's remaining ticks; ObjectiveView/HUD consume the same state.
- `TOOL_USED` for melee retains `tool`, `target_id`, `affected`, and additionally publishes actual `remaining` and `ready_at_tick`. New rejection reasons are `melee_empty` and `melee_cooldown`.
- Prevalidation checks the upcoming commit tick; execution revalidates after all movement. A request that commits exactly at `ready_at_tick` is legal. A request one tick earlier is rejected without cost/noise.
- **Fingerprint schema is now 10**, including the new stock/timer/rules. Replay headers use 10 and pin the changed rules hash. Old schema-9 hashes/logs are historical and must not be presented as current exact matches. Map geometry and sensing configuration are unchanged.

The input adapter still emits ordinary MELEE actions. Diagnostic Human/action drivers now inspect their own stock/recovery before choosing one, preserving their ordinary observation boundary. These helpers are not the future Companion algorithm.

## Run and inspect

```sh
uv sync --locked --all-extras
uv run --locked echo-heist
uv run --locked python -m tests.fixtures.interactions.melee_capture --output output/melee-balance/hud
uv run --locked python scripts/checks/run.py
```

Normal controls remain Space stun, Q Echo, F EMP, C crouch and Shift sprint. The native melee audit saves eight states: two charges, first hit/recovery, recovery rejection, pause, recovered with one charge, second strike/zero, empty rejection and retry/two. It uses real Simulation/input in a clearly labeled practice layout with one stationary guard and guard AI disabled. Separate normal Human mission runs use the actual four-guard security registry.

## Suhita's next action

Complete P04-SR first. When retrieving this P05 branch, preserve these implemented rules rather than rebuilding unlimited melee. Adapt Companion utility/rollouts to actual `melee_charges` and `melee_cooldown_remaining`; controller predictions cannot bypass Simulation validation. Keep both fields in immutable own observations and resource-aware evaluations, including normal simulation-tick recovery during rollouts.

Existing typed P04 deployment/startup/controller seams are untouched. Remaining P05-SR1 tool/capture edge cases, all SR2 environment lifecycles and final object placements still belong to Suhita. Approval of this small subset does not complete her SR1 slice or P05. Read the [presentation handoff](P05.md) for the other consumers. No teammate message was sent; the narrow implementation claim is released after verification.

## Verified builds

All three [runtime CI jobs](https://github.com/khalid999devs/Echo_Heist/actions/runs/41048163778) pass. [Matching Windows x64 artifact](https://github.com/khalid999devs/Echo_Heist/actions/runs/41048163778/artifacts/12973975606): extract the hosted artifact, then its versioned game ZIP, and launch `EchoHeist.exe`. This build includes limited melee; the older `59fffba` artifact does not. Suhita still verifies physical Windows play/audio.

Local Mac: `dist/echo-heist-0.1.0a1-macos-arm64.zip`, source `68d0c69`; app and fresh ZIP **9/9 native checks**, audio ready, ad-hoc signed. This replaces the previous file at that path. Build hash/bytes are in the new evidence. This rule/HUD change required no new art/audio assets or dependencies.
