"""P06 experience service: real scored reports, history, profiles, preferences, protocol switch."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from echo_heist.autonomy.gateway import NexusGateway, connect_experience, connect_gateway
from echo_heist.core.contracts.autonomy.model import ControlMode
from echo_heist.core.contracts.autonomy.policy import PRESETS, DeploymentRequest, PolicySelection
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.experience.model import (
    Achievement,
    DesktopPreferences,
    KeyAssignment,
    ResultRequest,
)
from echo_heist.core.contracts.experience.ports import ExperienceUnavailable
from echo_heist.core.contracts.results import RunOutcome
from echo_heist.core.contracts.security.model import SensorRules
from echo_heist.infrastructure.persistence.experience import (
    HISTORY_FILE,
    PREFERENCES_FILE,
    PROFILES_FILE,
)
from echo_heist.infrastructure.resources import load_sensor_rules, resource_bytes
from echo_heist.level.io import load_tiled_map
from echo_heist.level.model import LevelData


@pytest.fixture(scope="module")
def level() -> LevelData:
    return load_tiled_map(resource_bytes("data/maps/vault-five-zone.json"))


@pytest.fixture(scope="module")
def sensors() -> SensorRules:
    return load_sensor_rules()


def finish(
    gateway: NexusGateway, request: DeploymentRequest, key: str, *, abort: bool
) -> ResultRequest:
    run = gateway.deploy(request)
    if abort:
        run.step(abort=True)
    while run.presentation_snapshot().mission_end is None and run.tick < 9_000:
        run.step(())
    end = run.presentation_snapshot().mission_end
    assert end is not None
    return ResultRequest(key, request.map_id, request.seed, request.mode, end, 30, run.tools)


def test_scored_reports_are_authoritative_matched_and_persisted(
    tmp_path: Path, level: LevelData, rules: GameRules, sensors: SensorRules
) -> None:
    gateway = connect_gateway(level, rules, sensors, tmp_path)
    service = connect_experience(gateway, tmp_path)
    map_id = level.static_map.map_id
    aborted = finish(gateway, DeploymentRequest("HUMAN", 7, map_id), "app:1", abort=True)
    # A request that does not describe a finished attempt gets no report.
    wrong = ResultRequest("app:x", map_id, 8, ControlMode.HUMAN, aborted.end, 30)
    assert service.report(wrong) is None
    # Rejected metadata must leave the real finished run available.
    assert service.report(replace(aborted, tools=replace(aborted.tools, echo=1))) is None
    assert service.report(replace(aborted, ticks_per_second=60)) is None
    report = service.report(aborted)
    assert report is not None and report.matches(aborted)
    assert (report.result.score, report.result.grade, report.policy_label) == (0, "F", "Human")
    assert service.report(aborted) is report  # one report per run key
    win = finish(gateway, DeploymentRequest("COMPANION", 1042, map_id), "app:2", abort=False)
    scored = service.report(win)
    assert scored is not None and scored.result.outcome == RunOutcome.WIN
    r = scored.result
    assert r.score == r.completion_points + r.stealth_points + r.pace_points
    assert r.completion_points == 50 and r.stealth_points == 40 - 12 * r.detection_encounters
    assert Achievement.AI_MASTER in scored.achievements and scored.policy_label == "Balanced"
    assert r.policy_id == "BALANCED-RETREAT-EMP_IF_TRAPPED-BALANCED"
    assert r.decisive_events and r.decisive_events[-1].kind.value == "MISSION_ENDED"
    assert any(dict(event.details).get("algorithm") == "MCTS" for event in r.decisive_events)
    # A fresh process sees the same history, newest first.
    again = connect_experience(connect_gateway(level, rules, sensors, tmp_path), tmp_path)
    assert [h.run_key for h in again.history()] == ["app:2", "app:1"]
    assert again.history()[0] == scored


def test_profiles_save_overwrite_limit_delete_and_survive_restart(
    tmp_path: Path, level: LevelData, rules: GameRules, sensors: SensorRules
) -> None:
    service = connect_experience(connect_gateway(level, rules, sensors, tmp_path), tmp_path)
    first = service.save_profile("Night run", PRESETS["GHOST"])
    updated = service.save_profile("night RUN", PRESETS["RUSH"])
    assert updated.profile_id == first.profile_id and len(service.profiles()) == 1
    for index in range(31):
        service.save_profile(f"P{index}", PolicySelection())
    with pytest.raises(ExperienceUnavailable):
        service.save_profile("one too many", PolicySelection())
    with pytest.raises(ValueError):
        service.save_profile("x" * 25, PolicySelection())
    service.delete_profile(first.profile_id)
    with pytest.raises(ExperienceUnavailable):
        service.delete_profile(first.profile_id)
    restarted = connect_experience(connect_gateway(level, rules, sensors, tmp_path), tmp_path)
    profiles = restarted.profiles()
    assert len(profiles) == 31 and all(p.profile_id != first.profile_id for p in profiles)
    # A saved custom policy is labelled by its profile name in reports.
    custom = restarted.save_profile("Careful", PolicySelection(risk=PRESETS["GHOST"].risk))
    assert restarted._label(DeploymentRequest("COMPANION", 1, "m", custom.policy)) == "Careful"


@pytest.mark.parametrize("name", [PROFILES_FILE, HISTORY_FILE, PREFERENCES_FILE])
def test_damaged_files_are_kept_aside_once_and_newer_files_never_overwritten(
    tmp_path: Path, level: LevelData, rules: GameRules, sensors: SensorRules, name: str
) -> None:
    service = connect_experience(connect_gateway(level, rules, sensors, tmp_path), tmp_path)
    read = {
        PROFILES_FILE: service.profiles,
        HISTORY_FILE: service.history,
        PREFERENCES_FILE: service.preferences,
    }[name]
    (tmp_path / name).write_text("{not json", encoding="utf-8")
    with pytest.raises(ExperienceUnavailable, match="kept as"):
        read()
    assert len(list(tmp_path.glob("*.corrupt-*.json"))) == 1
    read()  # started fresh
    newer = json.dumps({"schema": 99, "profiles": [], "reports": [], "controls": []})
    (tmp_path / name).write_text(newer, encoding="utf-8")
    fresh = connect_experience(connect_gateway(level, rules, sensors, tmp_path), tmp_path)
    with pytest.raises(ExperienceUnavailable, match="newer build"):
        {PROFILES_FILE: fresh.profiles, HISTORY_FILE: fresh.history}.get(name, fresh.preferences)()
    with pytest.raises(ExperienceUnavailable):
        if name == PROFILES_FILE:
            fresh.save_profile("x", PolicySelection())
        elif name == PREFERENCES_FILE:
            fresh.save_preferences(DesktopPreferences())
        else:
            raise ExperienceUnavailable("history is written only with a report")
    assert (tmp_path / name).read_text(encoding="utf-8") == newer


def test_preferences_round_trip_and_protocol_switch_persists(
    tmp_path: Path, level: LevelData, rules: GameRules, sensors: SensorRules
) -> None:
    gateway = connect_gateway(level, rules, sensors, tmp_path)
    service = connect_experience(gateway, tmp_path)
    chosen = DesktopPreferences((KeyAssignment("echo", (113, 120)),), subtitles=False)
    service.save_preferences(chosen)
    assert connect_experience(gateway, tmp_path).preferences() == chosen
    state = gateway.set_protocols_enabled(False)
    assert not state.enabled and state.active is None
    restarted = connect_gateway(level, rules, sensors, tmp_path)
    assert not restarted.protocols().enabled
    assert restarted.set_protocols_enabled(True).enabled
