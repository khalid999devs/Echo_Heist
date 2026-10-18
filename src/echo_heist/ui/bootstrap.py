"""Minimal P01 window, deliberately separate from Suhita's upcoming game scenes."""

from dataclasses import replace
from io import BytesIO
from pathlib import Path

import pygame

from echo_heist import __version__
from echo_heist.core.contracts.world import SIMULATION_HZ
from echo_heist.infrastructure.persistence.settings import (
    MAX_WINDOW_SIZE,
    MIN_WINDOW_SIZE,
    SettingsStore,
)
from echo_heist.infrastructure.resources import (
    BootstrapConfig,
    load_bootstrap_config,
    resource_bytes,
)


def _draw_foundation(
    canvas: pygame.Surface,
    config: BootstrapConfig,
    mark: pygame.Surface,
    audio_state: str,
    settings_notice: str | None,
) -> None:
    foreground = pygame.Color(config.foreground)
    accent = pygame.Color(config.accent)
    muted = pygame.Color(config.muted)
    canvas.fill(config.background)
    title = pygame.font.Font(None, 82)
    body = pygame.font.Font(None, 32)
    small = pygame.font.Font(None, 25)
    canvas.blit(mark, (80, 88))
    canvas.blit(small.render(config.stage, True, accent), (232, 108))
    canvas.blit(title.render(config.title, True, foreground), (228, 142))
    pygame.draw.line(canvas, accent, (80, 252), (1200, 252), 2)
    canvas.blit(body.render("The foundation is ready.", True, foreground), (80, 294))
    rows = (
        "Package resources loaded from the installed application",
        f"Pure simulation contract: {SIMULATION_HZ} fixed ticks per second",
        f"Audio: {audio_state}  |  Version: {__version__}",
        "Mission, movement and playable scenes arrive in Phase 02",
    )
    for index, text in enumerate(rows):
        canvas.blit(body.render(text, True, muted), (80, 354 + index * 48))
    if settings_notice:
        canvas.blit(small.render("Settings notice: see the run report.", True, accent), (80, 580))
    canvas.blit(small.render("ESC TO CLOSE", True, accent), (80, 646))
    canvas.blit(small.render("ECHO HEIST / DEVELOPMENT BUILD", True, muted), (828, 646))


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
        pygame.display.set_caption(f"{config.title} - Foundation")
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
        _draw_foundation(canvas, config, mark, audio_state, loaded.notice)
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    running = False
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
                running = False
            clock.tick(config.target_fps)
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
            "diagnostic": "phase-1-desktop-shell",
            "version": __version__,
            "frames": frames,
            "video_driver": pygame.display.get_driver(),
            "window_size": list(actual_size),
            "audio": audio_state,
            "resources_loaded": True,
            "settings_saved": saved.saved,
            "settings_notice": loaded.notice or saved.notice,
            "settings_path": str(store.path.resolve()),
        }
    except pygame.error as error:
        raise RuntimeError(f"Cannot initialize or render the desktop: {error}") from error
    finally:
        pygame.quit()
