# Three-minute class proposal deck

2026-10-25, requested by Khalid. Replaces the 17-slide Blue Edition for the live class presentation; that edition and its guides remain as historical references. No game code, phase status or scoring changed.

## Brief

The instructor requires five sections in **three minutes**, with no slide limit: Introduction, Game Overview, UI Design (interface design/mockup), AI Agents (how many) and Algorithms. Audience is the whole class plus the supervisor. Khalid asked for algorithms to be the main part, so they get six slides. Slides carry only short labels. Speaker notes hold a timed spoken script of about 150 to 160 s (393 words at a normal 150 words per minute), leaving about 20 s for transitions, plus "If asked" answers for supervisor questions. Tooling sits on the closing slide rather than on a separate tech-stack slide, to save time.

Deliverables (ignored `output/`): `output/class-presentation/ECHO_HEIST_AI_Lab_Proposal.pptx`, the matching `.pdf`, and `fonts/` (Oxanium + OFL). Present from the PDF, or install Oxanium first; the classroom PowerPoint otherwise substitutes the heading font.

| Slide | Section | Content |
| --- | --- | --- |
| 1 | Cover | Title art, Member 1 Khalid 2207035, Member 2 Suhita 2207052 |
| 2 | 01 Introduction | Premise (NEXUS, intruder, lockdown) and our goal |
| 3–4 | 02 Game Overview | Four-step mission, two modes; six core features with lockdown/pursuit captures |
| 5–7 | 03 UI Design | Title, briefing, settings; HUD, map, result; Workshop, F3 Lab View, F2 Companion panel |
| 8 | 04 AI Agents | Five agents with roles and their algorithms |
| 9 | 05 Algorithms | Guard FSM (Sentinel and Tracker art) with real sight, identification and memory values |
| 10 | 05 Algorithms | BFS vs A* on one example grid: 55 vs 17 tiles checked for the same 12-step path |
| 11 | 05 Algorithms | The five fuzzy rules and real outputs (0.21 and 0.64) |
| 12 | 05 Algorithms | Minimax tree with an alpha-beta cut; NEXUS task priorities |
| 13 | 05 Algorithms | Companion pipeline and the four MCTS stages |
| 14 | 05 Algorithms | Companion configuration: four blocks, 81 policies, presets, tune-and-retest loop |
| 15 | Closing | Thanks, team, a "built with" row (Python, pygame-ce, Tiled, pytest, PyInstaller) and a platforms row (Windows, macOS) |

## Truth boundaries

- Every screen is a native capture from the quality reports or `output/phase04-presentation/`. The F2 Companion panel uses scripted fixture data; at Khalid's request it has no extra tag, its own small "scripted QA fixture" banner remains, and the slide 7 notes explain it. The Workshop capture is the shipped unavailable-deploy state.
- The FSM numbers come from `resources/data/gameplay/security.json` at 30 ticks per second. Fuzzy values come from running `investigate_urgency` itself; loudness 0.25 and 0.75 are stated inputs, not measured footsteps.
- The BFS/A* grid is an example. The builder runs both searches with the game's neighbour order and tie-breaking, so the tile counts are computed, not drawn by hand.
- The minimax tree is marked "example values", and the NEXUS priorities are design examples. They follow the blueprint design and are not telemetry. "64 playouts per decision" is the planned starting MCTS budget from PHASE_04.
- The Companion is configured, not trained: four Workshop blocks with three choices each (`ui/scenes/design/model.py`). The agent roster follows the blueprint. Slide 8 notes state today's status: Sentinels and the Tracker run; Interceptor, NEXUS and Companion are P04 work.
- The platforms row shows the V1 targets, Windows x64 and macOS Apple Silicon, whose archives already build. Its notes say physical Windows play testing is still pending and Linux waits for proper testing.

## Review of the earlier deck (`docs/idea/deck/AI_presentation.pptx`)

It matched the 17-slide Blue Edition. Stale against the current state: slide 9 "Tracker planned P03", slide 13 "Sentinel subset has tests", slide 15 "P03 active". P03 is complete, with two Sentinels and the Tracker's A*. Rubric gaps: no roll numbers, no explicit agent count, and only four screens (title, map, pause, settings, briefing and results were missing). Seventeen dense slides do not fit three minutes. Facts that still hold: algorithm roles, 24 × 4 = 96 planned runs, scoring, team roles and the 64-iteration start.

## Rebuild and verification

Sources: `output/class-presentation/build/make_assets.py` (backgrounds from the real map JSON and game art, character crops) and `build_deck.js` (pptxgenjs with react-icons and sharp).

```sh
python make_assets.py <repo>
NODE_PATH=<node_modules> node build_deck.js <repo> ../ECHO_HEIST_AI_Lab_Proposal.pptx <pptx-skill>/scripts
```

Actual results: `validate.py` PASS. A LibreOffice render with a task-scoped fontconfig exported 15 pages with Oxanium/Arial embedded (`pdffonts`). Every slide image was inspected and overflow, overlap and margin defects were fixed. The deck text has no em dashes. Microsoft PowerPoint on the classroom machine is NOT_RUN.
