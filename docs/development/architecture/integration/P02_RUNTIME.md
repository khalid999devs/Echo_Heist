# P02 runtime integration: Khalid -> Suhita

Owner: Khalid; work/khalid-p02. Status: P02-K1/K2 DONE; full P02 awaits Suhita integration. This narrow contract was published before implementation to expose shared-file changes. The [actual P02 handoff](../../tracking/handoffs/khalid/day_01/P02.md) now contains exact signatures, migration notes and verification.

## Ownership and composition

Khalid owns core simulation/initial abilities, `ui/input/human.py`, `ui/presenters/objective.py` and an explicitly diagnostic `diagnostics/human_preview.py`. He does not edit app.py/bootstrap.py, Suhita's map loader/resources or scenes/rendering. Suhita connects these modules in her actual heist scene and composition root after integration. Missing scene work does not authorize taking it over.

The existing StaticMap/MapObject/ActorSpawn constructors remain valid. Type names for mission objects follow the PDF: `Core`, `Exit`, `Spawn`. Pass the selected stable Core/Exit IDs to MissionSpec; core does not implement a second Tiled importer. Door/Prop/hide-object systems remain Suhita's P05 backend work. P02 core interaction handles theft; unsupported environment interactions reject explicitly until their real system is connected.

## Physical and controller values

- Tiles stay zero-based `(x, y)` integer cells, x right/y down. Positions use **30,000 integer units per tile**, with spawns at tile centers. Additive `position` fields on OwnStatus/EntityView allow sub-tile rendering; existing tile fields remain available for planning. Actor radius and speed are supplied by the shared rules.
- MOVE direction accepts normalized intent components -1/0/1, including diagonals. Simulation normalizes speed and resolves collision; sprint is a flag. All controllers use the same rules.
- Preserve the existing action kinds and strict current-observation tick. One actor intent per tick; duplicate intents all reject. Movement is continuous, so a single MOVE no longer travels a whole tile.
- Hold INTERACT continuously in range/reach of the Core for the configured duration. Explicit target_id selects it; no target selects the nearest legal interaction, then stable ID. Movement, release or invalid action resets theft progress. Only the configured operative can steal/extract.
- Controller observations remain immutable and filtered. P02 adds only own physical/mission progress and legal core-interaction hints; full sensing is P03. Never send PresentationSnapshot or Simulation to a controller.

## Construction and outcome

The composition root will load versioned game rules through `infrastructure.resources.load_game_rules()` and pass them explicitly to Simulation; core itself performs no resource/disk/pygame IO. MissionSpec selects operative/core/exit and mode. Anchorless diagnostic runs can omit MissionSpec.

Mission completion before scoring uses a separate unscored MissionEnd value (WIN/CAPTURED/ABORTED). StepResult gains a mission_end field; its existing terminal RunResult remains None until real P06 scoring is connected. Results screens must show outcome without inventing a score/grade. The final handoff supplies the exact implemented signatures.

Capture is physical adjacent contact with valid line of reach and a telegraph. A stationary guard is sufficient for the P02 gate; active defenders are P03. Tools resolve before capture completion; completed capture wins a same-tick extraction tie. No defeat from noise, observation, lockdown or depleted stock alone. Terminal steps are idempotent. Pausing means calling no simulation steps.

Echo/EMP/melee perform real initial effects and resource/range checks. Echo is a separate nonphysical decoy, never an actor that can steal/extract. P03 supplies guard perception of it; P05 completes environment/effect integration. Approved scoring rules remain unchanged and unimplemented until P06.

## Consumer handoff

Before integrating, read `tracking/handoffs/khalid/day_01/P02.md` when present, inspect the branch diff and use the actual signatures/examples there. Full P02 stays open until both owners' work and the combined Human win/capture/pause/retry gate pass. Khalid stops at P02-K1/K2.

Implemented configuration type: `core/contracts/config/gameplay.py:GameRules`; `Simulation(world_map, spawns, *, rules, mission=None, seed=1042)`. `step(actions=(), *, abort=False)` returns StepResult with unscored mission_end. `HumanInput.feed(events)` returns separate PAUSE/FOCUS_LOST/OBJECTIVE/LAB/QUIT requests; `action_for(own_observation)` supplies one intent per tick. Scene owner handles pause/focus explicitly and runs no ticks while paused.
