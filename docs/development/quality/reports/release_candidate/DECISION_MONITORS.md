# Live AI decision monitors

2026-11-20, Khalid. Companion and guard monitor review on runtime `92e196c`, based on the [five-guard candidate](CORE_SECURITY.md).

## Use the monitors

Launch Companion Infiltration from the Workshop. Choose a preset and seed with NEXUS memory reset to baseline. With **F2**, use the mouse or **1–3** for Companion, NEXUS and Interceptor. The Companion panel shows the resolved current action, the last Monte Carlo tree search choice and trigger, option visits and mean rollout rewards, and the active A* waypoint and cost. An immediate utility response can interrupt that plan.

Press **F3** and use **1–5** to inspect each guard. The panel shows its current state, filtered sight and hearing, the evidence backing its goal, and the measured search or fuzzy rule evaluation. The Interceptor tab shows minimax depth, evaluated leaves, alpha-beta pruning and the assigned gate. The capture report names the guard that completed the grab.

## Native playthroughs

Cocoa and CoreAudio, 1280 × 720 and 1440 × 900. Runs used the normal gateway, preset policies, authored facility and props. The renderer consumed telemetry from committed steps. Local screenshots and event/decision traces are under `output/decision-monitors/`.

| Preset | Seed | Result | Simulation tick |
| --- | ---: | --- | ---: |
| Balanced | 1042 | Cargo Airlock, 64/B | 2826 |
| Rush | 1042 | Vault Sentinel capture, 0/F | 1059 |
| Balanced | 4 | Core Interceptor capture, 0/F | 1143 |

Balanced selected **Switch route** after seeing the Security Sentinel in lockdown. The search allocated 58 of 64 visits to that option, with a mean reward of 0.63. It later used its final stun to break the Research Tracker's grab and reached Cargo.

Rush spent all its tools. Its search at tick 1040 gave **Wait** 27 visits and **Advance** 26. Actual execution then tried to pull out of reach during the grab. The Vault Sentinel completed the capture at tick 1059. The panel can show that immediate escape attempt beside the earlier Wait plan. Wins still require stealing the Core and crossing a real extraction point. Captures still require a defender to complete a grab. Seeded sampling supplies MCTS rollouts.

## Trace integrity

The earlier monitor could label a translated directive as the latest MCTS winner. An **Alternate** choice could appear as **Advance** while its original reason and visits still referred to switching. The search winner and trigger now stay attached to their evaluation tick. The runtime also samples its most recent action and any actual rejection for the execution display. The route overlay hides invalidated A* plans.

The complete 96-run comparison reproduced every outcome, elapsed tick and simulation fingerprint from the previous candidate. There were 14 wins, 82 captures and zero runner caps. The sampled search evaluation counts and choice tallies now describe the actual winning alternatives. The first repeated run matched.

## Package and checks

- `uv run --locked --all-extras python scripts/checks/run.py` passed structure, lint, formatting, strict mypy and 337 tests.
- `uv run --locked python scripts/experiments/comparison.py --output-dir output/decision-monitors/comparison` produced the current comparison. Outcomes, elapsed ticks and fingerprints were checked against the earlier Core security run.
- `uv run --locked --all-extras python scripts/packaging/build.py` built the Apple Silicon ZIP from a clean checkout of `92e196c`. Fresh extraction passed codesign verification and all nine frozen checks with Cocoa and audio ready. The ZIP is 114,115,571 bytes, SHA-256 `5e513fdeab5bc196d1c661eb2be2a0c7741defb50081a3e9bcb444b07b3471e7`.
- Hosted Linux checks and the Windows x64 and macOS arm64 builds and frozen smoke passed on the same runtime. Physical Windows gameplay is still a delivery gate. [Candidate CI](https://github.com/khalid999devs/Echo_Heist/actions/runs/44622732600).
