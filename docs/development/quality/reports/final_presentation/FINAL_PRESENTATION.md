# Final presentation build: movement fixes, guard roster, evidence and materials

2026-11-22, Khalid. Uncommitted working tree on `main` after `dd4f156`. Fingerprint schema 17.

## What changed in the game

Reported problems: guards that surrounded the thief without grabbing, a Companion that stalled, and a Companion that pushed against a stunned guard "like a wall". An automated glitch probe then found further cases. All fixes keep the approved scoring.

- **Bodies.** A stunned or EMP-disabled guard no longer blocks anyone. Guards slide past each other. Two bodies already inside each other's clearance may always move apart. An intruder crouched under a desk only blocks by plain body contact, so a robot at a desk edge no longer walls off the corridor in front of it. A guard whose move is fully blocked by an intruder's body turns toward that body (`motion.toward`), and its normal sight decides what happens next.
- **Grabs.** A witnessed locker can be inspected and grabbed. A chaser next to a stunned guard grabs without restarting.
- **Guard steering.** Corner snags slide toward the lane. A guard that can see the thief on an open straight line runs straight at it, and keeps that course for one second when sight flickers. Before this, a chaser re-centring on tile paths ran alongside a fleeing thief or stepped back each time the thief hopped between two rows. A guard that drifts off the start of its path replans from where it stands. A half-seen shape is watched for 10 ticks before the guard goes to check, and the guard keeps looking toward a shape lost in the last second. This removed per-tick flicker of the identifying/checking label and cone at the edge of sight range.
- **Pursuit tuning.** Chase speed 125%, pursuit pressure 103% of sprint after 1 s of steady sight (`phase02.json`).
- **Companion.** Its watched-by check uses the guards' real cone geometry. It predicts the lane of a patrol that left view, reroutes when a guard holds the next gate, commits to an exit, and damps flip-flopping turns (escapes may turn at once). Escapes keep their heading among equally good steps, judge each step by where it actually leads, always count the guard being escaped, and never aim at a flee spot past that guard. When a guard stands in a one-tile corridor ahead, it steps back two tiles and waits. Under a desk it stays hidden while a guard was seen within 3 tiles in the last 45 ticks.
- **Guard roster (user override).** At the user's request the facility now has two Trackers and two Interceptors. The Vault guard (`guard-vault`, previously `guard-core-sentinel`) is a Tracker and the Cargo guard is an Interceptor, so the six guards are two Sentinels (Service, Security), two Trackers (Research, Vault) and two Interceptors (Core, Cargo). The blueprint allows 2-3 Sentinels, 1-2 Trackers and one Interceptor, about 5-6 guards in all; the second Interceptor is the user's explicit override. Each Interceptor searches only the gates of its home zone (Core Chamber: Research and Security gates; Service Wing: Stairs A, Stairs B and the Entry gate), so the two never hold the same gate and every escape keeps a branch open.
- **Interceptor telemetry.** `NexusTrace.interceptors` carries every Interceptor's latest plan instead of one. The F2 Interceptor tab shows one named card per Interceptor, policy-decision event ids include the guard id, and the experiment harness counts searches and gate changes per guard.

New logic lives in `ai/guards/steering.py` (`open_line`, `glancing`, `spot_lapsed`), `ai/companion/stealth/lanes.py` (`side_lane`, `backoff`, `guard_near`, `away_goal`) and `core/simulation/systems/motion.py` (`toward`). `controller.py` stays at 1,000 lines.

## Verification

Scripts named below without a repository path live in the presentation workspace, `../Echo_Heist_archive/presentation-build/work/` (outside the repository, see the last section).

