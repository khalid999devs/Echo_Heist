from dataclasses import replace
from math import hypot

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, StaticMap, tile_center
from echo_heist.core.simulation.engine import Simulation


@pytest.mark.parametrize("sprint", [False, True])
def test_speed_and_diagonal_normalization(rules: GameRules, sprint: bool) -> None:
    distances = []
    for direction in ((1, 0), (1, 1), (-1, -1)):
        sim = Simulation(
            StaticMap("open", 30, 30), (ActorSpawn("operative", (15, 15)),), rules=rules
        )
        for _ in range(rules.simulation_hz):
            sim.step((Action("operative", ActionKind.MOVE, sim.tick, direction, sprint=sprint),))
        position = sim.observe("operative").own_status.position
        assert position is not None
        origin = tile_center((15, 15))
        distances.append(hypot(position[0] - origin[0], position[1] - origin[1]))
    expected = rules.sprint_speed_units_per_second if sprint else rules.walk_speed_units_per_second
    assert all(abs(distance - expected) < rules.simulation_hz * 2 for distance in distances)
    assert distances[1] == distances[2]


def test_sprint_cannot_tunnel_through_wall_and_can_slide(rules: GameRules) -> None:
    fast = replace(rules, sprint_speed_units_per_second=900_000)
    world = StaticMap("wall", 8, 8, frozenset((3, y) for y in range(8)))
    sim = Simulation(world, (ActorSpawn("operative", (1, 1)),), rules=fast)
    sim.step((Action("operative", ActionKind.MOVE, 0, (1, 1), sprint=True),))
    position = sim.observe("operative").own_status.position
    assert position is not None
    assert position[0] + rules.actor_radius_units <= 3 * UNIT
    assert position[1] > tile_center((1, 1))[1]


def test_diagonal_corner_and_other_actor_block_physical_body(rules: GameRules) -> None:
    world = StaticMap("corner", 6, 6, frozenset({(2, 1), (1, 2)}))
    sim = Simulation(world, (ActorSpawn("operative", (1, 1)),), rules=rules)
    for _ in range(100):
        sim.step((Action("operative", ActionKind.MOVE, sim.tick, (1, 1)),))
    assert sim.observe("operative").own_status.tile == (1, 1)
    pair = Simulation(
        StaticMap("pair", 8, 8),
        (ActorSpawn("a", (1, 1)), ActorSpawn("b", (2, 1), ActorKind.COMPANION)),
        rules=rules,
    )
    for _ in range(50):
        pair.step((Action("a", ActionKind.MOVE, pair.tick, (1, 0)),))
    assert pair.observe("a").own_status.tile == (1, 1)


def test_step_order_is_stable_and_noise_is_not_per_render_frame(rules: GameRules) -> None:
    world = StaticMap("order", 10, 10)
    spawns = (ActorSpawn("a", (2, 2)), ActorSpawn("b", (7, 7), ActorKind.COMPANION))
    first, second = (Simulation(world, spawns, rules=rules) for _ in range(2))
    for _ in range(20):
        actions = (
            Action("a", ActionKind.MOVE, first.tick, (1, 0), sprint=True),
            Action("b", ActionKind.MOVE, first.tick, (-1, 0)),
        )
        assert first.step(actions) == second.step(reversed(actions))
    assert first.fingerprint() == second.fingerprint()
    sim = Simulation(world, (spawns[0],), rules=rules)
    noise = []
    for _ in range(30):
        result = sim.step((Action("a", ActionKind.MOVE, sim.tick, (1, 0), sprint=True),))
        noise.extend(event for event in result.events if event.kind == EventKind.NOISE_CREATED)
    assert len(noise) == 3
    assert all(
        dict(event.details)["radius_tiles"] == rules.sprint_noise_radius_tiles for event in noise
    )


def test_invalid_rules_and_spawn_fail_at_boundary(rules: GameRules) -> None:
    with pytest.raises(ValueError):
        replace(rules, capture_windup_ticks=0)
    with pytest.raises(ValueError):
        replace(rules, actor_radius_units=UNIT)
    with pytest.raises(ValueError):
        GameRules.from_payload({"schema_version": 1})
    with pytest.raises(ValueError, match="walkable"):
        Simulation(
            StaticMap("bad", 2, 2, frozenset({(0, 0)})), (ActorSpawn("a", (0, 0)),), rules=rules
        )
