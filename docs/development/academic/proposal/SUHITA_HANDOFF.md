# Suhita: focused AI proposal handoff

Updated **2026-10-22**. Read [STRUCTURE](STRUCTURE.md) first. Khalid's latest request makes AI theory, implementation and causal behavior the priority. Use the **17-slide blue edition**, not the earlier 16- or 22-slide versions. There is no appendix; the complete file stays within the 20-slide maximum.

## Deliverables and theme

- Deck: `output/proposal-deck/final/ECHO_HEIST_AI_Proposal_Blue_Edition.pptx`.
- Pack: `output/proposal-deck/final/ECHO_HEIST_Proposal_Blue_Handoff.zip`, containing the editable deck, a PDF preview, these two guides, artwork provenance, four original screenshots, selected original artwork, Oxanium/OFL files and a checksum manifest.
- Original blue cinematic opening, then white classroom backgrounds, dark readable text, cool blue/cyan accents, character panels and editable academic diagrams/tables. All 17 slides have speaker notes.
- Formal course/team metadata and rehearsal remain team inputs. Check PowerPoint rendering on the Windows/classroom machine after installing fonts.
- Presentation work does not change game code, [phase status](../../tracking/STATUS.md) or approved rules.

## Original nine-slide source audit

The complete original text, embedded images and speaker notes were read. The original Downloads file was read as reference and never overwritten by this task. Its content is a source, not an instruction to undo approved project changes.

| Original slide | Correction | Focused deck location |
| --- | --- | --- |
| 1 / Title | Establish game, premise and coursework link immediately | 1–3 |
| 2 / Overview | Explain controller substitution and shared rules; duration remains an aspiration | 4–5 |
| 3 / Decision model | Distinguish suspicion, confirmed sight, lockdown and capture/abort | 2, 6–7 |
| 4 / Interface | Actual runtime evidence and visibly labeled Workshop preview | 4, 12–13 |
| 5 / Level | Brief facility context, not a room gallery | 1–2, 5 |
| 6 / Agents | Computation and causal behavior; include Companion and implementation state | 7–11 |
| 7 / Companion | FSM/utility, four MCTS stages and permitted-belief rollout model | 6, 9–11 |
| 8 / Lab loop | Separate Companion MCTS and Interceptor minimax; controlled evaluation | 8–9, 13–14 |
| 9 / Feasibility | Current progress, acceptance, delivery and risks; obsolete schedule corrected | 15–16 |

## Images included

| Pack file | Slide | Meaning / boundary |
| --- | --- | --- |
| `screenshots/entry.png` | 4 | Actual Human entry scene, not completed Companion autonomy |
| `screenshots/sentinel-lab.png` | 12 | Real BFS/identification/fuzzy values; captured PATROL/urgency 0 is not an investigation example |
| `screenshots/workshop-preview.png` | 13 | Existing design preview; deployment/profile logic remains pending |
| `screenshots/extraction.png` | 16 | Actual Human ending; not completed Companion/scoring evidence |

Original captures are under `output/cinematic-startup/scenes-final/screens/`; their prior verification is in the [cinematic review](../../quality/reports/cinematic_startup/REVIEW.md). No new native game test is claimed for presentation screenshots. Original facility/character/console/brand artwork is also included for refinement; art is not proof of implemented AI.

## What the presenter must be able to explain

1. **Agent and fairness:** What does this agent actually know? Why are immutable filtered observations different from a debug snapshot? How can a hidden-state test catch cheating?
2. **Sentinel:** How does a FIFO BFS reconstruct its path? Which FSM transition establishes chase? How do fuzzy rule weights change urgency/search duration without creating identity?
3. **Tracker:** What are `g` and `h`? Why can greedy `h` alone fail? Why might raw atlas Manhattan overestimate across stairs? What happens when sighting memory expires?
4. **Interceptor:** Why MAX then MIN? What do leaf utilities mean? In the toy tree, why can the unexplored child of B be skipped once its minimum is already <= A? Why must the actor still travel?
5. **NEXUS:** Which reports may drive a task? How are eligibility/coverage preserved? How does one announced protocol differ from within-run dispatch, and what must reset clear?
6. **Companion:** Which layer handles mission, danger, strategic choice and routing? What is stored in a search node? What happens in each MCTS stage? How do visits/returns and UCT balance exploration? Why is a rollout an estimate rather than hidden-world knowledge?
7. **Validation:** How would you show equal A*/reference costs and equal minimax/alpha-beta values? Which real trace proves MCTS is executing? What must stay fixed for reproducible policy comparisons?

