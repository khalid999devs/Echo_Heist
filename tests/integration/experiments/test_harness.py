"""P07 registry/harness: valid 24-scenario suite, deterministic records, softlock regression."""

import pytest

from echo_heist.autonomy.mission import AutonomousMission
from echo_heist.core.contracts.autonomy.policy import PRESETS, DeploymentRequest
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.world import MissionPhase
from echo_heist.experiments.harness import Facility, run_scenario
from echo_heist.experiments.scenarios import CATEGORIES, Suite, load_suite
from echo_heist.infrastructure.resources import (
    load_environment_rules,
    load_scoring_rules,
    load_sensor_rules,
    resource_bytes,
)
from echo_heist.level.environment import build_environment
from echo_heist.level.io import load_tiled_map
from echo_heist.level.security import build_security_registry


@pytest.fixture(scope="module")
def facility(rules: GameRules) -> Facility:
    level = load_tiled_map(resource_bytes("data/maps/vault-five-zone.json"))
    return Facility(
        level,
        rules,
        load_sensor_rules(),
        build_security_registry(level, rules),
        build_environment(level, load_environment_rules()),
        load_scoring_rules(),
    )


@pytest.fixture(scope="module")
def suite() -> Suite:
    return load_suite()


def test_registry_has_24_valid_starts_across_every_category(
    facility: Facility, suite: Suite
) -> None:
    assert len(suite.scenarios) == 24 and suite.map_id == facility.level.static_map.map_id
    assert {s.category for s in suite.scenarios} == set(CATEGORIES)
    assert [name for name, _ in suite.policies] == ["GHOST", "BALANCED", "RUSH", "CUSTOM"]
    assert all(dict(suite.policies)[name] == PRESETS[name] for name in PRESETS)
    for scenario in suite.scenarios:
        run = AutonomousMission(
            facility.level,
            facility.rules,
            facility.sensors,
            facility.registry,
            DeploymentRequest("COMPANION", scenario.seed, suite.map_id),
            protocol=None,
            protocol_state=None,
            environment=facility.environment,
            start=scenario.start,
            hold_ticks=scenario.hold_ticks,
        )
        own = run.observe(run.actor_id)
        if scenario.start.tile is not None:
            assert own.own_status.tile == scenario.start.tile
        assert own.own_status.inventory == scenario.start.inventory()
        assert (own.phase == MissionPhase.LOCKDOWN) == scenario.start.core_held


def test_records_are_deterministic_and_carry_metadata(facility: Facility, suite: Suite) -> None:
    scenario = next(s for s in suite.scenarios if s.scenario_id == "s23-lockdown-core-chamber")
    first = run_scenario(facility, scenario, "RUSH", PRESETS["RUSH"], suite.tick_cap)
    second = run_scenario(facility, scenario, "RUSH", PRESETS["RUSH"], suite.tick_cap)
    first.pop("timing")
    second.pop("timing")
    assert first == second
    assert first["outcome"] in ("WIN", "CAPTURED")
    mcts = first["mcts"]
    assert isinstance(mcts, dict) and mcts["decisions"] > 0
    assert first["category"] == "lockdown-return" and first["seed"] == scenario.seed
    # Same seed, same start, different Workshop policy: a real decision change.
    ghost = run_scenario(facility, scenario, "GHOST", PRESETS["GHOST"], suite.tick_cap)
    assert ghost["fingerprint"] != first["fingerprint"]
    assert ghost["mcts"] != first["mcts"] or ghost["route_zones"] != first["route_zones"]


@pytest.mark.parametrize("scenario_id", ["s06-upper-stairs-late", "s08-lower-stairs-late"])
def test_pursuit_reaches_an_outcome_around_either_stair_route(
    facility: Facility, suite: Suite, scenario_id: str
) -> None:
    scenario = next(s for s in suite.scenarios if s.scenario_id == scenario_id)
    record = run_scenario(facility, scenario, "BALANCED", PRESETS["BALANCED"], suite.tick_cap)
    assert record["outcome"] != "TIMEOUT"


@pytest.mark.parametrize(
    ("scenario_id", "policy", "reached"),
    [
        ("s03-patrol-6s", "RUSH", "security-control"),
        ("s16-service-corridor-late", "GHOST", "core-chamber"),
    ],
)
def test_policies_resume_goal_progress_after_repeated_retreats(
    facility: Facility, suite: Suite, scenario_id: str, policy: str, reached: str
) -> None:
    scenario = next(s for s in suite.scenarios if s.scenario_id == scenario_id)
    record = run_scenario(facility, scenario, policy, PRESETS[policy], 4_000)
    assert record["outcome"] in ("WIN", "CAPTURED")
    assert reached in record["route_zones"]
    assert record["mcts"]["utility_override_ticks"] > 0
