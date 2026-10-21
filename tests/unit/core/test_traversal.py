"""Stairs are authoritative graph edges, with legal reach and occupied landings."""

import pytest

from echo_heist.ai.navigation.grid import bfs
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.security.model import GuardPatrol, SecuritySpec
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, StairLink, StaticMap, tile_center
from echo_heist.core.perception.sensors import line_of_sight, sound_reaches
from echo_heist.core.simulation.engine import Simulation
from echo_heist.infrastructure.resources import load_sensor_rules


def atlas() -> StaticMap:
    gap = frozenset((x, y) for x in (4, 5) for y in range(7))
    return StaticMap(
        "two-floors",
        11,
        7,
        gap,
        gap,
        stairs=(
            StairLink("up", (3, 3), "down", (6, 3)),
            StairLink("down", (6, 3), "up", (3, 3)),
        ),
    )


def test_stairs_connect_navigation_and_sound_without_vision_through_floor() -> None:
    world = atlas()
    assert bfs(world, (2, 3), (7, 3)).path == ((2, 3), (3, 3), (6, 3), (7, 3))
    assert sound_reaches(world, world.opaque_tiles, (2, 3), (7, 3), 3)
    assert not sound_reaches(world, world.opaque_tiles, (2, 3), (7, 3), 2)
    assert not line_of_sight(world, tile_center((3, 3)), tile_center((6, 3)))
    with pytest.raises(ValueError, match="reciprocal"):
        StaticMap("broken", 11, 7, stairs=(StairLink("up", (3, 3), "missing", (6, 3)),))


def test_reachable_stair_commits_travel_and_rejects_remote_target(rules: GameRules) -> None:
    sim = Simulation(atlas(), (ActorSpawn("operative", (3, 3)),), rules=rules)
    assert sim.observe("operative").interactions[0].kind == "Stair"
    result = sim.step((Action("operative", ActionKind.INTERACT, 0, target_id="up"),))
    assert [event.kind for event in result.events] == [EventKind.STAIR_STARTED]
    assert sim.observe("operative").own_status.tile == (3, 3)
    for _ in range(rules.stair_travel_ticks):
        result = sim.step()
    assert EventKind.STAIR_USED in [event.kind for event in result.events]
    assert sim.observe("operative").own_status.tile == (6, 3)
    result = sim.step((Action("operative", ActionKind.INTERACT, sim.tick, target_id="up"),))
    assert dict(result.events[0].details)["reason"] == "invalid_interaction_target"
    assert sim.observe("operative").own_status.tile == (6, 3)
    sim.step((Action("operative", ActionKind.INTERACT, sim.tick, target_id="down"),))
    for _ in range(rules.stair_travel_ticks):
        sim.step()
    assert sim.observe("operative").own_status.tile == (3, 3)


def test_movement_interrupts_climb_and_clears_progress(rules: GameRules) -> None:
    sim = Simulation(atlas(), (ActorSpawn("operative", (3, 3)),), rules=rules)
    sim.step((Action("operative", ActionKind.INTERACT, 0, target_id="up"),))
    assert sim.observe("operative").own_status.stair_ticks_remaining > 0
    result = sim.step((Action("operative", ActionKind.MOVE, sim.tick, (-1, 0)),))
    assert EventKind.STAIR_CANCELED in [event.kind for event in result.events]
    for _ in range(rules.stair_travel_ticks):
        sim.step()
    assert not sim.observe("operative").own_status.stair_ticks_remaining
    assert sim.observe("operative").own_status.tile[0] < 4


def test_stairs_never_overlap_an_occupied_destination(rules: GameRules) -> None:
    sim = Simulation(
        atlas(), (ActorSpawn("operative", (3, 3)), ActorSpawn("other", (6, 3))), rules=rules
    )
    result = sim.step((Action("operative", ActionKind.INTERACT, 0, target_id="up"),))
    assert dict(result.events[0].details)["reason"] == "stair_landing_occupied"
    assert sim.observe("operative").own_status.tile == (3, 3)


def test_landing_is_rechecked_when_a_body_arrives_during_travel(rules: GameRules) -> None:
    sim = Simulation(
        atlas(),
        (ActorSpawn("operative", (3, 3)), ActorSpawn("other", (6, 4), ActorKind.COMPANION)),
        rules=rules,
    )
    sim.step((Action("operative", ActionKind.INTERACT, 0, target_id="up"),))
    for _ in range(12):
        sim.step((Action("other", ActionKind.MOVE, sim.tick, (0, -1)),))
    assert sim.observe("other").own_status.tile == (6, 3)
    events = []
    for _ in range(rules.stair_travel_ticks):
        events.extend(sim.step().events)
    assert any(
        event.kind == EventKind.ACTION_REJECTED
        and dict(event.details).get("reason") == "stair_landing_occupied"
        for event in events
    )
    assert sim.observe("operative").own_status.tile == (3, 3)
    assert not sim.presentation_snapshot().stairs


def test_autonomous_sentinel_uses_same_stair_and_replays(rules: GameRules) -> None:
    patrol = GuardPatrol("sentinel", ((2, 3), (7, 3)))
    world = atlas()
    spec = SecuritySpec((patrol,), load_sensor_rules(), world.opaque_tiles)
    first, second = (
        Simulation(
            world, (ActorSpawn("sentinel", (2, 3), ActorKind.SENTINEL),), rules=rules, security=spec
        )
        for _ in range(2)
    )
    traversals = 0
    for _ in range(220):
        result = first.step()
        assert result == second.step()
        assert first.fingerprint() == second.fingerprint()
        traversals += sum(event.kind == EventKind.STAIR_USED for event in result.events)
    assert traversals >= 2
