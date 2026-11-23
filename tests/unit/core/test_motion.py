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
from echo_heist.core.simulation.systems.motion import body_occupied, move_actor
from echo_heist.core.simulation.world import ActorState, WorldState
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
def test_chassis_blocks_sprint_but_a_stunned_guard_is_stepped_past(
    rules: GameRules, intruder: ActorKind
) -> None:
    rules = replace(rules, sprint_speed_units_per_second=960_000)
    # A one-tile lane with the guard standing in it: no way around the body.
    walls = frozenset((x, y) for x in range(8) for y in range(5) if not (y == 2 and 0 < x < 7))
    sim = Simulation(
        StaticMap("guard-chassis", 8, 5, walls, walls),
        (
            ActorSpawn("intruder", (1, 2), intruder),
            ActorSpawn("guard", (4, 2), ActorKind.SENTINEL),
        ),
        rules=rules,
        security=SecuritySpec(
            (GuardPatrol("guard", ((4, 2), (5, 2)), role=GuardRole.POST),), load_sensor_rules()
        ),
    )

    def move(direction: tuple[int, int], *, sprint: bool = False) -> None:
        sim.step((Action("intruder", ActionKind.MOVE, sim.tick, direction, sprint=sprint),))

    for _ in range(5):
        move((1, 0), sprint=True)
    blocked = sim.observe("intruder").own_status.position
    assert blocked is not None
    assert tile_center((4, 2))[0] - blocked[0] >= rules.guard_intruder_clearance_units

    hit = sim.step((Action("intruder", ActionKind.MELEE, sim.tick),))
    assert any(event.kind == EventKind.GUARD_STUNNED for event in hit.events)
    # The slumped body no longer walls off the lane: walk straight past it.
    for _ in range(20):
        move((1, 0))
    assert sim.observe("intruder").own_status.tile[0] >= 5
    assert sim.presentation_snapshot().mission_end is None


def test_overlapping_bodies_may_separate_but_not_press_closer(rules: GameRules) -> None:
    world = WorldState(
        {
            "intruder": ActorState("intruder", ActorKind.OPERATIVE, (60_000, 60_000)),
            "guard": ActorState("guard", ActorKind.SENTINEL, (66_000, 60_000)),
        }
    )
    intruder = world.actors["intruder"]
    assert body_occupied(world, intruder, (63_000, 60_000), rules)
    assert not body_occupied(world, intruder, (58_000, 60_000), rules)
    world.actors["guard"].stunned_until = 10
    assert not body_occupied(world, intruder, (66_000, 60_000), rules)


def test_a_guard_that_walks_into_an_unseen_body_turns_toward_it(rules: GameRules) -> None:
    # The thief stands at the guard's shoulder, outside a westward view cone.
    world = WorldState(
        {
            "guard": ActorState("guard", ActorKind.TRACKER, (66_000, 60_000), facing=(-1, 0)),
            "thief": ActorState("thief", ActorKind.COMPANION, (56_000, 50_000)),
        }
    )
    events: list[EventKind] = []
    move_actor(
        world,
        StaticMap("shoulder", 10, 10),
        rules,
        Action("guard", ActionKind.MOVE, 0, (-1, 0)),
        lambda kind, *_: events.append(kind),
    )
    guard = world.actors["guard"]
    assert guard.position == (66_000, 60_000) and events == [EventKind.ACTION_REJECTED]
    assert guard.facing == (-1, -1)


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
