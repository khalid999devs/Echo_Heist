# Development changelog

## 2026-10-21 - Denser facility and slower movement

- Rebuilt the actual five-zone layout as 23 compact rooms with 104 physical furnishings, narrower bent corridors and two railed stair gangways. Added original generated desk/planter/lab/pump/shelf/stair art, room floor treatments, signs, grates and cables.
- Extended the existing importer with optional typed Room/FloorDetail metadata, quarter-turn furnishing orientation and whole-room reachability checks. Stable map/anchor/guard IDs remain; coordinates changed in the [consumer contract](../architecture/integration/FACILITY_DENSITY.md).
- Reduced walk/sprint from 2.2/3.6 to 1.8/2.6 tiles/s, with proportional defender tuning. Preserved body radius, tools, capture and approved scoring. Tab now opens a paused room map, clears held input and ducks audio.
- All 96 behavior cases, structure/Ruff/strict types pass. Both routes complete real native extractions with stock tools; deliberate guard contact captures. Inspected 38 native screenshots and removed overlapping room/zone signs. [Current review](../quality/reports/facility_density/REVIEW.md) records actual build/CI evidence as it becomes available.
- Clean `764d8ff` macOS build and fresh ZIP extraction pass native Cocoa smoke with audio ready. [Hosted CI 39587400106](https://github.com/khalid999devs/Echo_Heist/actions/runs/39587400106) passes all three platform checks, Windows/macOS native builds and frozen dummy-video smoke. [Runnable handoff](handoffs/khalid/day_02/FACILITY_DENSITY.md) records the exact archive/hash and remaining boundaries.
- P03 remains partial; user-deferred P05 environment mechanics and later full V1 systems remain open.

## 2026-10-21 - Illustrated gameplay and movement review

- Added original generated floor/bulkhead textures, six facility props and operative/robot frame strips. Walking, sprinting and facing follow committed actor movement; visual animation never changes collision or sensing.
- Bundled Oxanium with its OFL notice, improved mouse feedback, objective direction, Core hold progress, route/control guide and event cues. Replaced review screenshots and recorded a short actual walk/sprint clip.
- Structure, Ruff, strict types and 70 focused cases pass. Final clean native build and hosted checks are recorded in the combined verification report.
- Kept glass breaking, doors, hiding and canisters in Phase 5 under the owner's explicit choice. Guard patrol/perception remains Phase 3.

## 2026-10-20 - Integrated and refined Phase 2 Human mission

- Retrieved Suhita's `work/suhita-p02` at `a98548a`, which already contains Khalid's four P02 commits. Retained her five-zone Tiled export, typed loader/validator, route tests and working scene composition; reviewed on a separate integration branch to preserve both owner branches.
- Replaced the flat greybox presentation with a generated original 2.5D facility backdrop, operative dossier art, detailed map/actor motifs, readable objective/status/minimap, cinematic title/briefing/outcome screens and pointer input mapped through window letterboxing. Artwork is visual only; the Tiled map and Simulation remain authoritative.
- Added real `GameFlow` integration cases for menu mouse input, pause freeze, same-seed retry, full Core theft/lockdown/extraction, capture and result navigation. The combined suite reaches 69 passing cases; core and approved scoring rules remain unchanged.
- Ran native Cocoa source scene captures for title, briefing, gameplay, lockdown, win and capture and inspected all six. Ran a frozen macOS app smoke with packaged art/map, real Cocoa video, isolated settings and matching headless trace. The final artifact/hosted CI status is recorded in [verification](../quality/reports/phase02/integration/VERIFICATION.md).
- Closed the P02 functional gate under the user's explicit integration direction. P03-P08, active patrol AI, Companion, Workshop, final score and interactive Windows release QA remain later work; no unrun platform check is marked PASS.

## 2026-10-18 - Khalid's P02 core gameplay and input handoff

- Completed P02-K1/K2 on work/khalid-p02 through real incremental commits. Preserved app/bootstrap, Suhita's level/io, map resources and scene/render files; published the contract/file claim before implementation.
- Added bundled validated gameplay rules/public config DTO, fixed-point normalized continuous movement/sprint, body collision/substeps/sliding, noise cadence, continuous theft/atomic lockdown, carrier-only extraction, unscored outcome/abort/terminal freeze, telegraphed contact capture and interrupt/tie precedence.
- Implemented initial real Echo path/stock/lifetime/nonphysical authority, radial EMP disable/stock/noise and single-target melee/stun/recovery immunity. P03 guard perception and P05 environment/effect work remain separate; approved scoring is unchanged and deferred to its assigned P06 implementation.
- Added remappable event-to-action input, focus/pause/UI requests and own-observation objective/interaction presentation. Added an explicitly diagnostic contact room without replacing the real game scene.
- Structure/lint/format/strict types and 45 tests pass. Real Cocoa scripted input traces produce WIN at tick 243 with three paused frames and CAPTURED at tick 94; screenshots were inspected. Fixed the stale post-terminal capture warning/ring found in that inspection.
- Clean 789da10 native Mac build/extracted Cocoa smoke passes all eight assertions. Hosted run 39141181536 passes Linux, Windows x64 and Mac arm64 checks/native jobs. Native builds still use the foundation entry pending scene integration; no five-zone/AI/release acceptance claim was made.
- Recorded the runnable P02 handoff and grouped QA summaries, released Khalid's claims, and left shared EH items/P02 IN_PROGRESS. Stopped at Khalid's slice boundary; no P03 or main merge.

## 2026-10-18 - Windows teammate startup handoff

- Added Suhita's native Windows x64 PowerShell setup: clone, isolated owner branch, Python 3.13 provisioning, locked dependencies, source checks, desktop launch and Windows native build/smoke commands.
- Linked the guide from the owner/startup guides, README, development hub and actual P01 handoff. Recorded exact P02-S1/S2 scope, Khalid's retained simulation/input ownership, integration dependencies, verification/report paths and the stop boundary.
- Kept P02 unclaimed/unstarted and Windows execution NOT_RUN until actual evidence arrives. No gameplay or dependency versions changed.
- First GitHub push exposed a workflow validation error before jobs started: runner.temp is unavailable in job-level env. Changed the cache path to github.workspace/.cache/uv; the initial failed run remains visible in history.
- Published main and the full original development history to the user-specified public origin. Verified a fresh clone through 99a8658 includes the Windows handoff and all nine commits; no gameplay work was started. Re-ran local structure/lint/format/strict typing and all 21 tests successfully; 209 local documentation links resolved before the publication-status update.
- The first executable CI run passed Linux checks and the Mac native build/smoke, but the existing unavailable-storage regression failed on Windows: a regular-file ancestor was reported as a missing settings file. Added nearest-existing-directory validation so load reports unwritable storage consistently and save preserves the blocking file. Kept the existing regression assertion rather than skipping or weakening it.
- Run 39136504276 at a5d1400 passes all three hosted jobs, including 21 tests per platform and Windows x64/Mac arm64 native builds plus all frozen smoke assertions with SDL dummy video. Added the actual CI evidence report and artifact instructions; Suhita's own interactive Windows QA and full-game release checks remain pending.

## 2026-10-18 - Phase 1 complete

- Initialized local main and committed actual progress in short separate steps: planning, Python setup/checks, deterministic contracts/runtime, desktop/settings and native packaging/CI. No remote or publication was created.
- Installed the Python 3.13.16 environment with a real lock; pygame-ce 2.5.8/platformdirs 4.13.4 and development/build versions are recorded in the runnable handoff. Global Python was unchanged; source license remains pending before publication.
- Implemented immutable map/action/event/observation/result boundaries, private fixed-tick diagnostic simulation, deterministic events/RNG namespaces and rejected-action handling. No P02+ game rules/AI were substituted with fake success.
- Added installed/frozen-safe SVG/JSON resources, a resizable desktop foundation, isolated/OS-writable settings, atomic JSON writes, corrupt recovery/future-version preservation and audio fallback.
- Added the 1,000-line/six-direct-file/test-placement checker with absolute/relative import guards, grouped useful tests and one combined check command. Local lint/format/types and 21 tests pass; negative structural probes reject actual violations.
- Built a wheel and installed/exercised it from an unrelated cwd. Built the native ad-hoc-signed Mac arm64 ZIP from clean commit 61a00a0, extracted it and passed all eight frozen headless/Cocoa/resource/settings/hash checks without development Python paths.
- Windows x64 binary-wheel resolution passes. Windows native execution, hosted CI and public Gatekeeper/download flow remain NOT_RUN; the three-target workflow is configured and locally parsed only.
- Completed P01-K1/K2/K3 and EH-001 through EH-005; released claims and prepared the exact runnable/API handoff for Suhita. P02 and all later implementation remain TODO. This assignment ends at the P01 boundary.

## 2026-10-18 - Eight phases, named balanced ownership and agent instructions

- Replaced active M0-M5 milestones with P01-P08, two phases per development day, retaining stable EH feature anchors and the complete-functional-draft requirement.
- Assigned Phase 1 entirely to Khalid. Allocated 80 estimated points each overall, with Khalid weighted toward architecture/core/strategy and Suhita toward game scene/level/interface design, while giving both substantive frontend/backend slices.
- Added eight detailed phase specifications, workload/speed guidance, owner-aware startup, Khalid/Suhita guides and claim/runnable-handoff instructions. Shared feature status cannot close while another owner's required slice remains unfinished.
- Added root AGENTS.md and detailed code rules: at most 1,000 lines per authored file, six maintained direct files per directory, meaningful responsibility subgroups and necessary tests only under grouped root tests. Preserved original source references and generated-lock integrity.
- Synchronized master plan, feature mapping, status, architecture/contracts, setup/workflow, quality/release guidance and risks/decisions. No game source, environment, tests, build or agent execution is claimed by these planning edits.
- Validated document links, eight phase definitions, slice references/points, 80/80 totals, dependency references, file/directory limits and preserved source/scoring content. Checks here concern planning/instructions, not implemented gameplay.

## 2026-10-18 - Four-day draft target and approved scoring revision

- Replaced the active four-week assumption with the user's target: complete working initial draft within four development days, preserving required gameplay/AI/Workshop scope.
- Replanned the critical path: Day 1 foundation/Human loop/basic tools, Day 2 opposing AI including real fuzzy/MCTS, Day 3 Workshop/interfaces/scoring/presentation, Day 4 integration/regression/experiments/native draft builds. Public release retains its own evidence gates.
- Proposed a concrete scoring replacement in chat, then received explicit user approval before updating scoring specifications: 50 completion + up to 40 stealth (minus 12 per distinct confirmed detection encounter) + up to 10 pace; S/A/B/C thresholds retained, unsuccessful runs 0/F, tools reported without direct penalty.
- Added SCORING.md, shared-encounter semantics, integer pace calculation, examples and verification cases; added EH-033 for implementation. Further scoring-rule changes require prior proposal/approval in chat.
- Updated master plan, scope, contracts, workflow prompt, quality/release guidance, status, backlog and risk/decision registers. Game implementation and real platform tests remain TODO.
- Checked local document links, task dependency/day order, unchanged source files and the approved scoring examples, bounds, monotonicity and rank reachability. These are planning/math checks, not gameplay verification.

## 2026-10-18 - Blueprint-based planning baseline

- Read the complete 19-page V1.2 blueprint and visually checked its release page. Preserved both original idea files unchanged.
- Recorded the user priorities: free downloadable itch.io V1, Windows x64 and macOS Apple Silicon primary, tested Linux optional, browser/Steam outside V1.
- Created the grouped development hub, R01-R27 traceability matrix, M0-M5 roadmap, architecture/contracts, initial setup specification, effort guidance, test/experiment plans, asset register, release gates and ordered backlog.
- Documented tunable defaults, source revision vs game version, unreachable initial C rank, detailed actor-readability requirement and known toolchain/platform risks.
- Inspected environment: workspace had the idea PDF/text, no Git repository/game source; local host arm64/Python 3.14.4; pygame/pytest absent. Implementation, dependency resolution, hosted CI, packages and hardware QA remain TODO.
- Verified documentation links, requirement/backlog identifiers, task dependency order and unchanged source hash in the planning validation pass. No gameplay/test/build success is claimed.

Future entries should record task IDs, resulting behavior, actual checks with outcomes, changed tuning/decisions, evidence paths and the next ready task. Do not copy the entire backlog into each entry.

## 2026-10-21 — Cinematic UI, licensed audio and first live stealth cluster

Khalid followed the owner's new brief and grouped screenshot inspirations, replaced the title with the approved perspective cinematic, blended shared UI surfaces, integrated CC0 context music/event sounds and real Settings, then began the first P03 subset. One Sentinel now uses immutable filtered sensors, actual BFS/fuzzy/FSM behavior, identification, investigation/chase/search/return and expiring evidence. Physical Entry/Service furniture, compact HUD, sensor cones and real F3 telemetry are connected. 89 behavior cases and native playthrough/screens pass; see the [review](../quality/reports/phase02/presentation/REVIEW.md). Remaining shared P03/P04-P08 functionality stays open, including the owner-deferred P05 environment mechanics.
