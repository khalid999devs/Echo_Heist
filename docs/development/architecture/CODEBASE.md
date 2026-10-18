# Proposed codebase architecture

Blueprint basis: PDF pp. 16-17. This design is planned; none of these modules exists yet.

Required: follow [code rules](../workflow/CODE_RULES.md), with no authored file over 1,000 lines and no maintained directory over six direct files. The [phase/workload plan](../planning/WORKLOAD.md) assigns both developers actual frontend/backend work; package ownership does not mean one developer owns every file in a layer.

## Package layout

Use one installable `src` package, preserving the PDF's functional boundaries inside `echo_heist`:

```text
AGENTS.md                      # agent discovery; detailed instructions under docs/development
README.md                      # player/developer entry instructions
pyproject.toml                  # dependencies, optional dev/build tools, entry point, checks
uv.lock                        # generated dependency lock after compatibility verification
.gitignore                     # environments, caches, generated artifacts and local state
LICENSE                        # owner-selected source license before public release
src/echo_heist/
  __init__.py
  __main__.py                  # python -m echo_heist
  app.py                       # scene orchestration and application lifecycle
  core/                        # simulation, entities, actions, events, observations, mission, scoring
  level/                       # typed map model, JSON loader/validator, geometry, navigation
  ai/                          # controllers, beliefs, BFS/A*, fuzzy, minimax, MCTS, NEXUS
  workshop/                    # policy models, presets, policy-to-weight translation
  ui/                          # pygame input, scenes, HUD, camera, rendering, audio
  infrastructure/              # resource lookup, writable paths, JSON files, logs
  resources/
    assets/                    # sprites, fonts, audio and effects
    data/                      # Tiled JSON, balance config, dialogue and presets
tests/
  conftest.py                   # only genuinely shared fixtures
  unit/                        # grouped core/navigation/intelligence/policies subdirectories
  integration/                 # grouped mission/perception/persistence/replay subdirectories
  smoke/                       # grouped useful desktop/resource checks
  fixtures/                    # grouped maps/tactics/profiles
scripts/                       # grouped checks/experiments/packaging helpers
packaging/                     # PyInstaller spec and platform metadata
.github/workflows/             # checks and native artifact builds
docs/idea/                     # preserved design source
docs/development/              # grouped engineering and tracking documents
```

Keep assets/data inside the package so source, wheel and frozen builds resolve the same resource tree. Tiled editor/source files may live under an asset-authoring directory if later needed; only validated runtime exports enter resources. Do not create dozens of empty modules in the first batch. Split modules as working systems grow.

## Responsibility groups and file budgets

The root has exactly six reserved maintained files listed above. Avoid additional root dot-config files; use the existing configuration and meaningful subdirectories. Package `__init__.py` counts toward each directory's limit. These are planned groupings, not an instruction to create empty files:

| Area | Meaningful subgroups as needed | Main responsibility |
| --- | --- | --- |
| core | contracts, simulation, perception, abilities, environment, scoring | Simulation-owned data and deterministic rules |
| level | model, io | Shared geometry/types; Suhita's typed loader/validation/registries |
| ai | navigation, guards, inference, planning, companion, director | Khalid's strategy/algorithms; Suhita's director/protocol systems |
| ui | input, diagnostics, scenes, render, audio | Khalid's input/presenters; Suhita's scene/render/audio architecture |
| ui/scenes | frontdoor, deployment, mission, outcome | Prevent menus/Workshop/heist/results/epilogue exceeding one flat folder |
| infrastructure | resources, persistence, telemetry | Explicit IO adapters, no import-time side effects |
| tests | unit, integration, smoke, fixtures, each further grouped | Necessary behavior evidence in one master tree |

For example, keep simulation engine/world/mission/motion/capture plus an initializer within six files; put scoring in its own group instead of adding a seventh sibling. Split MCTS/tree/rollout code by actual responsibility when needed, not to generate a file per method. Apply the same rule to maps, assets and reports by grouping logical families. Large generated artifacts remain outside the maintained source tree.

Khalid establishes the actual contract/import map in P01. Both agents must read that handoff and claim exact files before editing; the phase's owner boundaries guide parallel work. All test-only code/fixtures remain under `tests/`, never adjacent to source modules.

## Ownership and imports

