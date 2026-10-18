# Risks, decisions and open questions

Updated: 2026-10-18. Decisions below are proposed engineering defaults unless identified as required by the source/user. Record validation and changes here as implementation proceeds.

## Risk register

| ID | Risk / impact | Mitigation and trigger | Responsibility | State |
| --- | --- | --- | --- | --- |
| RK01 | Required work misses the four-day draft target | Integrate Human loop on Day 1, all algorithms on Day 2, full interface on Day 3; reserve Day 4 for fixes/builds; cut optional polish/Linux first and report precise checkpoint gaps | Both | OPEN |
| RK02 | Windows/native Mac build or test access unavailable | Khalid confirms native runners/testers in P01; first available smoke build there; never infer Windows acceptance from Mac results | Khalid | OPEN |
| RK03 | Python/dependency/architecture mismatch | P01 verifies Python 3.13.16/Mac arm64 package and Windows x64 locked-wheel resolution; complete actual Windows execution before a release claim | Khalid | OPEN |
| RK04 | Hidden state leaks into Companion, NEXUS or rollouts | Explicit immutable observations, forbidden-import checks and noninterference tests at each controller boundary | Both | OPEN |
| RK05 | Algorithm names hide placeholder or unused implementations | Log actual calls/metrics; compare minimax modes; test real MCTS stages; demonstrate policy changes in controlled scenarios | Khalid | OPEN |
| RK06 | Determinism breaks through wall time, global RNG or ordering | Integer ticks, separate RNG streams, stable ties, full run header/action replay; compare target builds before broader claims | Khalid | OPEN |
| RK07 | Capture/doors/patrols create softlocks or unfair corners | Tick-boundary tests, lockdown connectivity, physical playtests, path-stall diagnostics; fix any unavoidable mandatory capture | Both | OPEN |
| RK08 | MCTS/search stalls rendering or simulation | Event-driven bounded searches, profile named machines, spread fixed iterations across ticks if needed; keep safe legal fallback | Khalid | OPEN |
| RK09 | Save paths or missing resources break frozen apps | P01 resource/writable-path baseline; Suhita's profile/settings adapters; both validate native persistence | Khalid + Suhita | OPEN |
| RK10 | Mac download security/permissions block real users | Test downloaded quarantined ZIP/.app, signing state and supported per-app opening steps on target OS; preserve bundle metadata | Khalid | OPEN |
| RK11 | Asset/font/audio/source licensing incomplete | Record provenance on import, choose source license before public release, ship required notices and credits | Both | OPEN |
| RK12 | Workshop choices are cosmetic or one policy stalls forever | Pair Khalid's planners with Suhita's actual profiles on same seeds, report timeout/stalls and tune from evidence | Khalid + Suhita | OPEN |
| RK13 | Academic evidence arrives too late or misses rubric | Run headers/metrics on Day 2, draft demo on Day 3, record draft evidence on Day 4; resolve actual submission rubric/deadline | Both | OPEN |
| RK14 | Telemetry grows without bounds or includes privileged data in normal UI | Separate debug/controller channels, bound history, retain compact summaries and link large raw artifacts | Khalid | OPEN |
| RK15 | Scoring double-counts a team chase or discourages intended tactics | Implement approved shared encounter lifetime, no direct gadget penalty, integer pace/ranks and score breakdown tests | Both | OPEN |
| RK16 | Concurrent owner edits or undocumented API drift break integration | One writer per slice/file, actual P01 contract map, claim/handoff records and combined phase gate checks | Both | OPEN |
| RK17 | Equal estimated points hide unequal real effort | Record active effort/blockers at phase gates and transfer bounded unstarted tasks with updated context/points | Both | OPEN |

## Decision register

