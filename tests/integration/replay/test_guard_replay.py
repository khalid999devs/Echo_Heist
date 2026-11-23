"""Default-security routes on the packaged map: real outcomes, traces and exact replay."""

from dataclasses import replace

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.security.model import SensorRules
from echo_heist.core.simulation.replay import build_header, verify_replay
from echo_heist.diagnostics.facility_routes import Branch, anchor
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
    # Starting 4.5 seconds later lets the Service patrol turn away first.
    return run_route(
        "upper",
        level,
        rules,
        sensors,
        registry,
        route_steps(level, "upper", "upper"),
        wait_start_ticks=135,
    )


def test_entry_route_wins_with_real_guard_algorithms(
    level: LevelData,
    upper: ScenarioResult,
) -> None:
    assert upper.outcome == "WIN"
    assert upper.final_tiles[level.operative_id] == anchor(level, "entry-exit")
    assert upper.events["CORE_TAKEN"] == upper.events["LOCKDOWN_STARTED"] == 1
    assert upper.algorithms["BFS"] > 0 and upper.algorithms["A*"] > 0
    assert upper.max_expanded["A*"] > 0 and upper.events["SIGHTING_CONFIRMED"] > 0
    assert upper.algorithms["ALPHA-BETA"] > 0


def test_exposed_cargo_return_is_caught_after_taking_the_core(
    level: LevelData, rules: GameRules, sensors: SensorRules, registry: SecurityRegistry
) -> None:
    result = run_route(
        "cargo",
        level,
        rules,
        sensors,
        registry,
        route_steps(level, "upper", "upper", exit_id="cargo-exit"),
        wait_start_ticks=135,
    )
    assert result.events["CORE_TAKEN"] == 1
    # The Cargo Interceptor searches its own Service Wing gates and walks to
    # Stairs B, closing the corridor the Service Sentinel is sweeping.
    assert result.intercept_posts["guard-cargo"][0] == "choke-service-research"
    assert result.outcome == "CAPTURED" and result.capture_by == "guard-service"
    assert result.events["CAPTURE_COMPLETED"] == 1


def test_blind_return_through_the_predicted_gate_is_intercepted(
    level: LevelData, rules: GameRules, sensors: SensorRules, registry: SecurityRegistry
) -> None:
    """P04: after the lockdown the Interceptor searches the escape branches,
    picks the Research Return gate and walks there; returning blindly along that
    branch runs into it on the way, while the alternate corridor (above) wins."""
    result = run_route(
        "research-return",
        level,
        rules,
        sensors,
        registry,
        route_steps(level, "upper", "lower"),
        wait_start_ticks=135,
    )
    assert result.outcome == "CAPTURED" and result.events["CORE_TAKEN"] == 1
    assert result.capture_by == "guard-core" and result.algorithms["ALPHA-BETA"] > 0
    assert result.intercept_posts["guard-core"][-1] == "choke-research-core"
    # Each Interceptor defends only its home gates: the second one holds the
    # Service Wing end of the same predicted Research branch.
    assert result.intercept_posts["guard-cargo"] == ("choke-service-research",)
    assert registry.graph is not None
    gate = registry.graph.node("choke-research-core").tile
    core = registry.graph.core_tile
    caught = result.final_tiles[level.operative_id]

    def steps(a: tuple[int, int], b: tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # Caught at the predicted gate: the Interceptor patrols the hall beside it,
    # holds it before the runner arrives and grabs it within reach of the gate.
    assert steps(caught, gate) <= 4 < steps(core, gate)


@pytest.mark.parametrize(
    ("branch", "captor"),
    [("lower", "guard-research"), ("upper", "guard-service")],
)
def test_careless_route_is_captured_by_a_live_defender(
    level: LevelData,
    rules: GameRules,
    sensors: SensorRules,
    registry: SecurityRegistry,
    branch: Branch,
    captor: str,
) -> None:
    result = run_route(
        f"{branch}-no-tools",
        level,
        rules,
        sensors,
        registry,
        route_steps(level, branch, "lower", exit_id="cargo-exit"),
        use_tools=False,
    )
    assert result.outcome == "CAPTURED" and result.capture_by == captor
    assert "CHASE" in result.states[captor]
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
    assert log.header.fingerprint_schema == 17 and log.header.registry_revision == registry.revision
    header = build_header(
        level.static_map, rules, sensors, registry_revision=registry.revision, seed=1042
    )
    # Drop one real intent: the event stream must diverge at exactly that tick.
    index = next(
        i
        for i, actions in enumerate(log.actions)
        if actions and i > 40 and actions[0].kind != ActionKind.WAIT
    )
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
