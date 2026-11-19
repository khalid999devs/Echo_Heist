"""The real AutonomyGateway: deployment, NEXUS protocol persistence and reset.

Both Human and Companion attempts are deployed through the same Simulation,
defender registry and NEXUS. The active protocol is chosen between attempts
from persisted, legitimately observed evidence; it is announced through
``protocols()`` before deployment and fixed for the attempt. Disk access happens
only at construction, on reset and once when an attempt ends; never in drawing.
"""

from dataclasses import replace
from pathlib import Path

from echo_heist.ai.director import protocols as rules_of
from echo_heist.ai.director.protocols import ProtocolMemory
from echo_heist.autonomy.experience import ExperienceService
from echo_heist.autonomy.mission import AutonomousMission, ResultListener
from echo_heist.core.contracts.autonomy.model import ControlMode, ProtocolState
from echo_heist.core.contracts.autonomy.policy import DeploymentRequest
from echo_heist.core.contracts.autonomy.runtime import DeploymentUnavailable, RuntimeAvailability
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.results import MissionEnd
from echo_heist.core.contracts.security.director import NexusStatus
from echo_heist.core.contracts.security.model import GuardRole, SensorRules
from echo_heist.infrastructure.persistence.protocols import (
    FILE_NAME,
    FutureProtocolVersion,
    ProtocolStore,
)
from echo_heist.infrastructure.resources import load_environment_rules, load_scoring_rules
from echo_heist.level.environment import build_environment
from echo_heist.level.model import LevelData
from echo_heist.level.security import build_security_registry


class NexusGateway:
    def __init__(
        self,
        level: LevelData,
        rules: GameRules,
        sensors: SensorRules,
        store: ProtocolStore | None,
    ) -> None:
        self.level, self.rules, self.sensors, self.store = level, rules, sensors, store
        self.registry = build_security_registry(level, rules)
        # Doors, glass, canisters and lockers authored in the map (P05-SR2).
        self.environment = build_environment(level, load_environment_rules())
        self.scoring = load_scoring_rules()
        # Optional P06 listener that receives each attempt's authoritative score.
        self.result_listener: ResultListener | None = None
        graph = self.registry.graph
        homes = {
            value.zone_id
            for value in self.registry.assignments
            if value.role == GuardRole.INTERCEPTOR
        }
        # Sectors an Interceptor can actually reinforce from its home gates.
        self.reinforceable = frozenset(
            zone
            for node in (graph.nodes if graph else ())
            if homes & set(node.zones)
            for zone in node.zones
            if zone not in homes
        )
        self.problem = ""
        self.memory = ProtocolMemory()
        if store is not None:
            try:
                self.memory = store.load()
            except FutureProtocolVersion as error:
                self.problem = str(error)
            except OSError as error:
                self.problem = f"NEXUS memory could not be read: {error}"
        self.attempt_notice = ""

    def availability(self) -> RuntimeAvailability:
        return RuntimeAvailability(
            frozenset({ControlMode.HUMAN, ControlMode.COMPANION}), not self.problem, self.problem
        )

    def protocols(self) -> ProtocolState:
        if self.problem:
            raise DeploymentUnavailable(self.problem)
        return rules_of.state(self.memory)

    def reset_protocols(self) -> ProtocolState:
        if self.problem:
            raise DeploymentUnavailable(self.problem)
        cleared = rules_of.reset(self.memory)
        if self.store is not None:
            try:
                self.store.save(cleared)
            except OSError as error:
                raise DeploymentUnavailable(f"NEXUS memory reset failed: {error}") from error
        self.memory = cleared
        return rules_of.state(cleared)

    def set_protocols_enabled(self, enabled: bool) -> ProtocolState:
        """Turn NEXUS adaptation on or off for later attempts (persisted).

        Disabling clears any selected protocol so the next attempt is the
        baseline; recorded evidence is kept for when it is enabled again.
        """
        if self.problem:
            raise DeploymentUnavailable(self.problem)
        if type(enabled) is not bool:
            raise ValueError("The protocol switch must be a boolean")
        updated = replace(
            self.memory,
            revision=self.memory.revision + 1,
            enabled=enabled,
            active=self.memory.active if enabled else None,
            rationale=self.memory.rationale if enabled else "",
        )
        if self.store is not None:
            try:
                self.store.save(updated)
            except OSError as error:
                raise DeploymentUnavailable(f"NEXUS memory not saved: {error}") from error
        self.memory = updated
        return rules_of.state(updated)

    def deploy(self, request: DeploymentRequest) -> AutonomousMission:
        if request.map_id != self.level.static_map.map_id:
            raise DeploymentUnavailable(f"Map {request.map_id!r} is not loaded")
        protocol = self.memory.active if self.memory.enabled and not self.problem else None
        state = None if self.problem else rules_of.state(self.memory)
        return AutonomousMission(
            self.level,
            self.rules,
            self.sensors,
            self.registry,
            request,
            protocol=protocol,
            protocol_state=state,
            on_end=self._attempt_ended,
            environment=self.environment,
            scoring=self.scoring,
            on_result=self.result_listener,
        )

    def _attempt_ended(self, _end: MissionEnd, status: NexusStatus | None) -> ProtocolState | None:
        """Record the finished attempt's legitimate evidence exactly once."""
        if status is None or self.problem:
            return None
        updated = rules_of.record_attempt(self.memory, status.evidence, self.reinforceable)
        self.memory = updated
        if self.store is not None:
            try:
                self.store.save(updated)
            except OSError as error:
                self.attempt_notice = f"NEXUS memory not saved: {error}"
        return rules_of.state(updated)


def connect_gateway(
    level: LevelData, rules: GameRules, sensors: SensorRules, data_dir: Path | None
) -> NexusGateway:
    """Composition helper for the desktop startup worker."""
    store = ProtocolStore(data_dir / FILE_NAME) if data_dir is not None else None
    return NexusGateway(level, rules, sensors, store)


def connect_experience(gateway: NexusGateway, data_dir: Path | None) -> ExperienceService:
    """The real P06 experience service, fed by every attempt the gateway deploys."""
    service = ExperienceService(
        gateway.level.static_map.map_id,
        gateway.scoring,
        data_dir,
        ticks_per_second=gateway.rules.simulation_hz,
    )
    gateway.result_listener = service.attempt_finished
    return service
