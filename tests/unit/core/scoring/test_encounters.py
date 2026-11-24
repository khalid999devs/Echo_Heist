"""Team detection encounters: counted once, kept fresh by evidence or a grab, reset by expiry."""

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.results import MissionSpec, RunOutcome
from echo_heist.core.contracts.security.model import GuardPatrol, SecuritySpec
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, MapObject, StaticMap, Tile
from echo_heist.core.scoring.encounters import EncounterState, update
from echo_heist.core.simulation.engine import Simulation
from echo_heist.infrastructure.resources import load_sensor_rules

TTL = load_sensor_rules().memory_ticks


def test_state_machine_counts_once_and_reacquires_only_after_expiry() -> None:
    state = EncounterState()
    assert update(state, 10, [10, 10], grab_active=False, ttl_ticks=TTL)  # two guards
    assert not update(state, 11, [11], grab_active=False, ttl_ticks=TTL)  # continuous sight
    update(state, 11 + TTL, [], grab_active=False, ttl_ticks=TTL)  # brief break, still fresh
    assert state.active
    assert not update(state, 12 + TTL, [12 + TTL], grab_active=False, ttl_ticks=TTL)
    assert state.count == 1
    update(state, 13 + 2 * TTL, [], grab_active=True, ttl_ticks=TTL)  # a grab keeps it open
    assert state.active
    update(state, 14 + 2 * TTL, [], grab_active=False, ttl_ticks=TTL)
    assert not state.active
    assert update(state, 20 + 2 * TTL, [20 + 2 * TTL], grab_active=False, ttl_ticks=TTL)
    assert state.count == 2 and state.raw_confirmations == 5
    # A stale relayed timestamp can never refresh an expired encounter by itself.
    update(state, 30 + 4 * TTL, [], grab_active=False, ttl_ticks=TTL)
    assert not update(state, 31 + 4 * TTL, [-5], grab_active=False, ttl_ticks=TTL)
    assert not state.active and state.count == 2


def facility(
    rules: GameRules,
    kind: ActorKind,
    player: Tile,
    *,
    second: bool = False,
    wall: bool = False,
) -> Simulation:
    border = frozenset((x, y) for x in range(14) for y in range(10) if x in (0, 13) or y in (0, 9))
    # An optional opaque wall at x=8 that does not block sound.
    solid = border | (frozenset((8, y) for y in range(1, 9)) if wall else frozenset())
    world = StaticMap(
        "encounters",
        14,
        10,
        solid,
        solid,
        objects=(MapObject("core", "Core", (11, 7)), MapObject("exit", "Exit", (1, 1))),
    )
    patrols = [GuardPatrol("sentinel", ((3, 3), (6, 3), (6, 6), (3, 6)))]
    spawns = [
        ActorSpawn("intruder", player, kind),
        ActorSpawn("sentinel", (3, 3), ActorKind.SENTINEL),
    ]
    if second:
        patrols.append(GuardPatrol("tracker", ((3, 5), (6, 5)), role=patrols[0].role))
        spawns.append(ActorSpawn("tracker", (3, 5), ActorKind.SENTINEL))
    return Simulation(
        world,
        tuple(spawns),
        rules=rules,
        mission=MissionSpec(
            "intruder", "core", "exit", "COMPANION" if kind == ActorKind.COMPANION else "HUMAN"
        ),
        security=SecuritySpec(tuple(patrols), load_sensor_rules(), border),
    )


@pytest.mark.parametrize("kind", [ActorKind.OPERATIVE, ActorKind.COMPANION])
def test_a_real_pursuit_is_one_encounter_and_emp_cannot_reset_it(
    rules: GameRules, kind: ActorKind
) -> None:
    sim = facility(rules, kind, (5, 3), second=True)
    confirmations = 0
    for _ in range(24):  # identification takes 22 ticks at this range
        result = sim.step()
        confirmations += sum(e.kind == EventKind.SIGHTING_CONFIRMED for e in result.events)
    assert confirmations >= 1
    sim.step((Action("intruder", ActionKind.EMP, sim.tick),))
    for _ in range(5):
        sim.step()
    assert sim._world.encounters.count == 1 and sim._world.encounters.active
    end = sim.step((Action("intruder", ActionKind.WAIT, sim.tick),), abort=True)
    assert end.terminal is not None and end.terminal.outcome == RunOutcome.ABORTED
    assert (end.terminal.score, end.terminal.grade) == (0, "F")
    assert end.terminal.detection_encounters == 1
    assert end.terminal.mode == ("COMPANION" if kind == ActorKind.COMPANION else "HUMAN")
    assert any(e.kind == EventKind.MISSION_ENDED for e in end.terminal.decisive_events)


def test_hearing_echo_and_unseen_movement_never_count(rules: GameRules) -> None:
    sim = facility(rules, ActorKind.OPERATIVE, (9, 3), wall=True)  # behind an opaque wall
    sim.step((Action("intruder", ActionKind.ECHO, 0),))
    heard = 0
    for index in range(80):
        direction = (0, 1) if (index // 20) % 2 == 0 else (0, -1)
        sim.step((Action("intruder", ActionKind.MOVE, sim.tick, direction, sprint=True),))
        heard += len(sim.observe("sentinel").heard_events)
    assert heard > 0  # the sentinel really heard sprinting through the wall
    assert sim._world.encounters.count == 0
    assert sim.terminal_result() is None  # nothing is scored before the mission ends
