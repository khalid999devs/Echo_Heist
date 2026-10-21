"""Desktop window/settings/audio lifecycle; frames are delegated to the P02 scene flow."""

from dataclasses import replace
from io import BytesIO
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
from echo_heist.ui.scenes.flow import GameFlow


def _logical_events(
    events: list[pygame.event.Event],
    window_size: tuple[int, int],
    logical_size: tuple[int, int],
) -> list[pygame.event.Event]:
    """Translate pointer coordinates through the letterbox used for rendering."""
    width, height = window_size
    logical_width, logical_height = logical_size
    scale = min(width / logical_width, height / logical_height)
    rendered_width = max(1, int(logical_width * scale))
    rendered_height = max(1, int(logical_height * scale))
    offset_x = (width - rendered_width) // 2
    offset_y = (height - rendered_height) // 2
    mapped: list[pygame.event.Event] = []
    for event in events:
        if event.type not in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            mapped.append(event)
            continue
        x, y = event.pos
        point = (
            int((x - offset_x) * logical_width / rendered_width),
            int((y - offset_y) * logical_height / rendered_height),
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
        pygame.display.init()
        pygame.font.init()
        flags = pygame.FULLSCREEN if settings.fullscreen else pygame.RESIZABLE
        screen = pygame.display.set_mode((settings.window_width, settings.window_height), flags)
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
        canvas = pygame.Surface((config.logical_width, config.logical_height))
        flow = GameFlow((config.logical_width, config.logical_height), settings=settings)
        audio = AudioDirector(
            enabled=audio_state == "ready",
            music_volume=settings.music_volume,
            sfx_volume=settings.sfx_volume,
        )
        display_fullscreen = settings.fullscreen
        clock = pygame.time.Clock()
        elapsed_ms = 0
        while flow.running:
            logical_size = (config.logical_width, config.logical_height)
            events = _logical_events(pygame.event.get(), screen.get_size(), logical_size)
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
            flow.draw(canvas)
            width, height = screen.get_size()
            scale = min(width / config.logical_width, height / config.logical_height)
            size = (
                max(1, int(config.logical_width * scale)),
                max(1, int(config.logical_height * scale)),
            )
            screen.fill(config.background)
            screen.blit(
                pygame.transform.smoothscale(canvas, size),
                ((width - size[0]) // 2, (height - size[1]) // 2),
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
        saved_settings = replace(
            flow.settings,
            window_width=max(MIN_WINDOW_SIZE[0], min(actual_size[0], MAX_WINDOW_SIZE[0])),
            window_height=max(MIN_WINDOW_SIZE[1], min(actual_size[1], MAX_WINDOW_SIZE[1])),
        )
        saved = store.save(saved_settings)
        return {
            "diagnostic": "phase-2-game-scenes",
            "version": __version__,
            "frames": frames,
            "video_driver": pygame.display.get_driver(),
            "window_size": list(actual_size),
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
