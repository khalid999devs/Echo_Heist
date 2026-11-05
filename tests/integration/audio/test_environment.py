"""Foreign environment audio requires legitimate hearing, with stable stereo/mix behavior."""

from dataclasses import replace

import pygame
import pytest

from echo_heist.core.contracts.environment.presentation import EnvironmentCue, EnvironmentCueKind
from echo_heist.core.contracts.events import HeardCue
from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.audio.model import AudioFrame
from echo_heist.ui.audio.spatial import environment_sound, stereo


def inputs():
    cue = EnvironmentCue(
        "glass-1",
        10,
        EnvironmentCueKind.GLASS,
        "pane",
        (999000, 90000),
        actor_id="guard",
        noise_event_id="noise-1",
        visible=True,
    )
    frame = AudioFrame("HEIST", "0", 1, tick=10, listener_position=(105000, 105000))
    return cue, frame


def test_unheard_and_stale_cues_are_silent_and_pan_uses_heard_tile():
    cue, frame = inputs()
    assert environment_sound(cue, frame) is None  # Visible does not grant hearing.
    heard = HeardCue("noise-1", "GLASS", (1, 3), 10)
    frame = replace(frame, heard_events=(heard,))
    sound = environment_sound(cue, frame)
    assert sound and sound[2] < 0  # Heard left, despite secret exact position far right.
    assert environment_sound(replace(cue, position=(0, 0)), frame) == sound
    assert environment_sound(cue, replace(frame, tick=150)) is None
    assert environment_sound(cue, replace(frame, tick=9)) is None
    assert environment_sound(cue, replace(frame, scene="TITLE")) is None
    own = replace(cue, actor_id="operative", position=(105000, 105000))
    assert environment_sound(own, replace(frame, heard_events=())) == ("glass", 0.32, 0.0)
    assert stereo(0.5, 0.6) == (0.2, 0.5)


def test_environment_cue_once_mix_pause_restart_and_exit(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.mixer.init()
    try:
        cue, frame = inputs()
        frame = replace(
            frame, environment_cues=(cue,), heard_events=(HeardCue("noise-1", "GLASS", (1, 3), 10),)
        )
        audio = AudioDirector(enabled=True)
        audio.update(frame, 0)
        before = audio.cues_played
        assert before == 1
        assert audio.channel_pans[4] < 0
        audio.update(frame, 17)
        assert audio.cues_played == before
        pan = audio.channel_pans[4]
        audio.volumes(0.5, 0)
        audio.update(replace(frame, paused=True), 17)
        assert audio.channel_pans[4] == pan and pygame.mixer.Channel(4).get_volume() == 0
        audio.volumes(0.5, 0.7)
        audio.update(frame, 17)
        assert audio.channel_pans[4] == pan and audio.cues_played == before + 2  # pause/unpause UI
        audio.update(replace(frame, run_id=2), 17)
        assert audio.cues_played == before + 3
        audio.update(replace(frame, run_id=2, scene="TITLE", environment_cues=()), 17)
        assert not any(pygame.mixer.Channel(i).get_busy() for i in range(4, 12))
    finally:
        pygame.mixer.quit()
