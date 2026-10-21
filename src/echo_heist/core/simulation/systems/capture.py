"""Physical contact wind-ups; full guard sensing/decisions are P03 work."""

from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.results import MissionSpec, RunOutcome
from echo_heist.core.contracts.world import ActorKind, StaticMap
from echo_heist.core.simulation.systems.mission import end_mission
from echo_heist.core.simulation.systems.motion import clear_reach, distance_squared
from echo_heist.core.simulation.world import GUARD_KINDS, CaptureState, Emit, WorldState


def update_captures(
    world: WorldState,
    world_map: StaticMap,
    rules: GameRules,
    mission: MissionSpec | None,
    emit: Emit,
    eligible_guards: frozenset[str] | None = None,
) -> None:
    for guard in world.actors.values():
        if guard.kind not in GUARD_KINDS:
            continue
        targets = (
            [
                actor
                for actor in world.actors.values()
                if actor.kind in (ActorKind.OPERATIVE, ActorKind.COMPANION)
                and (mission is None or actor.actor_id == mission.operative_id)
                and distance_squared(guard.position, actor.position) <= rules.capture_range_units**2
                and clear_reach(world_map, guard.position, actor.position)
            ]
            if not guard.incapacitated(world.tick)
            and (eligible_guards is None or guard.actor_id in eligible_guards)
            else []
        )
        targets.sort(
            key=lambda actor: (distance_squared(guard.position, actor.position), actor.actor_id)
        )
        previous = world.captures.get(guard.actor_id)
        if previous is not None and not any(t.actor_id == previous.target_id for t in targets):
            del world.captures[guard.actor_id]
            emit(EventKind.CAPTURE_CANCELED, guard.actor_id, (("target_id", previous.target_id),))
            previous = None
        if previous is None and targets:
            previous = CaptureState(targets[0].actor_id, world.tick + rules.capture_windup_ticks)
            world.captures[guard.actor_id] = previous
            emit(
                EventKind.CAPTURE_STARTED,
                guard.actor_id,
                (
                    ("target_id", previous.target_id),
                    ("completes_at_tick", previous.completes_at),
                ),
            )
        if previous is not None and world.tick >= previous.completes_at:
            emit(EventKind.CAPTURE_COMPLETED, guard.actor_id, (("target_id", previous.target_id),))
            end_mission(
                world, previous.target_id, RunOutcome.CAPTURED, emit, capture_by=guard.actor_id
            )
            return