| Check | Command or tool | Result |
| --- | --- | --- |
| Full gate | `uv run --locked python scripts/checks/run.py` | Structure, ruff, format and mypy clean; **359 passed** |
| Glitch probe | `glitch_probe.py 1 181`, Ghost, Balanced, Rush | 540 missions, **0 flags** (blocked ≥ 45 ticks, two-tile jitter, grab churn, facing flips) |
| Seed sweep | `balance.py 1 401` | Rush 2 wins (seeds 42 and 54, both 76 points, rank A) and 75 Core thefts in 400; Balanced 0 wins, 8 thefts; Ghost 0 wins, 1 theft. Rush captures by guard: Vault Tracker 117, Research Tracker 86, Security Sentinel 73, Service Sentinel 64, Core Interceptor 55, Cargo Interceptor 3 |
| Pressure comparison | `scripts/experiments/comparison.py --output-dir ../Echo_Heist_archive/presentation-build/experiments` | 96 captures in 96, median capture at tick 626 (20.9 s); same hash `6ea4616b37f0…` on two runs; first-run repeat matched; p95 tick 1.7 ms median. The two slowest missions rerun alone peak at 12.6 ms; single ticks of up to 83 ms in the full runs moved between missions from run to run and came from load on the machine |
| Human routes | `react_route.run_v4`, seed 1042 | Gadget run (`near`, 5, 45) WIN at tick 2138, 76 points, rank A, 2 encounters. Capture run (`enter`, 8, 15, Security approach) CAPTURED at 1667 by the Vault Tracker. The old quiet route (`timing3.py`) is now caught by the Vault Tracker at the Core and was retired |

The first glitch probe on the new roster flagged one mission (seed 1, Balanced): the Research Tracker and the robot pushed against each other for 103 ticks at the Stairs B landing because the robot stood just outside the Tracker's cone. The bump rule above fixed it; the robot sweep and probe were then rerun on the final code.

Re-pinned tests: robot win seed 388 → 42 (exit `cargo-exit`). Registry and scene tests expect the new roles. The exposed Cargo return is now caught by the Service Sentinel while the Cargo Interceptor holds Stairs B, and the blind Research return asserts the Cargo Interceptor's Stairs B post as well as the Core Interceptor's capture. New unit tests cover the row-hopping chase, the half-seen stare, escape heading, the one-tile back-off, the flee goal and the bumped guard turning.

## Gameplay recordings

All takes are recorded from the native game window by `record_final.py` with game audio. Human takes send scripted key events through the real Human input adapter, first verified headless, then replayed tick for tick into the window.

| Take | Seed | What it shows | Result | Recording |
| --- | --- | --- | --- | --- |
| `human-showcase` | 1042 | Echo from the Service locker (tick 201), staircase A, a second Echo from the Vault recess (896), Core (1132) with a Vault Tracker grab broken by a stun and a Core Interceptor grab broken by the EMP, staircase A down, Cargo locker while the Cargo Interceptor and Research Tracker pass, Research Tracker grab at the exit broken by a stun | WIN through Cargo at 2138 (1:11), 76 points, rank A, 2 encounters | 85.9 s, 3 late frames, max audio gap 22,272 bytes |
| `human-caught` | 1042 | Long hide in the Vault recess beside the Vault Tracker, Core at 1388, stuns and the EMP, then both Trackers grab together | CAPTURED at 1667 (0:56) by the Vault Tracker | 66.5 s, 1 late frame |
| `companion-win` | 42, Rush | Live MCTS, NEXUS and both Interceptor cards; theft at 1014; escape through the Research gate and staircase A | WIN through Cargo at 2207 (1:13), 76 points, rank A | 90.3 s, 1 late frame, max audio gap 26,624 bytes (re-recorded once after a take with a 5.9 s stall from machine load) |
| `companion-capture` | 82, Rush | Theft at 1091, Vault Tracker grab and stun, Echo and EMP against the Research Tracker, both Trackers close in | CAPTURED at 1438 by the Research Tracker | 61.0 s, 3 late frames |
| `guard-monitor` | 42, Rush | F3 monitor on the Service Sentinel, Vault Tracker, Core Interceptor, Cargo Interceptor and Research Tracker | Not a full mission | 54.5 s, 0 late frames |
| `companion-desk` | 19, Rush | The robot under the desk beside the Core Chamber while a guard walks past (ticks 976 to 1126) | Not a full mission | 44.8 s, 1 late frame |

