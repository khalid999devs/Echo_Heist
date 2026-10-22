# Current development status

Updated **2026-10-22, Asia/Dhaka**. **P01 and P02 are DONE. P03 is IN_PROGRESS and is the next implementation priority.** P05 has an explicitly requested early crouch subset; P04/P06/P07/P08 are not complete. Advanced-looking screens and successful desktop builds do not close these missing behavior gates.

The latest integrated baseline is `ec8ca48` on main; runtime code is `600698a`, clean packaged source `c2213c2`. The current ownership revision is documentation only. Main's [three CI jobs passed](https://github.com/khalid999devs/Echo_Heist/actions/runs/39746051343). Retrieve the [consumer handoff](handoffs/khalid/presentation/CINEMATIC_STARTUP.md), [review](../quality/reports/cinematic_startup/REVIEW.md) and [exact build evidence](../quality/reports/cinematic_startup/verification/BUILD.json).

## Completed and verified

| Area | Working now | Evidence / boundary |
| --- | --- | --- |
| Foundation / P01 | Grouped repository, locked Python/pygame-ce, pure fixed-tick Simulation, immutable contracts, resources/settings, CI and PyInstaller pipeline | [P01 handoff](handoffs/khalid/day_01/P01.md); original Khalid-only work |
| Human heist / P02 | Movement/collision, core theft, mandatory lockdown, original extraction, fair interruptible capture, pause/retry and basic Echo/EMP/melee | [Combined P02](handoffs/khalid/day_01/P02_INTEGRATION.md); Suhita's map/loader contribution and Khalid's core/refinement preserved |
| Facility | Five zones, two decks, 14 rooms, two branch routes/cross-link/stairs, 101 furnishings, accurate fixture bodies and three under-desk clearances | Current fingerprint 7; conservative route tiles differ from physical obstacle bounds |
| Character / movement | Close camera, walk/run/crouch animation, grounded shadow, C crouch/creep, timed 3-second sprint / 4-second recharge, quiet walking / louder sprint | Existing implementation reused; no separate sitting action |
| First P03 subset | One live Sentinel with filtered sight/hearing, BFS/FSM/fuzzy, legitimate reports, chase/search/return and capture integration | Other three guard posts retain P02 contact behavior; no complete Tracker/Interceptor/NEXUS yet |
| Presentation | Cinematic loading/title, desktop icon, entry/extraction pressure doors, responsive menus/HUD/settings, map, timed stairs, distinct win/capture/abort endings | Airlock animation does not implement P05 physical doors |
| Scene detail / audio | Material/lighting variety, contextual laboratory props/aftermath, reduced flashing, event SFX, ambient/context music, nonblocking fades and single hover cues | 29 recordings with provenance; actual simulation events drive gameplay feedback |
| Later scene designs | Workshop, Companion, Guide/Lab and epilogue designs/navigation | Existing previews must be connected to real logic before their phase gates pass |
| Verification | 149 tests/full checks; 56 scene states, both default-security route wins/capture, 780 motion frames, startup variants | [Actual review](../quality/reports/cinematic_startup/REVIEW.md); no new runtime tests implied by this doc revision |
| Performance | Native measured p95 16.889 ms, 3,000 measured frames, no sustained growth in 12-restart audit | Scoped to this baseline/hardware, not proof for future full AI or every machine |
| Builds | Matching Mac arm64 / Windows x64 archives; Mac app and fresh ZIP each pass nine native Cocoa checks with audio | Windows native CI build + frozen dummy-video smoke pass; **physical Windows gameplay/audio NOT_RUN** |

## Phase checkpoints and remaining work

| Phase | Status | Remaining gate | Revised integration lead |
| --- | --- | --- | --- |
| P01 — Foundation | DONE | None | Khalid, complete |
| P02 — Human heist | DONE | None; maintain regressions as later systems integrate | Complete combined review |
| P03 — Perception/defenders | IN_PROGRESS | Tracker A*, full registry/geometry revisions, remaining fair sensing/hiding/capture integration, real guard diagnostics and replay evidence | Suhita; Khalid visual acceptance |
| P04 — Autonomous strategy | TODO | Companion FSM/utility/A*/real MCTS, Interceptor/minimax/alpha-beta, NEXUS dispatch/protocol persistence/reset and first-launch AI mode | Suhita; Khalid visual acceptance |
| P05 — Tools/environment | IN_PROGRESS, early subset only | Finish shared Echo/EMP/melee edge cases; functional doors/glass/canisters/locker hiding and their scene/audio integration | Suhita; Khalid visual acceptance |
| P06 — Workshop/full flow | TODO | Editable saved policies/profiles, seed/reset/retry semantics, approved scoring/encounters, history, full settings/accessibility and all screens connected | Khalid; Suhita behavior acceptance |
| P07 — Integrated evidence | TODO | Complete both-mode QA, fairness/replay/performance/accessibility, experiment harness and blocker fixes | Khalid + Suhita |
| P08 — Functional draft delivery | TODO | Full comparison, final feature audit, candidate primary packages, physical platform QA, source/credits/demo handoff | Khalid + Suhita |

Required functionality remains R01-R27 in [scope](../planning/V1_SCOPE.md); no missing mechanic is relabeled as future polish. Approved 50/40/10 scoring is **specified but not implemented**. Current results are unscored. Public itch.io downloads, gameplay video/academic submission, license decisions and wider platform validation remain separate release work. Linux has source CI only; no tested Linux desktop release. Browser/Steam are outside V1.

## Current ownership and next action

The owner changed the split on 2026-10-22. **Khalid owns complex graphics/scenes/presentation and desktop delivery; Suhita owns most gameplay/AI/persistence logic.** See [Workload](../planning/WORKLOAD.md), including revised KR/SR IDs, file seams, historical-credit preservation and 48/60 remaining estimates. The old whole-project 80/80 estimate is not a measured effort record.

- **Suhita next:** P03-SR1/SR2/SR3 on `work/suhita-p03`; finish the P03 logic from current main, verify on Windows and hand off real APIs/events. [Owner guide](../workflow/owners/SUHITA.md), [Windows commands and pasteable prompt](../workflow/setup/WINDOWS_SUHITA.md).
- **Khalid next:** P03-KR1/KR2; guard cues, genuine diagnostics and scene/geometry integration. [Owner guide](../workflow/owners/KHALID.md).
- No new runtime slice is claimed by this planning update. Check [claims/handoffs](HANDOFFS.md) before editing. P03 closes only after both queues and the combined gate pass; P04 then becomes ready.

The original four-development-day / eight-phase target remains, with actual progress reported honestly: implementation began 2026-10-18 and P03 is still open on 2026-10-22 after requested visual refinements. Day labels are the original sequence, not proof the target was met or a fresh four-day promise. Available hours/deadline, physical Windows QA, broader Mac/download testing and source licensing remain open inputs in [Risks](RISKS_AND_DECISIONS.md).

## Historical evidence

Earlier verified refinements remain in [Changelog](CHANGELOG.md), [handoff index](HANDOFFS.md), [scene presentation](handoffs/khalid/day_02/SCENE_PRESENTATION.md), [closer camera](handoffs/khalid/day_02/CLOSE_CAMERA.md), [responsive facility](handoffs/khalid/presentation/SCENE_FINISH.md), and [materials/crouch](handoffs/khalid/presentation/MATERIALS_AND_CROUCH.md). They document their own older test counts, coordinates, hashes and scopes. The latest cinematic/fixture handoff supersedes their fingerprint/geometry consumer baseline; it does not erase their contributions.
