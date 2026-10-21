# ECHO HEIST: The Core Rebellion — Full Gameplay, Environment and UI Implementation Brief

## Your role and references

You are the lead game engineer, technical artist, level designer, and UI developer for **ECHO HEIST: The Core Rebellion — Chapter One**.

We are building a polished, playable **2D top-down sci-fi stealth game** using Python and pygame-ce. Our targets are native Windows and macOS desktop builds, with a free release on itch.io.

You have two primary references:

1. **ECHO HEIST Complete V1 Development Blueprint (19-page PDF)** — the authoritative source for our approved story, game mechanics, AI algorithms, architecture, mission logic, and completion requirements.
2. **Attached gameplay/UI screenshot** — a visual reference for the atmosphere, overall game presentation, facility design, room organization, and desktop interface.

The screenshot contains concept art, not an existing game. Use the game window in the screenshot as inspiration, not the surrounding ChatGPT/image-gallery interface.

**Your task is to implement this experience in the actual game, not generate mockup screenshots.**

First inspect the existing repository, determine what is already implemented, identify gaps, and improve the current project incrementally. Do not overwrite working systems or unnecessarily rebuild the architecture.

Where the visual concept conflicts with the approved blueprint, follow the blueprint. Do not add unsupported gameplay mechanics merely because an AI-generated reference image depicts them.

---

## 1. Visual direction

The finished game should look like a modern, atmospheric indie sci-fi stealth game.

**Visual style**
- True 2D top-down / near-orthographic perspective, not an isometric 3D game.
- Detailed neo-industrial research facility with a slightly pixel-art-inspired appearance.
- Dark graphite, charcoal, navy, and blue-gray structural materials.
- Cyan and teal for technology, terminals, friendly indicators, and the energy core.
- Amber for caution, guard vision cones, and machinery lights.
- Red for confirmed security alerts, dangerous states, and the mandatory lockdown.
- Subtle reflections, ambient shadows, wall-edge shading, illuminated panels, animated equipment, and restrained glow.
- Cohesive sprite scale, proportions, and lighting direction across every room.

The atmosphere should feel mysterious, expensive, restricted, and technologically advanced.

Avoid making the world look like a simple maze drawn from rectangles. Every area should have architecture and equipment consistent with its actual purpose.

Also avoid excessive bloom, visual noise, oversized labels, and too many glowing elements. Gameplay must remain readable.

### Critical requirement: a large, believable facility

The map must feel significantly larger than one desktop screen.

Design one connected research facility with multiple substantial rooms, long corridors, service areas, distinct entrances, and meaningful alternative routes.

The camera follows the operative or companion and reveals the world as they move. Players should not see the entire facility on one screen during ordinary gameplay.

The mission briefing may show a schematic overview of the whole facility.

Use a tile-based world with a configurable logical tile size (initially 32 px if appropriate). The existing blueprint suggests approximately 80 × 56 tiles as a starting point, but adjust dimensions and room proportions if needed for a convincing 10–20-minute mission.

Use camera scrolling, proper collision boundaries, occlusion, and object rendering layers.

---

## 2. Facility architecture and interior design

The facility has **five interconnected gameplay zones**:

Entry / Extraction → Service Wing → Security Control or Research Floor → Core Chamber.

Both middle branches reconnect, and at least one alternate cross-link provides meaningful route choices.

Do not scatter decorative objects randomly. Arrange everything like a functioning research facility.

### Zone A — Entry and Extraction

Create a controlled entrance consisting of an airlock, reception/security checkpoint, and connected loading or logistics area.

Include:
- Reinforced airlock doors with access panels.
- Security checkpoint desk and monitor.
- Storage lockers, equipment cabinets, and wall signage.
- A few cargo trolleys, crates, and utility containers.
- Clear floor markings guiding staff movement.
- One recognizable extraction point that becomes active when the core is retrieved.

Initially the area should feel relatively calm and help the player understand movement and stealth.

The same location becomes the final extraction destination during lockdown.

### Zone B — Service Wing

This is the industrial maintenance area.

