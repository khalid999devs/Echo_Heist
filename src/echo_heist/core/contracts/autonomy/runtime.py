"""Structural ports: Suhita implements orchestration; UI never implements AI.

The existing Simulation satisfies MissionRuntime. An autonomous implementation
must select actions from filtered observations and forward them to Simulation.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from echo_heist.core.contracts.actions import Action
from echo_heist.core.contracts.autonomy.model import AutonomyTelemetry, ControlMode, ProtocolState
from echo_heist.core.contracts.autonomy.policy import DeploymentRequest
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.results import PresentationSnapshot, StepResult


class DeploymentUnavailable(RuntimeError):
    """An expected unavailable/failed deployment or protocol operation."""


@dataclass(frozen=True, slots=True)
class RuntimeAvailability:
    modes: frozenset[ControlMode] = frozenset()
    protocols: bool = False
    reason: str = "Companion controller is not connected yet."

    def __post_init__(self) -> None:
        object.__setattr__(self, "modes", frozenset(ControlMode(mode) for mode in self.modes))


class MissionRuntime(Protocol):
    @property
    def tick(self) -> int: ...
    @property
    def ticks_per_second(self) -> int: ...
    def observe(self, actor_id: str) -> Observation: ...
    def presentation_snapshot(self) -> PresentationSnapshot: ...
    def step(self, actions: Iterable[Action] = (), *, abort: bool = False) -> StepResult: ...
    def fingerprint(self) -> str: ...


class AutonomousRun(Protocol):
    @property
    def actor_id(self) -> str: ...
    @property
    def mode(self) -> ControlMode: ...
    @property
    def runtime(self) -> MissionRuntime: ...
    def telemetry(self) -> AutonomyTelemetry: ...


class AutonomyGateway(Protocol):
    def availability(self) -> RuntimeAvailability: ...
    def protocols(self) -> ProtocolState: ...
    def reset_protocols(self) -> ProtocolState: ...
    def deploy(self, request: DeploymentRequest) -> AutonomousRun: ...
