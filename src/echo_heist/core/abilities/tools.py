"""Initial real Echo/EMP/melee effects, shared by Human and Companion."""

from dataclasses import replace

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.world import StaticMap
from echo_heist.core.simulation.systems.motion import clear_reach, distance_squared
from echo_heist.core.simulation.world import GUARD_KINDS, ActorState, EchoState, Emit, WorldState


def melee_target(
    world: WorldState, world_map: StaticMap, rules: GameRules, action: Action
) -> ActorState | None:
    actor = world.actors[action.actor_id]
    targets = [
        guard
        for guard in world.actors.values()
        if guard.kind in GUARD_KINDS
        and (action.target_id is None or action.target_id == guard.actor_id)
        and distance_squared(actor.position, guard.position) <= rules.melee_range_units**2
        and clear_reach(world_map, actor.position, guard.position)
    ]
    return min(
        targets,
        key=lambda guard: (distance_squared(actor.position, guard.position), guard.actor_id),
        default=None,
    )


def tool_reason(
    world: WorldState, world_map: StaticMap, rules: GameRules, action: Action
) -> str | None:
    actor = world.actors[action.actor_id]
    if action.kind == ActionKind.ECHO and actor.inventory.echo_charges <= 0:
        return "echo_empty"
    if action.kind == ActionKind.EMP and actor.inventory.emp_charges <= 0:
        return "emp_empty"
    if action.kind == ActionKind.MELEE and melee_target(world, world_map, rules, action) is None:
        return "no_reachable_guard"
    return None


def advance_echoes(world: WorldState) -> None:
    for echo_id in tuple(world.echoes):
        echo = world.echoes[echo_id]
        echo.index += 1
        if echo.index >= len(echo.path):
            del world.echoes[echo_id]


def use_tool(
    world: WorldState, world_map: StaticMap, rules: GameRules, action: Action, emit: Emit
) -> None:
    actor = world.actors[action.actor_id]
    details: list[tuple[str, str | int | bool | None]] = [("tool", action.kind.value)]
    if action.kind == ActionKind.ECHO:
        actor.inventory = replace(actor.inventory, echo_charges=actor.inventory.echo_charges - 1)
        path = tuple(reversed(actor.path[-rules.echo_history_ticks :]))
        path += (path[-1],) * (rules.echo_history_ticks - len(path))
        echo_id = f"echo:{world.next_echo_id}"
        world.next_echo_id += 1
        world.echoes[echo_id] = EchoState(echo_id, actor.actor_id, path)
        details.extend((("echo_id", echo_id), ("remaining", actor.inventory.echo_charges)))
    elif action.kind == ActionKind.EMP:
        actor.inventory = replace(actor.inventory, emp_charges=actor.inventory.emp_charges - 1)
        details.append(("remaining", actor.inventory.emp_charges))
        for guard in world.actors.values():
            if (
                guard.kind in GUARD_KINDS
                and distance_squared(actor.position, guard.position) <= rules.emp_radius_units**2
            ):
                guard.disabled_until = max(
                    guard.disabled_until, world.tick + rules.emp_disable_ticks
                )
                emit(
                    EventKind.GUARD_DISABLED,
                    guard.actor_id,
                    (("until_tick", guard.disabled_until),),
                )
        _noise(world, actor, "EMP", rules.emp_noise_radius_tiles, emit)
    else:
        target = melee_target(world, world_map, rules, action)
        assert target is not None  # validated before dispatch; no actor moves during tools
        guard = target
        affected = world.tick >= guard.melee_immune_until
        if affected:
            guard.stunned_until = world.tick + rules.melee_stun_ticks
            guard.melee_immune_until = guard.stunned_until + rules.melee_immunity_ticks
            emit(EventKind.GUARD_STUNNED, guard.actor_id, (("until_tick", guard.stunned_until),))
        details.extend((("target_id", guard.actor_id), ("affected", affected)))
        _noise(world, actor, "MELEE", rules.melee_noise_radius_tiles, emit)
    emit(EventKind.TOOL_USED, actor.actor_id, tuple(details))


def _noise(world: WorldState, actor: ActorState, kind: str, radius: int, emit: Emit) -> None:
    emit(
        EventKind.NOISE_CREATED,
        actor.actor_id,
        (
            ("kind", kind),
            ("x", actor.tile[0]),
            ("y", actor.tile[1]),
            ("radius_tiles", radius),
        ),
    )
