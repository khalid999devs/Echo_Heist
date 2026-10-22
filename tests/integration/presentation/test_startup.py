"""Opening input isolation and resource-worker lifetime, not cosmetic snapshots."""

from threading import Event
from threading import enumerate as running_threads
from time import monotonic

import pygame
import pytest

from echo_heist.infrastructure.persistence.settings import Settings
from echo_heist.ui.startup.sequence import open_game


@pytest.fixture
def screen(monkeypatch: pytest.MonkeyPatch) -> pygame.Surface:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.display.init()
    pygame.font.init()
    target = pygame.display.set_mode((1280, 720))
    pygame.event.clear()
    yield target
    assert not any(thread.name == "echo-resource-loader" for thread in running_threads())
    pygame.quit()


def test_skip_cannot_launch_a_mission_and_silent_settings_are_respected(
    screen: pygame.Surface,
) -> None:
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    result = open_game(
        screen, Settings(sfx_volume=0, reduced_flashing=True), mute=False, minimum_ms=2200
    )
    assert result.game is not None
    assert result.report["completed"] and result.report["skip_requested"]
    assert result.report["sound_cues"] == 0
    assert result.game.audio.enabled and len(result.game.audio.music_data) == 5
    assert result.game.audio.current_music == "title"
    flow = result.game.flow
    flow.frame(pygame.event.get(), 16)
    assert flow.scene.value == "TITLE" and flow.session is None and flow.runs_started == 0


def test_close_during_loading_cancels_and_joins_before_pygame_shutdown(
    screen: pygame.Surface, monkeypatch: pytest.MonkeyPatch
) -> None:
    entered = Event()
    event_get = pygame.event.get

    def preparing(*args: object, **kwargs: object) -> None:
        entered.set()
        loading = kwargs["loading"]
        assert callable(loading)
        until = monotonic() + 3
        while monotonic() < until:
            loading(0.1, "Preparing the facility")
            entered.wait(0.001)
        raise AssertionError("Loading cancellation was not delivered")

    def events() -> list[pygame.event.Event]:
        return [pygame.event.Event(pygame.QUIT)] if entered.is_set() else event_get()

    monkeypatch.setattr("echo_heist.ui.scenes.flow.GameFlow", preparing)
    monkeypatch.setattr(pygame.event, "get", events)
    result = open_game(screen, Settings(), mute=True)
    assert result.game is None and result.report["cancelled"]
    assert not result.report["completed"]


def test_resource_failure_propagates_without_a_live_worker(
    screen: pygame.Surface, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing(*args: object, **kwargs: object) -> None:
        raise ValueError("invalid packaged map")

    monkeypatch.setattr("echo_heist.ui.scenes.flow.GameFlow", failing)
    with pytest.raises(RuntimeError, match="invalid packaged map"):
        open_game(screen, Settings(), mute=True)
