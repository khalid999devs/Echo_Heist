"""NEXUS and the Interceptor in the packaged Simulation: evidence-limited and physical."""

from dataclasses import replace
from itertools import pairwise

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.security.director import TaskKind
from echo_heist.core.contracts.world import MissionPhase, tile_center
from echo_heist.core.simulation.engine import Simulation
from echo_heist.diagnostics.guard_evidence import RouteDriver, route_steps
from echo_heist.infrastructure.resources import load_sensor_rules, resource_bytes
from echo_heist.level.io import load_tiled_map
from echo_heist.level.model import LevelData
from echo_heist.level.security import build_security_registry


@pytest.fixture(scope="module")
def level() -> LevelData:
    return load_tiled_map(resource_bytes("data/maps/vault-five-zone.json"))


def simulation(
    level: LevelData, rules: GameRules, spawn: tuple[int, int] | None = None
) -> Simulation:
    registry = build_security_registry(level, rules)
    spawns = tuple(
        replace(value, tile=spawn) if spawn and value.actor_id == level.operative_id else value
        for value in level.spawns()
    )
    return Simulation(
        level.static_map,
        spawns,
        rules=rules,
        mission=level.mission(),
        security=registry.spec(load_sensor_rules()),
    )


def test_nexus_ignores_where_an_unseen_intruder_really_is(
    level: LevelData, rules: GameRules
) -> None:
    first, second = simulation(level, rules), simulation(level, rules, (5, 21))
    for _ in range(240):
        for sim in (first, second):
            sim.step((Action(level.operative_id, ActionKind.WAIT, sim.tick),))
        assert first.nexus_status() == second.nexus_status()
        assert first.presentation_snapshot().guards == second.presentation_snapshot().guards
    assert first.fingerprint() != second.fingerprint()  # the hidden worlds really differ


def test_lockdown_interceptor_searches_and_walks_to_its_gate(
    level: LevelData, rules: GameRules
) -> None:
    sim = simulation(level, rules)
    driver = RouteDriver(rules, level.operative_id)
    pending = route_steps(level, "lower", "lower")
    taken: int | None = None
    path: list[tuple[int, int]] = []
    announcements: set[tuple[str, int | None]] = set()
    lockdown_plans = []
    while sim.tick < 4000 and sim.presentation_snapshot().mission_end is None:
        observation = sim.observe(level.operative_id)
        if pending and pending[0] == "HOLD":
            if observation.phase == MissionPhase.LOCKDOWN:
                pending.pop(0)
                continue
            action = Action(
                level.operative_id, ActionKind.INTERACT, sim.tick, target_id=level.core_id
            )
        elif pending and isinstance(pending[0], tuple):
            if driver.arrived(observation, pending[0]):
                pending.pop(0)
                continue
            action = driver.action(observation, pending[0])
        else:
            action = Action(level.operative_id, ActionKind.WAIT, sim.tick)
        result = sim.step((action,))
        if any(event.kind == EventKind.CORE_TAKEN for event in result.events):
            taken = result.tick
        status = sim.nexus_status()
        assert status is not None
        if status.announcement:
            announcements.add((status.announcement, status.announcement_tick))
        plan = dict(sim.intercept_plans()).get("guard-core")
        if (
            taken is not None
            and plan is not None
            and plan.evidence_tick >= taken
            and (not lockdown_plans or lockdown_plans[-1] != plan)
        ):
            lockdown_plans.append(plan)
        if taken is not None:
            core = next(a for a in sim.presentation_snapshot().actors if a.actor_id == "guard-core")
            assert core.position is not None
            path.append(core.position)
    assert taken is not None and announcements == {(next(iter(announcements))[0], taken)}
    status = sim.nexus_status()
    assert status is not None
    assert any(
        order.guard_id == "guard-core"
        and order.task == TaskKind.INTERCEPT
        and order.evidence_tick == taken
        for order in status.dispatches
    )
    # Searched on the first post-alarm evidence (the order or its own lost sighting).
    plan = lockdown_plans[0]
    assert plan.depth == 3 and len(plan.hypotheses) >= 2
    assert plan.evaluated_leaves > 0 and plan.pruned_branches > 0
    assert plan.post_id == "choke-research-core"
    # Physical travel: bounded per-tick displacement, and it reaches the chosen gate.
    limit = rules.interceptor_speed_units_per_second * 140 // 100 // rules.simulation_hz + 1
    assert all(abs(a[0] - b[0]) + abs(a[1] - b[1]) <= 2 * limit for a, b in pairwise(path))
    post = tile_center(plan.post_tile)
    assert min(abs(p[0] - post[0]) + abs(p[1] - post[1]) for p in path) <= 3_000
