# Current development status

Updated: 2026-10-21, Asia/Dhaka.

Active target: complete working initial draft in **eight phases over four development days**. Day 1 implementation started on 2026-10-18. Owners: Khalid and Suhita; estimated allocation 80 points each. P01 and the complete Human P02 gate are DONE after user-directed integration review of Suhita's branch. A first P03 Sentinel/perception subset is now implemented; shared P03 and P04-P08 remain open.

## Eight-phase checkpoints

| Day / phase | Target | Integrator | Actual status |
| --- | --- | --- | --- |
| 1 / P01 | Environment/filesystem/contracts/runnable shell; Khalid-only | Khalid | DONE |
| 1 / P02 | Five-zone scene, complete Human loop and basic tools | Suhita planned; Khalid completed integration review | DONE; both owner slices accepted on actual map with Human win/capture/pause/retry evidence |
| 2 / P03 | Fair sensors, active defenders, BFS/A*/fuzzy and replay | Khalid | IN_PROGRESS; one Sentinel/perception subset, Tracker/shared registry gate open |
| 2 / P04 | Autonomous Companion/MCTS, Interceptor/minimax and NEXUS | Khalid | TODO |
| 3 / P05 | Complete tools/props and scene/audio feedback | Suhita | TODO |
| 3 / P06 | Workshop/profiles, scoring, settings/full UI and ending | Suhita | TODO |
| 4 / P07 | Full integration/fairness/evidence and usability | Khalid | TODO |
| 4 / P08 | Complete functional audit, primary archives and runnable draft handoff | Khalid | TODO |

## Actual state

| Area | Status | Evidence |
| --- | --- | --- |
| Source review | DONE | All 19 PDF pages extracted/read; p. 19 visually checked; PDF hash in development hub |
| Development plan and document groups | DONE | Indexed documents in [development hub](../README.md) |
| Architecture and setup specification | DONE | [Codebase](../architecture/CODEBASE.md), [contracts](../architecture/DATA_CONTRACTS.md), [setup](../workflow/INITIAL_SETUP.md) |
| Revised schedule and scoring design | DONE | Four-day plan and [50/40/10 scoring](../planning/SCORING.md), explicitly approved in chat |
| Eight-phase ownership, agent startup and code rules | DONE | Named queues and executable structure checker enforce the authored-file/directory/test-layout baseline |
| Local Git/source package/dependencies | DONE | main with incremental commits; installed 0.1.0a1 package, Python 3.13.16 and real uv.lock |
| GitHub source and teammate bootstrap | DONE | [Public repository](https://github.com/khalid999devs/Echo_Heist), main pushed with original history; fresh clone verified through 99a8658; [Windows handoff](../workflow/setup/WINDOWS_SUHITA.md) prepared |
| P01 contracts/runtime/resources/settings | DONE | [Runnable handoff](handoffs/khalid/day_01/P01.md); pure headless diagnostic and actual desktop shell |
| P02 core gameplay/input | DONE | Continuous physics, mission/capture/initial tools, Human input and objective presenter; [owner handoff](handoffs/khalid/day_01/P02.md) |
| P02 five-zone map/scene | DONE | Suhita's `a98548a` map/loader/flow retained; illustrated floor/bulkhead/props/actor strips and refined sci-fi UI; [integration verification](../quality/reports/phase02/integration/VERIFICATION.md) |
| AI / Workshop / final scoring | IN_PROGRESS | One real Sentinel uses filtered sensors, BFS/FSM/fuzzy/search/report expiry; remaining advanced defenders, autonomous Companion, Workshop and final scoring are pending |
| Local automated checks | DONE | Structure/lint/format/strict types and **111** focused cases pass on the two-floor lab revision; [current review](../quality/reports/two_floor_lab/REVIEW.md) |
| Hosted CI | PASS for two-floor revision | [39610664321](https://github.com/khalid999devs/Echo_Heist/actions/runs/39610664321) at `8d551d8`: all Linux/Windows/macOS checks, native primary builds and frozen dummy-video smoke |
| Native packaging | PASS for local macOS furnished slice | Clean `123225b` app and fresh ZIP extraction each pass all eight Cocoa frozen checks with audio ready; [exact archive/hash](../quality/reports/two_floor_lab/BUILD.json) |
| V1 platform/hardware QA | NOT_RUN | Suhita's interactive Windows desktop/download QA, wider macOS/download behavior and full-game release matrix remain untested |
| Assets and licensing | IN_PROGRESS | Original generated scene/tile/prop/actor art plus Oxanium/OFL recorded in [asset register](../assets/ASSETS.md); remaining production set and source license pending |
| itch.io/video/submission | TODO | GitHub source is published; game distribution, gameplay video and academic submission are still pending |

P02 is a playable Human draft, not the full V1 game. The standard app launches the actual five-zone scene; P03-P08 and public-release gates remain separate. Outcomes are unscored until P06. One Sentinel now patrols/senses/chases/searches; three other posts retain P02 contact behavior. The current compact atlas has two floors, 14 purposeful rooms and 63 physical furnishings. Entry/Service are downstairs, Security/Research/Core upstairs; two reciprocal stair pairs and the original branch/cross-link routes remain open. Shift uses the owner-approved three-second louder sprint/four-second recharge; walking stays at 2.5 tiles/s and sprint at 3.7. Tab pauses on both floor plans. A Chapter 01 card, clear briefing/mode/Launch separation and Audio/Display groups replace the crowded opening. Compact HUD, CC0 context audio and persisted mix settings remain connected. Clinical lighting, soft contact shadows, native alpha-correct compositing and a distinct original extraction ending are connected. The 3D-style title art is an illustration; gameplay collision comes only from the validated Tiled map.

## Next action

Continue P03 from the [first stealth contracts](../architecture/integration/STEALTH_SLICE.md) and [current two-floor handoff](handoffs/khalid/day_02/TWO_FLOOR_LAB.md). Retrieve its [changed stair/sprint/map contract](../architecture/integration/TWO_FLOOR_LAB.md) before editing coordinates. Shared registry, Tracker A* and remaining cues/fixtures are still required before the P03 gate can close. Suhita's interactive Windows x64 check remains useful platform evidence and must not be represented as complete until run on her machine.

## Open inputs to resolve during development

- Available hours and academic submission deadline; implementation began on 2026-10-18 and the working-draft target stays four days.
- Suhita's Windows x64 desktop/manual QA and minimum supported OS/hardware. The hosted Windows x64 runner now builds and executes the frozen foundation successfully with dummy video.
- Wider macOS test versions and signing/notarization approach; only macOS 26.4.1 arm64 native smoke is verified, with ad-hoc signing.
- Source license and asset provenance. GitHub origin is now khalid999devs/Echo_Heist; Suhita uses her own account and needs collaborator access to push her owner branch.

These do not prevent preparing the local foundation. They must be resolved before the corresponding release claims or external actions. See the [risk register](RISKS_AND_DECISIONS.md).

Current follow-up: [38 native screen states and both route wins](../quality/reports/two_floor_lab/REVIEW.md). The [runnable handoff](handoffs/khalid/day_02/TWO_FLOOR_LAB.md) records the current archive, source commit and actual native/hosted status. Full V1 and manual Windows QA remain open.
