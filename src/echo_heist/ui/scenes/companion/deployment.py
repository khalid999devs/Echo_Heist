"""Explicit runtime handoff, honest availability and backend-owned protocol reset."""

from echo_heist.core.contracts.autonomy.model import ControlMode, ProtocolState
from echo_heist.core.contracts.autonomy.policy import (
    DeploymentRequest,
    Emergency,
    GuardReaction,
    Navigation,
    PolicySelection,
    Risk,
)
from echo_heist.core.contracts.autonomy.runtime import (
    AutonomousRun,
    AutonomyGateway,
    DeploymentUnavailable,
    RuntimeAvailability,
)
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.world import ActorKind, StaticMap
from echo_heist.level.model import LevelData
from echo_heist.ui.scenes.design.model import WorkshopDraft


def selection(draft: WorkshopDraft) -> PolicySelection:
    return PolicySelection(
        tuple(Navigation)[draft.choices[0]],
        tuple(GuardReaction)[draft.choices[1]],
        tuple(Emergency)[draft.choices[2]],
        tuple(Risk)[draft.choices[3]],
    )


def restore_selection(draft: WorkshopDraft, policy: PolicySelection) -> None:
    draft.choices = [
        tuple(Navigation).index(policy.navigation),
        tuple(GuardReaction).index(policy.guard_reaction),
        tuple(Emergency).index(policy.emergency),
        tuple(Risk).index(policy.risk),
    ]
    from echo_heist.ui.scenes.design.model import PRESET_VALUES

    draft.preset = next(
        (i for i, values in enumerate(PRESET_VALUES) if tuple(draft.choices) == values), -1
    )


def same_facility(physical: StaticMap, authored: StaticMap) -> bool:
    """The runtime plays the authored map: same identity, stairs and objects.

    Its physical geometry may add committed prop state (intact glass, closed
    doors) on top of the authored walls, but never removes an authored wall.
    """
    return (
        physical.map_id == authored.map_id
        and (physical.width, physical.height) == (authored.width, authored.height)
        and physical.stairs == authored.stairs
        and physical.objects == authored.objects
        and authored.blocked_tiles <= physical.blocked_tiles
        and authored.opaque_tiles <= physical.opaque_tiles
    )


class DeploymentPanel:
    def __init__(self, gateway: AutonomyGateway | None = None) -> None:
        self.gateway = gateway
        self.available = RuntimeAvailability()
        self.protocol_state: ProtocolState | None = None
        self.notice = ""
        self.refresh()

    @property
    def can_deploy(self) -> bool:
        return ControlMode.COMPANION in self.available.modes

    @property
    def can_reset(self) -> bool:
        return self.protocol_state is not None and self.protocol_state.can_reset

    def protocols_for(self, mode: ControlMode) -> ProtocolState | None:
        return self.protocol_state if mode in self.available.modes else None

    def refresh(self) -> None:
        if self.gateway is None:
            return
        try:
            self.available = self.gateway.availability()
            self.protocol_state = self.gateway.protocols() if self.available.protocols else None
            self.notice = ""
        except DeploymentUnavailable as error:
            self.available = RuntimeAvailability(reason=str(error))
            self.protocol_state = None
            self.notice = str(error)

    def reset(self) -> bool:
        if self.gateway is None or not self.can_reset:
            self.notice = "NEXUS memory reset is not available."
            return False
        try:
            state = self.gateway.reset_protocols()
        except DeploymentUnavailable as error:
            self.notice = str(error)
            return False
        self.protocol_state = state
        self.notice = "NEXUS memory reset."
        return True

    @property
    def can_toggle_memory(self) -> bool:
        return self.protocol_state is not None and callable(
            getattr(self.gateway, "set_protocols_enabled", None)
        )

    def toggle_memory(self) -> None:
        if not self.can_toggle_memory or self.gateway is None or self.protocol_state is None:
            self.notice = "NEXUS memory is unavailable."
            return
        try:
            self.protocol_state = self.gateway.set_protocols_enabled(
                not self.protocol_state.enabled
            )
        except DeploymentUnavailable as error:
            self.notice = str(error)
        else:
            self.notice = (
                "NEXUS memory enabled." if self.protocol_state.enabled else "NEXUS memory disabled."
            )

    def deploy(
        self, request: DeploymentRequest, level: LevelData, rules: GameRules
    ) -> AutonomousRun | None:
        if request.mode == ControlMode.HUMAN and request.mode not in self.available.modes:
            return None  # The verified built-in Human runtime is still available.
        if self.gateway is None or request.mode not in self.available.modes:
            raise DeploymentUnavailable(self.available.reason)
        run = self.gateway.deploy(request)
        snapshot = run.runtime.presentation_snapshot()
        actor = next((actor for actor in snapshot.actors if actor.actor_id == run.actor_id), None)
        expected = (
            ActorKind.COMPANION if request.mode == ControlMode.COMPANION else ActorKind.OPERATIVE
        )
        if (
            run.mode != request.mode
            or actor is None
            or actor.kind != expected
            or run.runtime.tick != 0
            or run.runtime.ticks_per_second != rules.simulation_hz
            or not same_facility(snapshot.world_map, level.static_map)
        ):
            raise DeploymentUnavailable("Runtime does not match this mission, mode or rules.")
        return run
