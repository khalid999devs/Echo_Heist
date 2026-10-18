# Verification and quality gates

Status: P01 foundation and P02-K1/K2 have 45 implemented passing cases; [actual P02 verification](reports/phase02/khalid/VERIFICATION.md) distinguishes constructed mechanics/native traces from pending full-game gates. The scenarios below remain the complete-game acceptance plan.

Schedule: begin behavior checks on Day 1, exercise the full interface by Day 3, and run the integrated working-draft gate on Day 4. Public-release checks remain separate and evidence-based.

Eight-phase ownership: each owner verifies their meaningful behavior in P01-P06; Khalid leads P07 fairness/replay/performance integration, Suhita leads P07 scenarios/usability/persistence checks, and both verify P08 delivery. Follow [code rules](../workflow/CODE_RULES.md): all automated tests and test-only fixtures belong under grouped root `tests/`, with unit/integration/smoke separated by purpose and subsystem. Add files only for necessary behavioral coverage, not every module or cosmetic change.

## Blueprint acceptance scenarios

Retain the source IDs from PDF p. 18.

| ID | Scenario | Required assertion | Evidence type |
| --- | --- | --- | --- |
| T01 | Fresh profile selects Human or AI | Both start without an unlock, prior success or recording | UI/integration and native manual QA |
| T02 | Unobserved Companion reaches and takes core | One CORE_TAKEN, immediate lockdown, objective becomes extraction | Simulation integration |
| T03 | Glass breaks behind opaque wall within acoustic reach | Guard investigates sound source; no hidden intruder position or confirmed contact is created | Perception integration and fuzzy trace |
| T04 | Tracker loses LOS during chase | Pursues last-seen tile, searches plausible neighbors, expires stale memory; cannot track hidden movement | Integration and information-boundary test |
| T05 | EMP lands during capture wind-up before resolution | Disable/cancel grab, spend one charge, emit noise; no capture | Tick-boundary integration |
| T06 | Interceptor receives plausible route reports | Legal reachable post, physical travel, logged minimax and pruning nodes | Search test plus integration |
| T07 | Same seed/config with memory reset; then changed policy | Identical same-config replay; constructed policy-sensitive scenarios change real decisions | Determinism and paired-policy test |
| T08 | Exit crossed without core, then with core after theft | No premature win; mandatory lockdown; only real carrier extraction wins | Mission integration |

## Additional risk-based tests

| Area | Meaningful checks |
| --- | --- |
| Map/navigation | Five zones, branch/cross-link reachability, core/exit anchors, malformed objects, dynamic-door invalidation, no diagonal planner corner cutting |
| Movement | Normalized diagonal speed, sprint tunneling, continuous collision and four-neighbor AI following, interaction blocked by walls |
| Perception | Occlusion, cone boundaries, sound attenuation/reach, event age, report provenance, seen/unseen hide entry, cue vs identity separation |
| Controller isolation | No forbidden imports/world references; nested immutability; identical observation + RNG yields identical decision despite changed hidden world |
| BFS/A* | BFS shortest unit paths; A* optimality against a reference Dijkstra on small graphs with nonnegative costs; no-path and changed door cases |
| Fuzzy inference | Membership boundaries, overlapping rules, zero-activation fallback, bounded urgency; sound/decoy cannot fabricate visual identification |
| Minimax | Pruned/unpruned equal values on identical trees; legal tie handling; measurable pruning on a constructed tree; travel time influences choice |
| MCTS | Legal candidates, UCT selection, expansion, visit/reward backpropagation, deterministic budget/seed, belief-only rollouts, policy-sensitive preference and stale-action fallback |
| Tools/capture | Echo path ordering and no mission authority; EMP range/stock/no recharge; stun before grab resolves; melee reach, single target and immunity; capture/extraction tie |
| Objects/events | Glass breaks once; canister final impact noise; stable interaction ties; CORE_TAKEN atomicity; no duplicate alarms per overlap frame |
| NEXUS | Evidence-limited dispatch, sector coverage, at most one announced adaptation, full reset, alternate extraction path retained |
| Mission/results | Win/capture/abort distinct, terminal idempotence, approved 50/40/10 score and rank boundaries, shared detection encounters, no direct gadget/noise/lockdown penalties, pause freezes simulation time |
| Persistence | Settings/policy round trip, invalid enums/bounds/version, corrupt recovery, atomic update, future-version preservation, writable paths in frozen app |
| Replays | Action ticks + initial memory + map/config/policy versions required; identical local replay hashes; target-OS comparison before cross-platform claims |