| ID | Decision | Status / basis | Revisit condition |
| --- | --- | --- | --- |
| D01 | Desktop first: Windows x64 + macOS arm64; Linux only after testing; free itch.io downloads | REQUIRED: user clarification and PDF p. 19 | Explicit owner-approved release scope change |
| D02 | Python + pygame-ce + Tiled JSON + pytest + native PyInstaller one-folder | REQUIRED: PDF pp. 16, 19 | Demonstrated blocker and owner-approved technology change |
| D03 | One installable `src/echo_heist` package with pure simulation and typed controller boundaries | PROPOSED: maps PDF boundaries into a testable Python package | Evidence that structure obstructs actual integration |
| D04 | Python 3.13.16 project baseline, uv.lock, Ruff/mypy/pytest and optional PyInstaller tools | VERIFIED in P01 on macOS arm64; Windows binary-wheel resolution passes; exact versions in handoff | Actual Windows native execution remains required before support claims |
| D05 | Deeply immutable observations; belief-only MCTS; no controller WorldState access | REQUIRED: PDF pp. 12-13, 16 | Cannot be weakened for convenience |
| D06 | 30 Hz simulation, 60 FPS presentation target, deterministic search iterations | PROPOSED defaults: PDF pp. 5, 13 | Performance and feel measurements |
| D07 | EMP/stun resolves before capture; completed same-tick capture precedes extraction | First part REQUIRED by p. 8; tie precedence PROPOSED to resolve an unspecified edge | Playtest evidence; preserve recoverable interruption semantics |
| D08 | Separate policy profiles from seed/reset deployment settings while accepting combined source example | PROPOSED: PDF p. 17 example contains both | Contract implementation and migration review |
| D09 | Same-build/config/runtime replay determinism first; broader cross-platform guarantee only after validation | PROPOSED conservative verification scope | Windows/macOS action replay and hash evidence |
| D10 | Complete working initial draft in eight phases over four development days; retain independent public-release gates | REQUIRED: user's schedule/phase overrides on 2026-10-18; actual start date unassigned | Only an explicit user change can replace the target; record missed gates honestly |
| D11 | GPT-6.1 Sol Extra high for planning; High for bounded foundation/implementation | RECOMMENDATION: [workflow](../workflow/AI_WORKFLOW.md) | Actual quality/latency/cost on project tasks |
| D12 | Score = 50 extraction + max(0, 40 - 12 per distinct detection encounter) + up to 10 pace; unchanged S/A/B/C thresholds; failure 0/F; no direct tool penalty | APPROVED by user in chat on 2026-10-18; [specification](../planning/SCORING.md) supersedes PDF scoring defaults | Further scoring-rule changes require proposal in chat and explicit approval before adoption |
| D13 | P01 is Khalid-only; later slices give both developers frontend/backend work with strength-weighted 80/80 estimated points | REQUIRED ownership direction; concrete allocation in [Workload](../planning/WORKLOAD.md) | Rebalance actual effort through bounded task transfers without losing context |
| D14 | At most 1,000 lines per authored file, six maintained direct files per directory and proportionate tests only under grouped root tests | REQUIRED: user codebase rules; [details](../workflow/CODE_RULES.md) | Group by real responsibility; no silent limit exceptions or test proliferation |

## Open decisions

| ID | Question | Working handling | Resolve by |
| --- | --- | --- | --- |
| Q01 | Available hours and academic deadline? | Implementation began 2026-10-18; owners Khalid/Suhita; keep the eight-phase/four-day target and record actual effort | Before the remaining phase scheduling |
| Q02 | Minimum OS and supported hardware? | Advertise none as tested until recorded; test candidates early | Before P07 candidate |
| Q03 | Mac signing/notarization resources? | Preserve truthful unsigned/ad-hoc fallback and validate install flow; signing preferred when available | Before final artifacts |
| Q04 | Source license, copyright owners and public PDF redistribution? | No invented license; prepare source/asset provenance for owner decision | Before public GitHub |
| Q05 | Baseline difficulty, Speedrunner threshold and target success rate? | Measure complete runs and failure causes; calibrate shared pace reference from draft candidate | Day 4 balancing |
| Q07 | Exact input remapping scope and same-tick action priorities? | Implement the PDF's configurable controls and deterministic central validation; Khalid records priority in P01 contracts | Before P02 gameplay integration |

When changing a decision, record date, old/new behavior, affected requirements, evidence and migration/retest impact. Required scope changes need project-owner authorization; ordinary choices within scope can proceed and be documented without repeated approvals.

Resolved Q06: the user approved the replacement score/ranks in chat; D12 and SCORING.md are authoritative. Scoring is an explicit exception to ordinary autonomous tuning: propose further rule changes in chat and wait for approval.
