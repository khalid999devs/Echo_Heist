from dataclasses import replace
from math import hypot

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.results import MissionSpec
from echo_heist.core.contracts.security.model import GuardPatrol, GuardState, SecuritySpec
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, MapObject, StaticMap, Tile
from echo_heist.core.simulation.engine import Simulation
from echo_heist.infrastructure.resources import load_sensor_rules


def simulation(
    rules: GameRules, player: Tile, *, opaque: frozenset[Tile] = frozenset()
) -> Simulation:
    border = frozenset((x, y) for x in range(12) for y in range(10) if x in (0, 11) or y in (0, 9))
    world = StaticMap("sentinel-fixture", 12, 10, border | opaque, border | opaque)
    patrol = GuardPatrol("sentinel", ((3, 3), (6, 3), (6, 6), (3, 6)))
    spec = SecuritySpec((patrol,), load_sensor_rules(), world.opaque_tiles)
    return Simulation(
        world,
        (ActorSpawn("operative", player), ActorSpawn("sentinel", (3, 3), ActorKind.SENTINEL)),
        rules=rules,
        security=spec,
    )


def test_timed_sprint_is_audible_while_light_walk_stays_local(rules: GameRules) -> None:
    walk = simulation(rules, (3, 6))
    run = simulation(rules, (3, 6))
    walk.step((Action("operative", ActionKind.MOVE, 0, direction=(0, 1)),))
    run.step((Action("operative", ActionKind.MOVE, 0, direction=(0, 1), sprint=True),))
    assert not walk.observe("sentinel").heard_events
    heard = run.observe("sentinel").heard_events
    assert any(cue.kind == "SPRINT" and cue.tile == (3, 6) for cue in heard)
    run.step()  # controller consumes the last committed observation on its next tick
    guard = run.presentation_snapshot().guards[0]
    assert guard.state == GuardState.INVESTIGATE


def test_bfs_patrol_is_physical_and_unseen_position_cannot_change_decisions(
    rules: GameRules,
) -> None:
    wall = frozenset((8, y) for y in range(1, 9))
    first, second = simulation(rules, (10, 6), opaque=wall), simulation(rules, (10, 7), opaque=wall)
    traces = []
    start = next(
        actor.position
        for actor in first.presentation_snapshot().actors
        if actor.actor_id == "sentinel"
    )
    for _ in range(100):
        traces.extend(first.step().events)
        second.step()
        assert first.observe("sentinel") == second.observe("sentinel")
        assert first.presentation_snapshot().guards == second.presentation_snapshot().guards
    end = next(
        actor for actor in first.presentation_snapshot().actors if actor.actor_id == "sentinel"
    )
    assert end.position != start and first.observe("sentinel").map_static.can_walk(end.tile)
    assert any(
        event.kind == EventKind.POLICY_DECISION
        and dict(event.details).get("algorithm") == "BFS"
        and dict(event.details).get("expanded_nodes", 0) > 0
        for event in traces
    )
    assert first.fingerprint() != second.fingerprint()


def test_hearing_reveals_only_occluded_noise_origin(rules: GameRules) -> None:
    sim = simulation(rules, (5, 2), opaque=frozenset({(4, 3)}))
    sim.step((Action("operative", ActionKind.MOVE, 0, (1, 0), sprint=True),))
    observation = sim.observe("sentinel")
    assert not observation.visible_entities
    assert observation.heard_events[0].tile == (5, 2)
    sim.step()
    view = sim.presentation_snapshot().guards[0]
    assert view.state == GuardState.INVESTIGATE and view.target == (5, 2)
    assert view.last_seen_tile is None and view.identification_ticks == 0


def test_identification_reports_actual_tick_and_emp_interrupts_capture(rules: GameRules) -> None:
    sim = simulation(rules, (4, 3))
    events = []
    for _ in range(12):
        events.extend(sim.step().events)
        if sim.presentation_snapshot().captures:
            break
    assert any(event.kind == EventKind.SIGHTING_CONFIRMED for event in events)
    report = sim.observe("sentinel").shared_reports[0]
    assert report.tile == (4, 3) and report.tick < sim.tick
    assert sim.presentation_snapshot().captures
    result = sim.step((Action("operative", ActionKind.EMP, sim.tick),))
    assert any(event.kind == EventKind.CAPTURE_CANCELED for event in result.events)
    assert result.mission_end is None and not sim.presentation_snapshot().captures


