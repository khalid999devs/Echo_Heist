"""Instrument the real native bootstrap; capture frames without saving during loading."""

import argparse
import json
from pathlib import Path
from time import perf_counter

import pygame

from echo_heist.infrastructure.persistence.settings import Settings, SettingsStore
from echo_heist.ui import bootstrap
from echo_heist.ui.render.layout.viewport import interface_origin, logical_size_for
from echo_heist.ui.scenes.menus import CHAPTER_CARD, MODE_BUTTONS, TITLE_BUTTONS
from echo_heist.ui.scenes.settings import OPTION_RECTS
from echo_heist.ui.startup.sequence import OpenedGame


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/cinematic-startup/capture"))
    parser.add_argument("--skip", action="store_true")
    parser.add_argument("--close", action="store_true")
    parser.add_argument("--resize", action="store_true")
    parser.add_argument("--fullscreen", action="store_true")
    parser.add_argument("--reduced", action="store_true")
    parser.add_argument("--mute", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    profile = args.output / "profile"
    SettingsStore(profile / "settings.json").save(
        Settings(fullscreen=args.fullscreen, reduced_flashing=args.reduced)
    )
    original_flip, original_open = pygame.display.flip, bootstrap.open_game
    started = perf_counter()
    screenshots: dict[str, pygame.Surface] = {}
    sample_times = [0, 0.35, 0.8, 1.5, 2.3, 2.55]
    opened: OpenedGame | None = None
    seen: list[str] = []
    injected = resized = False
    video_frames: list[bytes] = []

    def opening(*args: object, **kwargs: object) -> OpenedGame:
        nonlocal opened
        opened = original_open(*args, **kwargs)
        return opened

    def click(rect: pygame.Rect, screen: pygame.Surface) -> pygame.event.Event:
        logical = logical_size_for(screen.get_size())
        origin = interface_origin(logical)
        point = tuple(
            round((value + offset) * actual / axis)
            for value, offset, actual, axis in zip(
                rect.center, origin, screen.get_size(), logical, strict=True
            )
        )
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point)

    def flip() -> None:
        nonlocal injected, resized
        original_flip()
        screen = pygame.display.get_surface()
        assert screen is not None
        elapsed = perf_counter() - started
        if sample_times and elapsed >= sample_times[0]:
            sample = sample_times.pop(0)
            screenshots[f"opening-{sample:.2f}"] = screen.copy()
        # A small raw video capture is encoded after shutdown, never PNG IO in
        # the loading loop. Timings remain an instrumented native review.
        video_frames.append(
            pygame.image.tobytes(pygame.transform.smoothscale(screen, (768, 432)), "RGB")
        )
        if args.resize and not resized and elapsed > 0.6:
            pygame.display.set_mode((1024, 768), pygame.RESIZABLE)
            resized = True
        if (args.skip or args.close) and not injected and elapsed > 0.65:
            pygame.event.post(
                pygame.event.Event(pygame.QUIT)
                if args.close
                else pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
            )
            injected = True
        if opened is not None and opened.game is not None and len(seen) < 5:
            flow = opened.game.flow
            assert flow.runs_started == 0 and flow.session is None
            seen.append(flow.scene.value)
            screenshots[f"menu-{len(seen)}-{flow.scene.value.lower()}"] = screen.copy()
            controls = (CHAPTER_CARD, MODE_BUTTONS[3], TITLE_BUTTONS[2], OPTION_RECTS[4])
            event = (
                click(controls[len(seen) - 1], screen)
                if len(seen) <= 4
                else pygame.event.Event(pygame.QUIT)
            )
            pygame.event.post(event)
        if elapsed > 30:
            raise RuntimeError("Native opening did not finish within 30 seconds")

    bootstrap.open_game = opening
    pygame.display.flip = flip
    try:
        result = bootstrap.run_desktop(profile, mute=args.mute)
    finally:
        pygame.display.flip = original_flip
        bootstrap.open_game = original_open
    expected = [] if args.close else ["TITLE", "MODE", "TITLE", "SETTINGS", "TITLE"]
    assert seen == expected, seen
    assert result["resources_loaded"] is not args.close
    for name, surface in screenshots.items():
        pygame.image.save(surface, str(args.output / f"{name}.png"))
    with (args.output / "opening.rgb").open("wb") as stream:
        for frame in video_frames:
            stream.write(frame)
    report = {
        "bootstrap": result,
        "native_pointer_routes": seen,
        "opening_input_did_not_launch_mission": True,
        "resize_requested": args.resize,
        "fullscreen_requested": args.fullscreen,
        "captured_frames": len(video_frames),
        "raw_video_size": [768, 432],
        "scope": (
            "Native injected-input bootstrap review, not physical Windows QA; "
            "raw frames captured in memory"
        ),
    }
    (args.output / "STARTUP.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
