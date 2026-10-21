# Implementation brief audit and first milestone

Date: 2026-10-21. Developer: Khalid. Source: [owner's complete brief](IMPLEMENTATION_BRIEF.md), [original blueprint](../../../idea/ECHO_HEIST_Complete_V1_Game_Development_Blueprint.pdf), and [visual inspirations](../../../screenshots/README.md).

This is the repository snapshot **before** the milestone implementation. The [current runtime contract](../../architecture/integration/STEALTH_SLICE.md) and [review](../../quality/reports/phase02/presentation/REVIEW.md) record what was subsequently implemented. Missing-system statements below describe the audit baseline.

## Existing behavior

- P01 packaging, locked Python environment, resource/settings storage and deterministic headless checks work.
- P02 continuous movement/sprint, body collision, Echo replay, EMP, melee, Core hold, single lockdown transition, extraction and telegraphed contact capture work.
- The five-zone 64×36 Tiled map validates both routes and cross-link. Camera scrolls, but rooms remain sparse and too much blocked space looks like generic bulkhead.
- Current branch has a new perspective cinematic title, shared glass/gradient rendering, corrected atlas regions, 21 screen captures and a seven-second source clip. These are presentation changes, not proof of stealth AI.
- Last complete suite: 70 cases plus structure/Ruff/mypy. The new branch has not yet been built or published.

## Missing or limited

- Guards remain stationary; observations are own-only. No active sight/hearing/investigation/chase/search, BFS patrol or fuzzy decisions are connected yet.
- Tracker A*, Interceptor minimax, NEXUS, MCTS Companion, Workshop and final approved score are not implemented. No fake metrics or autonomous-success claim is acceptable.
- Hiding, doors, glass breaking and rolling canisters remain P05 by the owner's earlier explicit choice. The new brief specifies the full target but does not justify fabricated interim interactions.
- Audio device initialization exists but there are no music tracks or event cues. Main menu lacks the full target navigation; active HUD uses too much space.
- Furniture currently decorates blocked regions rather than forming a convincing playable room cluster. Every newly introduced physical furnishing must have explicit matching collision/occlusion.

## First implementation milestone: working stealth room cluster

Keep the application and complete Human mission launchable while proving one playable room cluster before expanding the entire facility.

1. Preserve cinematic menu work; simplify gameplay to a compact objective, tools, elapsed time, alert cue and optional compact map, leaving at least 80% of the viewport clear.
2. Furnish a deliberate service/research approach with map-owned collision and clear walkways. Retain both mission routes and extraction direction.
3. Connect one Sentinel to real BFS patrol and observation-driven sight/hearing, identification, investigation, chase, last-known search and recovery. Sensor cones and cue states must represent the same rules used by Simulation.
4. Source CC0 music/effects, record author/source/hash/license, and add context music plus event-driven footstep/tool/capture/lockdown/outcome cues. Provide separate volume controls and silent fallback.
5. Verify fairness, collision/reachability, noise-only knowledge, recoverable chase, tools/capture interrupts, deterministic replay and real win/fail. Capture the actual native scene and rebuild the package.

This begins Khalid's P03 work and a user-authorized presentation/audio follow-up. It does not mark shared P03, Suhita's registry/visual acceptance, or P04-P08 complete. Subsequent milestones extend the furnished facility, finish the required AI algorithms/Companion/Workshop, then complete interactions, reports, audio polish and platform gates.

## Major risks and controls

- Artwork can overhang collision: use authored object footprints, validate bounds and paths, and show the actual scene rather than a mockup.
- AI can accidentally read hidden state: controllers take immutable Observation and memory; only Simulation applies decisions. Sound supplies a cue position, not secret actor coordinates.
- Audio can obscure tactical cues: restrained background levels, bounded SFX channels, clear context transitions and separate volumes.
- New scope can be mistaken for finished V1: preserve phase ownership/status and record what is actually connected, tested and still pending.
