from dataclasses import replace

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, StaticMap
from echo_heist.core.simulation.engine import Simulation


def contact(rules: GameRules) -> Simulation:
    return Simulation(
        StaticMap("tools", 12, 8),
        (
            ActorSpawn("operative", (3, 3)),
            ActorSpawn("a-guard", (4, 3), ActorKind.SENTINEL),
            ActorSpawn("b-guard", (3, 4), ActorKind.TRACKER),
            ActorSpawn("far", (8, 3), ActorKind.INTERCEPTOR),
        ),
        rules=rules,
    )


def test_emp_cancels_all_grabs_on_completion_tick_and_never_recharges(rules: GameRules) -> None:
    sim = contact(rules)
    sim.step()
    for _ in range(rules.capture_windup_ticks - 1):
        sim.step()
    result = sim.step((Action("operative", ActionKind.EMP, sim.tick),))
    assert result.mission_end is None
    kinds = [event.kind for event in result.events]
    assert kinds.count(EventKind.CAPTURE_CANCELED) == 2
    assert kinds.count(EventKind.GUARD_DISABLED) == 2
    actors = {actor.actor_id: actor for actor in sim.presentation_snapshot().actors}
    assert actors["a-guard"].disabled and actors["b-guard"].disabled
    assert not actors["far"].disabled
    assert sim.observe("operative").own_status.inventory.emp_charges == 0
    rejected = sim.step((Action("operative", ActionKind.EMP, sim.tick),))
    assert rejected.events[0].details == (("reason", "emp_empty"),)
    assert not any(event.kind == EventKind.NOISE_CREATED for event in rejected.events)
    for _ in range(rules.emp_disable_ticks - 2):
        sim.step()
    assert sim.presentation_snapshot().actors[0].disabled  # stable ID a-guard
    sim.step()
    assert not sim.presentation_snapshot().actors[0].disabled
    assert sim.observe("operative").own_status.inventory.emp_charges == 0


def test_melee_targets_one_guard_then_recovery_immunity_is_noisy(rules: GameRules) -> None:
    sim = contact(rules)
    first = sim.step((Action("operative", ActionKind.MELEE, 0),))
    stunned = [event.actor_id for event in first.events if event.kind == EventKind.GUARD_STUNNED]
    assert stunned == ["a-guard"]  # equal-distance tie broken by stable ID
    # Disable the other captor so this test can reach melee recovery safely.
    sim.step((Action("operative", ActionKind.EMP, sim.tick),))
    for _ in range(rules.melee_stun_ticks):
        sim.step()
    repeated = sim.step((Action("operative", ActionKind.MELEE, sim.tick, target_id="a-guard"),))
    assert not any(event.kind == EventKind.GUARD_STUNNED for event in repeated.events)
    assert any(event.kind == EventKind.NOISE_CREATED for event in repeated.events)
    assert (
        dict(next(event for event in repeated.events if event.kind == EventKind.TOOL_USED).details)[
            "affected"
        ]
        is False
    )


def test_melee_cannot_reach_through_blocked_diagonal_corner(rules: GameRules) -> None:
    rules = replace(rules, melee_range_units=60_000)
    sim = Simulation(
        StaticMap("reach", 6, 6, frozenset({(2, 1), (1, 2)})),
        (
            ActorSpawn("operative", (1, 1)),
            ActorSpawn("guard", (2, 2), ActorKind.SENTINEL),
        ),
        rules=rules,
    )
    result = sim.step((Action("operative", ActionKind.MELEE, 0),))
    assert result.events[0].details == (("reason", "no_reachable_guard"),)
    assert not any(event.kind == EventKind.NOISE_CREATED for event in result.events)


def test_echo_replays_backwards_has_no_body_or_actor_authority_and_expires(
    rules: GameRules,
) -> None:
    sim = Simulation(StaticMap("echo", 15, 8), (ActorSpawn("operative", (3, 3)),), rules=rules)
    positions = [sim.observe("operative").own_status.position]
    for _ in range(30):
        sim.step((Action("operative", ActionKind.MOVE, sim.tick, (1, 0)),))
        positions.append(sim.observe("operative").own_status.position)
    sim.step((Action("operative", ActionKind.ECHO, sim.tick),))
    echo = sim.presentation_snapshot().echoes[0]
    assert echo.position == positions[-1]
    rejected = sim.step((Action(echo.echo_id, ActionKind.INTERACT, sim.tick),))
    assert rejected.events[0].details == (("reason", "unknown_actor"),)
    assert sim.presentation_snapshot().echoes[0].position == positions[-2]
    for _ in range(30):
        sim.step((Action("operative", ActionKind.MOVE, sim.tick, (-1, 0)),))
    assert sim.observe("operative").own_status.tile == (3, 3)
    for _ in range(rules.echo_history_ticks):
        sim.step()
    assert not sim.presentation_snapshot().echoes
    assert len(sim.presentation_snapshot().actors) == 1


def test_empty_echo_and_malformed_tools_never_spend_resources(rules: GameRules) -> None:
    sim = Simulation(StaticMap("stock", 8, 8), (ActorSpawn("operative", (3, 3)),), rules=rules)
    malformed = sim.step((Action("operative", ActionKind.EMP, 0, target_id="none"),))
    assert malformed.events[0].kind == EventKind.ACTION_REJECTED
    assert sim.observe("operative").own_status.inventory.emp_charges == 1
    for _ in range(3):
        sim.step((Action("operative", ActionKind.ECHO, sim.tick),))
    result = sim.step((Action("operative", ActionKind.ECHO, sim.tick),))
    assert result.events[0].details == (("reason", "echo_empty"),)
    assert sim.observe("operative").own_status.inventory.echo_charges == 0