Include:
- Maintenance workbenches and tool racks.
- Electrical panels and transformers.
- Pipes, conduits, ventilation machinery, generators, and coolant equipment.
- Storage shelves, movable-looking cargo crates, and maintenance carts.
- Narrow maintenance corridors connected to larger service passages.
- A small number of clearly marked hiding recesses or cabinets.
- An interactive metal canister that rolls or falls and creates noise.

Use a warmer industrial lighting style, with amber work lights and darker corners.

This zone introduces environmental noise, cover, and guard investigation.

### Zone C — Security Control

This should look like a realistic facility security headquarters.

Include:
- A main control desk with multiple surveillance displays.
- Operator chairs in front of consoles.
- Wall-mounted camera feeds or facility status screens.
- Communications terminals.
- Server and recording cabinets.
- A few lockers, access-control panels, and secure doors.
- Glass partitions separating control rooms from monitored corridors.

Security Control should feature broad, exposed sightlines and meaningful chokepoints.

The Interceptor can defend the junctions around this zone. These must be actual reachable positions, not instant-teleport destinations.

### Zone D — Research Floor

This is one of the most visually important environments.

Divide it into logically arranged laboratory rooms rather than one huge room filled with miscellaneous objects.

Possible connected areas:

**Main research lab**
- Research benches arranged in rows with walkable space between them.
- Computers, microscopes, testing instruments, and equipment racks.
- Rolling laboratory chairs tucked near desks.
- Storage cupboards, sample cabinets, and drawers.
- Wall terminals and small instrument displays.

**Testing and containment room**
- Transparent specimen or experimental containment chambers.
- Instrument consoles beside the chambers.
- Clearly marked hazard areas.
- Reinforced glass partitions and access doors.

**Analysis and observation room**
- Workstations facing scientific monitoring screens.
- A central analysis table or instrument station.
- Office chairs, document trays, storage and supporting equipment.
- Glass windows overlooking another room.

**Research storage / secondary corridor**
- Equipment cabinets, racks, sample storage, and a breakable glass equipment rack.
- Cover and alternative passages.

All furniture must be arranged naturally. Chairs belong with desks or instrument stations; monitors belong on workstations; equipment should have plausible access paths.

Do not obstruct walkways with random furniture.

The Research Floor is a potentially safer but longer route than Security Control, with more cover and occasional noise hazards.

### Zone E — Energy Core Chamber

This is the dramatic centerpiece of Chapter One.

Design a substantial circular or polygonal containment room, visually different from the rest of the facility.

Include:
- A large central reactor/containment structure.
- Glowing cyan experimental energy core on an interactable pedestal.
- Concentric machinery rings or containment equipment.
- Thick power cables and technical conduits connected to surrounding walls.
- Control terminals and diagnostic screens.
- Hazard markings and reinforced structural barriers.
- Space for guarded approaches and more than one escape direction.

The core should feel important, powerful, and dangerous.

Create a distinctive core idle animation: subtle light pulses, rotating illuminated rings, and restrained electrical effects.

**Once the core is stolen, the pedestal must visibly become empty.** Do not leave the energy core appearing fully intact as if nothing happened.

The theft triggers the global lockdown transition.

---

## 3. Design rules for every room

Every room must have a clear purpose and believable structure.

Follow these constraints:

- Keep primary walkways wide enough for natural movement and readable robot pursuit.
- Put large furniture against appropriate walls or in purposeful work clusters.
- Leave enough clearance around chairs, lab benches, machinery, and doors.
- Use glass partitions selectively to connect visible rooms without making every room completely exposed.
- Use wall-mounted lighting, access terminals, floor markings, hazard lines, and equipment details for environmental storytelling.
- Furnish each zone differently; do not reuse the same room arrangement everywhere.
- Distinguish physical obstacles, visual decoration, vision blockers, and interactable objects in the map data.
- Furniture that should block movement must actually have collision.
- Tall opaque objects should affect line of sight consistently.
- Decorative objects must not interfere with pathfinding unless explicitly marked as obstacles.
- Avoid creating accidental unreachable tiles or trapping the AI behind props.

