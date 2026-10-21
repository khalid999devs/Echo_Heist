"""Approved sprint timing, blocked input and real acoustic consequences."""

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.world import ActorSpawn, StaticMap
from echo_heist.core.simulation.engine import Simulation


def open_run(rules: GameRules) -> Simulation:
    return Simulation(StaticMap("sprint", 100, 5), (ActorSpawn("operative", (1, 2)),), rules=rules)


def move(sim: Simulation, *, sprint: bool = True) -> int:
    before = sim.observe("operative").own_status.position
    sim.step((Action("operative", ActionKind.MOVE, sim.tick, (1, 0), sprint=sprint),))
    after = sim.observe("operative").own_status.position
    assert before is not None and after is not None
    return after[0] - before[0]


def test_sprint_exhausts_then_walks_and_restores_on_exact_tick(rules: GameRules) -> None:
    sim = open_run(rules)
    for _ in range(rules.sprint_duration_ticks):
        assert move(sim) == rules.sprint_speed_units_per_second // rules.simulation_hz
    status = sim.observe("operative").own_status
    assert status.sprint_ticks_remaining == 0
    assert status.sprint_recharge_remaining == rules.sprint_recharge_ticks
    for _ in range(rules.sprint_recharge_ticks - 1):
        assert move(sim) == rules.walk_speed_units_per_second // rules.simulation_hz
        assert not sim.observe("operative").own_status.sprinting
    assert move(sim) == rules.sprint_speed_units_per_second // rules.simulation_hz
    assert (
        sim.observe("operative").own_status.sprint_ticks_remaining
        == rules.sprint_duration_ticks - 1
    )


def test_releasing_partial_burst_starts_full_recharge(rules: GameRules) -> None:
    sim = open_run(rules)
    for _ in range(10):
        move(sim)
    sim.step()
    assert (
        sim.observe("operative").own_status.sprint_recharge_remaining == rules.sprint_recharge_ticks
    )
    for _ in range(rules.sprint_recharge_ticks):
        sim.step()
    status = sim.observe("operative").own_status
    assert status.sprint_recharge_remaining == 0
    assert status.sprint_ticks_remaining == rules.sprint_duration_ticks
    assert not status.sprinting


def test_blocked_requests_do_not_consume_charge(rules: GameRules) -> None:
    wall = frozenset((2, y) for y in range(5))
    sim = Simulation(
        StaticMap("blocked", 5, 5, wall), (ActorSpawn("operative", (1, 2)),), rules=rules
    )
    for _ in range(20):
        move(sim, sprint=False)
    for _ in range(10):
        assert move(sim) == 0
        assert (
            sim.observe("operative").own_status.sprint_ticks_remaining
            == rules.sprint_duration_ticks
        )
    sim.step()
    assert sim.observe("operative").own_status.sprint_recharge_remaining == 0


def test_shift_during_recharge_does_not_fabricate_loud_sprint_steps(rules: GameRules) -> None:
    sim = open_run(rules)
    for _ in range(rules.sprint_duration_ticks):
        move(sim)
    events = []
    for _ in range(30):
        result = sim.step((Action("operative", ActionKind.MOVE, sim.tick, (1, 0), sprint=True),))
        events.extend(event for event in result.events if event.kind == EventKind.NOISE_CREATED)
    assert events
    assert all(dict(event.details)["kind"] == "FOOTSTEP" for event in events)
    assert all(
        dict(event.details)["radius_tiles"] == rules.walk_noise_radius_tiles for event in events
    )
