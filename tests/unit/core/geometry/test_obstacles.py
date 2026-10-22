"""Reserved placement tiles must not become invisible physical or sight barriers."""

from dataclasses import replace

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.world import ActorSpawn, ObstacleBounds, StaticMap, tile_center
from echo_heist.core.perception.sensors import line_of_sight
from echo_heist.core.simulation.engine import Simulation
from echo_heist.core.simulation.systems.motion import body_fits, clear_reach


def rack_map() -> StaticMap:
    reserved = frozenset({(3, 2), (3, 3)})
    rack = ObstacleBounds("rack", 105_000, 60_000, 120_000, 120_000, reserved)
    return StaticMap("rack", 10, 8, reserved, reserved, obstacles=(rack,))


def test_walk_and_sight_use_physical_fixture_bounds_and_keep_walls_solid() -> None:
    world = rack_map()
    # Empty left half of the placement footprint is real walkable floor.
    fringe = (96_000, 90_000)
    assert body_fits(world, fringe, 6000)
    assert not body_fits(world, (102_000, 90_000), 6000)
    assert clear_reach(world, (96_000, 45_000), (96_000, 135_000))
    assert line_of_sight(world, (96_000, 45_000), (96_000, 135_000))
    assert not line_of_sight(world, (112_500, 45_000), (112_500, 135_000))
    wall = replace(world, blocked_tiles=world.blocked_tiles | {(2, 5)})
    assert not body_fits(wall, tile_center((2, 5)), 6000)
    assert not world.can_walk((3, 2))  # conservative tile navigation is preserved


def test_fast_motion_stops_at_fixture_edge_and_replay_includes_geometry(rules: GameRules) -> None:
    tuned = replace(rules, sprint_speed_units_per_second=900_000, actor_radius_units=6000)
    world = rack_map()
    runs = [Simulation(world, (ActorSpawn("operative", (1, 3)),), rules=tuned) for _ in range(2)]
    for sim in runs:
        for _ in range(8):
            sim.step((Action("operative", ActionKind.MOVE, sim.tick, (1, 0), sprint=True),))
        own = sim.observe("operative").own_status
        assert own.position is not None and 96_000 <= own.position[0] <= 99_000
    assert runs[0].fingerprint() == runs[1].fingerprint()
    wider = replace(world, obstacles=(replace(world.obstacles[0], left=90_000),))
    spawn = (ActorSpawn("operative", (1, 3)),)
    assert (
        Simulation(world, spawn, rules=rules).fingerprint()
        != Simulation(wider, spawn, rules=rules).fingerprint()
    )


def test_fine_desk_bounds_preserve_low_headroom_and_opaque_cover() -> None:
    desk = frozenset({(2, 2), (3, 2), (4, 2)})
    world = StaticMap(
        "desk",
        8,
        8,
        desk,
        desk,
        crouch_tiles=frozenset({(3, 2)}),
        obstacles=(ObstacleBounds("desk", 60_000, 60_000, 150_000, 90_000, desk),),
    )
    assert body_fits(world, tile_center((3, 2)), 6000, crouched=True)
    assert not body_fits(world, tile_center((3, 2)), 6000)
    assert not body_fits(world, tile_center((2, 2)), 6000, crouched=True)
    assert not line_of_sight(world, tile_center((3, 1)), tile_center((3, 3)))


def test_invalid_geometry_is_rejected_before_simulation() -> None:
    with pytest.raises(ValueError, match="integer"):
        replace(rack_map().obstacles[0], left=100_000.5)
    with pytest.raises(ValueError, match="reserved"):
        replace(rack_map().obstacles[0], right=121_000)
    with pytest.raises(ValueError, match="Duplicate"):
        replace(rack_map(), obstacles=rack_map().obstacles * 2)