**Hiding with a reason.** In the earlier fixed-hold route the player stayed in the Security locker for 13.1 s while a guard was on camera for only 4.6 s of it (`hide_audit.py`). The human runs in `react_route.py` react only to what a player could see: active guards inside the camera window (about 20 × 11 tiles) on the same floor. They skip the Security locker when no guard is in view, enter a hide only with a guard on screen and leave once the guard has been off screen for 20 ticks. Every hide in the gadget run has a guard on camera for its whole length (Service locker 2.1 s, Vault recess 3.8 s, Cargo locker 5.1 s).

**Camera coverage.** `guard_screen.py` counts the seconds each guard spends inside the camera window. In the gadget run every guard is on camera: Service 12.8 s, Security 15.7 s, Vault Tracker 13.1 s, Research Tracker 6.7 s, Core Interceptor 5.5 s and Cargo Interceptor 8.0 s.

## Presentation materials

- **Deck:** `output/final/ECHO_HEIST_Final_Presentation.pptx` and `.pdf`, 24 slides in the proposal theme, four parts: the game, gameplay videos, the AI, one decision step by step. At the user's request there is no results slide and no test or simulation counts on the slides. On 2026-11-22 the deck was cut from 28 to 24 slides (two ways to play merged into the opening slide, the mission steps merged with the score, the MCTS tree merged with the UCT working and the mission ending) and restyled to the proposal deck's components: character cards on a glow, a native mood diagram, fuzzy rules as pills, NEXUS jobs as priority bars, big stat callouts, rounded tables without grid lines and spaced-caps media labels. The closing slide shows the Windows and macOS platform badges as in the proposal. It embeds 15 real-speed clips without audio (cut from the native 720p takes by `cut_clips.py`) and the two double-speed runs with game audio. `autoplay.py` adds PowerPoint's "start automatically" timing to every video slide; the short clips loop. The deck passes `validate.py`.
- **Traced decision:** tick 1014 of Rush seed 42, the theft. The Core Interceptor's alpha-beta holds the Security gate (value 0.2947, 25 of 40 endings, 15 branches skipped, same answer as minimax), the Cargo Interceptor holds Stairs B (value 0.1, 27 endings, 21 skipped), and the robot's MCTS picks Advance through the Research gate (23 of 64 tries). Data: `report/data/chapter8.json` and `mcts.json` from `decision_data.py` and `mcts_tree.py`; the seed 388 trace is kept as `chapter8-388.json` and `mcts-388.json`.
- **Figures:** `diagrams.py` draws the mood machine, architecture, mission steps, minimax tree and MCTS tree as hand-laid SVG in the deck's colours and Oxanium font, rendered to PNG with `rsvg-convert` (fontconfig backend), replacing the earlier Graphviz figures. The minimax tree shows each route's value as a bar, the thief's best route per gate, the chosen gate and the routes where alpha-beta skipped endings. `guard_map.py` colours patrol loops by guard type, adds a legend and joins matching staircases with a dashed line.
- **Report:** `output/final/Echo_Heist_Final_Project_Report.docx` and `.pdf` (25 pages after the spacing pass below), rebuilt with the new roster, screenshots, Chapter 8 trace, results and the new figures. A wording pass removed repeated template phrases, shortened long rule lists and plural-corrected the guard roles; tables now have a blue header row and light banding.
- **Independent review (2026-11-23):** at the user's request a separate reviewer agent checked every slide and page against `chapter8.json`, `mcts.json`, `facts.json` and the game config. It confirmed the fuzzy, minimax, alpha-beta, route-weight and score arithmetic and found no dashes or test counts on the slides. Fixes made from its findings:
  - **Slide 20:** now shows each route's total length and the real weight rule. The worked ending shows the gap and the × weight step.
  - **UCT values:** shown to four decimals so the sums add up.
  - **Reward explained:** the MCTS result (raw score, mapped to 0 to 1 by (raw + 120) ÷ 260, from `ai/companion/tactics.py`) is now explained in report 8.8 and the slide notes.
  - **Robot's route:** report 8.7 notes that the robot's real route was not among the Interceptor's six listed routes.
  - **Naming:** Companion naming, mood labels and fuzzy set names were made consistent.
  - **Slide 22:** shows 7 key decision points at a readable size.
  - **Report text:** fewer analogies and template labels. The private repository reference says access is on request.
  - **Windows:** the notes state that hands-on testing of the final Windows build is still open.
  - **Figure labels:** larger.

  After the user spotted an agenda title overlapping its text in a viewer without Oxanium:
  - **Fallback check:** the deck was rendered with Oxanium mapped to Arial (`build/fonts-fallback.conf`). The agenda titles now have room for two lines.
  - **Rules slide:** slide 4 became "Rules: how a mission works", with an explicit capture rule.
  - **A\* example:** slide 15 now shows the worked heuristic (plain guess 39 steps, ours 36).
  - **Requirements check:** the deck covers every item in the teacher's slide notice: overview, rules, mechanics, algorithms, double-speed videos, step-by-step tracing, minimax and MCTS trees, and heuristic calculations.

  Final layout check:
  - **Automated deck check:** `work/deck_check.py` measures every text box with real font metrics, in Oxanium and with Arial standing in. It found no overflow, no colliding text boxes, nothing off the slide and no missing pictures. All 17 embedded videos are present.
  - **Visual pass:** all 24 slides and 23 report pages were checked at full size.
  - **Report captions:** 34 captions, numbered in order, with no duplicates, and every figure or table referenced in the text exists.
  - **Report additions:** the guard patrol map is now Figure 2.2, so the report has every diagram the slides have.
  - **Report page 7:** no longer half empty; the screenshot grid can start below the section text.
  - **Report spacing pass:**
    - Body text at 1.15 line spacing, with 8 pt after each paragraph.
    - Lists close with a full gap.
    - Larger gaps above chapter and section headings.
    - Every table, code box and figure gets the same space after it.
    - The 40-row ending table (Table 8.2) starts on its own page.
    - The report is now 25 pages.

  Not changed:
  - **Background:** the plain content background stays, following the user's earlier request for no art behind text.
  - **Fonts:** Oxanium is not embedded in the .pptx, so it must be installed on the presenting machine (the PDF embeds it).

  Final recheck before submission (2026-11-23):
  - **Slide 15 clip replaced:** the user spotted a glitch in `tracker-catch`, which was cut from the seed 82 `companion-capture` take at 48.0 to 53.8 s. A pursuing guard above the Core Chamber corridor keeps walking into the wall beside the door for about five seconds (game time 0:42 to 0:47) instead of going round. The slide now uses `tracker-astar`, cut from the `guard-monitor` take at 26.9 to 31.1 s. In it, the F3 monitor shows the Vault Tracker planning a 27-step A* path to a radio report (40 tiles expanded), then spotting the robot and replanning to it with only a few tiles per plan.
  - **Other clips:** the slide 9 capture clip does not show the problem; its pursuing guard walks along the wall to the door.
  - **Video 04 recut:** the guard is the Vault Tracker. Once its stun wears off at 45.4 s of the take, it walks into the Core Chamber wall and stays there until the capture at 53.4 s. `export_final.py` now leaves out 45.2 to 53.4 s of that take and joins the two parts with a 0.5 s crossfade. Both versions of `04 Robot - Caught by the Trackers` run to the robot breaking the Vault Tracker's grab (game time 0:39), then fade to the CAPTURED report, which names the Research Tracker. The full-speed version is 52.3 s and the 2x version 22.5 s, and both decode to the last frame.
  - **Still open:** the game code was not changed, so the wall-walking pursuit remains an open movement bug. Re-recording seed 82 would repeat it, because runs are deterministic.
  - **Report numbers:** the text was reread, and every Chapter 8 number was recomputed: route weights, all 40 endings, the minimax levels, the alpha-beta bounds, the UCT scores and the fuzzy example.
  - **Report fixes:**
    - The guard mood diagram had its two Chase and Search labels swapped.
    - "The remaining 1 ending" now reads "the last ending".
    - The hand-worked examples are introduced as "Here are five of them".
    - The UCT formula's spacing is fixed.
    - Szepesvári is spelled correctly.
    - The Word file's "last modified by" field names the authors instead of "Un-named".
  - **Report checks:** still 25 pages, with Times New Roman and Courier New embedded in the PDF, and `validate.py` passes.

  Report restyle after the user's review (2026-11-23):
  - **Colours:** headings and the title are near black. Table headers are light grey with black text, and table rows, borders and the key words box use neutral greys. The only blue left is the reference links.
  - **Captions:** 10 pt italic in a softer grey. Table captions are left-aligned with their full-width tables, and the gap between a figure caption and the next table caption is wider.
  - **Diagrams:** the mood and architecture diagrams no longer have a white outline behind their arrow labels. The labels are a shade lighter and were moved so none touches a line. The slide figures were not changed.
  - **Pseudocode:** 10 pt Courier New (was 9 pt) with 1.1 line spacing and more padding, and an even 12 pt gap above and below each box. Long lines were rewrapped so none breaks inside the box.
  - **Equations:** formulas are Word equations (OMML) written by `report_math.js`: stacked fractions, a real square root, an overbar, a brace for the escape-score cases, and true minus, times, infinity, alpha and beta signs. Display equations cover the score, fuzzy urgency, escape score, route weight, UCT and the MCTS result. Worked numbers in the text are inline equations, and Table 8.1 routes use arrows.
  - **New explanations:** the report now defines the variables in the escape-score and UCT formulas, and says what MAX and MIN mean in Table 8.3.
  - **Layout fixes:** Table 8.3 has tighter rows so it fits on one page, and the hand-worked endings in 8.4 are left-aligned so the inline equations do not stretch word spacing.
  - **References:** full author names instead of initials, italic journal and book titles, clickable blue links (9 link annotations in the PDF) and 7 pt between entries.
  - **Checks:** 26 pages, all 34 captions in order with no missing references, no dashes, and `validate.py` passes. LibreOffice drew the equations in Liberation Serif and OpenSymbol; Word will use Cambria Math.

  Final report correction (2026-11-23), at the user's request:
  - **Section 9 shortened:** it keeps only automatic tests, the wide robot test, the stress test, speed and known limits, each in two or three plain sentences. The glitch-checker, replay fingerprint and recording details, the search and decision counts from the stress runs, and the human-run bullet were removed from the report (they stay in this record).
  - **Semicolons removed:** every semicolon in the report was replaced with a comma or a full stop, including Table 8.3, which now separates children with commas, and the team table. Pseudocode statements that shared a line now sit on separate lines.
  - **Checks:** still 26 pages, 34 captions with no missing references, no dashes, 9 clickable links, and `validate.py` passes.
