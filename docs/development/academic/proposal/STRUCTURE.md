# ECHO HEIST: focused AI lab proposal

Revised for Khalid and Suhita, **2026-10-22**. The latest direction is **at least 15 and at most 20 slides total**, with academic AI theory/implementation as the main subject. This draft has **17 slides total, no appendix**. It supersedes the earlier 16- and 22-slide drafts.

Deliverable: `output/proposal-deck/final/ECHO_HEIST_AI_Proposal_Blue_Edition.pptx`. Transfer pack: `output/proposal-deck/final/ECHO_HEIST_Proposal_Blue_Handoff.zip`. This task never overwrites the original Downloads presentation.

Authority: [blueprint](../../../idea/ECHO_HEIST_Complete_V1_Game_Development_Blueprint.pdf), approved overrides, [contracts](../../architecture/DATA_CONTRACTS.md), [experiment plan](../../quality/EXPERIMENTS.md) and [actual status](../../tracking/STATUS.md). The presentation is a proposal with truthful progress labels, not evidence that unfinished systems already work.

## Narrative and slide allocation

| Slide | Subject | What the teacher should understand |
| --- | --- | --- |
| 1 | Game / idea / team | Original blue cinematic facility; a stealth heist to recover the core and survive lockdown |
| 2 | Story → coursework | NEXUS takeover, mission and why patrols, uncertain clues and competing routes need BFS/A*/FSM/fuzzy/minimax/MCTS |
| 3 | AI lab objectives | Distinct decision roles, fair inputs and inspectable behavior; white lab concept illustration |
| 4 | Human vs AI / AI vs AI | Controller substitution under shared rules; illustrated mode panels and actual Human scene |
| 5 | Agent model / PEAS | Performance, environment, actuators and sensors; partial observation and hybrid representations |
| 6 | Architecture / fairness | Immutable observations, legal actions, one Simulation and separate presentation diagnostics |
| 7 | **AI 1/3: Sentinel / Tracker** | FIFO BFS, FSM, Sugeno urgency and evidence-backed A*; input → decision → behavior |
| 8 | **AI 2/3: Interceptor / NEXUS** | Minimax/pruning example, physical interception and evidence-driven guard task assignment |
| 9 | **AI 3/3: Companion** | Mission FSM, emergency utility, all four MCTS stages and risk-aware A* |
| 10 | Algorithm choices / limits | Why different methods solve different layers; assumptions and computational cost |
| 11 | Verification | Reference paths, alpha-beta equivalence, actual MCTS updates and hidden-state invariance |
| 12 | Current runtime evidence | Real Sentinel BFS/identification/fuzzy display, with concise explanatory callouts |
| 13 | Workshop experiment | Change a preference, fix conditions, inspect behavior; current preview remains labeled |
| 14 | Evaluation | 24 scenarios × four policies = 96 planned runs; full denominator and meaningful metrics |
| 15 | Implementation / team | Eight phases in one compact table; real current state and team responsibilities |
| 16 | Deliverables / acceptance | Working modes, reproducible AI evidence, source/video/builds; distinct actual extraction scene |
| 17 | References | Project authority and primary algorithm foundations |

The first **two** slides establish what the game is, its premise, the team's idea and the connection to AI coursework. Slides 5–14 carry the academic explanation. Four selected captures support mode context, actual diagnostics, policy configuration and the ending; avoid room galleries or lengthy lore.

## The three core AI slides

Every core slide connects **input → computation → decision → visible behavior**, rather than listing algorithm names.

**Slide 7:** The Sentinel FSM selects its state/target; BFS uses a FIFO frontier and parent reconstruction to route on a unit-cost graph. Fuzzy memberships produce a bounded Sugeno urgency that changes local search duration. The supplied-input example is reproduced from the actual function: at distance 2 and no sight, walk salience 0.25 gives 0.2143; sprint salience 0.75 gives 0.6400. A sound can cause investigation but cannot confirm identity. The planned Tracker uses A* to an evidence-backed last-seen tile, then loses that target when memory expires. Explain `g`, `h`, best-cost records and the stair-heuristic caveat.

**Slide 8:** The Interceptor selects the post with best worst-case defender coverage. In the illustrative tree, evaluating A gives `min(8, 6) = 6`; B's first response is 4, so `beta <= alpha` permits pruning the rest of B. The actor physically travels to A. This is an academic example, not telemetry. NEXUS separately scores/assigns tasks from legitimate events, checks eligibility and retains coverage; it is not the Companion's MCTS controller.

**Slide 9:** The mission FSM chooses the goal; utility can interrupt danger; MCTS selects/expands/rolls out/backpropagates over legal strategic options; A* executes the selected target route. Notes explain UCT, visit/return updates, initial 64-iteration/depth-4 defaults, a proposed most-visits final-choice convention and the no-hidden-world rollout boundary. These are proposed P04 details, not finished code. A sound design or sample future does not guarantee a winning action.

Full names for rehearsal: breadth-first search (BFS), finite-state machine (FSM), Monte Carlo tree search (MCTS), upper confidence bounds applied to trees (UCT), and alpha-beta pruning. A* is pronounced “A star.”

## Visual and copy standards

- Use the **original blue cinematic title background** on slide 1, with a native dark-blue gradient for readable copy. This follows Khalid's latest instruction; the other main slides retain white classroom backgrounds.
- White `#FFFFFF`, ink `#142F44`, blue `#086C9F`, cyan `#19C8E0` and amber `#945D00` connect the academic slides to the game's identity. Native tables use dark-blue headers and pale-blue alternating rows.
- Oxanium headings, Arial body, fixed margins and generous gutters. Character panels, consistent captions, clear decision arrows and original game emblems provide a gamified visual language. Do not place text against a busy part of an image.
- Keep only needed copy visible. Notes hold definitions, pseudocode, assumptions, UCT, sources and explanations of what causes behavior.
- Preserve editable tables, text and native decision diagrams. Keep images proportional, with character crops excluding neighboring sprite poses. Do not flatten academic content into pictures.
- Use the four real captures appropriately: Human entry, real Sentinel diagnostics, Workshop preview and Human extraction. Distinguish these from concept artwork and illustrative tree values.
- The new slide 3 lab diorama is concept illustration, not game evidence. [Artwork provenance and generation prompt](ARTWORK.md) are included in the handoff. The cover continues to use the original game asset.
- The transfer pack includes a 17-page PDF preview for consistent viewing as well as the editable PPTX, source art, selected captures and licensed fonts. Check the editable deck on the actual Windows/classroom PowerPoint setup before presenting.

## Rehearsal and missing inputs

No current speaking duration or exact marking rubric was provided. Rehearse the full 17-slide route, devoting most explanation time to slides 5–11. If a strict three-minute slot is later confirmed, agree a shorter route with the teacher; do not rush detailed formulas across 17 slides or silently add backup pages beyond the maximum.

The team still needs formal names/student IDs, institution/course/section/instructor and proposal date/term. Add only confirmed fields. Preserve [approved scoring](../../planning/SCORING.md), the original four-development-day/eight-phase target and the actual unfinished progress. Refining slides does not start a gameplay phase.
