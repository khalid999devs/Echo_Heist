"""NEXUS protocol memory: evidence, one protocol, persistence, recovery and full reset."""

import json
from pathlib import Path

import pytest

from echo_heist.autonomy.gateway import NexusGateway
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.autonomy.model import ControlMode
from echo_heist.core.contracts.autonomy.policy import DeploymentRequest, PolicySelection
from echo_heist.core.contracts.autonomy.runtime import DeploymentUnavailable
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.results import MissionEnd, RunOutcome
from echo_heist.core.contracts.security.director import NexusEvidence, NexusStatus
from echo_heist.infrastructure.persistence.protocols import FILE_NAME, ProtocolStore
from echo_heist.infrastructure.resources import load_sensor_rules, resource_bytes
from echo_heist.level.io import load_tiled_map
from echo_heist.level.model import LevelData


@pytest.fixture(scope="module")
def level() -> LevelData:
    return load_tiled_map(resource_bytes("data/maps/vault-five-zone.json"))


def gateway(level: LevelData, rules: GameRules, folder: Path) -> NexusGateway:
    return NexusGateway(level, rules, load_sensor_rules(), ProtocolStore(folder / FILE_NAME))


def finish(service: NexusGateway, evidence: NexusEvidence) -> None:
    end = MissionEnd(RunOutcome.CAPTURED, 100, "operative", "guard-core")
    service._attempt_ended(end, NexusStatus(100, (), "", None, evidence))


def wait_run(service: NexusGateway, level: LevelData, ticks: int) -> str:
    run = service.deploy(DeploymentRequest(ControlMode.HUMAN, 7, level.static_map.map_id))
    for _ in range(ticks):
        run.step((Action(level.operative_id, ActionKind.WAIT, run.tick),))
    return run.fingerprint()


def test_evidence_selects_one_persisted_protocol_and_reset_clears_it(
    level: LevelData, rules: GameRules, tmp_path: Path
) -> None:
    service = gateway(level, rules, tmp_path)
    assert service.availability().modes == {ControlMode.HUMAN, ControlMode.COMPANION}
    baseline = service.protocols()
    assert baseline.active is None and baseline.enabled and not baseline.can_reset
    finish(service, NexusEvidence(echo_witnessed=1))
    assert service.protocols().active is None  # one witnessed decoy is below threshold
    # Several kinds of evidence at once still expose exactly one justified protocol.
    finish(service, NexusEvidence(1, (("research-floor", 3),), 1))
    state = service.protocols()
    assert state.active is not None and state.active.protocol_id == "REINFORCE_ROUTE:research-floor"
    assert state.active.evidence == ("3 confirmed contacts in research-floor",)
    reloaded = gateway(level, rules, tmp_path)
    assert reloaded.protocols() == state and reloaded.memory.attempts == 2
    cleared = reloaded.reset_protocols()
    assert cleared.active is None and not cleared.can_reset and cleared.revision > state.revision
    saved = json.loads((tmp_path / FILE_NAME).read_text())
    assert saved["attempts"] == 0 and saved["totals"]["contacts"] == {} and saved["active"] is None


def test_reset_memory_reproduces_the_baseline_attempt(
    level: LevelData, rules: GameRules, tmp_path: Path
) -> None:
    service = gateway(level, rules, tmp_path)
    before = wait_run(service, level, 240)
    for _ in range(2):
        finish(service, NexusEvidence(0, (("security-control", 1),), 0))
    assert service.protocols().active is not None
    run = service.deploy(DeploymentRequest(ControlMode.HUMAN, 7, level.static_map.map_id))
    nexus = run.telemetry().nexus
    assert nexus is not None and nexus.announcement_tick == 0 and "REINFORCE" in nexus.announcement
    adapted = wait_run(service, level, 240)
    assert adapted != before  # the Interceptor really holds the reinforced gate
    service.reset_protocols()
    assert wait_run(service, level, 240) == before


def test_a_real_attempt_records_its_observed_evidence_exactly_once(
    level: LevelData, rules: GameRules, tmp_path: Path
) -> None:
    service = gateway(level, rules, tmp_path)
    request = DeploymentRequest(
        ControlMode.COMPANION, 1, level.static_map.map_id, PolicySelection()
    )
    run = service.deploy(request)
    while run.presentation_snapshot().mission_end is None and run.tick < 9_000:
        run.step(())
    assert service.memory.attempts == 1 and service.memory.totals.contacts
    for _ in range(5):
        run.step(())  # further steps after the end never record again
    assert service.memory.attempts == 1
    telemetry = run.telemetry().protocols
    assert telemetry is not None and telemetry.revision == service.protocols().revision


def test_corrupt_memory_is_quarantined_and_future_memory_is_refused(
    level: LevelData, rules: GameRules, tmp_path: Path
) -> None:
    path = tmp_path / FILE_NAME
    path.write_text("{broken")
    service = gateway(level, rules, tmp_path)
    assert service.protocols().active is None
    assert list(tmp_path.glob("nexus-memory.corrupt-*.json"))
    future = {"schema": 99, "revision": 4}
    path.write_text(json.dumps(future))
    refusing = gateway(level, rules, tmp_path)
    assert not refusing.availability().protocols
    with pytest.raises(DeploymentUnavailable):
        refusing.reset_protocols()
    assert json.loads(path.read_text()) == future  # never silently overwritten
    # Play is still possible; it simply runs without any adaptation.
    run = refusing.deploy(DeploymentRequest(ControlMode.HUMAN, 7, level.static_map.map_id))
    assert run.telemetry().protocols is None
