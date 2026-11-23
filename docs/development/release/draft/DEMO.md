# Final presentation runbook

Use the current desktop build, seed **1042** for Human mode and **Rush, seed 42 and 82** for the Companion win and capture. The [final presentation report](../../quality/reports/final_presentation/FINAL_PRESENTATION.md) records the final build, its checks and the slide and report files. The [lab gameplay report](../../quality/reports/release_candidate/LAB_GAMEPLAY.md) records the earlier stealth revision. The [earlier rehearsal](../../quality/reports/release_candidate/FINAL_REHEARSAL.md) retains the original algorithm evidence. Use a fresh local data directory for the presentation so earlier settings, policies and learned protocols stay out of the rehearsal.

```sh
uv run --locked echo-heist --seed 1042 --data-dir .local/presentation-demo
```

The Mac app can also launch from the locally extracted presentation ZIP. For an isolated profile, run the following from the directory containing the extracted app.

```sh
"./Echo Heist.app/Contents/MacOS/EchoHeist" --seed 1042 --data-dir "$PWD/presentation-profile"
```

Keep `output/videos/` available offline. The deck in `output/final/` embeds 17 short real-speed clips and two double-speed runs, and each one starts by itself when its slide opens. Start with the six-second opening clip if you are presenting from video. The full-speed takes include their result screens.

## Four-minute walkthrough

| Time | Show | Explain |
| --- | --- | --- |
| 0:00–0:25 | Title → Play Chapter → Tab facility map | One heist, two playable modes and two exit airlocks. The same simulation enforces movement, tools, detection, capture and extraction. |
| 0:25–1:05 | Human gadget heist (seed 1042, double speed). An Echo from the Service locker, a second Echo at the Vault recess, the theft with a stun and the EMP, the Cargo locker and a stun at the exit. | Hides only when a guard is in view. Holding E takes the Core and triggers lockdown. Every guard type appears on camera. 76 points, rank A, two encounters. |
| 1:05–2:55 | Workshop → seed 42 → Rush → Deploy with NEXUS memory off. F2 → 1 for Companion, 2 for NEXUS, 3 for the Interceptors. | The bot stuns a grab and hides in a locker, stuns the Vault Tracker and fires its EMP in Security Control, and takes the Core at 33.8 s. The Core Interceptor holds the Security gate and the Cargo Interceptor holds Stairs B, so the bot leaves through the Research gate, hides from the Research Tracker, takes staircase A and leaves through Cargo at 1:13 with 76 points. |
| 2:55–3:35 | Review & Retry → seed 82 → Rush, or play the recorded capture. | The bot takes the Core, stuns the Vault Tracker, uses an Echo and its EMP on the Research Tracker, then both Trackers close in and the Research Tracker catches it at 47 seconds. |
| 3:35–4:15 | Results and experiment summary. D opens decision details. | Show the outcome, detected encounters and tool usage. The 24 hard situations per policy produced 96 captures. Over 1,200 normal deployments Rush won twice; the live demos use two normal deployments. |

For a live Human attempt, select Human and Launch Mission. Crouch with C and move under a desk, or press E at a locker. Use the Security staircase A to approach the Core, hold E to steal it, and return via staircase A to the Cargo Airlock. Travel behind bulkheads to break sight, then wait in the Cargo locker while the Cargo Interceptor and the Research Tracker pass. Use Q for an Echo decoy, F for EMP and Space for a close stun. The offline recording preserves the demonstrated route if a live attempt goes differently.

## Algorithm talking points

- **Sentinel, F3.** Breadth-first search finds a route in grid steps. The finite-state machine moves between patrol, investigation, chase, search and return. Fuzzy rules combine graded cues into urgency. The panel shows actual rule weights and outputs.
- **Tracker, F3.** A* uses a goal-distance heuristic. When contact is lost, the Tracker searches the last legitimate position and nearby tiles until its evidence expires. Show the evidence timestamp and goal on the panel.
- **Companion, F2 → 1.** The mission state machine sets the objective. MCTS uses selection, expansion, rollout and backpropagation to compare tactical options. The game uses 64 simulations with a depth cap of four. Visits count sampled search effort. Mean reward is the model's estimate from those samples. Risk-weighted A* plans the tile route, and utility can interrupt the plan during immediate danger.
- **Interceptor, F2 → 3.** Depth-limited minimax weighs possible escape routes and selects a gate. Alpha-beta skips branches that cannot affect the choice. There are two Interceptors and each searches only its own zone's gates. At the theft on Rush seed 42 (tick 1014), the Core Interceptor's minimax and alpha-beta both chose the Security gate at value 0.2947; plain minimax evaluated 40 endings and alpha-beta 25, skipping 15 branches. In the same tick the Cargo Interceptor chose Stairs B and the robot's MCTS advanced through the Research gate. Each guard still walks to its post with A*.
- **NEXUS, F2 → 2.** Rules dispatch defenders using evidence and the lockdown signal. With memory enabled, a prior rehearsal recorded three witnessed decoys and the Workshop offered **Verify Echo** for the next attempt. Reset clears the protocol. Keep memory off for the paired Rush runs.

## Offline materials

Use the H.264/AAC MP4s in `output/videos/` for widescreen playback. The robot take shows live MCTS, NEXUS orders and both Interceptors' searches. The F3 take shows individual guard evidence, paths and fuzzy urgency. The Human capture and the seed 82 robot capture both show the two Trackers closing in. The slides and printed report are in `output/final/` and the proposal deck is in `output/proposal/`. The current policy comparison is in `../Echo_Heist_archive/presentation-build/experiments/runs.csv`. The earlier memory evidence folder was removed in the 2026-11-22 cleanup; its numbers remain in the rehearsal report.
