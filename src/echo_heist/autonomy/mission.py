"""One deployed attempt: the real Simulation plus controller orchestration.

Human mode forwards the player's supplied actions unchanged. Companion mode
ignores supplied input and asks the Companion controller, which reads only the
Companion's own filtered Observation. Every mutation is a Simulation step. After
each committed step an immutable telemetry record is cached for presentation;
``telemetry()`` never runs a search, reads disk or feeds anything back to AI.
"""

from collections.abc import Callable, Iterable
from dataclasses import replace

from echo_heist.ai.companion.briefing import GuardBrief, MissionBriefing
from echo_heist.ai.companion.controller import CompanionController
from echo_heist.core.contracts.actions import Action
from echo_heist.core.contracts.autonomy.model import (
    AutonomyTelemetry,
    ControlMode,
    GuardTask,
    InterceptorTrace,
    NexusTrace,
    ProtocolState,
)
from echo_heist.core.contracts.autonomy.policy import DeploymentRequest
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.results import MissionEnd, PresentationSnapshot, StepResult
from echo_heist.core.contracts.security.director import ActiveProtocol, NexusStatus
from echo_heist.core.contracts.security.model import SensorRules
from echo_heist.core.contracts.world import ActorKind
from echo_heist.core.simulation.engine import Simulation
from echo_heist.level.model import LevelData
from echo_heist.level.security import SecurityRegistry

COMPANION_ID = "echo-companion"
TASK_LABELS = {
    "PROTECT_EXIT": "PROTECT EXIT",
    "INTERCEPT": "INTERCEPT",
    "SUPPORT_PURSUIT": "SUPPORT PURSUIT",
    "INVESTIGATE_NOISE": "CHECK SOUND",
}

type AttemptEnded = Callable[[MissionEnd, NexusStatus | None], ProtocolState | None]


def build_briefing(level: LevelData, registry: SecurityRegistry) -> MissionBriefing:
    """Public facts only: the map/graph, cover, anchors and the defender roster."""
    if registry.graph is None:
        raise ValueError("The Companion needs the public route graph")
    core = next(obj.tile for obj in level.static_map.objects if obj.object_id == level.core_id)
    return MissionBriefing(
        level.core_id,
        core,
        registry.graph.exit_tile,
        registry.graph,
        tuple(sorted(level.static_map.crouch_tiles)),
        tuple(
            GuardBrief(value.guard_id, value.kind, value.zone_id) for value in registry.assignments
        ),
    )


class AutonomousMission:
    """Implements AutonomousRun and MissionRuntime for one attempt."""

    def __init__(
        self,
        level: LevelData,
        rules: GameRules,
        sensors: SensorRules,
        registry: SecurityRegistry,
        request: DeploymentRequest,
        *,
        protocol: ActiveProtocol | None,
        protocol_state: ProtocolState | None,
        on_end: AttemptEnded | None = None,
    ) -> None:
        self._mode = ControlMode(request.mode)
        companion = self._mode == ControlMode.COMPANION
        self._actor_id = COMPANION_ID if companion else level.operative_id
        spawns = tuple(
            replace(spawn, actor_id=self._actor_id, kind=ActorKind.COMPANION)
            if companion and spawn.actor_id == level.operative_id
            else spawn
            for spawn in level.spawns()
        )
        self.simulation = Simulation(
            level.static_map,
            spawns,
            rules=rules,
            mission=replace(level.mission(self._mode.value), operative_id=self._actor_id),
            seed=request.seed,
            security=registry.spec(sensors, protocol),
        )
        self.request, self.protocol = request, protocol
        self.controller = (
            CompanionController(
                self._actor_id,
                build_briefing(level, registry),
                request.policy,
                rules,
                seed=request.seed,
                sight_range_tiles=sensors.sight_range_tiles,
                half_angle_degrees=sensors.half_angle_degrees,
            )
            if companion
            else None
        )
        self._protocol_state = protocol_state
        self._on_end = on_end
        self._ended = False
        self._telemetry = self._sample()

    # MissionRuntime -------------------------------------------------------
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
        if abort:
            result = self.simulation.step(abort=True)
        elif self.controller is not None:
            if self.simulation.presentation_snapshot().mission_end is None:
                choice = self.controller.act(self.simulation.observe(self._actor_id))
                result = self.simulation.step((choice,))
            else:
                result = self.simulation.step(())
        else:
            result = self.simulation.step(supplied)
        self._telemetry = self._sample()
        if result.mission_end is not None and not self._ended:
            self._ended = True
            if self._on_end is not None:
                # The service records this attempt once and returns its new state.
                self._protocol_state = self._on_end(
                    result.mission_end, self.simulation.nexus_status()
                )
                self._telemetry = self._sample()
        return result

    # AutonomousRun --------------------------------------------------------
    @property
    def actor_id(self) -> str:
        return self._actor_id

    @property
    def mode(self) -> ControlMode:
        return self._mode

    @property
    def runtime(self) -> "AutonomousMission":
        return self

    def telemetry(self) -> AutonomyTelemetry:
        return self._telemetry

    def _sample(self) -> AutonomyTelemetry:
        status = self.simulation.nexus_status()
        plans = dict(self.simulation.intercept_plans())
        nexus = None
        if status is not None:
            plan = next(iter(plans.items()), None)
            nexus = NexusTrace(
                max(0, status.evaluated_tick),
                status.announcement,
                status.announcement_tick,
                tuple(
                    GuardTask(
                        order.guard_id,
                        TASK_LABELS[order.task.value],
                        order.target,
                        order.evidence_tick,
                    )
                    for order in status.dispatches
                ),
                InterceptorTrace(
                    plan[0],
                    plan[1].evaluated_tick,
                    plan[1].post_id,
                    plan[1].post_tile,
                    plan[1].depth,
                    plan[1].evaluated_leaves,
                    plan[1].pruned_branches,
                    plan[1].value,
                )
                if plan is not None
                else None,
            )
        trace = self.controller.trace if self.controller is not None else None
        return AutonomyTelemetry(trace, nexus, self._protocol_state)
