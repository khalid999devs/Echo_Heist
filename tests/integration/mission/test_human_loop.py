from dataclasses import replace

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.results import MissionSpec, RunOutcome
from echo_heist.core.contracts.world import (
    ActorKind,
    ActorSpawn,
    MapObject,
    MissionPhase,
    StaticMap,
    tile_center,
)
from echo_heist.core.simulation.engine import Simulation


def mission(rules: GameRules, *, kind: ActorKind = ActorKind.OPERATIVE) -> Simulation:
    world = StaticMap(
        "mission-test",
        9,
        5,
        objects=(MapObject("core", "Core", (6, 2)), MapObject("exit", "Exit", (1, 2))),
    )
    return Simulation(
        world,
        (ActorSpawn("operative", (1, 2), kind),),
        rules=rules,
        mission=MissionSpec(
            "operative", "core", "exit", "HUMAN" if kind == ActorKind.OPERATIVE else "COMPANION"
        ),
    )


@pytest.mark.parametrize("kind", [ActorKind.OPERATIVE, ActorKind.COMPANION])
def test_real_carrier_theft_lockdown_and_original_exit(rules: GameRules, kind: ActorKind) -> None:
    sim = mission(rules, kind=kind)
    assert sim.step().mission_end is None  # starts at exit without core
    for _ in range(100):
        if sim.observe("operative").interactions:
            break
        sim.step((Action("operative", ActionKind.MOVE, sim.tick, (1, 0)),))
    assert sim.observe("operative").interactions
    for _ in range(rules.core_interaction_ticks - 1):
        result = sim.step((Action("operative", ActionKind.INTERACT, sim.tick),))
        assert not sim.observe("operative").own_status.inventory.core_held
    result = sim.step((Action("operative", ActionKind.INTERACT, sim.tick),))
    assert [event.kind for event in result.events][-2:] == [
        EventKind.CORE_TAKEN,
        EventKind.LOCKDOWN_STARTED,
    ]
    assert sim.observe("operative").phase == MissionPhase.LOCKDOWN
    assert sim.observe("operative").own_status.inventory.core_held
    again = sim.step((Action("operative", ActionKind.INTERACT, sim.tick),))
    assert all(event.kind != EventKind.CORE_TAKEN for event in again.events)
    for _ in range(120):
        result = sim.step((Action("operative", ActionKind.MOVE, sim.tick, (-1, 0)),))
        if result.mission_end:
            break
    assert result.mission_end is not None and result.mission_end.outcome == RunOutcome.WIN
    assert result.terminal is None  # no fabricated P06 score/rank
    terminal_hash, terminal_tick = sim.fingerprint(), sim.tick
    assert sim.step().events == ()
    assert sim.tick == terminal_tick and sim.fingerprint() == terminal_hash


def test_theft_requires_unbroken_valid_hold_and_correct_actor(rules: GameRules) -> None:
    sim = mission(rules)
    out_of_range = sim.step((Action("operative", ActionKind.INTERACT, 0),))
    assert out_of_range.events[0].kind == EventKind.ACTION_REJECTED
    for _ in range(100):
        if sim.observe("operative").interactions:
            break
        sim.step((Action("operative", ActionKind.MOVE, sim.tick, (1, 0)),))
    for _ in range(12):
        sim.step((Action("operative", ActionKind.INTERACT, sim.tick),))
    sim.step()
    assert sim.observe("operative").own_status.interaction_progress_ticks == 0
    wrong = sim.step((Action("operative", ActionKind.INTERACT, sim.tick, target_id="exit"),))
    assert wrong.events[0].kind == EventKind.ACTION_REJECTED
    for _ in range(23):
        sim.step((Action("operative", ActionKind.INTERACT, sim.tick),))
    assert not sim.observe("operative").own_status.inventory.core_held


