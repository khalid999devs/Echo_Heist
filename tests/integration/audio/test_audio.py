"""Decode shipped audio and verify event deduplication, context and independent volumes."""

from dataclasses import replace

import pygame
import pytest

from echo_heist.core.contracts.events import EventKind, GameEvent
from echo_heist.core.contracts.world import MissionPhase
from echo_heist.ui.audio.director import AudioDirector, event_cue
from echo_heist.ui.audio.model import AudioFrame
from echo_heist.ui.scenes.flow import GameFlow, Scene
from echo_heist.ui.scenes.menus import MODE_BUTTONS, TITLE_BUTTONS


def test_hover_and_click_on_already_selected_buttons_are_audible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.font.init()
    pygame.mixer.init()
    try:
        flow = GameFlow((1280, 720))
        audio = AudioDirector(enabled=True)
        audio.update(flow.audio_frame(), 0)
        count = audio.cues_played
        point = TITLE_BUTTONS[0].center
        flow.frame([pygame.event.Event(pygame.MOUSEMOTION, pos=point)], 0)
        audio.update(flow.audio_frame(), 20)
        assert audio.cues_played == count + 1
        assert pygame.mixer.Channel(0).get_volume() > 0.15
        flow.frame([pygame.event.Event(pygame.MOUSEMOTION, pos=point)], 0)
        audio.update(flow.audio_frame(), 20)
        assert audio.cues_played == count + 1  # no repeated sound while staying inside
        flow.frame([pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=point, button=1)], 0)
        audio.update(flow.audio_frame(), 20)
        assert flow.scene == Scene.MODE and audio.cues_played == count + 2
        # Human is selected already; a click still needs its own confirmation.
        flow.frame(
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=MODE_BUTTONS[0].center, button=1)], 0
        )
        audio.update(flow.audio_frame(), 20)
        assert flow.scene == Scene.MODE and audio.cues_played == count + 3
    finally:
        pygame.mixer.quit()


def test_shipped_audio_context_deduplication_pause_and_mix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.mixer.init()
    try:
        audio = AudioDirector(enabled=True)
        assert audio.report()["audio_assets_loaded"] == 29
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
        before_reset = audio.cues_played
        audio.update(replace(heist, run_id=2, paused=True), 20)
        assert audio.cues_played == before_reset + 3  # new attempt may reuse event IDs
        audio.volumes(0.0, 0.7)
        audio.update(replace(heist, run_id=2), 20)
        assert pygame.mixer.music.get_volume() == 0
        audio.update(AudioFrame("WORKSHOP", "0", 2, MissionPhase.LOCKDOWN), 300)
        assert not pygame.mixer.Channel(2).get_busy()
        assert audio.current_music == "title"
    finally:
        pygame.mixer.quit()


def test_quiet_walk_loud_sprint_and_unheard_events_do_not_leak(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    walk = GameEvent("w", 1, EventKind.NOISE_CREATED, "operative", (("kind", "FOOTSTEP"),))
    sprint = replace(walk, event_id="s", details=(("kind", "SPRINT"),))
    walk_cue, sprint_cue = event_cue(walk), event_cue(sprint)
    assert walk_cue is not None and sprint_cue is not None
    assert walk_cue[0].startswith("walk-") and sprint_cue[1] > 4 * walk_cue[1]
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.mixer.init()
    try:
        audio = AudioDirector(enabled=True)
        frame = AudioFrame("HEIST", "0", 1, MissionPhase.INFILTRATE)
        audio.update(frame, 0)
        hidden = replace(sprint, event_id="foreign-1", actor_id="companion")
        before = audio.cues_played
        audio.update(replace(frame, events=(hidden,)), 20)
        assert audio.cues_played == before
        heard = replace(hidden, event_id="foreign-2")
        audio.update(
            replace(frame, events=(heard,), audible_event_ids=frozenset({heard.event_id})), 20
        )
        assert audio.cues_played == before + 1
        audio.update(replace(frame, sprint_recharge_remaining=1), 20)
        audio.update(frame, 20)
        ready_count = audio.cues_played
        assert ready_count == before + 2
        audio.update(frame, 100)
        assert audio.cues_played == ready_count
        audio.update(replace(frame, scene="TITLE"), 300)
        assert not pygame.mixer.Channel(3).get_busy()
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
