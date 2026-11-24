# Companion planner and light easing (0.1.0a3)

Asked for by Khalid in chat on **2026-11-24**, after the project showcase. He saw the robot thief lose almost every run and asked that it win far more often through better decision making, with no scripted shortcuts. He asked for it to see about as much as a human sees on screen, for the game to stay natural and interesting, and for human play to become only a little easier. He allowed free tuning now that the showcase was over. Scoring is unchanged.

## What was wrong

Measured on 0.1.0a2 with `seed_sweep.py` and per-tick traces.

- The guards were fully deterministic. The mission seed only fed the Companion's MCTS dice, so a robot without dice would play every run of a personality the same way, and a human could learn the whole facility by heart.
- The robot saw a circle of 8 tiles in line of sight, while a human sees a whole screen of the current floor, guards behind walls included, with each guard's state label.
- Its decision layers fought each other. MCTS hold orders, utility overrides and a step gate each paused or redirected the same move, and none of them predicted where a guard would look a few seconds later.
- After the theft it kept walking towards a gate an Interceptor already held, retried a stair whose landing was taken, and walked back through the Core room on a stale route.

## What changed

| Change | Where |
| --- | --- |
| Guards keep their routes but get a rhythm per seed. Each one starts its round up to 3 s late and lingers 1 to 3 times the normal pause at every corner, drawn from the mission seed. One seed still replays exactly. | `core/simulation/engine.py`, `ai/guards/steering.py` |
| The thief sees its own floor about one screen around it, 7 tiles each way across and 4 up and down, through walls, like the human camera. Guards it sees carry the same state label a player reads (PATROL, CHECKING, PURSUIT and so on). | `security.json`, `core/simulation/systems/security.py`, `core/contracts/observations.py` |
| Foresight. The robot learns each guard's beat from its own sightings: where it pauses, which way it turns (a pausing guard already faces its way out), which junctions it walks straight through, its speed and pause lengths. It then predicts every remembered guard's possible poses for the next 7 seconds, early and late, with possible turns at junctions and walls it has not seen yet. A place it can see empty rules out a guard being there. | `ai/companion/spacetime/foresight.py` |
| Space-time A*. Each move is planned over tiles and fifths of a second against those predictions. The robot walks, waits, sprints when a gap is closing and nobody is close enough to hear, takes stairs, or slips into cover when every way is about to be watched. It lifts the Core only when nobody will look before the lift is done. | `ai/companion/spacetime/planner.py` |
| One decision loop. A grab is broken first, then MCTS chooses the route and gadget at real decision points, then the planner times every step. Waiting, hiding and retreating are no longer MCTS moves, so the F2 monitor shows MCTS weighing routes and decoys and the plan the robot is following. | `ai/companion/stealth/agent.py` |
| Route memory. Guards seen hunting or holding a post are routed around, a junction where the robot was spotted is avoided for 50 seconds, a stair whose landing was blocked is avoided for 10 seconds, and the exit is chosen by the cost of its route now. | `ai/companion/stealth/agent.py` |
| A chasing guard runs straight at a thief only when both of its shoulders clear the way. Before, a guard beside a desk corner could switch every tick between running and stepping back and freeze in place. | `ai/guards/steering.py` |
| Light easing for everyone. Identification takes 0.73 s instead of 0.6 s (0.27 s instead of 0.2 s right beside a guard), the view cone is 104 degrees instead of 112, the pursuit grace is 1.3 s instead of 1.0 s and guards gain 10% speed in lockdown instead of 20%. | `security.json`, `phase02.json` |

## Evidence

`uv run --locked python scripts/experiments/seed_sweep.py 1 101 --workers 6`, 300 Companion missions (Ghost, Balanced and Rush on seeds 1 to 100), five minutes of game time each, through the same Simulation, defenders, NEXUS, props and scoring as the game.

| | 0.1.0a2, seeds 1 to 400 | 0.1.0a3, seeds 1 to 100 |
| --- | --- | --- |
| Missions | 1,200 | 300 |
| Core thefts (Ghost, Balanced, Rush) | 168 (38, 37, 93), 14% | 132 (39, 44, 49), 44% |
| Wins (Ghost, Balanced, Rush) | 3 (0, 0, 3), 0.25% | 30 (8, 10, 12), 10% |
| Still free at five minutes | 0 | 67 (26, 22, 19) |

The game has no time limit, so a robot still free at five minutes has not lost. The winning seeds are Ghost 5, 30, 40, 62, 65, 82, 83 and 97, Balanced 5, 8, 12, 22, 30, 55, 56, 64, 65 and 83, and Rush 4, 19, 27, 45, 57, 58, 66, 70, 72, 77, 78 and 92, with ranks A and B.

During development the same planner was measured step by step on seeds 1 to 30 with the easing applied. Each fix below was kept only when it helped there.

- Prediction bugs found by tracing single runs. A turn learned at a corner was skipped when the guard had just stepped onto that corner, a guard that had just turned was predicted to turn again on the same tile, and line of sight was tested to tile centres only, so the robot was seen through a doorway at angles it judged blocked.
- Hiding was made consistent. The planner and the leave check had used different rules, so the robot entered and left cover every few ticks.
- After the theft the robot no longer follows a junction route chosen before the theft, and remembers gates, stairs and posts that turned out to be held.
- With the light easing the robot won 7 of 90 such runs at +20% lockdown speed and 11 of 90 at +10%.

`scripts/checks/run.py` passes with 373 tests, including new unit tests for the planner (waiting out a watched tile, running a closing gap, hiding when cornered, closed stairs, route costs) and for foresight (learning a turn, ignoring a junction a guard walked through, ruling out a place seen empty, a searching guard looking every way, routing around a posted guard). Pinned seeds changed with the new guard rhythm. Rush seed 19 is the pinned Companion win, and the scripted human routes now wait 180 ticks (route driver) or 300 frames (scene driver) at the start, inside the window in which they win.

## Known limits

- The robot wins about one mission in ten, far short of the six in ten that was asked for. Most losses come after the theft. The Research Tracker catches it near the Research stairs, the Vault Tracker catches it near the Core, and before the theft the Cargo Interceptor catches Ghost runs in the Service Wing.
- A guard that turns somewhere the robot never saw it turn can still surprise it. Prediction uses only the robot's own sightings.
- About one robot mission in five is still free after five minutes, waiting for a gap.
- The glitch probe from the presentation build, run on Ghost seeds 1 to 24, flags the robot stepping back and forth between two tiles above the Core room door in 7 missions (and turning on the spot in 11) while it waits for the Vault Tracker, and the Vault Tracker repeating a grab in 2. Two nearly equal plans alternate as the robot crosses the tile edge. A small price on stepping straight back removed every flag on Ghost seeds 1 to 15, but over seeds 1 to 100 the robots then froze in most runs and won 6 times instead of 30, so it was not shipped.
- The earlier Companion decision loop is still in `controller.py`, as the base class the new agent builds on.
- Hands-on human play of this build has not been recorded yet.
