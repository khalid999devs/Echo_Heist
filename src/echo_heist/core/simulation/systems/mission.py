"""Only Simulation-owned mission rules can transfer the core or end a run."""

from dataclasses import replace

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.observations import InteractionHint
from echo_heist.core.contracts.results import MissionEnd, MissionSpec, RunOutcome
from echo_heist.core.contracts.world import MapObject, MissionPhase, StaticMap, tile_center
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
    if world.actors[actor_id].stair_source_id is not None:
        return ()
    stairs = stair_hints(world, world_map, actor_id)
    if stairs:
        return stairs
    if mission is None or actor_id != mission.operative_id or world.core_owner is not None:
        return ()
    if world.mission_end is not None:
        return ()
    actor = world.actors[actor_id]
    core = mission_object(world_map, mission.core_object_id)
    target = tile_center(core.tile)
    if distance_squared(actor.position, target) > rules.interaction_range_units**2:
        return ()
    if not clear_reach(world_map, actor.position, target, allow_solid_end=True):
        return ()
    return (
        InteractionHint(
            core.object_id, "Core", rules.core_interaction_ticks, world.interaction_ticks
        ),
    )


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
    if action.target_id is not None and action.target_id != hints[0].target_id:
        return "invalid_interaction_target"
    return None


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
) -> None:
    if world.mission_end is not None:
        return
    world.phase = {
        RunOutcome.WIN: MissionPhase.WON,
        RunOutcome.CAPTURED: MissionPhase.CAPTURED,
        RunOutcome.ABORTED: MissionPhase.ABORTED,
    }[outcome]
    world.mission_end = MissionEnd(outcome, world.tick, operative_id, capture_by)
    world.captures.clear()
    emit(
        EventKind.MISSION_ENDED,
        operative_id,
        (("outcome", outcome.value), ("capture_by", capture_by)),
    )


def check_extraction(
    world: WorldState, world_map: StaticMap, mission: MissionSpec | None, emit: Emit
) -> None:
    if mission is None or world.mission_end is not None:
        return
    actor = world.actors[mission.operative_id]
    exit_tile = mission_object(world_map, mission.exit_object_id).tile
    if (
        world.core_owner == actor.actor_id
        and actor.inventory.core_held
        and exit_tile in actor.traversed_tiles
    ):
        end_mission(world, actor.actor_id, RunOutcome.WIN, emit)
