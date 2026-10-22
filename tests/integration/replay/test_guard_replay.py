"""Default-security routes on the packaged map: real outcomes, traces and exact replay."""

from dataclasses import replace

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.security.model import SensorRules
from echo_heist.core.simulation.replay import build_header, verify_replay
from echo_heist.diagnostics.facility_routes import Branch
from echo_heist.diagnostics.guard_evidence import (
    ScenarioResult,
    build_simulation,
    replay_matches,
    route_steps,
    run_route,
)
from echo_heist.infrastructure.resources import load_sensor_rules, resource_bytes
from echo_heist.level.io import load_tiled_map
from echo_heist.level.model import LevelData
from echo_heist.level.security import SecurityRegistry, build_security_registry


@pytest.fixture(scope="module")
def level() -> LevelData:
    return load_tiled_map(resource_bytes("data/maps/vault-five-zone.json"))


@pytest.fixture(scope="module")
def sensors() -> SensorRules:
    return load_sensor_rules()


@pytest.fixture(scope="module")
def registry(level: LevelData, rules: GameRules) -> SecurityRegistry:
    return build_security_registry(level, rules)


@pytest.fixture(scope="module")
def upper(
    level: LevelData, rules: GameRules, sensors: SensorRules, registry: SecurityRegistry
) -> ScenarioResult:
    return run_route("upper", level, rules, sensors, registry, route_steps(level, "upper", "upper"))


@pytest.mark.parametrize(("branch", "back"), [("lower", "lower"), ("cross", "upper")])
def test_default_security_routes_win_with_real_guard_algorithms(
    level: LevelData,
    rules: GameRules,
    sensors: SensorRules,
    registry: SecurityRegistry,
    upper: ScenarioResult,
    branch: Branch,
    back: Branch,
) -> None:
    result = run_route(branch, level, rules, sensors, registry, route_steps(level, branch, back))
    for outcome in (upper, result):
        assert outcome.outcome == "WIN"
        assert outcome.events["CORE_TAKEN"] == outcome.events["LOCKDOWN_STARTED"] == 1
        assert outcome.algorithms["BFS"] > 0 and outcome.algorithms["A*"] > 0
        assert outcome.max_expanded["A*"] > 0 and outcome.events["SIGHTING_CONFIRMED"] > 0


def test_careless_route_is_captured_by_a_live_defender(
    level: LevelData, rules: GameRules, sensors: SensorRules, registry: SecurityRegistry
) -> None:
    result = run_route(
        "lower-no-tools",
        level,
        rules,
        sensors,
        registry,
        route_steps(level, "lower", "lower"),
        use_tools=False,
    )
    assert result.outcome == "CAPTURED" and result.capture_by in {
        value.guard_id for value in registry.assignments
    }
    assert result.events["CAPTURE_STARTED"] >= result.events["CAPTURE_COMPLETED"] == 1


def test_recorded_run_replays_exactly_and_detects_changed_inputs(
    level: LevelData,
    rules: GameRules,
    sensors: SensorRules,
    registry: SecurityRegistry,
    upper: ScenarioResult,
) -> None:
    assert replay_matches(level, rules, sensors, registry, upper)
    log = upper.log
    assert log.header.fingerprint_schema == 8 and log.header.registry_revision == registry.revision
    header = build_header(
        level.static_map, rules, sensors, registry_revision=registry.revision, seed=1042
    )
    # Drop one real intent: the event stream must diverge at exactly that tick.
    index = next(i for i, actions in enumerate(log.actions) if actions and i > 40)
    edited = replace(
        log,
        actions=(
            *log.actions[:index],
            (Action(level.operative_id, ActionKind.WAIT, index),),
            *log.actions[index + 1 :],
        ),
    )
    check = verify_replay(build_simulation(level, rules, sensors, registry, 1042), edited, header)
    assert not check.matched and check.first_divergent_tick == index + 1
    other = replace(header, sensor_hash="0" * 64)
    assert not verify_replay(
        build_simulation(level, rules, sensors, registry, 1042), log, other
    ).matched
