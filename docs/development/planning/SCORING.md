# Approved V1 scoring

Status: approved by the user in chat on 2026-10-18; implementation pending. This replaces the numerical scoring defaults on blueprint p. 18. The original PDF stays unchanged. Further changes to scoring weights, penalties, rank rules or scoring meaning must be proposed in chat and approved before adoption.

## Why change the original defaults

The blueprint awards 60 points just for extraction and sets B at 60. With nonnegative bonuses, every successful run is at least B, making C unreachable. Rewarding unspent tools can also discourage the intended emergency tactics. The approved replacement gives completion a strong floor, makes every success rank attainable and prioritizes stealth over speed.

## Score and ranks

For a successful extraction:

`score = 50 + max(0, 40 - 12 * detection_encounters) + pace_points`

| Component | Points | Rule |
| --- | --- | --- |
| Completion | 50 | Award only for actual carrier extraction, after terminal resolution |
| Stealth | 0-40 | Start at 40; subtract 12 per distinct confirmed detection encounter, floor 0 |
| Pace | 0-10 | Gentle capped time bonus based on active simulation duration; no mission deadline |

| Outcome / score | Grade |
| --- | --- |
| Successful extraction, 90-100 | S |
| Successful extraction, 75-89 | A |
| Successful extraction, 60-74 | B |
| Successful extraction, 50-59 | C |
| Capture or abort | F, final score 0 |

Use one integer scoring function for both modes. Gadget usage, normal movement noise, Echo use, EMP/melee use and mandatory lockdown have no direct point deduction. Show tool counts in results so players can compare tactics. A failed run can still show useful time/detection/tool statistics, but never an extraction bonus or successful grade.

## A distinct detection encounter

Begin an encounter when a guard actually confirms the real intruder and no detection encounter is active. Count that encounter once across the entire defender team. Other guards confirming the same pursuit, repeated sight ticks, radio relays, or a brief break/reacquisition of LOS do not create extra penalties.

Keep the encounter active while any legitimate confirmed-sighting memory/report is fresh, or a capture attempt from that pursuit is active. End it only after all such evidence expires and no corresponding grab remains. Use simulation ticks and original observation timestamps; relayed reports must not make stale evidence fresh. The sighting-memory TTL follows the versioned sensing configuration, initially approximately 5 seconds. Stun/EMP does not erase that evidence or reset the encounter.

Hearing, partial suspicion, seeing an Echo, inspecting an unwitnessed hide spot and the core alarm do not count as confirmed detection. A later genuine confirmation after the prior encounter has ended starts a new one. Persistent NEXUS adaptation history does not keep a live encounter open. Simulation owns this encounter state; renderers and controllers cannot change it.

## Pace calculation and calibration

Let `T` be completed-run simulation ticks and `T_ref > 0` the versioned reference duration in ticks:

`pace_points = (10 * T_ref) // max(T, T_ref)`

This awards 10 at or below the reference duration, 5 at twice it and progressively less for longer runs. It never subtracts points, ends the mission or grants more than 10. Exclude menus, pause and rendering delays by using simulation ticks. No-frame/device timing differences enter scoring.

Start with a clearly marked draft reference of 900 simulation seconds (15 minutes), within the source's 10-20 minute pacing target. During Day 4, compare successful Human and Balanced Companion runs and calibrate one shared per-map reference; do not give different policies/modes different scoring curves. Record the chosen reference and scoring version/hash with run metadata so comparisons remain valid. This calibration implements the approved pace concept; changes to weights, deductions or ranks still need prior chat approval.

## Examples and important properties

At the reference duration, pace is 10. At twice the reference, pace is 5:

| Detection encounters | At reference time | At twice reference time |
| --- | --- | --- |
| 0 | 100 / S | 95 / S |
| 1 | 88 / A | 83 / A |
| 2 | 76 / A | 71 / B |
| 3 | 64 / B | 59 / C |
| 4 or more | 60 / B | 55 / C |

All S/A/B/C grades are reachable. A clean win stays at least 90 even if pace reaches zero. One confirmed encounter caps the score at 88, so fast exposed movement cannot earn S. More time/encounters never increase the score. No amount of activity, gadgets or repeated event emission can farm bonus points.

Retain achievements as separate win-only labels: Ghost for no confirmed detection, AI Master for Companion victory, and Speedrunner at a separately playtested duration threshold. They do not add score or change the grade.

## Required verification

- Test grade boundaries at 59/60, 74/75 and 89/90 and clamp successful scores to 50-100.
- Verify the examples above, pace bounds, zero-duration safety, pause exclusion and exact integer arithmetic.
- Confirm multiple guards/continuous sight/report relays count once; true post-expiry rediscovery counts again.
- Confirm noise/suspicion/Echo/lockdown do not count, and EMP/stun cannot reset an active encounter.
- Confirm every rank is reachable through valid input metrics, failures remain 0/F, and neither mode has scoring advantages.
- Show completion/stealth/pace subtotals, encounter count and unpenalized tool counts in results; keep the score/grade explanations aligned with actual code.