Prioritize believable interiors and navigation clarity over filling every empty tile.

The player should feel that they are infiltrating a functioning facility, not walking through a decorative maze.

---

## 4. Actual gameplay experience

The game must support the complete mission:

**Enter → Infiltrate → Steal Core → Lockdown → Extract.**

The operative must move through the environment, observe enemies, take cover, avoid detection, and choose between different routes.

Implement proper player animation and interaction feedback.

### Controls

Use the blueprint's default controls, keeping them configurable:

- WASD / arrows — Movement.
- Shift — Sprint, increasing footstep noise.
- E — Interact with doors, hiding spots, objects, and the core.
- Q — Deploy Echo hologram.
- F — Activate EMP.
- Space — Emergency melee strike.
- Tab — Objective summary.
- Esc — Pause.
- F3 — Optional AI Lab View.

### Stealth and detection

Guards have visible directional vision cones.

Walls and appropriate furniture block sight.

A guard that hears a sound investigates its position without automatically knowing the operative's location.

Detection should progress through suspicion, visual spotting, confirmed discovery, pursuit, and searching.

Confirmed discovery is recoverable. Being chased should not instantly end the game.

After losing visual contact, guards search the last known location rather than tracking the player magically.

Capture requires a short visible capture wind-up. A completed capture ends the run.

There is no health bar, no combat damage system, no permanent robot elimination, and no limited lives.

### Player abilities

**Echo:** Approximately three charges. Creates a cyan holographic decoy retracing around 2.5 seconds of recent movement, potentially distracting security.

**EMP:** One charge. Briefly disables nearby robots, but emits a detectable electrical disturbance.

**Emergency melee:** A short-range stun against one adjacent robot. Loud and dangerous, intended only to create an escape opportunity.

**Hiding:** Explicit hiding locations, with detection rules that account for whether a guard saw the operative enter.

Use the blueprint for the precise rule contracts and initial balancing values.

---

## 5. Intelligent security robots

The facility should normally contain roughly five or six physical security robots, in addition to the nonphysical NEXUS supervisor.

Use visually distinct silhouettes and recognizable behavior.

### Sentinel — BFS + FSM + Fuzzy Logic

A slower patrol/security robot.

- Moves along assigned patrol routes using BFS.
- Detects and investigates local visual and audible disturbances.
- Uses fuzzy inference to evaluate uncertain cues and investigation urgency.
- Changes between patrol, suspicious, investigate, chase/search, and return states.
- Never learns the operative's hidden position from an unrelated sound.

### Tracker — Heuristic A* + FSM + Memory

A more mobile pursuit robot.

- Uses A* with an appropriate Manhattan heuristic for navigation.
- Pursues actual sightings and permitted security reports.
- Remembers the last confirmed position for a limited time.
- Searches plausible surrounding locations after losing sight.
- Can choose an incorrect search direction because its information is incomplete.

### Interceptor — Minimax + Alpha-Beta Pruning

A strategic defensive robot.

- Evaluates probable intruder routes and defensive chokepoints.
- Uses bounded minimax search with alpha-beta pruning on an abstract route graph.
- Physically moves to the chosen interception location.
- May predict the wrong route.
- Must not read secret future movements or teleport.

### NEXUS — Rule-Based and Utility AI

A nonphysical facility supervisory intelligence.

- Receives legitimate guard reports and security events.
- Coordinates investigation and defensive assignments.
- Controls alarm states and the mandatory lockdown.
- Prioritizes confirmed threats over unrelated events.
- Can apply a limited, announced countermeasure across later attempts based on observed tactics.

Make their algorithms functional and testable, not decorative labels in the interface.

---

## 6. Autonomous Companion — AI vs AI gameplay

Both modes must be accessible immediately:

1. **Human Infiltration** — The player controls the operative.
2. **Companion Infiltration** — An autonomous AI robot attempts the same mission against NEXUS and its defenders.

The companion may succeed or fail on its first-ever deployment.

