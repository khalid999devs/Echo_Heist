"""Khalid's results/profile/preferences screens on the real P06 services (no fixtures)."""

from pathlib import Path

import pygame

from echo_heist.autonomy.gateway import connect_experience, connect_gateway
from echo_heist.core.contracts.autonomy.policy import PRESETS
from echo_heist.core.contracts.experience.model import DesktopPreferences
from echo_heist.infrastructure.resources import load_game_rules, load_sensor_rules
from echo_heist.ui.render.autonomy.protocols import TOGGLE_MEMORY
from echo_heist.ui.scenes.companion.deployment import selection
from echo_heist.ui.scenes.design.workshop import WORKSHOP_CONTROLS
from echo_heist.ui.scenes.experience.preferences import EXTRA_SETTINGS, KEY_FOOTER, KEY_ROWS
from echo_heist.ui.scenes.experience.profiles import PROFILE_ACTIONS, PROFILE_BUTTON
from echo_heist.ui.scenes.flow import GameFlow, Scene, load_level
from echo_heist.ui.scenes.menus import CHAPTER_CARD, MODE_BUTTONS, TITLE_BUTTONS


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
    for rect in (TITLE_BUTTONS[2], EXTRA_SETTINGS[0], KEY_ROWS[3]):
        flow.frame([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)], 0)
    flow.frame([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_l)], 0)
    flow.frame([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=KEY_FOOTER[1].center)], 0)
    assert flow.preferences.notice == "Preferences saved."
    for _ in range(2):
        flow.frame([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)], 0)
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

    # A fresh flow represents a relaunch with persisted history/preferences.
    relaunched_gateway = connect_gateway(level, rules, load_sensor_rules(), tmp_path)
    relaunched = GameFlow(
        (1280, 720),
        level=level,
        rules=rules,
        autonomy_gateway=relaunched_gateway,
        experience_gateway=connect_experience(relaunched_gateway, tmp_path),
    )
    assert any(
        item.action == "right" and pygame.K_l in item.keys
        for item in relaunched.preferences.preferences.controls
    )
    relaunched.frame(
        [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=TITLE_BUTTONS[1].center)], 0
    )
    assert relaunched.inspector.open and relaunched.inspector.history[0].run_key == report.run_key
    relaunched.inspector.open = False
    relaunched.scene = Scene.WORKSHOP
    relaunched.frame(
        [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=TOGGLE_MEMORY.center)], 0
    )
    assert not connect_gateway(level, rules, load_sensor_rules(), tmp_path).protocols().enabled


def test_new_policy_can_be_loaded_directly_after_saving(tmp_path: Path) -> None:
    pygame.font.init()
    level, rules = load_level(), load_game_rules()
    gateway = connect_gateway(level, rules, load_sensor_rules(), tmp_path)
    experience = connect_experience(gateway, tmp_path)
    experience.save_profile("First", PRESETS["GHOST"])
    flow = GameFlow(
        (1280, 720),
        level=level,
        rules=rules,
        autonomy_gateway=gateway,
        experience_gateway=experience,
    )

    def click(rect: pygame.Rect) -> None:
        flow.frame([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)], 0)

    click(CHAPTER_CARD)
    click(MODE_BUTTONS[1])
    click(WORKSHOP_CONTROLS[2])
    assert selection(flow.designs.draft) == PRESETS["RUSH"]
    click(PROFILE_BUTTON)
    flow.frame(
        [
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_n),
            pygame.event.Event(pygame.TEXTINPUT, text="Demo Rush"),
        ],
        0,
    )
    click(PROFILE_ACTIONS[0])
    click(PROFILE_ACTIONS[1])
    assert selection(flow.designs.draft) == PRESETS["RUSH"]
    assert flow.profiles.name == "Demo Rush"
