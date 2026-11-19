# Current development status

2026-11-16 Suhita update: `work/suhita-p06-p08` is merged with main 34d68cf (`59ed6ff`) and pushed for review; 328 tests pass on the Linux shell, 327/328 natively on Windows (bootstrap smoke times out on that laptop's slow startup for every commit). [Handoff](handoffs/suhita/day_04/P06_P08.md), [Windows QA](../quality/reports/phase08/suhita/WINDOWS_QA.md).

2026-11-10 visual follow-up: [robot/light/wiring handoff](handoffs/khalid/day_04/ROBOT_LIGHTING.md) records four-direction sixteen-pose robot walk/fast gaits, source-directed room shadows and connected wall/machine services. Current fingerprint stays 12; this is a presentation refinement, not closure of pending scoring/persistence/platform gates.


Updated **2026-11-10, Asia/Dhaka**. PRs #2–#6 are merged into **main**, preserving original commits. Latest runtime merge **bf3db94** equals the reviewed P05 tree. Read the [merged runtime handoff](../quality/reports/phase05/review/INTEGRATION.md), [P04 review](../quality/reports/phase04/review/REVIEW.md) and [P05 review](../quality/reports/phase05/review/REVIEW.md). Older branch/count/schema statements in dated reports are historical.

Current baseline: **fingerprint 12 / 301 tests**. Structure/Ruff/format/strict mypy pass. Reviewed heads and merged runtime pass Linux headless and Windows x64/macOS arm64 build/frozen smoke CI. Actual Mac production UI/audio review passes. Hosted artifact storage is full; a successful validation job does not prove an archive was uploaded. Physical Windows full-game review and final delivery remain separate.

## Implemented

| Area | Working result |
| --- | --- |
| P01/P02 | Locked foundation, pure fixed-tick Simulation/contracts, desktop packaging; actual Human tools, Core theft/lockdown/extraction, capture, pause/retry |
| P03 | Real BFS/FSM/fuzzy Sentinels and A* Tracker; fair evidence, radio/expiry, hiding/capture, geometry and deterministic replay |
| Facility/presentation | Five zones/two decks, 14 rooms, furnished art/lighting/materials, exact bodies, reciprocal stairs, under-desk crouch; cinematic loading/title/entry/extraction, full-display UI/input/audio |
| Movement/tools | Walk/run/crouch, 3 s sprint/4 s recharge with real louder noise; approved two-charge melee/four-second recovery and shared both-mode tool/capture edge rules |
| P04 runtime | Real Companion FSM/utility/observed-risk A*/64-iteration belief-only MCTS; physical Interceptor depth-3 minimax/alpha-beta; evidence-limited NEXUS, versioned protocol persistence/reset and production gateway |
| P04 connected UI | Real decision/Interceptor/NEXUS tabs, first deployment, actual autonomous win/capture, pause, evidence-backed protocol and confirmed reset; chosen action remains visible |
| P05 lifecycle | Three doors, two glass panes, three canisters, five lockers; committed geometry/once-only acoustic cues, witnessed/unseen hiding and fresh-press E. Real Human canister/locker native review |
| P06 presentation | Result/profile/history ports, same/new seed and session remap/caption/contrast UI. Authoritative backing services still pending; no fabricated scores/history |

Native prop-enabled Companion seed 1042 **WIN at 2463**; seed 4 **CAPTURED at 1180**. Four-seed deterministic P05 report matches Suhita's hash; Balanced wins 4/4 in each prop comparison, Rush/Ghost weaker. One Ghost test reaches the runner cap; it is not a gameplay timeout. Current whole-game performance is not accepted merely because earlier presentation-only profiling passed.

## Remaining gates / next work

| Phase | Status | Remaining result |
| --- | --- | --- |
| P01/P02/P03 | DONE | Preserve accepted behavior/contracts |
| P04 | Runtime and real-data review merged; combined sign-off retained IN_PROGRESS | Integration lead reconciles full gate with recorded actual algorithm/protocol/visual evidence; no missing runtime implementation claim |
| P05 | SR runtime merged; Khalid Mac connected acceptance verified | Current-build physical Windows gameplay/audio and combined sign-off |
| P06 | IN_PROGRESS: KR consumers ready; SR1/SR2/SR3 scoring, encounters, reports/history/profiles/preferences and production `ExperienceGateway` on `work/suhita-p06-p08` (merged with main 34d68cf) | Khalid's connected acceptance of real scores/profiles/history/preferences against the existing screens, then the combined gate |
| P07 | IN_PROGRESS: Khalid current-build review; SR1/SR2 24-scenario registry/harness, guard corridor-deadlock fix and guide accuracy on `work/suhita-p06-p08` | Both-mode fairness/replay/scenarios, Ghost/Rush balance, whole-game performance/memory/usability |
| P08 | IN_PROGRESS: Khalid delivery preparation; SR2 96-run comparison done ([report](../quality/experiments/POLICY_COMPARISON.md)); SR1 Windows QA partial: native checks, build/smoke and 8 of 15 in-game steps pass; Human-play steps remain ([checklist](../quality/reports/phase08/suhita/WINDOWS_QA.md)) | Final primary packages, clean-machine/platform QA, complete comparison/feature audit, licensing/credits/media/demo and delivery |

Khalid's [connected Mac handoff](handoffs/khalid/day_04/CONNECTED_REVIEW.md) records 22 actual interaction views, 21 current UI views and both-mode/full-Companion profiling; guide descriptions now match the actual algorithms. P06 real services are supplied by Suhita's [P06-P08 handoff](handoffs/suhita/day_04/P06_P08.md) ([verification](../quality/reports/phase06/suhita/VERIFICATION.md)), pending PR review.

Suhita's P04-SR1/SR2/SR3 and P05-SR1/SR2 code is merged. Preserve it and finish outstanding gate evidence before a separately assigned P06 slice. Khalid's remaining connected review is scoped above. All PR-review editing claims are released; inspect [claims](HANDOFFS.md) before new work. [Owner-aware startup](../workflow/START_HERE.md), [Windows guide](../workflow/setup/WINDOWS_SUHITA.md), [workload](../planning/WORKLOAD.md).

The four-development-day target is not a demonstrated finished V1. Required [scope](../planning/V1_SCOPE.md) is retained. Release remains free desktop itch.io, Windows x64/macOS Apple Silicon primary; Linux optional after testing, browser/Steam future. No approved scoring/melee change was made in this review.
