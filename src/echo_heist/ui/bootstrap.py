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
from echo_heist.ui.scenes.flow import GameFlow


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
        flow = GameFlow((config.logical_width, config.logical_height))
        clock = pygame.time.Clock()
        elapsed_ms = 0
        while flow.running:
            flow.frame(pygame.event.get(), elapsed_ms)
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
            pygame.image.save(screen, str(screenshot))
        actual_size = screen.get_size()
        saved_settings = replace(
            settings,
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
