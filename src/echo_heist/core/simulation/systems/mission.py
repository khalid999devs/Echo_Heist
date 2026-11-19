"""Only Simulation-owned mission rules can transfer the core or end a run."""

from dataclasses import replace

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.observations import InteractionHint
from echo_heist.core.contracts.results import MissionEnd, MissionSpec, RunOutcome
from echo_heist.core.contracts.world import MapObject, MissionPhase, Scalar, StaticMap, tile_center
from echo_heist.core.environment.lifecycle import hints as prop_hints
from echo_heist.core.simulation.systems.motion import clear_reach, distance_squared
from echo_heist.core.simulation.systems.traversal import stair_hints
from echo_heist.core.simulation.world import Emit, WorldState


def mission_object(world_map: StaticMap, object_id: str) -> MapObject:
    matches = [obj for obj in world_map.objects if obj.object_id == object_id]
    if len(matches) != 1:
        raise ValueError(f"Mission needs one map object with ID {object_id!r}")
    return matches[0]


def interaction_hints(
    world: WorldState,
    world_map: StaticMap,
    rules: GameRules,
    mission: MissionSpec | None,
    actor_id: str,
) -> tuple[InteractionHint, ...]:
    """Offered interactions, closest valid object first with a stable ID tie-break.

    Standing on a stair landing keeps offering only that stair (P02/P03
    behavior). A hidden intruder is only offered leaving its locker. Core
    progress already under way stays first so a held E never flips targets.
    """
    actor = world.actors[actor_id]
    if actor.stair_source_id is not None or world.mission_end is not None:
        return ()
    if actor.hidden_in is None:
        stairs = stair_hints(world, world_map, actor_id)
        if stairs:
            return stairs
    options = list(prop_hints(world, world_map, rules, actor_id))
    if actor.hidden_in is not None:
        return tuple(hint for _, hint in options)
    if mission is not None and actor_id == mission.operative_id and world.core_owner is None:
        core = mission_object(world_map, mission.core_object_id)
        target = tile_center(core.tile)
        reach = distance_squared(actor.position, target)
        if reach <= rules.interaction_range_units**2 and clear_reach(
            world_map, actor.position, target, allow_solid_end=True
        ):
            hint = InteractionHint(
                core.object_id, "Core", rules.core_interaction_ticks, world.interaction_ticks
            )
            started = world.interaction_actor == actor_id and world.interaction_ticks > 0
            options.append((-1 if started else reach, hint))
    options.sort(key=lambda option: (option[0], option[1].target_id))
    return tuple(hint for _, hint in options)


def interaction_reason(
    world: WorldState,
    world_map: StaticMap,
    rules: GameRules,
    mission: MissionSpec | None,
    action: Action,
) -> str | None:
    hints = interaction_hints(world, world_map, rules, mission, action.actor_id)
    if not hints:
        return "no_reachable_interaction"
    if action.target_id is not None and all(h.target_id != action.target_id for h in hints):
        return "invalid_interaction_target"
    return None


def interaction_target(
    world: WorldState,
    world_map: StaticMap,
    rules: GameRules,
    mission: MissionSpec | None,
    action: Action,
) -> InteractionHint:
    """The validated hint an INTERACT resolves to (explicit target or the first)."""
    hints = interaction_hints(world, world_map, rules, mission, action.actor_id)
    return next(h for h in hints if action.target_id in (None, h.target_id))


def update_theft(
    world: WorldState,
    rules: GameRules,
    mission: MissionSpec | None,
    actions: tuple[Action, ...],
    emit: Emit,
) -> None:
    held = next((a for a in actions if a.kind == ActionKind.INTERACT), None)
    if mission is None or held is None or world.core_owner is not None:
        world.interaction_actor = None
        world.interaction_ticks = 0
        return
    if held.actor_id != mission.operative_id:
        world.interaction_actor = None
        world.interaction_ticks = 0
        return
    world.interaction_actor = held.actor_id
    world.interaction_ticks += 1
    emit(EventKind.ACTION_ACCEPTED, held.actor_id, (("interaction", mission.core_object_id),))
    if world.interaction_ticks < rules.core_interaction_ticks:
        return
    actor = world.actors[held.actor_id]
    actor.inventory = replace(actor.inventory, core_held=True)
    world.core_owner = actor.actor_id
    world.phase = MissionPhase.LOCKDOWN
    world.interaction_ticks = 0
    world.interaction_actor = None
    emit(EventKind.CORE_TAKEN, actor.actor_id, (("core_id", mission.core_object_id),))
    emit(EventKind.LOCKDOWN_STARTED, actor.actor_id, (("exit_id", mission.exit_object_id),))


def end_mission(
    world: WorldState,
    operative_id: str,
    outcome: RunOutcome,
    emit: Emit,
    *,
    capture_by: str | None = None,
    extraction_id: str | None = None,
) -> None:
    if world.mission_end is not None:
        return
    world.phase = {
        RunOutcome.WIN: MissionPhase.WON,
        RunOutcome.CAPTURED: MissionPhase.CAPTURED,
        RunOutcome.ABORTED: MissionPhase.ABORTED,
    }[outcome]
    world.mission_end = MissionEnd(outcome, world.tick, operative_id, capture_by, extraction_id)
    world.captures.clear()
    details: tuple[tuple[str, Scalar], ...] = (
        ("outcome", outcome.value),
        ("capture_by", capture_by),
    )
    if extraction_id is not None:
        details += (("exit_id", extraction_id),)
    emit(EventKind.MISSION_ENDED, operative_id, details)


def check_extraction(
    world: WorldState, world_map: StaticMap, mission: MissionSpec | None, emit: Emit
) -> None:
    if mission is None or world.mission_end is not None:
        return
    actor = world.actors[mission.operative_id]
    if world.core_owner != actor.actor_id or not actor.inventory.core_held:
        return
    exits = {mission_object(world_map, key).tile: key for key in mission.exit_ids}
    for tile in actor.traversed_tiles:
        if tile in exits:
            end_mission(world, actor.actor_id, RunOutcome.WIN, emit, extraction_id=exits[tile])
            break
