# Final presentation runbook

Use the current desktop build, seed **1042** for Human mode and **Rush, seed 44 and 18** for the Companion win and capture. The [lab gameplay report](../../quality/reports/release_candidate/LAB_GAMEPLAY.md) records the stealth revision. The [earlier rehearsal](../../quality/reports/release_candidate/FINAL_REHEARSAL.md) retains the original algorithm evidence. Use a fresh local data directory for the presentation so earlier settings, policies and learned protocols stay out of the rehearsal.

```sh
uv run --locked echo-heist --seed 1042 --data-dir .local/presentation-demo
```

The Mac app can also launch from the locally extracted presentation ZIP. For an isolated profile, run the following from the directory containing the extracted app.

```sh
"./Echo Heist.app/Contents/MacOS/EchoHeist" --seed 1042 --data-dir "$PWD/presentation-profile"
```

Keep the lab gameplay ZIP available offline. Start with the six-second launch clip if you are presenting from video. Four mission recordings include their result screens, and two shorter clips focus on the live decision monitors.

## Four-minute walkthrough

| Time | Show | Explain |
| --- | --- | --- |
| 0:00–0:25 | Title → Play Chapter → Tab facility map | One heist, two playable modes and two exit airlocks. The same simulation enforces movement, tools, detection, capture and extraction. |
| 0:25–1:05 | Human highlights. Reach Stair A, take the Core and return through Stair B to Cargo. | Sprint trades speed for noise. A guard investigates the sound tile. Holding E takes the Core and triggers lockdown. Extraction requires the Core. |
| 1:05–2:55 | Workshop → seed 44 → Rush → Deploy with NEXUS memory off. F2 → 1 for Companion, 2 for NEXUS, 3 for Interceptor. | The same bot uses the Service and Cargo lockers and extracts at 61.5 simulated seconds. Show cover, a route decision and the AI Master badge. |
| 2:55–3:35 | Review & Retry → seed 18 → Rush, or play the end of the recorded capture. | The bot takes the Core and hides three times. A later grab completes at 100.7 simulated seconds. |
| 3:35–4:15 | Results and experiment summary. D opens decision details. | Show the outcome, detected encounters and tool usage. The 24 situations per policy produced 95 captures and one timeout. The live demos use two normal deployments. |

For a live Human attempt, select Human and Launch Mission. Crouch with C and move under a desk, or press E at a locker. Use the Security staircase A to approach the Core, hold E to steal it, and return via Research staircase B to the Cargo Airlock. Travel behind bulkheads to break sight, then wait for the Cargo Sentinel to move past the locker. Use Q for an Echo decoy, F for EMP and Space for a close stun. The offline recording preserves the demonstrated route if a live attempt goes differently.

## Algorithm talking points

- **Sentinel, F3.** Breadth-first search finds a route in grid steps. The finite-state machine moves between patrol, investigation, chase, search and return. Fuzzy rules combine graded cues into urgency. The panel shows actual rule weights and outputs.
- **Tracker, F3.** A* uses a goal-distance heuristic. When contact is lost, the Tracker searches the last legitimate position and nearby tiles until its evidence expires. Show the evidence timestamp and goal on the panel.
- **Companion, F2 → 1.** The mission state machine sets the objective. MCTS uses selection, expansion, rollout and backpropagation to compare tactical options. The game uses 64 simulations with a depth cap of four. Visits count sampled search effort. Mean reward is the model's estimate from those samples. Risk-weighted A* plans the tile route, and utility can interrupt the plan during immediate danger.
- **Interceptor, F2 → 3.** Depth-limited minimax weighs possible escape routes and selects a gate. Alpha-beta skips branches that cannot affect the choice. In the controlled example at guard tile `(59, 26)`, both searches chose the Research gate at value 0.255333. Plain minimax evaluated 23 leaves and alpha-beta evaluated 9. The guard still travels to its post.
- **NEXUS, F2 → 2.** Rules dispatch defenders using evidence and the lockdown signal. With memory enabled, a prior rehearsal recorded three witnessed decoys and the Workshop offered **Verify Echo** for the next attempt. Reset clears the protocol. Keep memory off for the paired Rush runs.

## Offline materials

Use the H.264/AAC MP4s in `output/lab-gameplay/clips` for widescreen playback. The Companion monitor clip shows live MCTS and A*. The enemy monitor clip shows NEXUS orders, the Interceptor's search and individual guard evidence. The current policy comparison is in `output/lab-gameplay/work/stealth/comparison-final/runs.csv`. The earlier controlled alpha-beta sample and memory evidence are in `output/final-rehearsal/`.