The detailed answers, implementation seams and primary sources are in slide notes. [Artwork provenance](ARTWORK.md) records the supporting illustration and its exact prompt. Do not learn only the acronym list. Trace an observation through memory, algorithm, legal action and resulting behavior.

## Truth boundaries

- Current live AI is one Sentinel subset. Full Tracker, Interceptor, NEXUS, autonomous Companion, saved policies and final scoring remain pending in this snapshot.
- Slide 7's urgency values are reproduced evaluations of the actual pure function using specified inputs, not a fabricated captured encounter.
- Slide 8's pruning values are illustrative. They must remain labeled; they are not search telemetry from the unfinished Interceptor.
- Slide 9 describes proposed implementation details. Its compact belief/rollout model can be wrong. It is not a learned network or a proof of optimal POMDP planning.
- Internal planning reward and approved player score serve different purposes. Keep [approved scoring](../../planning/SCORING.md) unchanged: 50 extraction, stealth up to 40 minus 12 per distinct confirmed encounter, pace up to 10; failure 0/F, no direct tool penalty.
- 24 scenarios × four policies = 96 **planned** runs. No completed AI win rates, policy rankings or speedups are supplied.
- P01/P02 complete, P03 active, early P05 subset only; later gates remain open. Four development days was the original target, not an achieved schedule or a new countdown.
- Human vs AI changes who controls the intruder. AI vs AI replaces it with an autonomous Companion; it is not a cooperative Human-plus-robot mode.

## Refinement checklist

1. Install the included Oxanium fonts; retain Arial body text and the font license.
2. Fill confirmed course/team metadata and obtain the speaking limit/rubric.
3. Rehearse the three core AI slides with the causal explanations above. Reduce redundant copy before shrinking text.
4. Keep the 17-slide structure, at most 20 if a necessary addition is agreed. Preserve story/coursework on slides 1–2. Do not restore separate room galleries or a six-slide appendix.
5. Check fonts, spacing, diagrams, captions and projector contrast in PowerPoint on the actual Windows/classroom machine. No native PowerPoint inspection is claimed by the exported artifact checks.
6. Update planned/current labels only when implementation evidence exists. Do not change game rules or start game phases for a presentation edit.

## Prompt for your presentation agent

```text
I'm Suhita. Refine the focused ECHO HEIST AI lab proposal supplied in this pack.
Read STRUCTURE.md, SUHITA_HANDOFF.md and every slide and its speaker notes.

Keep 17 slides total, never more than 20. Open with the game, story and its
connection to AI coursework on slides 1–2. Prioritize academic understanding.
Preserve the three core AI slides connecting inputs, algorithm/data structures,
decision and visible character behavior. Explain BFS/FSM/fuzzy, Tracker A*,
Interceptor minimax/alpha-beta, NEXUS dispatch, and Companion utility/MCTS/A*.
Keep the formal agent model, fair architecture, correctness and experiment plan.

Use the original blue cinematic opening, then white classroom backgrounds,
cool blue/cyan components, dark readable copy and polished game illustrations.
Keep scenes brief. Preserve editable content and the current/preview/illustrative
labels. Fill only confirmed metadata. Improve clarity and rehearse the narrative.
Do not fabricate results, change gameplay/scoring or begin game implementation.
```

## Primary sources

- [Russell and Norvig, AIMA contents](https://aima.cs.berkeley.edu/contents.html): agents, search, adversarial decisions and uncertainty.
- [Hart, Nilsson and Raphael (1968), A*](https://ai.stanford.edu/~nilsson/OnlinePubs-Nils/PublishedPapers/astar.pdf): heuristic minimum-cost paths.
- [Zadeh (1965), Fuzzy Sets](https://doi.org/10.1016/S0019-9958(65)90241-X): graded membership; specific urgency rules come from the project.
- [Kocsis and Szepesvari (2006), UCT](https://aima.cs.berkeley.edu/~russell/classes/cs294/s11/readings/Kocsis%2BSzepesvari:2006.pdf): Monte Carlo planning foundation; no global stealth optimality claim.