It must not depend on a human playthrough, manually scripted fixed route, or privileged enemy coordinates.

Its intelligence combines:

- FSM for mission phases and high-level behavior.
- Heuristic A* for risk-aware navigation.
- Monte Carlo Tree Search (MCTS) for meaningful tactical choices at junctions or threat events.
- Utility AI for immediate priorities, emergencies, and gadget decisions.
- A static knowledge base plus dynamic observation-based memory.

The Workshop provides Ghost, Balanced, and Rush presets and editable settings for navigation, guard reaction, emergency response, and risk tolerance.

After each run, generate a real report with observed threats, important decisions, failure or success reason, resources used, and relevant algorithm data.

This is player-guided AI configuration and testing, not automatic neural-network training.

Human and companion modes must share the same game world, guard behaviors, interaction rules, and win/loss conditions.

---

## 7. Cleaner gameplay UI

The previous visual references sometimes contain too many large panels and buttons. Do not reproduce that clutter.

The new design should be clean, restrained, and easy to understand.

### Main menu

Show:
- ECHO HEIST title and subtitle.
- Human Infiltration.
- Companion Infiltration.
- AI Workshop.
- Mission Report.
- Settings.
- Quit.

Use a simple vertical menu, one clearly highlighted selection, and a detailed facility scene behind it.

Do not wrap every menu item inside multiple decorative boxes.

### Mission briefing

Show:
- Concise storyline and objective.
- Mode selection.
- Companion preset selection only where applicable.
- An attractive full-facility schematic or preview.
- One obvious Launch action.

Do not add unsupported shops, upgrades, access-keycard quests, or mission rewards.

### In-game HUD

Keep roughly 80% or more of the game viewport visually unobstructed.

Display only:
- Current primary objective.
- Echo and EMP charges, plus melee availability.
- Elapsed time.
- Current suspicion/alert indicator.
- Optional compact minimap.

Avoid displaying the game's giant logo, long mission descriptions, and large side menus during active gameplay.

Let the environment remain the focus.

### AI vs AI spectator screen

Keep the playable world large.

Provide a compact, optionally collapsible Lab View showing:
- Companion FSM state and current action.
- Observed threat information.
- MCTS chosen action, visit counts, and scores.
- Current A* route.
- Relevant enemy states.
- Pause and simulation-speed controls.

Do not present a false AI explanation or fabricated metrics.

### Results screens

Provide:
- Mission Complete or Mission Failed.
- Actual outcome, elapsed time, detections and ability usage.
- Success rank or failure cause.
- Important companion decisions when applicable.
- Retry, Workshop, and Main Menu navigation.

Use the Replication Seed epilogue only after a valid Chapter One victory.

---

## 8. Lockdown cinematic transition

The core theft must feel like the turning point of the heist.

On successful core interaction:

1. Remove the energy core from its pedestal.
2. Mark the operative as carrying the core.
3. Transition the global game state to LOCKDOWN exactly once.
4. Play a brief dramatic audio/visual alarm transition.
5. Switch security lighting from predominantly cyan/amber to red emergency accents.
6. Show NEXUS announcing the critical breach.
7. Change guards' tactical assignments and extraction pressure.
8. Update the objective to **Escape to Extraction**.

The world must remain navigable, with legitimate alternate escape routes.

Do not create an arbitrary countdown or shut every exit.

Lockdown should increase tension through security behavior and environmental presentation, not unfair automatic defeat.

---

## 9. Rendering and technical implementation

Continue using the approved Python + pygame-ce architecture.

Use Tiled JSON or a compatible layered map format.

Recommended map/render layers:

1. Ground and floor tiles.
2. Floor markings and low decoration.
3. Structural walls and partitions.
4. Room furniture and collision objects.
5. Interactive objects.
6. Characters and robots.
7. Foreground occluders.
8. Lighting and atmospheric effects.
9. Guard vision cones and gameplay indicators.
10. Screen-space HUD.

Handle sprite ordering and occlusion correctly.

Use the existing headless simulation for actual game-state logic, rather than placing gameplay logic inside rendering routines.

