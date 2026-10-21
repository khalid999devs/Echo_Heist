"""Regression checks for missed clicks, drag capture and honest scene transitions."""

import pygame

from echo_heist.ui.bootstrap import _logical_events
from echo_heist.ui.scenes.design.screens import LAB_CONTROLS
from echo_heist.ui.scenes.design.workshop import WORKSHOP_CONTROLS
from echo_heist.ui.scenes.flow import GameFlow, Scene
from echo_heist.ui.scenes.menus import CHAPTER_CARD, MODE_BUTTONS, TITLE_BUTTONS
from echo_heist.ui.scenes.navigation.controls import PAUSE_BUTTONS
from echo_heist.ui.scenes.settings import OPTION_RECTS


def click(rect: pygame.Rect) -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)


def test_visible_chapter_and_preview_clicks_never_launch_an_unrequested_run() -> None:
    pygame.font.init()
    flow = GameFlow((1280, 720))
    flow.frame([click(CHAPTER_CARD), click(MODE_BUTTONS[2])], 0)
    assert flow.scene == Scene.MODE and flow.runs_started == 0
    flow.frame([click(MODE_BUTTONS[1])], 0)
    assert flow.scene == Scene.WORKSHOP and flow.session is None
    flow.frame([click(WORKSHOP_CONTROLS[0]), click(WORKSHOP_CONTROLS[3])], 0)
    assert flow.designs.draft.choices[0] == 1
    flow.frame([click(WORKSHOP_CONTROLS[8])], 0)
    assert flow.runs_started == 0 and flow.designs.notice
    flow.frame([click(WORKSHOP_CONTROLS[7]), click(LAB_CONTROLS[2])], 0)
    assert flow.scene == Scene.LAB and flow.session is None
    flow.frame([click(LAB_CONTROLS[2])], 0)
    assert flow.scene == Scene.WORKSHOP


def test_slider_drag_releases_outside_track_and_ignores_letterbox() -> None:
    pygame.font.init()
    flow = GameFlow((1280, 720))
    flow.frame([click(TITLE_BUTTONS[2])], 0)
    flow.frame([click(OPTION_RECTS[0]), pygame.event.Event(pygame.MOUSEMOTION, pos=(900, 255))], 0)
    assert flow.settings.music_volume == 1.0
    flow.frame([pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(900, 255))], 0)
    flow.frame([pygame.event.Event(pygame.MOUSEMOTION, pos=(65, 255))], 0)
    assert flow.settings.music_volume == 1.0
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(10, 359))
    assert _logical_events([event], (1280, 1440), (1280, 720))[0].pos[1] == -1


def test_pause_settings_returns_to_same_frozen_mission_and_mouse_resume() -> None:
    pygame.font.init()
    flow = GameFlow((1280, 720))
    flow.frame([click(CHAPTER_CARD)], 0)
    flow.frame([click(MODE_BUTTONS[2])], 0)
    assert flow.session is not None
    flow.frame([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)], 0)
    before = flow.session.simulation.fingerprint()
    flow.frame([click(PAUSE_BUTTONS[2])], 0)
    assert flow.scene == Scene.SETTINGS
    flow.frame([], 5000)
    flow.frame([click(OPTION_RECTS[4])], 0)
    assert flow.scene == Scene.HEIST and flow.session.paused
    assert flow.session.simulation.fingerprint() == before
    flow.frame([click(PAUSE_BUTTONS[0])], 0)
    assert not flow.session.paused
