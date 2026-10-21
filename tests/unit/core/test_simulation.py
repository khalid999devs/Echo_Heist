from dataclasses import FrozenInstanceError

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.world import ActorSpawn, StaticMap
from echo_heist.core.simulation.engine import Simulation
from echo_heist.core.simulation.randomness import seeded_rng
from echo_heist.diagnostics.foundation import run_fixture
from echo_heist.infrastructure.resources import load_game_rules


def simulation() -> Simulation:
    return Simulation(
        StaticMap("test", 4, 4, frozenset({(2, 1)})),
        (ActorSpawn("operative", (1, 1)),),
        rules=load_game_rules(),
    )


def test_identical_seed_and_actions_repeat_state_and_events() -> None:
    first = run_fixture(1042)
    assert first == run_fixture(1042)
    assert first["tick"] == 5
    assert first["events"] == 6
    assert first["final_tile"] == [0, 0]
    assert run_fixture(1043)["state_hash"] != first["state_hash"]


def test_rng_streams_are_reproducible_and_independent() -> None:
    world = seeded_rng(1042, "world")
    first = [world.random() for _ in range(5)]
    cosmetic = seeded_rng(1042, "cosmetic")
    for _ in range(100):
        cosmetic.random()
    repeated = seeded_rng(1042, "world")
    assert first == [repeated.random() for _ in range(5)]
    assert first != [cosmetic.random() for _ in range(5)]


@pytest.mark.parametrize("issued_tick", [-1, 1])
def test_stale_and_future_actions_do_not_move_or_spend_stock(issued_tick: int) -> None:
    sim = simulation()
    before = sim.observe("operative").own_status
    result = sim.step((Action("operative", ActionKind.MOVE, issued_tick, (0, 1)),))
    assert result.tick == 1
    assert result.events[0].details == (("reason", "stale_or_future_tick"),)
    assert sim.observe("operative").own_status == before


def test_blocked_and_malformed_actions_are_rejected_without_side_effects() -> None:
    sim = simulation()
    # Push up to the wall before checking a blocked step; speed is tunable.
    for _ in range(10):
        sim.step((Action("operative", ActionKind.MOVE, sim.tick, (1, 0)),))
    before = sim.observe("operative").own_status
    blocked = sim.step((Action("operative", ActionKind.MOVE, sim.tick, (1, 0)),))
    assert blocked.events[0].kind == EventKind.ACTION_REJECTED
    assert blocked.events[0].details == (("reason", "blocked"),)
    malformed = sim.step((Action("operative", ActionKind.EMP, sim.tick, sprint=True),))
    assert malformed.events[0].details == (("reason", "unexpected_movement_payload"),)
    assert sim.observe("operative").own_status == before


def test_duplicate_intents_reject_all_choices_independent_of_input_order() -> None:
    actions = (
        Action("operative", ActionKind.MOVE, 0, (0, 1)),
        Action("operative", ActionKind.WAIT, 0),
    )
    first, second = simulation(), simulation()
    assert first.step(actions) == second.step(reversed(actions))
    assert first.observe("operative").own_status.tile == (1, 1)
    assert first.fingerprint() == second.fingerprint()


def test_old_observations_and_snapshots_are_immutable_values() -> None:
    sim = simulation()
    previous = sim.observe("operative")
    snapshot = sim.presentation_snapshot()
    with pytest.raises(FrozenInstanceError):
        previous.own_status.tile = (3, 3)
    with pytest.raises(AttributeError):
        previous.map_static.blocked_tiles.add((0, 0))
    sim.step((Action("operative", ActionKind.MOVE, 0, (0, 1)),))
    assert previous.own_status.tile == (1, 1)
    assert snapshot.actors[0].tile == (1, 1)
    assert sim.observe("operative").own_status.position != previous.own_status.position
