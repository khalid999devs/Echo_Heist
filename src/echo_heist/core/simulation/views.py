"""Own-only P02 observations and explicitly privileged presentation values."""

from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.observations import EntityView, Observation, OwnStatus
from echo_heist.core.contracts.results import (
    CaptureView,
    EchoView,
    MissionSpec,
    PresentationSnapshot,
    StairView,
)
from echo_heist.core.contracts.security.model import GuardView, SecuritySpec
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
            facing=actor.facing,
            disabled=world.tick < actor.disabled_until,
            stunned=world.tick < actor.stunned_until,
            sprint_ticks_remaining=actor.sprint_ticks_remaining,
            sprint_recharge_remaining=max(0, actor.sprint_ready_at - world.tick),
            sprinting=actor.sprinting,
            stair_ticks_remaining=max(0, actor.stair_arrives_at - world.tick),
        ),
        visible_entities=world.visible_entities.get(actor_id, ()),
        heard_events=world.heard_cues.get(actor_id, ()),
        shared_reports=world.security_reports if actor_id in world.guard_memories else (),
        visual_cues=world.visual_cues.get(actor_id, ()),
        interactions=interaction_hints(world, world_map, rules, mission, actor_id),
    )


def presentation(
    world: WorldState, world_map: StaticMap, rules: GameRules, security: SecuritySpec | None = None
) -> PresentationSnapshot:
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
                actor.facing,
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
        guards=tuple(
            GuardView(
                actor_id,
                memory.state,
                world.actors[actor_id].facing,
                memory.identity_ticks,
                security.rules.identification_ticks,
                security.rules.sight_range_tiles,
                security.rules.half_angle_degrees,
                memory.target,
                memory.last_seen_tile,
                memory.last_seen_tick,
                memory.path,
                memory.expanded_nodes,
                memory.urgency,
            )
            for actor_id, memory in world.guard_memories.items()
        )
        if security is not None
        else (),
        stairs=tuple(
            StairView(
                actor.actor_id,
                link.tile,
                link.destination,
                max(0, actor.stair_arrives_at - world.tick),
                rules.stair_travel_ticks,
            )
            for actor in world.actors.values()
            if actor.stair_source_id is not None
            for link in world_map.stairs
            if link.object_id == actor.stair_source_id
        ),
    )
