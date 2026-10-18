# V1 scope and traceability

Authority: [blueprint](../../idea/ECHO_HEIST_Complete_V1_Game_Development_Blueprint.pdf), with the user's explicit platform priorities, eight-phase/four-day working-draft target, named workload and chat-approved scoring revision. Implementation and test artifacts listed below are planned, not existing.

## Required scope

| ID | Requirement | PDF pages | Planned acceptance evidence |
| --- | --- | --- | --- |
| R01 | One Chapter One heist: enter, steal core, mandatory lockdown, return to original extraction | 1-3, 6 | T02, T08; complete gameplay recording |
| R02 | Human vs AI and autonomous Companion vs defenders available on first launch | 1, 5, 12, 15, 18 | T01; fresh-profile checks in both packages |
| R03 | Five connected zones, upper/lower branches, a cross-link, valid return paths during lockdown | 3 | Map validator, route checks, physical playthrough |
| R04 | Capture-based failure; discovery and noise remain recoverable; no health/combat damage system | 6, 8 | Capture, escape, stun, and terminal-order integration tests |
| R05 | LOS, acoustic reach, uncertain suspicion, decaying sighting memory, witnessed hiding | 6-7, 9-11 | T03, T04; observation noninterference tests |
| R06 | Three Echo charges; recent path replay decoy cannot carry core or extract | 7-8 | Ability tests and visible decoy demonstration |
| R07 | One nonregenerating EMP, temporary disable, grab cancellation, electrical noise | 8 | T05; boundary tick tests |
| R08 | Adjacent single-target melee, temporary stun, loudness, recovery immunity | 8 | Range, reach, immunity, and no-destruction tests |
| R09 | Stateful doors, hiding spots, canister and once-only breakable glass | 7 | Interaction priority and duplicate-event tests |
| R10 | Sentinel executes BFS, FSM, and fuzzy suspicion based on permitted cues | 9 | BFS correctness, membership/rule traces, T03 |
| R11 | Tracker executes heuristic A*, legitimate reports, last-seen search and expiry | 10 | Path correctness and T04 |
| R12 | Interceptor executes bounded minimax with alpha-beta and travels to a legal post | 10 | T06; pruned/unpruned equivalence and node metrics |
| R13 | NEXUS coordinates from evidence, retains coverage, mandates lockdown | 11 | Report provenance, dispatch limit and lockdown tests |
| R14 | At most one announced evidence-backed NEXUS adaptation across attempts; reset toggle | 11 | Persistence/reset comparisons; no hidden-policy access |
| R15 | Autonomous Companion uses mission FSM, utility, observed-risk A*, and real bounded MCTS | 12-13 | T07; autonomous win/fail; UCT/rollout/backpropagation traces |
| R16 | Workshop has four validated blocks, Ghost/Balanced/Rush presets, profiles and meaningful policy variation | 14 | Save/load and invalid config tests; paired policy experiment |
| R17 | Menu/mode/Workshop/heist/results/epilogue flow; retry same seed, new seed, edit policy | 2, 15 | Manual navigation matrix and result tests |
| R18 | Objective, alert, stock, core/time HUD; Companion decisions; algorithm guide and Lab View evidence | 5, 13, 15, 18 | Screenshots, real telemetry, mode-specific information review |
| R19 | Pause, restart warning, window/fullscreen scaling, music/SFX sliders, reduced flashing, subtitles, non-color status cues | 5, 15 | Laptop-resolution, focus, mute, pause and accessibility QA |
| R20 | Headless deterministic simulation; shared actions; immutable filtered observations; belief-only rollouts | 16-17 | Replay hashes, import boundaries, hidden-state mutation tests |
| R21 | Versioned writable settings/profiles/history/telemetry; legal, serializable inputs | 17 | Corrupt-file recovery, migration and packaged save tests |
| R22 | Results explain win/capture, time, detection encounters, tools, approved score/grade and decisive AI choices | 14-15, 18 + user-approved scoring revision | Score tests and explainable result snapshots |
| R23 | Seeded policy comparisons and genuine algorithm execution evidence | 18 | Reproducible experiment suite and academic report |
| R24 | Python + pygame-ce; Tiled JSON; pytest; PyInstaller one-folder builds | 16, 19 | Clean install/run, native build manifests |
| R25 | Free itch.io Windows x64 and macOS arm64 downloads; Linux x64 only if tested | 19 + user | Clean-machine release matrix |
| R26 | Public GitHub source, run/test guide, license/credits, screenshots, gameplay video and academic submission | 18-19 | Public-link checks and submission checklist |
| R27 | Readable sci-fi facility, distinct actors, gameplay-backed audio, core/Echo/EMP effects, short narrative | 2, 4, 19 | Asset register, playtest and scene review |

## Tunable defaults

Map dimensions, tile size, guard count within the proposed roster, movement speeds, capture duration, memory TTL, sound radii, scores, search budgets and script wording are starting values. Keep them in versioned data, record reasons for adjustments, and rerun affected tests/experiments. Preserve the meaning of the mechanics and required algorithms.

The blueprint proposes 10-20 minutes for a successful run; treat that as a pacing target to evaluate, never a mission countdown. The user approved [replacement scoring](SCORING.md): 50 extraction + up to 40 stealth (minus 12 per distinct confirmed encounter) + up to 10 pace; S >=90, A >=75, B >=60, C below 60 on success, 0/F on failure. Tool use is reported without a direct deduction. This fixes the original 60-point completion floor that made C unreachable. Further scoring-rule changes require prior chat approval.

## Four-day draft boundary

All required gameplay, opposing AI algorithms, Workshop settings, result/retry flow, persistence and baseline readability must be complete after P08 on Day 4. [Eight phases](phases/README.md) assign this work to Khalid/Suhita, with P01 setup entirely Khalid's. Simple art and cosmetic issues may remain; later accuracy/polish cannot absorb missing required features. Linux/optional effects stay outside the sprint. Public-release validation remains required before advertising platform support.

## Outside V1

Browser deployment, Steam integration, networking/multiplayer, a second playable mission, physical NEXUS boss, procedural campaign, neural-network/RL training, arbitrary user code, a visual programming language, permanent guard kills, health bars, inventory progression, a full lighting engine, and an elaborate cutscene system.

## Scope pressure

Cut extra props beyond the essential interactions, lighting upgrades, cinematic embellishments, extra audio layers, advanced Lab View charts, and optional Linux first. Keep a readable Lab View with actual algorithm metrics. If required features exceed capacity, revise the schedule; do not present an incomplete demonstration as finished V1.
