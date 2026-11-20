# Final presentation runbook

Use the current desktop build and seed **1042**. The [rehearsal report](../../quality/reports/release_candidate/FINAL_REHEARSAL.md) records the build, exact outcomes and algorithm evidence. Use a fresh local data directory for the presentation so earlier settings, policies and learned protocols stay out of the rehearsal.

```sh
uv run --locked echo-heist --seed 1042 --data-dir .local/presentation-demo
```

The Mac app can also launch from the locally extracted presentation ZIP. For an isolated profile, run the following from the directory containing the extracted app.

```sh
"./Echo Heist.app/Contents/MacOS/EchoHeist" --seed 1042 --data-dir "$PWD/presentation-profile"
```

Keep `output/final-rehearsal/ECHO HEIST - Presentation Demo.mp4` available offline as a 1:50 backup. It contains edited footage from the production game. The same folder contains complete Human, Balanced and Rush recordings.

## Four-minute walkthrough

| Time | Show | Explain |
| --- | --- | --- |
| 0:00–0:25 | Title → Play Chapter → Tab facility map | One heist, two playable modes and two exit airlocks. The same simulation enforces movement, tools, detection, capture and extraction. |
| 0:25–1:05 | Human highlights. Reach Stair A, take the Core and return through Stair B to Cargo. | Sprint trades speed for noise. A guard investigates the sound tile. Holding E takes the Core and triggers lockdown. Extraction requires the Core. |
| 1:05–2:55 | Workshop → Balanced → Deploy with NEXUS memory off. F2 → 1 for Companion, 2 for NEXUS, 3 for Interceptor. | Start the run before explaining the algorithms. The tested mission completes in 94.2 seconds. Show a move, a plan and its outcome. |
| 2:55–3:35 | Review & Retry → Rush and deploy on the same seed. Use the recorded capture if time is tight. | At tick 1040, Wait received 27 visits and Advance received 26. A real grab then prompted a utility escape attempt. The Vault Sentinel finished the capture. |
| 3:35–4:15 | Results and experiment summary. D opens decision details. | The comparison ran 24 scenarios per policy. Show the denominator, wins and captures. Explain why the one live run and the 24-scenario result answer different questions. |

For a live Human attempt, select Human and Launch Mission, follow the Security staircase marked A, hold E at the Core, and use the Research staircase B to reach Cargo. The recorded win waited 1.5 seconds after insertion before starting the route. Use Q for an Echo decoy, F for EMP and Space for a close stun. Sprint timing, cover and tool use change patrol reactions. The offline recording preserves the demonstrated route if a live attempt goes differently.

## Algorithm talking points

- **Sentinel, F3.** Breadth-first search finds a route in grid steps. The finite-state machine moves between patrol, investigation, chase, search and return. Fuzzy rules combine graded cues into urgency. The panel shows actual rule weights and outputs.
- **Tracker, F3.** A* uses a goal-distance heuristic. When contact is lost, the Tracker searches the last legitimate position and nearby tiles until its evidence expires. Show the evidence timestamp and goal on the panel.
- **Companion, F2 → 1.** The mission state machine sets the objective. MCTS uses selection, expansion, rollout and backpropagation to compare tactical options. The game uses 64 simulations with a depth cap of four. Visits count sampled search effort. Mean reward is the model's estimate from those samples. Risk-weighted A* plans the tile route, and utility can interrupt the plan during immediate danger.
- **Interceptor, F2 → 3.** Depth-limited minimax weighs possible escape routes and selects a gate. Alpha-beta skips branches that cannot affect the choice. In the controlled example at guard tile `(59, 26)`, both searches chose the Research gate at value 0.255333. Plain minimax evaluated 23 leaves and alpha-beta evaluated 9. The guard still travels to its post.
- **NEXUS, F2 → 2.** Rules dispatch defenders using evidence and the lockdown signal. With memory enabled, a separate completed Rush run recorded three witnessed decoys and the Workshop offered **Verify Echo** for the next attempt. Reset clears the protocol. Keep memory off for the paired Balanced and Rush demo.

## Offline materials

Use the 1280 × 720 edited MP4 as a single playback file. For slides, use the matching screenshots under `output/final-rehearsal/` for the Human lockdown, Balanced route switch, Guard Monitor, Interceptor gate, and Rush capture. Show `ui/nexus-learned.png` if the instructor asks about persistence. The raw evidence files include `native-rehearsal.json`, `alpha-beta.json`, `nexus-memory.json` and `comparison/runs.csv`.
