"""Khalid's results/profile/preferences screens on the real P06 services (no fixtures)."""

from pathlib import Path

import pygame

from echo_heist.autonomy.gateway import connect_experience, connect_gateway
from echo_heist.core.contracts.autonomy.policy import PRESETS
from echo_heist.core.contracts.experience.model import DesktopPreferences
from echo_heist.infrastructure.resources import load_game_rules, load_sensor_rules
from echo_heist.ui.scenes.flow import GameFlow, Scene, load_level


def test_real_report_history_profile_and_preferences_round_trip(tmp_path: Path) -> None:
    pygame.font.init()
    level, rules = load_level(), load_game_rules()
    gateway = connect_gateway(level, rules, load_sensor_rules(), tmp_path)
    experience = connect_experience(gateway, tmp_path)
    experience.save_preferences(DesktopPreferences(subtitles=False, high_contrast=True))
    flow = GameFlow(
        (1280, 720),
        level=level,
        rules=rules,
        autonomy_gateway=gateway,
        experience_gateway=experience,
    )
    assert flow.preferences.preferences.high_contrast and not flow.preferences.notice
    assert flow._start_run()
    flow.airlock.skip()
    session = flow.session
    assert session is not None
    session.simulation.step(abort=True)
    session.terminal_result = None  # the screen must get the score from the service
    flow.frame([], 16)
    assert flow.scene == Scene.RESULTS
    report = flow.reports.report
    assert report is not None and report.policy_label == "Human"
    assert (report.result.score, report.result.grade) == (0, "F")
    assert flow.reports.history() == (report,)
    flow.profiles.refresh()
    saved = experience.save_profile("Quiet", PRESETS["GHOST"])
    flow.profiles.refresh()
    assert flow.profiles.profiles == (saved,) and not flow.profiles.notice
