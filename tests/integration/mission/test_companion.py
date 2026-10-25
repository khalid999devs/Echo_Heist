"""The autonomous Companion on the packaged mission: real wins, real captures, fair inputs."""

from dataclasses import replace

import pytest

from echo_heist.ai.companion import tactics
from echo_heist.ai.companion.controller import CompanionController, Directive
from echo_heist.autonomy.mission import COMPANION_ID, AutonomousMission, build_briefing
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.autonomy.model import CompanionTrace
from echo_heist.core.contracts.autonomy.policy import DeploymentRequest, PolicySelection
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.results import RunOutcome
from echo_heist.core.contracts.security.model import SensorRules
from echo_heist.core.contracts.world import ActorKind, Inventory
from echo_heist.core.simulation.engine import Simulation
from echo_heist.diagnostics.guard_evidence import RouteDriver, route_steps
from echo_heist.infrastructure.resources import load_sensor_rules, resource_bytes
from echo_heist.level.io import load_tiled_map
from echo_heist.level.model import LevelData
from echo_heist.level.security import SecurityRegistry, build_security_registry

WIN_SEED, CAPTURE_SEED = 6, 1  # Balanced outcomes on this map/rules revision


@pytest.fixture(scope="module")
def level() -> LevelData:
    return load_tiled_map(resource_bytes("data/maps/vault-five-zone.json"))


@pytest.fixture(scope="module")
def sensors() -> SensorRules:
    return load_sensor_rules()


@pytest.fixture(scope="module")
def registry(level: LevelData, rules: GameRules) -> SecurityRegistry:
    return build_security_registry(level, rules)


def deploy(
    level: LevelData, rules: GameRules, sensors: SensorRules, registry: SecurityRegistry, seed: int
) -> AutonomousMission:
    request = DeploymentRequest("COMPANION", seed, level.static_map.map_id, PolicySelection())
    return AutonomousMission(
        level, rules, sensors, registry, request, protocol=None, protocol_state=None
    )


def play(run: AutonomousMission, limit: int = 9_000) -> tuple[list[CompanionTrace], list[str]]:
    traces: list[CompanionTrace] = []
    kinds: list[str] = []
    while run.tick < limit:
        result = run.step(())  # the UI supplies no movement or tools in Companion mode
        kinds.extend(event.kind.value for event in result.events)
        trace = run.telemetry().companion
        if trace is not None and (not traces or traces[-1].evaluated_tick != trace.evaluated_tick):
            traces.append(trace)
        if result.mission_end is not None:
            break
    return traces, kinds


@pytest.mark.parametrize(
    ("seed", "outcome"), [(WIN_SEED, RunOutcome.WIN), (CAPTURE_SEED, RunOutcome.CAPTURED)]
)
def test_companion_genuinely_wins_or_is_captured_without_recordings(
    level: LevelData,
    rules: GameRules,
    sensors: SensorRules,
    registry: SecurityRegistry,
    seed: int,
    outcome: RunOutcome,
) -> None:
    run = deploy(level, rules, sensors, registry, seed)
    actor = next(a for a in run.presentation_snapshot().actors if a.actor_id == COMPANION_ID)
    assert actor.kind == ActorKind.COMPANION and run.tick == 0
    traces, kinds = play(run)
    end = run.presentation_snapshot().mission_end
    assert end is not None and end.outcome == outcome and end.operative_id == COMPANION_ID
    if outcome == RunOutcome.WIN:
        assert kinds.count("CORE_TAKEN") == 1 and kinds.count("LOCKDOWN_STARTED") == 1
    # Real search evidence: 64 simulations, visits within budget, >=3 alternatives.
    assert traces and all(trace.simulations == 64 for trace in traces)
    assert all(sum(a.visits for a in trace.alternatives) <= 64 for trace in traces)
    assert any(len([a for a in t.alternatives if a.visits]) >= 3 for t in traces)
    assert any(a.mean_reward is None and not a.legal for t in traces for a in t.alternatives)
    assert any(t.path and t.path_cost is not None and t.expanded_nodes > 0 for t in traces)


def test_controller_depends_only_on_its_observations_and_seed(
    level: LevelData, rules: GameRules, sensors: SensorRules, registry: SecurityRegistry
) -> None:
    run = deploy(level, rules, sensors, registry, CAPTURE_SEED)
    observations: list[Observation] = []
    actions: list[Action] = []
    original = run.controller
    assert original is not None

    def recording(observation: Observation) -> Action:
        observations.append(observation)
        actions.append(choose(observation))
        return actions[-1]

    choose = original.act
    original.act = recording  # type: ignore[method-assign]
    play(run, 1_200)
    replica = CompanionController(
        COMPANION_ID,
        build_briefing(level, registry),
        PolicySelection(),
        rules,
        seed=CAPTURE_SEED,
        sight_range_tiles=sensors.sight_range_tiles,
        half_angle_degrees=sensors.half_angle_degrees,
    )
    assert [replica.act(observation) for observation in observations] == actions
    # The Companion's own view never contains radio reports or guard memories.
    assert all(not observation.shared_reports for observation in observations)


def test_stale_tool_choice_falls_back_to_a_legal_wait(
    level: LevelData, rules: GameRules, sensors: SensorRules, registry: SecurityRegistry
) -> None:
    run = deploy(level, rules, sensors, registry, WIN_SEED)
    controller = run.controller
    assert controller is not None
    observation = run.observe(COMPANION_ID)
    empty = replace(observation.own_status, inventory=Inventory(0, 0, False))
    controller.directive = Directive(tactics.EMP)
    action = controller._execute(replace(observation, own_status=empty), (13, 19))
    assert action.kind == ActionKind.WAIT


def test_human_actions_are_forwarded_unchanged_with_the_same_defenders(
    level: LevelData, rules: GameRules, sensors: SensorRules, registry: SecurityRegistry
) -> None:
    request = DeploymentRequest("HUMAN", 1042, level.static_map.map_id)
    run = AutonomousMission(
        level, rules, sensors, registry, request, protocol=None, protocol_state=None
    )
    direct = Simulation(
        level.static_map,
        level.spawns(),
        rules=rules,
        mission=level.mission(),
        seed=1042,
        security=registry.spec(sensors),
    )
    driver = RouteDriver(rules, level.operative_id)
    goals = [step for step in route_steps(level, "upper", "upper") if isinstance(step, tuple)]
    for _ in range(600):
        observation = direct.observe(level.operative_id)
        while goals and driver.arrived(observation, goals[0]):
            goals.pop(0)
        action = (
            driver.action(observation, goals[0])
            if goals
            else Action(level.operative_id, ActionKind.WAIT, observation.tick)
        )
        first, second = run.step((action,)), direct.step((action,))
        assert first.events == second.events
    assert run.fingerprint() == direct.fingerprint()
    assert run.tick == direct.tick == 600