Keep the authoritative WorldState separate from each AI's filtered Observation.

Use a fixed-step simulation, deterministic random seeds, and independent rendering.

For the visual layer:
- Create reusable tilesets and sprite atlases.
- Support directional character animation.
- Use glow/lighting selectively and efficiently.
- Cache static map surfaces and expensive visual effects where possible.
- Avoid recreating large texture surfaces every frame.
- Smoothly follow the operative/companion with a camera.
- Avoid camera jitter or character sliding.
- Maintain reliable frame pacing.

Design primarily for a MacBook Air-class desktop, with a 16:10-friendly window layout. Support practical windowed resolutions and fullscreen scaling without clipped controls or stretched gameplay.

Aim for responsive 60 FPS rendering where achievable, with a deterministic simulation rate as specified by the blueprint.

### Asset policy

Use original, properly licensed, or procedurally created assets.

Do not simply place the supplied reference screenshot as the game background.

The environment must be assembled from actual room geometry, tiles, sprites, and interactive objects so guards and operatives can move correctly.

If the current assets cannot achieve the target visual quality, improve the asset pipeline or identify suitable CC0/permissively licensed assets with attribution.

Prioritize consistent, high-quality visual assets over a large mixture of unrelated asset packs.

---

## 10. Development process

Do not attempt to implement every remaining feature simultaneously.

**First**, inspect the repository and provide a concise status assessment: existing systems, missing systems, visual limitations, and major risks.

**Second**, establish a complete playable vertical slice using one believable room cluster, working collision, camera, one guard, and the minimal HUD. This must demonstrate the intended art quality and stealth feel.

**Third**, extend that into the full five-zone facility, with purposeful room interiors, distinct route tradeoffs, and both mission directions.

**Fourth**, integrate and validate all enemy algorithms, autonomous companion behavior, tools, lockdown, result flow, and Workshop.

**Fifth**, polish animation, audio, lighting, UI, performance, packaging, and academic instrumentation.

At every stage, keep the game launchable.

Prefer implementing tested, reusable systems over one-off visual tricks.

Do not claim a feature works until it can be observed in an actual running game.

If a visual effect or mechanic is too expensive for the project timeline, propose a simpler implementation that preserves gameplay quality.

---

## 11. Required acceptance criteria

The task is complete only when:

- The application runs as a real desktop game, not a screenshot viewer.
- The facility feels large, connected, and believable.
- Rooms contain logically placed furniture and equipment appropriate to their purposes.
- Every visible physical obstacle has consistent collision behavior.
- Players can traverse the entire mission and explore both major routes.
- Guard sight, hearing, investigation, chase, and capture function correctly.
- Echo, EMP, and emergency melee affect real simulation behavior.
- Stealing the core visibly changes both the world and security state.
- A player can genuinely win or fail.
- The companion can independently win or fail in AI vs AI mode.
- Heuristic A*, BFS, fuzzy logic, minimax/alpha-beta, and MCTS are genuinely used where specified.
- The Workshop changes companion decisions measurably.
- UI is clean and readable at desktop resolutions.
- The AI Lab View and result reports show actual game events and algorithm values.
- The code remains modular, testable, and suitable for Windows/macOS packaging.

## Final quality target

Imagine a player opening ECHO HEIST on a MacBook.

They see a clean, cinematic menu over a convincing research facility.

They choose Human Infiltration or AI vs AI.

They enter a large, interconnected complex with realistic labs, maintenance areas, security control rooms, and a dramatic energy core chamber.

Security robots patrol, investigate, remember, predict, and react intelligently.

The player or autonomous companion must plan around these behaviors.

When the core is stolen, the entire atmosphere changes and the escape becomes the climax.

Finally, the game reports the result and allows meaningful experimentation through the AI Workshop.

**Build toward that complete playable experience. Prioritize believable environments, intelligent interactions, a strong stealth atmosphere, and clean UI over superficial visual complexity.**

Begin by auditing the current repository and outlining the first concrete implementation milestone. Then start implementing and testing it.