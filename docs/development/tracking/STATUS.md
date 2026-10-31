# Current development status

Updated **2026-10-31, Asia/Dhaka**. **PRs #2/#3/#4 are merged into main**, preserving original commits; [consolidation handoff](handoffs/khalid/day_03/MAIN.md). Retired Khalid branches are unnecessary. P01/P02/P03 are DONE; **P04 remains IN_PROGRESS**, awaiting actual SR algorithms and connected KR visual acceptance. Merging presentation does not close any remaining shared phase gate.

Current baseline: **fingerprint 10 / 246 tests**, [P06 consumer handoff](handoffs/khalid/day_03/P06.md) and [exact verification](../quality/reports/phase06/khalid/VERIFICATION.md). Main includes P04/P05/P06 presentation, applied limited melee, session controls/accessibility and current-build P07 review/P08 preparation. Human gameplay works; autonomous AI, full environment lifecycles, authoritative scores, policy/profile/history/preferences persistence and final delivery remain open. The original four-development-day target is not a demonstrated complete V1 delivery.

Historical detailed records: [P04](handoffs/khalid/day_02/phase04/P04.md), [P05](handoffs/khalid/day_03/P05.md), [melee](handoffs/khalid/day_03/MELEE.md), [P03 combined acceptance](../quality/reports/phase03/integration/VERIFICATION.md). They preserve exact original branches/commits/counts; current main supersedes their old checkout instructions and schema-9/7 source baselines.

## Completed and verified

| Area | Working result / boundary |
| --- | --- |
| P01 foundation | Locked Python/pygame-ce, grouped repository, pure fixed-tick Simulation, immutable contracts, resources/settings, CI and native packaging |
| P02 Human mission | Real movement/collision, tools, core theft/lockdown/extraction, fair interruptible capture, pause/retry and full Human scene flow |
| P03 defenders | Two real BFS/FSM/fuzzy Sentinels, A* Tracker with legitimate last-seen search/radio leads, sensing-only Core POST; provenance/expiry, witnessed versus unseen cover, geometry revisions and exact replay |
| P03 visuals | Distinct guard/capture/cue feedback; live selectable F3 sensors, actual last-plan metrics and original fuzzy inputs/memberships/activations; both decks/physical fixture and route review |
| Facility / movement | Five zones, two decks, 14 rooms, 101 furnishings, exact fixture bodies, reciprocal stairs, three real under-desk clearances; walk/run/crouch and 3 s sprint / 4 s recharge |
| Presentation | Cinematic loading/title/entry/extraction, contextual props/material/lighting, quiet walk/loud sprint, event audio/siren, responsive full-display menus/HUD/settings, map and endings |
| P03 verification | **195 tests/full checks**, five exact route replays, 40 native captured states, both native Human route wins and capture, real no-sight fuzzy evaluation (0.95 urgency / ID 0), hiding and fullscreen tab selection |
| P04 presentation in main | Typed gateway/deployment/telemetry ports, actual-actor camera/robot stairs, F2 decision/NEXUS/Interceptor panels, policy/protocol/reset and review/retry UI; independently tested with clearly labeled fixtures. Default Companion deployment stays unavailable pending the real SR gateway |
| P05/P06 consumers in main | Approved two-charge melee/recovery, listener-permitted prop/tool effects, actual-data result/profile/history ports, same/new seed, working session remaps/captions/contrast; services not fabricated |
| Latest current-build checks | 246 tests/full checks, five schema-10 replays, native Human both-route wins/capture and UI review, optimized restart profiling; complete AI-enabled gates remain open |
| Builds / platforms | Clean runtime Mac app/fresh ZIP each pass 9/9 native Cocoa checks with audio; current Windows x64/macOS arm64 build+dummy-smoke and Linux headless CI pass. Physical Windows retest of the combined build remains NOT_RUN |
| Performance scope | Native source loop render/audio/present p95 8.76 ms excluding simulation; 12-restart traced audit bounded in this run (1.048 MiB retained Python growth). It includes presentation outliers; full performance acceptance remains P07 |

Current main uses **fingerprint 10** from the approved limited melee; schema-9 P03 reports are historical. Retrieve the [guard contract](../architecture/integration/defenders/GUARD_CONTRACT.md) for original evidence tiles and retained actual fuzzy traces. Preserve the [physical fixture/input/startup contract](handoffs/khalid/presentation/CINEMATIC_STARTUP.md); its schema-7 hashes are historical. Scoring is unchanged and still awaits P06 implementation.

## Remaining phase gates

| Phase | Status | Required remaining result |
| --- | --- | --- |
| P01 / P02 / P03 | DONE | Maintain regressions and recorded contracts |
| P04 | IN_PROGRESS, KR independent implementation ready | SR Companion FSM/utility/A*/MCTS, Interceptor minimax/alpha-beta, NEXUS/persistence/reset, real gateway wiring and combined actual-data KR visual acceptance |
| P05 | IN_PROGRESS, independent presentation ready; connected acceptance pending | Complete tool/capture edge cases, doors/glass/canisters/full locker/object hiding and scene/audio lifecycle integration |
| P06 | IN_PROGRESS, independent KR consumers ready | Editable saved policies/profiles, approved scores/encounters/history, seed/reset/retry, full settings/accessibility and connected scenes |
| P07 | IN_PROGRESS, current-build review only | Whole-game both-mode fairness/replay/scenario/performance/usability evidence and blocker fixes |
| P08 | IN_PROGRESS, independent delivery preparation only | Complete comparison/feature audit, final primary packages, physical platform QA, source/credits/demo and functional-draft handoff |

Suhita's next queue: **P04-SR1/SR2/SR3** on `work/suhita-p04`; create it from current `origin/main`, or merge main into preserved existing work. All presentation ports/screens are already in main; do not fetch retired Khalid branches. Khalid's next P04 action is actual-data visual acceptance once her backend is published; his independent implementation is handed off and shared-file implementation claims are released for her narrow connection. The later 2026-10-25 user override authorized Khalid's independent P05 presentation only; that [handoff](handoffs/khalid/day_03/P05.md) is now ready. Suhita still finishes P04 before P05 lifecycle work. After P03, estimated remaining work was 43 Khalid / 48 Suhita points; hours are not measured. [Owner-aware startup](../workflow/START_HERE.md), [Windows guide and prompt](../workflow/setup/WINDOWS_SUHITA.md).

Advanced scene designs are not proof that their missing behavior works. Required R01-R27 functionality remains in [scope](../planning/V1_SCOPE.md). Public release stays free downloadable itch.io for Windows x64/macOS Apple Silicon; Linux is optional after its own testing, browser/Steam are future work. Full license/primary clean-machine/gameplay/demo gates remain separate from P03 and CI.

Earlier dated [handoffs](HANDOFFS.md), [changelog](CHANGELOG.md), [Suhita Windows report](../quality/reports/phase03/windows/VERIFICATION.md) and [PR review](../quality/reports/phase03/review/REVIEW.md) preserve their own original counts, scopes and pending status at the time. The combined P03 record supersedes their open KR1/KR2 integration dependency.
