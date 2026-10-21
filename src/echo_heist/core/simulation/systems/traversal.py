"""Simulation-owned stair transfers and fixed-tick sprint recovery."""

from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.observations import InteractionHint
from echo_heist.core.contracts.world import StaticMap, tile_center
from echo_heist.core.simulation.systems.motion import body_fits, distance_squared
from echo_heist.core.simulation.world import Emit, WorldState


def stair_hints(
    world: WorldState, world_map: StaticMap, actor_id: str
) -> tuple[InteractionHint, ...]:
    actor = world.actors[actor_id]
    if world.mission_end is not None:
        return ()
    return tuple(
        InteractionHint(link.object_id, "Stair", 1)
        for link in world_map.stairs
        if actor.tile == link.tile
    )


def use_stair(
    world: WorldState,
    world_map: StaticMap,
    rules: GameRules,
    actor_id: str,
    target_id: str | None,
    emit: Emit,
) -> None:
    actor = world.actors[actor_id]
    link = next(
        link for link in world_map.stairs if link.tile == actor.tile and link.object_id == target_id
    )
    destination = tile_center(link.destination)
    if not body_fits(world_map, destination, rules.actor_radius_units) or any(
        other.actor_id != actor_id
        and distance_squared(other.position, destination) < (2 * rules.actor_radius_units) ** 2
        for other in world.actors.values()
    ):
        emit(EventKind.ACTION_REJECTED, actor_id, (("reason", "stair_landing_occupied"),))
        return
    actor.position = destination
    actor.traversed_tiles = (link.tile, link.destination)
    emit(
        EventKind.STAIR_USED,
        actor_id,
        (
            ("stair_id", link.object_id),
            ("destination_id", link.destination_id),
            ("actor_kind", actor.kind.value),
        ),
    )


def update_sprint(world: WorldState, rules: GameRules, requested: frozenset[str]) -> None:
    for actor in world.actors.values():
        if actor.sprint_ready_at and world.tick >= actor.sprint_ready_at:
            actor.sprint_ticks_remaining = rules.sprint_duration_ticks
            actor.sprint_ready_at = 0
        if (
            actor.sprint_ticks_remaining < rules.sprint_duration_ticks
            and actor.actor_id not in requested
            and not actor.sprint_ready_at
        ):
            actor.sprint_ready_at = world.tick + rules.sprint_recharge_ticks
        actor.sprinting = False
