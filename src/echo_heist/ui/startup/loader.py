"""One resource worker, isolated off-screen surfaces and explicit ownership transfer."""

from concurrent.futures import Future
from dataclasses import dataclass
from queue import Empty, SimpleQueue
from threading import Event, Thread
from time import perf_counter
from typing import TYPE_CHECKING

import pygame

from echo_heist.infrastructure.persistence.settings import Settings
from echo_heist.ui.startup.sound import OpeningAudio

if TYPE_CHECKING:
    from echo_heist.ui.audio.director import AudioDirector
    from echo_heist.ui.scenes.flow import GameFlow


class LoadingCancelled(Exception):
    """The window closed before resource ownership reached the main loop."""


@dataclass(frozen=True, slots=True)
class LoadingProgress:
    fraction: float = 0.0
    label: str = "Preparing the facility"


@dataclass(frozen=True, slots=True)
class PreparedGame:
    flow: "GameFlow"
    audio: "AudioDirector"
    first_frame: pygame.Surface
    load_ms: float


class StartupLoader:
    """Only the worker touches game resources until the completed Future is read.

    No worker display/event calls. The opening pre-renders all its text before
    this worker starts: pygame font rendering must never run on both threads.
    Cancellation joins before pygame.quit, including startup errors.
    """

    def __init__(self, view_size: tuple[int, int], settings: Settings, *, mute: bool) -> None:
        self.progress = LoadingProgress()
        self._view_size = view_size
        self._updates: SimpleQueue[LoadingProgress] = SimpleQueue()
        self._cancel = Event()
        self.future: Future[PreparedGame] = Future()
        self.audio_future: Future[OpeningAudio] = Future()
        self._thread = Thread(
            target=self._prepare, args=(view_size, settings, mute), name="echo-resource-loader"
        )

    def start(self) -> None:
        self._thread.start()

    def cancel(self) -> None:
        self._cancel.set()

    def request_size(self, view_size: tuple[int, int]) -> None:
        self._view_size = view_size

    def close(self) -> None:
        self.cancel()
        self._thread.join()

    def poll(self) -> LoadingProgress:
        while True:
            try:
                self.progress = self._updates.get_nowait()
            except Empty:
                return self.progress

    def _publish(self, fraction: float, label: str) -> None:
        if self._cancel.is_set():
            raise LoadingCancelled
        self._updates.put(LoadingProgress(fraction, label))

    def _prepare(self, view_size: tuple[int, int], settings: Settings, mute: bool) -> None:
        began = perf_counter()
        try:
            opening_audio = OpeningAudio(settings, mute=mute)
            self.audio_future.set_result(opening_audio)
            # Delay the heavy scene imports until the window has already painted.
            from echo_heist.ui.audio.director import AudioDirector
            from echo_heist.ui.render.surfaces.formats import opaque_surface
            from echo_heist.ui.scenes.flow import GameFlow

            self._publish(0.01, "Preparing the facility")
            flow = GameFlow(
                view_size,
                settings=settings,
                loading=lambda value, _: self._publish(value * 0.78, "Preparing the facility"),
            )
            self._publish(0.78, "Connecting audio")
            director = AudioDirector(
                enabled=opening_audio.state == "ready",
                music_volume=settings.music_volume,
                sfx_volume=settings.sfx_volume,
                loading=lambda value: self._publish(0.78 + value * 0.17, "Connecting audio"),
            )
            self._publish(0.95, "Preparing the main menu")
            if flow.view_size != self._view_size:
                flow.resize(self._view_size)
            first_frame = opaque_surface(flow.view_size)
            # Warm the first menu's caches while the opening remains responsive.
            # This is an off-screen draw, with no running mission or display call.
            flow.draw(first_frame)
            # Prime the initial streamed track under the opening, not on the
            # first visible interactive frame. No later main-loop fade blocks.
            director.update(flow.audio_frame(), 0)
            self._publish(1.0, "Ready")
            self.future.set_result(
                PreparedGame(flow, director, first_frame, (perf_counter() - began) * 1000)
            )
        except Exception as error:
            self.future.set_exception(error)
