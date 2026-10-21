"""Decode shipped audio and verify event deduplication, context and independent volumes."""

from dataclasses import replace

import pygame
import pytest

from echo_heist.core.contracts.events import EventKind, GameEvent
from echo_heist.core.contracts.world import MissionPhase
from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.audio.model import AudioFrame
from echo_heist.ui.scenes.flow import GameFlow, Scene


def test_shipped_audio_context_deduplication_pause_and_mix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.mixer.init()
    try:
        audio = AudioDirector(enabled=True)
        assert audio.report()["audio_assets_loaded"] == 16
        assert all(sound.get_length() > 0 for sound in audio.sounds.values())
        frame = AudioFrame("TITLE", "0", 0)
        audio.update(frame, 0)
        assert audio.current_music == "title" and pygame.mixer.music.get_busy()
        events = (
            GameEvent("10:0", 10, EventKind.NOISE_CREATED, "operative", (("kind", "SPRINT"),)),
            GameEvent("10:1", 10, EventKind.TOOL_USED, "operative", (("tool", "ECHO"),)),
            GameEvent("10:2", 10, EventKind.LOCKDOWN_STARTED, "operative"),
        )
        heist = AudioFrame("HEIST", "0", 1, MissionPhase.LOCKDOWN, events=events)
        audio.update(heist, 300)
        assert audio.current_music == "urgent"
        assert pygame.mixer.Channel(2).get_busy()
        count = audio.cues_played
        audio.update(heist, 20)
        assert audio.cues_played == count  # repeated delivery cannot replay a tactical cue
        audio.volumes(0.5, 0.0)
        audio.update(heist, 20)
        normal_music = pygame.mixer.music.get_volume()
        assert normal_music > 0 and pygame.mixer.Channel(1).get_volume() == 0
        assert pygame.mixer.Channel(2).get_volume() == 0
        audio.update(replace(heist, paused=True), 20)
        assert 0 < pygame.mixer.music.get_volume() < normal_music
        audio.update(replace(heist, run_id=2), 20)
        assert audio.cues_played == count + 3  # event IDs may recur in a genuinely new attempt
        audio.volumes(0.0, 0.7)
        audio.update(replace(heist, run_id=2), 20)
        assert pygame.mixer.music.get_volume() == 0
        audio.update(AudioFrame("WORKSHOP", "0", 2, MissionPhase.LOCKDOWN), 300)
        assert not pygame.mixer.Channel(2).get_busy()
        assert audio.current_music == "title"
    finally:
        pygame.mixer.quit()


def test_settings_controls_change_real_values_and_return_to_menu() -> None:
    pygame.font.init()
    flow = GameFlow((1280, 720))

    def press(value: int) -> None:
        flow.frame([pygame.event.Event(pygame.KEYDOWN, key=value)], 16)

    for _ in range(2):
        press(pygame.K_DOWN)
    press(pygame.K_RETURN)
    assert flow.scene == Scene.SETTINGS
    press(pygame.K_RIGHT)
    press(pygame.K_DOWN)
    press(pygame.K_LEFT)
    press(pygame.K_DOWN)
    press(pygame.K_RETURN)
    assert flow.settings.music_volume == 0.55
    assert flow.settings.sfx_volume == 0.65
    assert flow.settings.reduced_flashing
    press(pygame.K_ESCAPE)
    assert flow.scene == Scene.TITLE
