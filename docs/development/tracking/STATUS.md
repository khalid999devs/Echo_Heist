# Current development status

Updated **2026-10-24, Asia/Dhaka**. **P01, P02 and P03 are DONE. P04 is next and unstarted.** P05 has only the early crouch subset; P06-P08 remain open. The original four-development-day target is not a demonstrated full V1 delivery.

Current combined runtime **11cee9b** preserves Suhita's P03 logic and Khalid's KR1/KR2 visuals. [Combined acceptance](../quality/reports/phase03/integration/VERIFICATION.md), [runnable handoff](handoffs/khalid/day_02/phase03/P03.md), [exact evidence](../quality/reports/phase03/integration/EVIDENCE.json), [hosted source CI](https://github.com/khalid999devs/Echo_Heist/actions/runs/40113930755). Review-record/integration commits may follow without changing runtime. P03 closure and PR #1 integration are explicitly requested by Khalid; original teammate commits/authorship remain preserved.

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
| Builds / platforms | Clean runtime Mac app/fresh ZIP each pass 9/9 native Cocoa checks with audio; current Windows x64/macOS arm64 build+dummy-smoke and Linux headless CI pass. Physical Windows retest of the combined build remains NOT_RUN |
| Performance scope | Native source loop render/audio/present p95 8.76 ms excluding simulation; 12-restart traced audit bounded in this run (1.048 MiB retained Python growth). It includes presentation outliers; full performance acceptance remains P07 |

Current consumer schema is **fingerprint 9**. Retrieve the [guard contract](../architecture/integration/defenders/GUARD_CONTRACT.md) for original evidence tiles and retained actual fuzzy traces. Preserve the [physical fixture/input/startup contract](handoffs/khalid/presentation/CINEMATIC_STARTUP.md); its schema-7 hashes are historical. Scoring is unchanged and still awaits P06 implementation.

## Remaining phase gates

| Phase | Status | Required remaining result |
| --- | --- | --- |
| P01 / P02 / P03 | DONE | Maintain regressions and recorded contracts |
| P04 | TODO, prerequisite ready | Real Companion FSM/utility/A*/MCTS, Interceptor minimax/alpha-beta, NEXUS/protocol persistence/reset and actual deployment; corresponding KR1/KR2 visuals |
| P05 | IN_PROGRESS, early crouch subset only | Complete tool/capture edge cases, doors/glass/canisters/full locker/object hiding and scene/audio lifecycle integration |
| P06 | TODO | Editable saved policies/profiles, approved scores/encounters/history, seed/reset/retry, full settings/accessibility and connected scenes |
| P07 | TODO | Whole-game both-mode fairness/replay/scenario/performance/usability evidence and blocker fixes |
| P08 | TODO | Complete comparison/feature audit, final primary packages, physical platform QA, source/credits/demo and functional-draft handoff |

Suhita's next queue: **P04-SR1/SR2/SR3**, fresh `work/suhita-p04` from synchronized main. Khalid's next queue: **P04-KR1/KR2**, with agreed real controller/protocol display contracts. Neither queue is claimed by this completed P03 task. After P03, estimated remaining work is 43 Khalid / 48 Suhita points; hours are not measured. [Owner-aware startup](../workflow/START_HERE.md), [Windows guide and prompt](../workflow/setup/WINDOWS_SUHITA.md).

Advanced scene designs are not proof that their missing behavior works. Required R01-R27 functionality remains in [scope](../planning/V1_SCOPE.md). Public release stays free downloadable itch.io for Windows x64/macOS Apple Silicon; Linux is optional after its own testing, browser/Steam are future work. Full license/primary clean-machine/gameplay/demo gates remain separate from P03 and CI.

Earlier dated [handoffs](HANDOFFS.md), [changelog](CHANGELOG.md), [Suhita Windows report](../quality/reports/phase03/windows/VERIFICATION.md) and [PR review](../quality/reports/phase03/review/REVIEW.md) preserve their own original counts, scopes and pending status at the time. The combined P03 record supersedes their open KR1/KR2 integration dependency.
