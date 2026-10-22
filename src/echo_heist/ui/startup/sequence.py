"""Keep OS events and display on the main thread while resources prepare."""

from dataclasses import dataclass
from statistics import median
from time import perf_counter

import pygame

from echo_heist.infrastructure.persistence.settings import Settings
from echo_heist.ui.render.layout.viewport import logical_size_for
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.startup.loader import PreparedGame, StartupLoader
from echo_heist.ui.startup.screen import OpeningScreen
from echo_heist.ui.startup.sound import OpeningAudio


@dataclass(frozen=True, slots=True)
class OpenedGame:
    game: PreparedGame | None
    audio_state: str
    report: dict[str, object]


def open_game(
    screen: pygame.Surface, settings: Settings, *, mute: bool, minimum_ms: int = 2200
) -> OpenedGame:
    """Called after the first logo flip; normal smoke runs can skip the logo hold.

    Quit cancels and drains the worker before pygame shutdown. Skip input never
    reaches the menu. No UI font rendering overlaps the worker's map text bake.
    """
    began = perf_counter()
    opening = OpeningScreen(reduced_motion=settings.reduced_flashing)
    opening_audio: OpeningAudio | None = None
    loader = StartupLoader(logical_size_for(screen.get_size()), settings, mute=mute)
    frames = 0
    gaps: list[float] = []
    previous = began
    skipped = closing = False
    ready_at: float | None = None
    ready_cue = False
    clock = pygame.time.Clock()
    overlay = opaque_surface(logical_size_for(screen.get_size()))
    loader.start()
    game: PreparedGame | None = None
    try:
        while True:
            now = perf_counter()
            elapsed = (now - began) * 1000
            if frames:
                gaps.append((now - previous) * 1000)
            previous = now
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    closing = True
                    loader.cancel()
                elif event.type == pygame.KEYDOWN or (
                    event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                ):
                    skipped = True
            progress = loader.poll()
            if opening_audio is None and loader.audio_future.done():
                opening_audio = loader.audio_future.result()
                opening_audio.play("signal", 0.24)
                opening_audio.play("bed", 0.08)
            if loader.future.done():
                if closing:
                    break
                game = loader.future.result()
                if not ready_cue:
                    if opening_audio is not None:
                        opening_audio.play("ready", 0.22)
                    ready_cue = True
                if ready_at is None and (skipped or elapsed >= minimum_ms):
                    ready_at = elapsed
            logical = logical_size_for(screen.get_size())
            loader.request_size(logical)
            if logical != overlay.get_size():
                overlay = opaque_surface(logical)
            blend = 0.0 if ready_at is None else min(1.0, (elapsed - ready_at) / 550)
            if game is not None and ready_at is not None:
                screen.blit(
                    game.first_frame
                    if game.first_frame.get_size() == screen.get_size()
                    else pygame.transform.smoothscale(game.first_frame, screen.get_size()),
                    (0, 0),
                )
            opening.draw(overlay, elapsed, progress, ready=game is not None, closing=closing)
            overlay.set_alpha(round(255 * (1 - blend * blend * (3 - 2 * blend))))
            screen.blit(
                overlay
                if overlay.get_size() == screen.get_size()
                else pygame.transform.smoothscale(overlay, screen.get_size()),
                (0, 0),
            )
            pygame.display.flip()
            frames += 1
            if blend >= 1:
                break
            clock.tick(60)
        if game is not None and not closing:
            actual = logical_size_for(screen.get_size())
            if game.flow.view_size != actual:
                game.flow.resize(actual)
    except Exception as error:
        raise RuntimeError(f"Cannot prepare the game: {error}") from error
    finally:
        loader.close()
        # Even cancellation during audio initialization releases its channels.
        if opening_audio is None and loader.audio_future.done():
            opening_audio = loader.audio_future.result()
        if opening_audio is not None:
            opening_audio.stop()
    ordered = sorted(gaps)
    return OpenedGame(
        None if closing else game,
        opening_audio.state if opening_audio is not None else "muted",
        {
            "completed": not closing,
            "cancelled": closing,
            "frames": frames,
            "elapsed_ms": round((perf_counter() - began) * 1000, 2),
            "resource_load_ms": round(game.load_ms, 2) if game is not None else None,
            "skip_requested": skipped,
            "sound_cues": opening_audio.cues if opening_audio is not None else 0,
            "frame_gap_ms": {
                "median": round(median(gaps), 2) if gaps else 0,
                "p95": round(ordered[int(len(ordered) * 0.95)], 2) if gaps else 0,
                "max": round(max(gaps), 2) if gaps else 0,
            },
        },
    )
