from dataclasses import replace
from math import hypot

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.results import MissionSpec
from echo_heist.core.contracts.security.model import GuardPatrol, GuardRole, SecuritySpec
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, MapObject, StaticMap, tile_center
from echo_heist.core.simulation.engine import Simulation
from echo_heist.infrastructure.resources import load_sensor_rules


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
    own, other = pair.observe("a").own_status.position, pair.observe("b").own_status.position
    assert own is not None and other is not None
    assert own[0] < other[0] and other[0] - own[0] >= 2 * rules.actor_radius_units


@pytest.mark.parametrize("intruder", [ActorKind.OPERATIVE, ActorKind.COMPANION])
def test_chassis_blocks_sprint_but_stun_buys_time_to_go_around(
    rules: GameRules, intruder: ActorKind
) -> None:
    rules = replace(rules, sprint_speed_units_per_second=960_000)
    # One tile wide approaching a guard, with a side bay at the contact point.
    open_tiles = {(x, 2) for x in range(1, 7)} | {(x, 3) for x in range(3, 7)}
    walls = frozenset((x, y) for x in range(8) for y in range(6) if (x, y) not in open_tiles)
    sim = Simulation(
        StaticMap("guard-chassis", 8, 6, walls, walls),
        (
            ActorSpawn("intruder", (1, 2), intruder),
            ActorSpawn("guard", (4, 2), ActorKind.SENTINEL),
        ),
        rules=rules,
        security=SecuritySpec(
            (GuardPatrol("guard", ((4, 2), (5, 2)), role=GuardRole.POST),), load_sensor_rules()
        ),
    )

    def sprint(direction: tuple[int, int]) -> None:
        sim.step((Action("intruder", ActionKind.MOVE, sim.tick, direction, sprint=True),))

    for _ in range(5):
        sprint((1, 0))
    blocked = sim.observe("intruder").own_status.position
    assert blocked is not None
    assert tile_center((4, 2))[0] - blocked[0] >= rules.guard_intruder_clearance_units

    hit = sim.step((Action("intruder", ActionKind.MELEE, sim.tick),))
    assert any(event.kind == EventKind.GUARD_STUNNED for event in hit.events)
    sprint((1, 0))
    assert sim.observe("intruder").own_status.position == blocked
    for _ in range(13):
        sprint((0, 1))
    for _ in range(24):
        sprint((1, 0))
    assert sim.observe("intruder").own_status.tile == (5, 3)
    assert sim.presentation_snapshot().mission_end is None


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
    assert len(noise) == (30 + rules.sprint_footstep_interval_ticks - 1) // (
        rules.sprint_footstep_interval_ticks
    )
    assert all(
        dict(event.details)["radius_tiles"] == rules.sprint_noise_radius_tiles for event in noise
    )


def test_invalid_rules_and_spawn_fail_at_boundary(rules: GameRules) -> None:
    with pytest.raises(ValueError):
        replace(rules, capture_windup_ticks=0)
    with pytest.raises(ValueError):
        replace(rules, actor_radius_units=UNIT)
    with pytest.raises(ValueError, match="Pursuit speed"):
        replace(rules, chase_guard_speed_percent=151)
    with pytest.raises(ValueError):
        GameRules.from_payload({"schema_version": 1})
    with pytest.raises(ValueError, match="walkable"):
        Simulation(
            StaticMap("bad", 2, 2, frozenset({(0, 0)})), (ActorSpawn("a", (0, 0)),), rules=rules
        )


def test_lockdown_accelerates_actual_guard_motion_without_buffing_player(rules: GameRules) -> None:
    tuned = replace(rules, core_interaction_ticks=1)
    world = StaticMap(
        "lockdown-speed",
        20,
        20,
        objects=(MapObject("core", "Core", (2, 2)), MapObject("exit", "Exit", (1, 1))),
    )
    spawns = (ActorSpawn("operative", (2, 2)), ActorSpawn("guard", (8, 8), ActorKind.SENTINEL))
    sim = Simulation(world, spawns, rules=tuned, mission=MissionSpec("operative", "core", "exit"))
    sim.step((Action("operative", ActionKind.INTERACT, 0, target_id="core"),))
    old_guard, old_player = (
        sim.observe("guard").own_status.position,
        sim.observe("operative").own_status.position,
    )
    assert old_guard is not None and old_player is not None
    sim.step(
        (
            Action("guard", ActionKind.MOVE, sim.tick, (1, 0)),
            Action("operative", ActionKind.MOVE, sim.tick, (1, 0)),
        )
    )
    guard, player = (
        sim.observe("guard").own_status.position,
        sim.observe("operative").own_status.position,
    )
    assert guard is not None and player is not None
    assert (
        guard[0] - old_guard[0]
        == rules.sentinel_speed_units_per_second
        * rules.lockdown_guard_speed_percent
        // 100
        // rules.simulation_hz
    )
    assert player[0] - old_player[0] == rules.walk_speed_units_per_second // rules.simulation_hz
