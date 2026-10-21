# First stealth slice: implemented runtime contracts

2026-10-21, Khalid. User-directed extension of the accepted P02 baseline. This is a verified subset of P03-K1/K2/K3, not completion of shared P03. The [implementation brief](../../planning/references/IMPLEMENTATION_BRIEF.md) remains the full target.

Subsequent environment revision: [furnished facility/movement contracts](FACILITY_DENSITY.md) supersede this checkpoint's nine-object layout, coordinates, speeds and text-only Tab guide. The remaining AI ownership and filtered-observation boundaries below still apply. The counts/evidence below describe the earlier checkpoint.

## Composition and ownership

`HeistSession` activates the Sentinel nearest Entry (`guard-service`) from the existing validated patrol route. Three other P02 posts retain physical contact capture; their advanced algorithms are pending. `GameFlow(security_enabled=False)` is an explicit legacy diagnostic fixture; the shipped default is True. Suhita's P03 registry/dynamic revision adapter is still open. Do not build a second importer around this temporary composition choice.

`Simulation(..., security: SecuritySpec | None = None)` owns guard memory and all mutation. Its optional parameter preserves anchorless/P02 fixtures. External intents for an internally controlled guard reject with `simulation_controlled_actor`; they cannot override or double-step it.

`ai/guards/sentinel.decide(Observation, GuardPatrol, SensorRules, GuardMemory)` returns frozen `GuardDecision(action, memory, facing)`. It imports contracts and pure navigation only, never Simulation or privileged presentation. The Simulation validates that any fresh remembered intruder tile/tick was actually in that guard's Observation. Immutable observations contain filtered visible entities, anonymous visual motion, heard cue origins and expiring source reports. Hearing never identifies a hidden actor.

## Sensors, decisions and events

`core/perception/sensors.py` supplies cone/range tests, conservative opaque/corner sight rays and bounded four-neighbor acoustic reach. Glass blocks movement/sound but allows vision according to map tags. The renderer uses the same sight-ray function; its sampled fan is a visual aid, not authoritative collision.

`resources/data/gameplay/security.json` supplies sensor, identity, memory/search/report and patrol-pause tick values. `SensorRules` validates exact fields, bounds and units. GameRules continues to own speeds, body size, tools and capture timings.

The Sentinel physically follows deterministic BFS routes. States: PATROL, SPOTTED, INVESTIGATE, CHASE, SEARCH, RETURN. Near/normal visual identification have different configured thresholds; confirmed sight alone creates a SIGHTING report. Noise/Echo motion can attract investigation without identity. Lost contact follows the last actually seen tile, searches briefly, then returns. Bounded Sugeno fuzzy urgency changes investigation/search behavior; no secret player coordinates or invented A*/MCTS values are used.

SIGHTING_CONFIRMED and REPORT_SENT retain the original observation tick. Reports expire from that tick; repeated delivery cannot refresh it. POLICY_DECISION includes actual BFS expansion count and fuzzy urgency when state/path goal changes. Capture requires confirmed current contact for the active Sentinel, retains the normal wind-up, and remains interruptible by escape/EMP/melee. Tools resolve before capture completion.

The privileged `PresentationSnapshot.guards` contains frozen GuardView values, separate from controller observations. F3 shows these actual values. Canonical fingerprint schema is now 3 and includes security rules, memory, facing, filtered sensor caches and reports, with sorted set serialization. Replay comparisons must use the same code/map/config, not compare old schema hashes.

## Physical room data and presentation

The Tiled `markers` layer accepts optional rectangular `Furniture` objects with whole-tile width/height, a known style and explicit boolean movement/vision/sound flags. Footprints cannot overlap solid geometry, escape bounds or block required routes/patrols. Parsing is independent of layer order. Static MapObject properties expose dimensions/style; renderer and collision use those exact footprints. No pixels infer geometry. Nine furnishings now occupy Entry/Service rooms; larger facility interiors remain a later milestone.

The normal HUD panels occupy about 10.5% of the 1280×720 canvas; notices/progress remain below 20% total coverage. ObjectiveView adds typed Echo/EMP counts and core ownership. The minimap removes the Core marker after theft. Lockdown changes real mission state, music, objective and emergency lighting; the socket becomes empty. P05 doors/glass/hiding/canisters remain deferred by the owner's explicit choice.

`ui/audio/AudioDirector` consumes only immutable AudioFrame values and committed events. Five context tracks and eleven SFX are bundled with CC0 notices/hashes; [audio sources and routing](../../assets/AUDIO.md) record provenance. The native bootstrap applies persisted independent music/effect volumes, mute/device fallback, reduced flashing and fullscreen. Playback cannot affect Simulation. Cocoa screenshot export explicitly writes RGB to avoid unused display alpha.

## Verification and next integration

89 focused cases, structure/Ruff/strict types pass. Tests cover BFS shortest paths, cone/glass/corner/acoustic rules, cue-only investigation, report expiry, capture interruption, paired hidden-position invariance, replay hashes, furniture validation and a real lower-route win with the live Sentinel. The native screenshot driver additionally completes the upper route using a real EMP and routes around the still-solid disabled body.

See the [current review](../../quality/reports/phase02/presentation/REVIEW.md) and [runnable handoff](../../tracking/handoffs/khalid/day_02/STEALTH_SLICE.md) for actual native build/CI evidence. Remaining P03 work includes Tracker A*, the shared registry/revision contract, complete guard roster/cues and hiding integration. Companion/MCTS/minimax/NEXUS, Workshop/scoring and P05 environment mechanics are still pending; do not claim full V1 or fill those screens with fake output.
