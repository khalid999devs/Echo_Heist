# Core room balance (0.1.0a2)

Approved by Khalid in chat on **2026-11-23**. He found the Core room too hard to beat, asked for changes in game logic only, and asked that nothing on the submitted slides, clips or report become untrue. He approved a four-step plan ("go ahead finish fully") and asked for a new GitHub release. Scoring is unchanged.

Release **v0.1.0a1** stays the presentation build. The traced moment on the slides (tick 1014 of Rush seed 42) and the demo runs replay exactly on that tag, not on 0.1.0a2.

## What made the room hard

Measured on v0.1.0a1 with `seed_sweep.py` and per-tick guard traces.

- The Vault Tracker and the Core Interceptor both looped within one to three tiles of the Core, so the Core was in a guard's view about half the time and the Vault Tracker passed right beside the thief.
- Each Tracker followed every radio sighting report in the facility. Whenever any guard saw the thief, the Vault Tracker left the Core and hunted across both floors, as far as the Service Wing. It made 69 catches far from the Core area in the 1,200-mission sweep.
- After the alarm, searches lasted 30% longer than normal.

## Changes

| Change | Where |
| --- | --- |
| Vault Tracker loop moved one tile east, to columns 58 and 59 of rows 21 to 24. It stays beside the Core. | `maps/vault-five-zone.json` |
| Core Interceptor loop moved to the hall in front of the Research gate, rows 28 and 29. After the alarm it still picks a gate with minimax. | map and `scripts/level/author_facility.py` |
| A Tracker follows a radio report only when the reported tile is within 18 tiles of its own patrol, the same reach NEXUS uses for nearby help. It still chases whatever it sees itself, on either floor. | `ai/guards/tracker.py` |
| Tracker walking speed is 2.0 tiles per second instead of 2.4. The +20% lockdown, +25% chase and 3%-over-sprint rules are unchanged and still relative to it. | `gameplay/phase02.json` |
| After the alarm, searches keep their normal length. Patrol pauses are still halved. | `ai/guards/steering.py` |
| Companion patience. In the Core Chamber it waits on an unseen tile while its next step is in a visible guard's cone, or beside a guard it saw in the last second, for at most 2.5 seconds, then rests 2 seconds. It uses only its own view and memory. | `ai/companion/stealth/timing.py` |

With the new loops the tiles next to the Core are watched 17% to 41% of the time instead of 44% to 63%, with gaps of up to 4 seconds (two minutes of patrol, idle thief, game sight test).

## Published numbers that did not change

Sight range 8 tiles and 112 degrees, 0.6 s identification (0.2 s right next to a guard), 5 s memory, thief walk 2.4 and sprint 4 tiles per second for 3 s with 4 s rest, every noise radius, +20% lockdown speed, +25% chase speed, the one-second pursuit rule at 3% over sprint, the 0.4 s grab, the 0.8 s Core hold, all gadget charges and effects, the six guards and their roles, NEXUS job priorities and the scoring. The Interceptor still plans with 11 and 13 ticks per tile.

## Evidence

`uv run --locked python scripts/experiments/seed_sweep.py 1 401 --workers 10`, 1,200 Companion missions (Ghost, Balanced and Rush on seeds 1 to 400). The v0.1.0a1 numbers reproduce the recorded presentation sweep exactly.

| | v0.1.0a1 | 0.1.0a2 |
| --- | --- | --- |
| Core thefts (Ghost, Balanced, Rush) | 84 (1, 8, 75) | 168 (38, 37, 93) |
| Runs that reached the Core Chamber | 516 | 737 |
| Vault Tracker catches far from the Core area | 69 | 14 |
| Wins | 2 (Rush seeds 42 and 54, rank A) | 3 (Rush seeds 105, 164 and 301, 60 points, rank B) |
| Timeouts | 0 | 0 |

The glitch probe from the presentation build (`glitch_probe.py 1 181`, 540 missions) flags 3 missions: two where a cornered robot steps between two tiles beside a Core-room locker for a few seconds before it is caught, and one grab churn by the Vault Tracker. v0.1.0a1 had none on the old routes. A third jitter case found during tuning was fixed by the patience memory.

`scripts/checks/run.py` passes with 360 tests. Seed 164 replaces seed 42 as the pinned Rush win, the report test now checks that a far Tracker ignores the radio, and the scripted blind return is caught within reach of the predicted gate.

## Known limits

- The robot still rarely escapes after the theft. Most of its runs that steal the Core are caught by the Vault Tracker or the Research Tracker within seconds, often after walking towards the gate an Interceptor already holds. Better escape planning is the next step for the Companion.
- The cornered-robot wobble above, in about 0.4% of robot missions.
- Hands-on human play of this build has not been recorded yet.
