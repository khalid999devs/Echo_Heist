# Feature backlog and owner-slice mapping

Status vocabulary: TODO / IN_PROGRESS / BLOCKED / DONE. All implementation remains TODO. P01-P08 replace the retired M0-M5 labels. See the [phase index](../planning/phases/README.md) for detailed owner assignments and the [workload table](../planning/WORKLOAD.md) for 80/80 estimated effort.

EH IDs are stable feature anchors, not exclusive single-person tasks. Named Pxx-Kx/Pxx-Sx slices own implementation. Where several slices contribute, the EH item becomes DONE only after all required contributions and feature acceptance pass. Phase completion is recorded separately in [Status](STATUS.md).

## Four-day execution map

| Day | Phases | Gate |
| --- | --- | --- |
| 1 | P01, P02 | Khalid-owned runnable foundation; integrated Human mission and scene |
| 2 | P03, P04 | Fair active defenders and autonomous Companion with actual required algorithms |
| 3 | P05, P06 | Complete tools/environment, Workshop, approved scoring, settings/full scene flow |
| 4 | P07, P08 | Fully integrated functional draft, evidence, primary desktop archives and handoff |

## Features

| ID | Phase | Responsible slices | Work item | Depends on | Scope | Required acceptance | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EH-000 | Planning | Planning baseline | Authoritative source, plan, workload and instructions | None | R01-R27 | Indexed documents and validation | DONE |
| EH-001 | P01 | P01-K1 | Interpreter/dependency/native runner baseline | EH-000 | R24-R25 | Resolved version/architecture and runner-access record | TODO |
| EH-002 | P01 | P01-K1 | Git, grouped package, lock, README, source-license status | EH-001 | R24, R26 | Clean locked install, entry point and six-file root budget | TODO |
| EH-003 | P01 | P01-K2 | Typed contracts, headless fixed tick, RNG and fixture | EH-002 | R20-R21 | Repeatable fixture and immutable observation boundary | TODO |
| EH-004 | P01 | P01-K3 | Desktop/resource/settings/bootstrap and input shell | EH-002 | R19, R21, R24 | Launch/save/recovery/audio checks outside project cwd | TODO |
| EH-005 | P01 | P01-K1, P01-K3 | Structure/lint/test checks, CI and available native smoke build | EH-003, EH-004 | R24-R25 | Actual checks/artifact evidence, other target status explicit | TODO |
| EH-006 | P02 | P02-S1, P02-S2 | Five-zone scene/map, Tiled importer and connectivity validation | EH-003, EH-004 | R03, R09 | Branches/cross-link/anchors and malformed-map diagnostics | TODO |
| EH-007 | P02 | P02-K1, P02-K2 | Human movement/collision/sprint/actions and interaction prompt | EH-006 | R04, R09, R20 | Speed/collision/legality tests and real input response | TODO |
| EH-008 | P02 | P02-K1, P02-S1 | Core ownership/theft, mandatory lockdown, extraction/result terminals | EH-007 | R01, R22 | T02/T08 mission rules, once-only events and visible objective/result | TODO |
| EH-011 | P02-P03 | P02-K1, P03-K1, P03-S2 | Fair capture/interrupt logic and telegraph | EH-008 | R04 | Human capture path, cancel/reach timing and active-guard integration | TODO |
| EH-019 | P02-P05 | P02-K1, P05-K1, P05-K2, P05-S2 | Initial legal tools, complete Echo/EMP/melee rules and feedback | EH-011 | R06-R08 | Real early tool legality; T05, stock/range/immunity/noise and effects complete by P05 | TODO |
| EH-012 | P02-P06 | P02-S1, P02-K2, P06-S2, P06-S3 | Menu/modes/HUD/pause/results and complete navigation | EH-008, EH-011 | R02, R17-R19 | Basic Human flow in P02, complete both-mode UI by P06 | TODO |
| EH-009 | P03 | P03-K1, P03-S1, P03-S2, P03-S3 | Fair sight/hearing/reports/hiding/expiry and cue data | EH-006, EH-007 | R05, R09 | Occlusion/acoustics/provenance and visible cue alignment | TODO |
| EH-010 | P03 | P03-K2, P03-S1, P03-S2 | Sentinel BFS/FSM and data-driven patrol | EH-009 | R10 | Shortest patrol, heard-only investigation, recoverable chase | TODO |
| EH-013 | P03-P07 | P03-K2, P07-K1, P07-S1 | Replay headers/events and fixed-seed experiment harness | EH-003, EH-009 | R20-R21, R23 | Replay reproducibility first, executable comparison harness by P07 | TODO |
| EH-014 | P03 | P03-K2, P03-S1 | Tracker A*, last-seen memory and dynamic geometry invalidation | EH-009, EH-010 | R11 | T04, optimal small-fixture paths and expiry/cache behavior | TODO |
| EH-021 | P03 | P03-K2, P03-K3, P03-S3 | Fuzzy suspicion and real rule/urgency diagnostics | EH-010 | R10 | Bounded inference, no false identity confirmation and actual gameplay trace | TODO |
| EH-015 | P04 | P04-K1, P04-S3 | Companion FSM/utility/observed-risk A* and visible AI mode | EH-008, EH-009, EH-014 | R02, R15 | Autonomous representative win/fail without a recording | TODO |
| EH-016 | P04 | P04-K2, P04-K3 | Interceptor minimax/alpha-beta, travel and metrics | EH-006, EH-009, EH-014 | R12 | T06, pruned/unpruned values and legal physical movement | TODO |
| EH-017 | P04 | P04-S1, P04-S3 | NEXUS evidence-based dispatch/coverage and alerts | EH-010, EH-014, EH-016 | R13 | Evidence-limited tasking and mandatory lockdown coordination | TODO |
| EH-018 | P04-P06 | P04-S2, P04-S3, P06-S1, P06-S2 | Protocol persistence, announcement and full reset/deployment wiring | EH-017 | R14, R21 | One justified announced protocol; reset reproduces baseline | TODO |
| EH-022 | P04 | P04-K1, P04-K3 | Bounded belief-only MCTS and real alternative metrics | EH-015, EH-016 | R15 | Four stages/legality/determinism; early tool-action subset from P02 available | TODO |
| EH-020 | P05 | P05-S1, P05-S2, P05-S3 | Stateful glass/canister/doors/hiding and audio-event coupling | EH-007, EH-009 | R09, R27 | Once-only interactions, geometry/cache revisions and actual cue mapping | TODO |
| EH-023 | P06 | P06-S1, P06-S2 | Validated Workshop/presets/profiles/seed/reset deployment | EH-004, EH-015, EH-022 | R16, R21 | Save/recovery, legal settings and meaningful policy-sensitive choices | TODO |
| EH-033 | P06 | P06-K1, P06-K2 | Approved scoring/encounters/pace and result breakdown | EH-008, EH-009 | R22 | Approved examples/boundaries, one chase counted once, every rank reachable | TODO |
| EH-024 | P06-P07 | P04-K3, P06-S2, P06-K2, P07-K2, P07-K3 | Live ticker/Lab View/guide/results explanations | EH-012, EH-016, EH-021, EH-023, EH-033 | R17-R18, R22 | Real metrics and complete flow by P06; accuracy/usability audited P07 | TODO |
| EH-025 | P05-P07 | P05-S2, P05-S3, P06-S2, P06-S3, P07-S2, P07-S3 | Minimum art/audio/narrative/ending and accessibility/settings | EH-020, EH-023 | R19, R27 | All baseline functions connected P06 and verified P07; provenance recorded | TODO |
| EH-026 | P07 | P07-K1, P07-K2, P07-K3, P07-S1, P07-S2, P07-S3 | T01-T08, fairness/determinism/softlock and UX integration | EH-018, EH-019, EH-024, EH-025 | R01-R23 | Combined candidate has no known blocking gameplay/fairness/save defect | TODO |
| EH-027 | P07-P08 | P07-K1, P07-S1, P08-S2 | 24-scenario/four-policy comparison, pruning, performance/balance | EH-026 | R23 | Full denominator, repeatable metadata, failure analysis and measured metrics | TODO |
| EH-028 | P08 | P08-K1, P08-S1 | Primary native draft archives/manifests and gameplay QA | EH-005, EH-026 | R24-R25 | Both archive hashes and separate actual native-test status | TODO |
| EH-030 | P08 | P08-K2, P08-S2, P08-S3 | Complete functional/source handoff, comparison, credits and demo materials | EH-025, EH-027, EH-028 | R26 | Exact candidate instructions, evidence, demonstration and open release checks | TODO |
| EH-029 | Outside P01-P08 | Optional owner assigned later | Optional Linux native archive and distro validation | EH-028 | R25 | Independent clean-machine report, or explicit omission | TODO |
| EH-031 | After full release gate | Khalid + Suhita, actual publishing context required | Public source/downloads, public-link verification and academic submission | EH-028, EH-030 | R25-R26 | Full release matrix/licenses, live free downloads/source/video and submission evidence | TODO |
| EH-032 | After complete draft/release | Owner assigned to actual issue | Measured accuracy/balance/polish and validated patches | EH-030 | R24-R26 | Reproduced issue, proportionate checks and versioned fix | TODO |

## Dependency interpretation and completion

Phase gates and slice dependencies are authoritative for incremental work. A feature spanning phases stays IN_PROGRESS while its later slices remain; consumers can use an explicitly handed-off verified subset (for example P02 tool legality) without falsely closing the whole feature. This avoids a cycle where P04 MCTS waits for P05 effects or P07 waits for its own audited guide.

EH-029 is optional. EH-031 is public distribution/submission, not a ninth functional phase; it may run on Day 4 if release checks pass. EH-032 improves a complete draft and cannot absorb missing required features. Record slice claims and actual evidence in [Handoffs](HANDOFFS.md) and phase gates in [Status](STATUS.md). No passing CI/build/native QA result is implied by this plan.
