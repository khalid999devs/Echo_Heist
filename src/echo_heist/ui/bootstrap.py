"""Desktop window/settings/audio lifecycle; frames are delegated to the P02 scene flow."""

from dataclasses import replace
from io import BytesIO
from math import floor
from os import environ
from pathlib import Path

import pygame

from echo_heist import __version__
from echo_heist.infrastructure.persistence.settings import (
    MAX_WINDOW_SIZE,
    MIN_WINDOW_SIZE,
    SettingsStore,
)
from echo_heist.infrastructure.resources import load_bootstrap_config, resource_bytes
from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.render.layout.viewport import logical_size_for
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.flow import GameFlow


def _logical_events(
    events: list[pygame.event.Event],
    window_size: tuple[int, int],
    logical_size: tuple[int, int],
) -> list[pygame.event.Event]:
    """Map window coordinates into the full responsive render surface."""
    width, height = window_size
    logical_width, logical_height = logical_size
    mapped: list[pygame.event.Event] = []
    for event in events:
        if event.type not in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            mapped.append(event)
            continue
        x, y = event.pos
        point = (
            floor(x * logical_width / max(1, width)),
            floor(y * logical_height / max(1, height)),
        )
        mapped.append(pygame.event.Event(event.type, {**event.dict, "pos": point}))
    return mapped


def run_desktop(
    data_dir: Path,
    *,
    smoke_frames: int | None = None,
    mute: bool = False,
    screenshot: Path | None = None,
) -> dict[str, object]:
    config = load_bootstrap_config()
    store = SettingsStore(data_dir / "settings.json")
    loaded = store.load()
    settings = loaded.settings
    frames = 0
    try:
        # SDL otherwise discards the click that focuses an inactive window.
        # Respect an explicit environment override; this only affects this process.
        environ.setdefault("SDL_MOUSE_FOCUS_CLICKTHROUGH", "1")
        pygame.display.init()
        pygame.font.init()
        flags = pygame.FULLSCREEN if settings.fullscreen else pygame.RESIZABLE
        screen = pygame.display.set_mode(
            (0, 0) if settings.fullscreen else (settings.window_width, settings.window_height),
            flags,
        )
        pygame.display.set_caption(config.title)
        mark = pygame.image.load(BytesIO(resource_bytes("assets/branding/mark.svg")), "mark.svg")
        pygame.display.set_icon(mark)
        audio_state = "muted"
        if not mute:
            try:
                pygame.mixer.init()
                pygame.mixer.music.set_volume(settings.music_volume)
                audio_state = "ready"
            except pygame.error:
                audio_state = "unavailable; continuing silently"
        logical_size = logical_size_for(screen.get_size())
        canvas = opaque_surface(logical_size)
        flow = GameFlow(logical_size, settings=settings)
        audio = AudioDirector(
            enabled=audio_state == "ready",
            music_volume=settings.music_volume,
            sfx_volume=settings.sfx_volume,
        )
        display_fullscreen = settings.fullscreen
        clock = pygame.time.Clock()
        elapsed_ms = 0
        while flow.running:
            new_size = logical_size_for(screen.get_size())
            if new_size != logical_size:
                logical_size = new_size
                canvas = opaque_surface(logical_size)
                flow.resize(logical_size)
            events = _logical_events(
                pygame.event.get(), pygame.display.get_window_size(), logical_size
            )
            flow.frame(events, elapsed_ms)
            audio.volumes(flow.settings.music_volume, flow.settings.sfx_volume)
            audio.update(flow.audio_frame(), elapsed_ms)
            if flow.settings.fullscreen != display_fullscreen:
                display_fullscreen = flow.settings.fullscreen
                dimensions = (
                    (0, 0)
                    if display_fullscreen
                    else (flow.settings.window_width, flow.settings.window_height)
                )
                screen = pygame.display.set_mode(
                    dimensions, pygame.FULLSCREEN if display_fullscreen else pygame.RESIZABLE
                )
                logical_size = logical_size_for(screen.get_size())
                canvas = opaque_surface(logical_size)
                flow.resize(logical_size)
            flow.draw(canvas)
            width, height = screen.get_size()
            screen.blit(
                canvas
                if (width, height) == logical_size
                else pygame.transform.smoothscale(canvas, (width, height)),
                (0, 0),
            )
            pygame.display.flip()
            frames += 1
            if smoke_frames is not None and frames >= smoke_frames:
                flow.running = False
            elapsed_ms = clock.tick(config.target_fps)
        if screenshot is not None:
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            rgb = pygame.image.frombytes(
                pygame.image.tobytes(screen, "RGB"), screen.get_size(), "RGB"
            )
            pygame.image.save(rgb, str(screenshot))
        actual_size = screen.get_size()
        windowed_size = (
            (flow.settings.window_width, flow.settings.window_height)
            if display_fullscreen
            else actual_size
        )
        saved_settings = replace(
            flow.settings,
            window_width=max(MIN_WINDOW_SIZE[0], min(windowed_size[0], MAX_WINDOW_SIZE[0])),
            window_height=max(MIN_WINDOW_SIZE[1], min(windowed_size[1], MAX_WINDOW_SIZE[1])),
        )
        saved = store.save(saved_settings)
        return {
            "diagnostic": "phase-2-game-scenes",
            "version": __version__,
            "frames": frames,
            "video_driver": pygame.display.get_driver(),
            "window_size": list(actual_size),
            "logical_viewport": list(logical_size),
            "fullscreen": pygame.display.is_fullscreen(),
            "audio": audio_state,
            **audio.report(),
            "resources_loaded": True,
            **flow.report(),
            "settings_saved": saved.saved,
            "settings_notice": loaded.notice or saved.notice,
            "settings_path": str(store.path.resolve()),
        }
    except pygame.error as error:
        raise RuntimeError(f"Cannot initialize or render the desktop: {error}") from error
    finally:
        pygame.quit()