def test_reports_expire_while_guard_is_disabled_and_external_guard_intents_reject(
    rules: GameRules,
) -> None:
    sim = simulation(rules, (5, 3))
    for _ in range(19):
        sim.step()
    assert sim.observe("sentinel").shared_reports
    result = sim.step(
        (
            Action("operative", ActionKind.EMP, sim.tick),
            Action("sentinel", ActionKind.MOVE, sim.tick, (0, -1)),
        )
    )
    assert any(
        event.kind == EventKind.ACTION_REJECTED
        and dict(event.details).get("reason") == "simulation_controlled_actor"
        for event in result.events
    )
    for _ in range(88):
        sim.step()
    assert not sim.observe("sentinel").shared_reports


def test_active_security_replay_repeats(rules: GameRules) -> None:
    first, second = (
        simulation(rules, (5, 2), opaque=frozenset({(4, 3)})),
        simulation(rules, (5, 2), opaque=frozenset({(4, 3)})),
    )
    for tick in range(50):
        actions = (
            (Action("operative", ActionKind.MOVE, tick, (1, 0), sprint=True),) if tick < 20 else ()
        )
        assert first.step(actions) == second.step(actions)
    assert first.fingerprint() == second.fingerprint()


@pytest.mark.parametrize("intruder_kind", [ActorKind.OPERATIVE, ActorKind.COMPANION])
@pytest.mark.parametrize("lockdown", [False, True])
def test_only_confirmed_pursuit_accelerates_guard(
    rules: GameRules, intruder_kind: ActorKind, lockdown: bool
) -> None:
    rules = replace(rules, core_interaction_ticks=1)
    world = StaticMap(
        "pursuit-speed",
        24,
        12,
        objects=(MapObject("core", "Core", (10, 4)), MapObject("exit", "Exit", (20, 4))),
    )
    spec = SecuritySpec((GuardPatrol("sentinel", ((3, 4), (18, 4))),), load_sensor_rules())
    spawns = (
        ActorSpawn("intruder", (10, 4), intruder_kind),
        ActorSpawn("sentinel", (3, 4), ActorKind.SENTINEL),
    )
    mission = MissionSpec("intruder", "core", "exit") if lockdown else None
    boosted = Simulation(world, spawns, rules=rules, security=spec, mission=mission)
    ordinary = Simulation(
        world,
        spawns,
        rules=replace(rules, chase_guard_speed_percent=100),
        security=spec,
        mission=mission,
    )
    if lockdown:
        for sim in (boosted, ordinary):
            sim.step((Action("intruder", ActionKind.INTERACT, sim.tick, target_id="core"),))
    saw_partial = saw_confirmed = False
    for _ in range(40):
        before = [sim.observe("sentinel").own_status.position for sim in (boosted, ordinary)]
        results = [sim.step() for sim in (boosted, ordinary)]
        after = [sim.observe("sentinel").own_status.position for sim in (boosted, ordinary)]
        distances = []
        for old, new in zip(before, after, strict=True):
            assert old is not None and new is not None
            distances.append(hypot(new[0] - old[0], new[1] - old[1]))
        state = boosted.presentation_snapshot().guards[0].state
        if state == GuardState.SPOTTED:
            saw_partial = True
            assert distances[0] == distances[1]
            assert boosted.observe("sentinel") == ordinary.observe("sentinel")
        elif state == GuardState.CHASE:
            saw_confirmed = True
            assert any(event.kind == EventKind.SIGHTING_CONFIRMED for event in results[0].events)
            assert distances[0] == (
                rules.sentinel_speed_units_per_second
                * max(
                    rules.chase_guard_speed_percent,
                    rules.lockdown_guard_speed_percent if lockdown else 100,
                )
                // 100
                // rules.simulation_hz
            )
            if lockdown:
                assert distances[0] == distances[1]  # no runaway stacked multiplier
            else:
                assert distances[0] > distances[1]
            break
    assert saw_partial and saw_confirmed