- `core` owns authoritative world state and the only mutation API: `Simulation.step(actions)`.
- Shared immutable action/observation/result records live in small contract modules in `core`; importing them must not expose a Simulation instance.
- `level` produces validated map/geometry values; it has no pygame or UI imports.
- `ai` imports contracts and pure path/search utilities. It cannot import Simulation implementation/state storage or persistence readers containing privileged run state.
- `workshop` maps validated policy fields into controller parameters; it cannot alter global physics, map geometry or guard sensing.
- `ui` converts input into legal action requests and renders a read-only presentation snapshot. It never resolves capture, awards points or decrements tools.
- `infrastructure` handles IO through explicit calls; it performs no file writes at import time.
- `app` is the composition root: creates services, selects controllers, changes scenes and manages lifecycle.

Use ordinary dataclasses/enums and short functions. Immutable observations must also contain immutable nested values, not mutable entities behind a frozen outer wrapper. Pass RNG and configuration explicitly. Avoid service locators, global mutable state, import-time pygame initialization and circular subsystem dependencies.

## One authoritative runtime

The proposed simulation rate is 30 Hz; presentation targets 60 FPS. Keep fixed-step accumulation outside core, bound catch-up work, and interpolate only presentation. Pause stops simulation ticks and duration-based mechanics. Do not derive gameplay from render FPS, audio playback time or wall-clock search cutoffs.

At each tick:

1. Read actions issued from the last permitted observations; use stable actor/action ordering.
2. Validate resources/range/cooldowns, resolve continuous movement and collision.
3. Resolve interactions and tools; emit once-only events, including core theft.
4. Calculate sight/hearing and update permitted memories.
5. Update NEXUS/guard decisions and capture wind-ups for subsequent execution/resolution.
6. Evaluate mission terminals and score; commit the state and canonical event stream.
7. Deliver new filtered observations and a presentation snapshot; render/audio consume committed events.

AI controllers return actions; they do not move themselves. UI scene navigation is separate from mission phase and guard FSM. Immediate EMP/stun interrupts are resolved before the affected guard's capture resolution. Resolve any same-tick win/capture tie explicitly and test it; proposed rule: completed valid capture takes precedence over extraction in that tick.

The scoring module implements the user's [approved completion/stealth/pace rules](../planning/SCORING.md). Use committed simulation events and integer tick durations, aggregate overlapping defender sightings into one encounter, and produce one immutable result breakdown. Tool usage and the required core alarm do not directly reduce points.

## Continuous motion, discrete planning

Human movement supports normalized diagonal input. Navigation algorithms use four-neighbor tile centers without corner cutting. These coexist by representing physical positions with consistent sub-tile units and mapping path nodes to movement directions. All controllers obey the same speed, collision and action rules. Test diagonal human movement, sprint substeps and guard route following at door edges.

Use stable integer ticks for durations and stable entity IDs for ties. Prefer fixed-point position units if needed to make cross-platform action replay stable. Initially guarantee repeatability for the same build/config/runtime; require Windows/macOS replay comparison before making a broader cross-platform determinism claim.

## Fairness by construction

Separate three views:

1. Authoritative state: Simulation only.
2. Per-agent observations: own status, permitted static map, actual sight/hearing, legitimate reports with age.
3. Presentation/debug view: may show extra diagnostics only through a separate non-controller path, clearly marked in Lab View.

A Companion planner receives only its belief state and policy. Its rollout model samples unknown guard hypotheses from permitted evidence. It never clones the hidden real world. NEXUS receives allowed security reports and the public core alarm, never the Companion's policy file or true unseen position.

Test information noninterference: modify unseen guard positions while preserving the supplied observation and RNG state; controller output/search diagnostics must remain identical. Also reject forbidden imports and mutable world references. Static map geometry is allowed knowledge; hidden live door/entity changes require observation or an explicit public facility event.

## Performance and recovery

Cache paths using occupancy revision and policy/risk context; invalidate on meaningful changes. Trigger minimax/MCTS on new evidence, junctions and objective changes. Start with bounded node/iteration budgets, not machine-speed timeouts. If the combined decision work exceeds the tick budget, spread a fixed number of search iterations over ticks and keep a legal interim action; cancellation/restart must be deterministic.

Measure simulation p95/p99 and strategic-search spikes on named primary machines. The 30 Hz simulation gives roughly 33 ms per tick; choose practical headroom from measurements. FPS, memory and package sizes are recorded rather than guessed. Handle no-path/invalid-action cases with legal wait/retreat and replanning; surface actionable diagnostics for invalid map/config/assets instead of hanging.