- **Videos:** `output/videos/`, full-speed 1080p takes and double-speed versions: 00 opening, 01 human gadget heist, 02 human capture, 03 robot escape (seed 42), 04 robot capture (seed 82, recut to leave out the wall glitch), 05 F3 guard monitor. Every file decodes to its last frame.

## Output folder and workspace

On 2026-11-22, at the user's request, `output/` was reduced to three folders: `proposal/` (the class proposal deck), `final/` (the deck and report) and `videos/`. The presentation workspace (deck and report builders, data, figures, clips and raw recordings) moved outside the repository to `../Echo_Heist_archive/presentation-build/`. The LinkedIn post and the proposal build sources were kept in `../Echo_Heist_archive/old-output/`. All other older evidence folders under `output/` (phase reviews, native builds, extracted packages, logs and superseded recordings) were deleted to free disk space. Older reports that link into those folders keep their recorded numbers, but the local files no longer exist.

On 2026-11-23, at the user's request, the submitted PDFs were also committed under [`docs/submission/`](../../../../submission/): `ECHO_HEIST_Final_Presentation.pdf` (24 slides, 39.8 MB) and `Echo_Heist_Final_Project_Report.pdf` (26 pages, 3.7 MB). They are byte-identical to the copies in `output/final/`. The .pptx, the .docx and the videos stay local.
