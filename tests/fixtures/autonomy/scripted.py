"""Synthetic telemetry and ordinary scripted inputs, used only for presentation QA.

There is no MCTS/minimax/NEXUS implementation here. The runtime forwards real
actions to the real Simulation, so geometry, capture and outcomes are not faked.
"""

from collections.abc import Iterable
from dataclasses import replace

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.autonomy.model import (
    Alternative,
    AutonomyTelemetry,
    CompanionTrace,
    ControlMode,
    GuardTask,
    InterceptorTrace,
    LearnedProtocol,
    NexusTrace,
    ProtocolState,
)
from echo_heist.core.contracts.autonomy.policy import DeploymentRequest
from echo_heist.core.contracts.autonomy.runtime import DeploymentUnavailable, RuntimeAvailability
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.results import PresentationSnapshot, StepResult
from echo_heist.core.contracts.world import ActorKind, MissionPhase
from echo_heist.core.simulation.engine import Simulation
from echo_heist.diagnostics.guard_evidence import RouteDriver, route_steps
from echo_heist.infrastructure.resources import load_sensor_rules
from echo_heist.level.model import LevelData
from echo_heist.level.security import build_security_registry

ACTOR_ID = "echo-layout-fixture"


class ScriptedRun:
    def __init__(
        self,
        level: LevelData,
        rules: GameRules,
        request: DeploymentRequest,
        protocols: ProtocolState,
        *,
        route: bool = False,
    ) -> None:
        self.mode = request.mode
        self.actor_id = ACTOR_ID
        spawns = tuple(
            replace(spawn, actor_id=ACTOR_ID, kind=ActorKind.COMPANION)
            if spawn.actor_id == level.operative_id
            else spawn
            for spawn in level.spawns()
        )
        registry = build_security_registry(level, rules)
        self.simulation = Simulation(
            level.static_map,
            spawns,
            rules=rules,
            mission=replace(level.mission(), operative_id=ACTOR_ID, mode="COMPANION"),
            seed=request.seed,
            security=registry.spec(load_sensor_rules()),
        )
        self.runtime = self
        self.request = request
        self.protocol_state = protocols
        self.telemetry_calls = 0
        self.supplied: list[Action] = []
        self.route_driver = RouteDriver(rules, ACTOR_ID, use_tools=True)
        self.pending = route_steps(level, "upper", "upper") if route else []
        self.route_enabled = route

    @property
    def tick(self) -> int:
        return self.simulation.tick

    @property
    def ticks_per_second(self) -> int:
        return self.simulation.ticks_per_second

    def observe(self, actor_id: str) -> Observation:
        return self.simulation.observe(actor_id)

    def presentation_snapshot(self) -> PresentationSnapshot:
        return self.simulation.presentation_snapshot()

    def fingerprint(self) -> str:
        return self.simulation.fingerprint()

    def step(self, actions: Iterable[Action] = (), *, abort: bool = False) -> StepResult:
        supplied = tuple(actions)
        self.supplied.extend(supplied)
        if abort:
            return self.simulation.step(abort=True)
        assert not supplied, "Companion presentation must not issue player movement/tools"
        observation = self.observe(ACTOR_ID)
        if self.route_enabled:
            while self.pending:
                goal = self.pending[0]
                if goal == "HOLD":
                    if observation.phase == MissionPhase.LOCKDOWN:
                        self.pending.pop(0)
                        continue
                    return self.simulation.step((Action(ACTOR_ID, ActionKind.INTERACT, self.tick),))
                assert isinstance(goal, tuple)
                if self.route_driver.arrived(observation, goal):
                    self.pending.pop(0)
                    continue
                return self.simulation.step((self.route_driver.action(observation, goal),))
        # A short ordinary movement is enough to prove active-actor camera/input behavior.
        action = (
            Action(ACTOR_ID, ActionKind.MOVE, self.tick, (1, 0))
            if self.tick < 8
            else Action(ACTOR_ID, ActionKind.WAIT, self.tick)
        )
        return self.simulation.step((action,))

    def telemetry(self) -> AutonomyTelemetry:
        self.telemetry_calls += 1
        own = self.observe(ACTOR_ID).own_status
        return AutonomyTelemetry(
            CompanionTrace(
                ACTOR_ID,
                0,
                "INFILTRATE",
                "ADVANCE",
                "Synthetic layout values; algorithms are not exercised by this fixture.",
                64,
                (
                    Alternative("ADVANCE", 48, 0.82),
                    Alternative("WAIT", 12, 0.51),
                    Alternative("HIDE", 4, 0.34),
                    Alternative("EMP", 0, None, False),
                ),
                ((own.tile[0] + 1, own.tile[1]),),
                3,
                7,
                "RETREAT" if self.tick > 20 else "",
                "Synthetic utility row for layout QA.",
            ),
            NexusTrace(
                0,
                "Synthetic announcement / presentation QA",
                0,
                (GuardTask("guard-service", "CHECK SOUND", (22, 20), 0),),
                InterceptorTrace("guard-core", 0, "choke-research-core", (32, 34), 3, 18, 7, 0.62),
            ),
            self.protocol_state,
        )


class ScriptedGateway:
    def __init__(self, level: LevelData, rules: GameRules, *, route: bool = False) -> None:
        self.level, self.rules, self.route = level, rules, route
        self.state = ProtocolState(
            3,
            True,
            LearnedProtocol(
                "layout-protocol",
                "Echo verification",
                "Synthetic protocol rationale for presentation and reset checks.",
                ("Fixture evidence only",),
            ),
            True,
        )
        self.reset_calls = 0
        self.fail_reset = False
        self.fail_deploy = False
        self.wrong_mode = False
        self.requests: list[DeploymentRequest] = []
        self.runs: list[ScriptedRun] = []

    def availability(self) -> RuntimeAvailability:
        return RuntimeAvailability(
            frozenset({ControlMode.COMPANION}), True, "Scripted QA fixture only"
        )

    def protocols(self) -> ProtocolState:
        return self.state

    def reset_protocols(self) -> ProtocolState:
        self.reset_calls += 1
        if self.fail_reset:
            raise DeploymentUnavailable("Fixture reset failed; previous memory retained.")
        self.state = ProtocolState(self.state.revision + 1, True, None, False)
        return self.state

    def deploy(self, request: DeploymentRequest) -> ScriptedRun:
        self.requests.append(request)
        if self.fail_deploy:
            raise DeploymentUnavailable("Fixture deployment failed; no attempt started.")
        run = ScriptedRun(self.level, self.rules, request, self.state, route=self.route)
        if self.wrong_mode:
            run.mode = ControlMode.HUMAN
        self.runs.append(run)
        return run
