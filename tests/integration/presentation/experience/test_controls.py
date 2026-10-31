"""Real input, focus, settings failure recovery and modal navigation regressions."""

from dataclasses import replace

import pygame
import pytest

from echo_heist.core.contracts.autonomy.model import ControlMode
from echo_heist.core.contracts.experience.model import DesktopPreferences
from echo_heist.infrastructure.persistence.settings import Settings
from echo_heist.ui.input.configuration import assign, bindings_for
from echo_heist.ui.scenes.experience.preferences import PreferencesPanel
from echo_heist.ui.scenes.flow import GameFlow, Scene
from echo_heist.ui.scenes.navigation.controls import ABORT_BUTTONS, PAUSE_BUTTONS
from tests.fixtures.experience.gateway import MemoryGateway


def key(code: int, **kwargs: object) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=code, **kwargs)


def click(rect: pygame.Rect) -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)


def test_remapping_rejects_conflicts_reserved_keys_and_cancel_preserves_binding() -> None:
    for code in (pygame.K_s, pygame.K_ESCAPE, pygame.K_TAB, pygame.K_F3):
        with pytest.raises(ValueError):
            assign(DesktopPreferences(), "up", code)
    panel = PreferencesPanel(None)
    panel.page = "CONTROLS"
    panel.handle([key(pygame.K_RETURN), key(pygame.K_i)], Settings())
    assert bindings_for(panel.preferences).up[0] == pygame.K_i
    panel.handle([key(pygame.K_RETURN), key(pygame.K_ESCAPE)], Settings())
    assert panel.capturing is None and bindings_for(panel.preferences).up[0] == pygame.K_i
    panel.handle([key(pygame.K_RETURN), pygame.event.Event(pygame.WINDOWFOCUSLOST)], Settings())
    assert panel.capturing is None


def test_settings_save_failure_preserves_session_and_defaults_keep_accessibility() -> None:
    gateway = MemoryGateway()
    panel = PreferencesPanel(gateway)
    panel.page = "ACCESSIBILITY"
    panel.handle([key(pygame.K_RETURN)], Settings())
    assert not panel.preferences.subtitles
    panel.selected = 2
    gateway.fail = True
    panel.handle([key(pygame.K_RETURN)], Settings())
    assert not panel.preferences.subtitles and "unavailable" in panel.notice
    gateway.fail = False
    panel.handle([key(pygame.K_RETURN)], Settings())
    assert gateway.prefs == panel.preferences
    panel.preferences = assign(panel.preferences, "up", pygame.K_i)
    panel.page, panel.selected = "CONTROLS", 10
    panel.handle([key(pygame.K_RETURN)], Settings())
    assert panel.preferences.controls == () and not panel.preferences.subtitles


def test_seed_modal_cancels_without_launch_and_remapped_movement_reaches_real_simulation() -> None:
    pygame.font.init()
    flow = GameFlow((1280, 720), security_enabled=False)
    flow._go(Scene.MODE)
    flow.frame([key(pygame.K_n)], 0)
    flow.frame([pygame.event.Event(pygame.TEXTINPUT, text="2147483648"), key(pygame.K_RETURN)], 0)
    assert flow.seed_dialog.open and flow.runs_started == 0
    flow.frame([key(pygame.K_ESCAPE)], 0)
    assert flow.seed == 1042
    flow.frame([key(pygame.K_n)], 0)
    flow.frame([pygame.event.Event(pygame.TEXTINPUT, text="55"), key(pygame.K_RETURN)], 0)
    assert flow.seed == 55 and flow.runs_started == 0
    flow.preferences.preferences = assign(DesktopPreferences(), "right", pygame.K_l)
    flow._start_run()
    assert flow.session
    flow.airlock.skip()
    before = flow.session.simulation.observe(flow.session.observer_id).own_status.position
    flow.frame([key(pygame.K_l)], 70)
    after = flow.session.simulation.observe(flow.session.observer_id).own_status.position
    assert after[0] > before[0]
    flow.frame([key(pygame.K_ESCAPE)], 0)
    frozen = flow.session.simulation.fingerprint()
    flow.frame([], 1000)
    assert frozen == flow.session.simulation.fingerprint()


def test_results_retry_and_new_seed_preserve_mode_and_do_not_start_unavailable_companion() -> None:
    pygame.font.init()
    flow = GameFlow((1280, 720))
    flow._start_run()
    assert flow.session and flow.last_deployment
    flow.airlock.skip()
    flow.frame([key(pygame.K_ESCAPE)], 0)
    flow.frame([click(PAUSE_BUTTONS[3])], 0)
    flow.frame([click(ABORT_BUTTONS[0])], 0)
    assert flow.scene == Scene.RESULTS and flow.reports.report is None
    flow.frame([key(pygame.K_d), key(pygame.K_r)], 0)
    assert flow.inspector.open and flow.runs_started == 1
    flow.frame([key(pygame.K_ESCAPE)], 0)
    flow.last_deployment = replace(flow.last_deployment, mode=ControlMode.COMPANION)
    flow.frame([key(pygame.K_n)], 0)
    flow.frame([pygame.event.Event(pygame.TEXTINPUT, text="777"), key(pygame.K_RETURN)], 0)
    assert flow.scene == Scene.WORKSHOP and flow.runs_started == 1
    assert flow.seed == 777 and flow.last_deployment.seed == 777