def test_capture_telegraph_escape_and_completion(rules: GameRules) -> None:
    world = StaticMap("contact", 8, 8)
    spawns = (ActorSpawn("operative", (3, 3)), ActorSpawn("guard", (4, 3), ActorKind.SENTINEL))
    first, second = (Simulation(world, spawns, rules=rules) for _ in range(2))
    start = first.step()
    assert start.mission_end is None
    assert start.events[0].kind == EventKind.CAPTURE_STARTED
    for _ in range(rules.capture_windup_ticks - 1):
        assert first.step().mission_end is None
    assert first.step().mission_end.outcome == RunOutcome.CAPTURED
    assert first.observe("operative").own_status.capture_ticks_remaining is None
    second.step()
    escaped = []
    for _ in range(20):
        escaped.extend(
            second.step((Action("operative", ActionKind.MOVE, second.tick, (-1, 0)),)).events
        )
    assert any(event.kind == EventKind.CAPTURE_CANCELED for event in escaped)
    assert second.presentation_snapshot().mission_end is None


def test_completed_capture_precedes_same_tick_extraction(rules: GameRules) -> None:
    rules = replace(
        rules,
        core_interaction_ticks=1,
        capture_windup_ticks=1,
        capture_range_units=60_000,
        walk_speed_units_per_second=900_000,
        sprint_speed_units_per_second=900_000,
    )
    world = StaticMap(
        "tie", 6, 5, objects=(MapObject("core", "Core", (3, 1)), MapObject("exit", "Exit", (1, 1)))
    )
    sim = Simulation(
        world,
        (ActorSpawn("operative", (2, 1)), ActorSpawn("guard", (2, 2), ActorKind.SENTINEL)),
        rules=rules,
        mission=MissionSpec("operative", "core", "exit"),
    )
    assert sim.step((Action("operative", ActionKind.INTERACT, 0),)).mission_end is None
    result = sim.step((Action("operative", ActionKind.MOVE, sim.tick, (-1, 0)),))
    assert sim.observe("operative").own_status.tile == (1, 1)
    assert result.mission_end.outcome == RunOutcome.CAPTURED
    assert result.mission_end.capture_by == "guard"


def test_abort_and_invalid_mission_anchors(rules: GameRules) -> None:
    sim = mission(rules)
    assert sim.step(abort=True).mission_end.outcome == RunOutcome.ABORTED
    with pytest.raises(ValueError, match="one map object"):
        Simulation(
            StaticMap("bad", 3, 3),
            (ActorSpawn("operative", (1, 1)),),
            rules=rules,
            mission=MissionSpec("operative", "missing", "exit"),
        )


def test_second_actor_cannot_steal_or_extract_another_carriers_core(rules: GameRules) -> None:
    world = StaticMap(
        "authority",
        9,
        6,
        objects=(
            MapObject("core", "Core", (6, 2)),
            MapObject("exit", "Exit", (1, 2)),
        ),
    )
    sim = Simulation(
        world,
        (
            ActorSpawn("operative", (5, 2)),
            ActorSpawn("other", (6, 3), ActorKind.COMPANION),
        ),
        rules=rules,
        mission=MissionSpec("operative", "core", "exit"),
    )
    rejected = sim.step((Action("other", ActionKind.INTERACT, 0),))
    assert rejected.events[0].kind == EventKind.ACTION_REJECTED
    for _ in range(rules.core_interaction_ticks):
        sim.step((Action("operative", ActionKind.INTERACT, sim.tick),))
    for target, direction in (((1, 3), (-1, 0)), ((1, 2), (0, -1))):
        expected = tile_center(target)
        for _ in range(120):
            position = sim.observe("other").own_status.position
            assert position is not None
            if max(abs(a - b) for a, b in zip(position, expected, strict=True)) < 2_000:
                break
            result = sim.step((Action("other", ActionKind.MOVE, sim.tick, direction),))
            assert result.mission_end is None
        else:
            raise AssertionError("Second actor did not reach the actual exit")
    assert sim.observe("other").own_status.tile == (1, 2)
    assert sim.presentation_snapshot().core_owner == "operative"


def test_contact_cannot_capture_across_solid_corner(rules: GameRules) -> None:
    rules = replace(rules, capture_range_units=60_000)
    sim = Simulation(
        StaticMap("contact-wall", 5, 5, frozenset({(2, 1), (1, 2)})),
        (
            ActorSpawn("operative", (1, 1)),
            ActorSpawn("guard", (2, 2), ActorKind.SENTINEL),
        ),
        rules=rules,
    )
    for _ in range(30):
        result = sim.step()
        assert not result.events and result.mission_end is None
