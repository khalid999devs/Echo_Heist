"""An entrance cannot advance unseen gameplay or swallow the first movement intent."""

from dataclasses import replace

import pygame
import pytest

from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.scenes.flow import GameFlow, Scene
from echo_heist.ui.scenes.menus import CHAPTER_CARD, MODE_BUTTONS


def launch(flow: GameFlow) -> None:
    for rect in (CHAPTER_CARD, MODE_BUTTONS[2]):
        flow.frame([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)], 0)


def test_entrance_freezes_unseen_simulation_and_movement_skips_without_lost_input() -> None:
    pygame.font.init()
    flow = GameFlow((1280, 720))
    launch(flow)
    assert flow.scene == Scene.HEIST and flow.session is not None
    before = flow.session.simulation.fingerprint()
    flow.frame([], 700)
    assert flow.airlock.active and flow.session.simulation.fingerprint() == before
    canvas = pygame.Surface((1280, 720))
    flow.draw(canvas)
    assert flow.session.simulation.fingerprint() == before
    flow.frame([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d)], 34)
    assert not flow.airlock.active
    assert flow.session.simulation.tick > 0
    assert flow.session.simulation.fingerprint() != before


def test_transition_sound_is_once_per_stage_and_quit_is_responsive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.font.init()
    pygame.mixer.init()
    try:
        flow = GameFlow((1280, 720))
        audio = AudioDirector(enabled=True)
        audio.update(flow.audio_frame(), 0)
        launch(flow)
        audio.update(flow.audio_frame(), 0)
        count = audio.cues_played
        audio.update(flow.audio_frame(), 17)
        assert audio.cues_played == count
        # Presentation stage serials do not become repeated movement/noise events.
        closing = replace(flow.audio_frame(), transition_serial=2, transition_cue="stair-arrive")
        audio.update(closing, 17)
        audio.update(closing, 17)
        assert audio.cues_played == count + 1
        flow.frame([pygame.event.Event(pygame.QUIT)], 0)
        assert not flow.running
        assert flow.session is not None and flow.session.simulation.tick == 0
    finally:
        pygame.mixer.quit()