Test invariants and externally visible behavior, not private method shapes or placeholder existence. Small fixtures make search/perception failures explainable; end-to-end scenarios ensure algorithms are actually used in the mission. Avoid requiring every preset to win every seed or asserting that different policies must diverge on every map.

Use the [approved scoring cases](../planning/SCORING.md) for exact examples. Assert that S/A/B/C are reachable, multiple guards/continuous sight/relayed reports count once per encounter, post-expiry rediscovery counts again, failed runs remain 0/F, and Human/Companion use identical score/reference settings. Test pace-reference metadata and matching result subtotals.

## Manual play and interface checks

Run both modes on the same complete map. Review input and remapping, camera, pause/resume/focus loss, restart/quit confirmation, keyboard navigation, all Workshop fields, same/new seed behavior, memory toggle, results and epilogue. Verify the algorithm guide describes actual implementation, and Lab View displays measured metrics rather than fixed samples.

Check 1366 x 768 and 1920 x 1080, window/fullscreen transitions, aspect/letterboxing and input coordinates. Verify text/icons without relying on color, readable critical subtitles, reduced flashing, separate music/SFX volume, mute and no-audio-device fallback. Gameplay-relevant audio must correspond to real NoiseEvents. Menus must remain usable when gameplay is paused.

Observe whether a new player understands the objective, tool stock, sighting vs capture, core lockdown and the return route. Record confusion, unfair blind-corner captures, path stalls, repeated waits and unintended softlocks. Static connectivity alone is insufficient.

## P08 / Day 4 complete working-draft gate

- Complete Chapter One mission with both first-launch modes, real required algorithms, tools, interactions, Workshop/profile/memory behavior and result/retry flow.
- T01-T08 and relevant regression checks pass; a real Companion win and fail and a Human complete mission are demonstrated.
- Approved scoring works with truthful breakdowns and all success grades reachable; no hidden-state or duplicate-encounter scoring shortcut is accepted.
- Simple coherent visuals/audio and all required controls/screens are usable. Cosmetic defects may be documented; no known crash, hang, save failure or gameplay blocker prevents completing/retrying the mission.
- Versioned source, locked setup instructions, short demonstration and Windows/macOS draft archives have recorded artifact/QA status. A missing required archive is explicitly incomplete delivery.
- Do not call a native test PASS without running it. A working local draft with pending platform QA remains a draft, and cannot be advertised as a tested public release.

## Public-release acceptance gate

- Required automated checks pass on the exact candidate; all T01-T08 have evidence.
- Both modes can genuinely win and fail. There is at least one documented cautious completion path and no known unavoidable mandatory encounter/lockdown softlock.
- Required algorithms execute in gameplay and produce inspectable decision evidence.
- Workshop changes affect decisions in controlled scenarios without changing game rules.
- There are zero known release-blocking crashes, save failures, illegal information leaks, hangs, mission breaks or inaccessible primary flows. Nonblocking issues are documented with impact.
- Named Windows x64 and macOS arm64 machines pass the release matrix on the exact downloaded archives; optional Linux has its own gate.
- Experiment results, asset provenance, screenshots, source instructions and video are ready. No unperformed check is recorded as PASS.

## QA report template

For each report under `quality/reports/`, record candidate version/commit/hash, OS/architecture/hardware, interpreter/build toolchain, mode/policy/seed/memory state, test IDs, steps, expected/actual result, evidence links, performance notes, defects/severity and tester/date. Use PASS, FAIL or NOT_RUN; a platform without evidence stays NOT_RUN.
