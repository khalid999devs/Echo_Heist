"""Own-only P02 observations and explicitly privileged presentation values."""

from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.observations import EntityView, Observation, OwnStatus
from echo_heist.core.contracts.results import (
    CaptureView,
    EchoView,
    MissionSpec,
    PresentationSnapshot,
)
from echo_heist.core.contracts.world import StaticMap
from echo_heist.core.simulation.systems.mission import interaction_hints
from echo_heist.core.simulation.world import WorldState


def observe(
    world: WorldState,
    world_map: StaticMap,
    rules: GameRules,
    mission: MissionSpec | None,
    actor_id: str,
) -> Observation:
    actor = world.actors[actor_id]
    captures = [
        max(0, capture.completes_at - world.tick)
        for capture in world.captures.values()
        if capture.target_id == actor_id
    ]
    return Observation(
        agent_id=actor_id,
        tick=world.tick,
        map_static=world_map,
        phase=world.phase,
        own_status=OwnStatus(
            actor.tile,
            actor.inventory,
            position=actor.position,
            interaction_progress_ticks=world.interaction_ticks
            if world.interaction_actor == actor_id
            else 0,
            capture_ticks_remaining=min(captures) if captures else None,
        ),
        interactions=interaction_hints(world, world_map, rules, mission, actor_id),
    )


def presentation(world: WorldState, world_map: StaticMap, rules: GameRules) -> PresentationSnapshot:
    return PresentationSnapshot(
        tick=world.tick,
        world_map=world_map,
        actors=tuple(
            EntityView(
                actor.actor_id,
                actor.kind,
                actor.tile,
                actor.position,
                world.tick < actor.disabled_until,
                world.tick < actor.stunned_until,
            )
            for actor in world.actors.values()
        ),
        phase=world.phase,
        echoes=tuple(
            EchoView(echo.echo_id, echo.path[echo.index], len(echo.path) - echo.index)
            for echo in world.echoes.values()
        ),
        captures=tuple(
            CaptureView(
                guard_id,
                capture.target_id,
                max(0, capture.completes_at - world.tick),
                rules.capture_windup_ticks,
            )
            for guard_id, capture in world.captures.items()
        ),
        core_owner=world.core_owner,
        mission_end=world.mission_end,
    )
