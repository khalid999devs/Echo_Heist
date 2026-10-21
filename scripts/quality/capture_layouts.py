"""Native responsive layout/input review, including actual desktop fullscreen."""

import argparse
import json
from pathlib import Path

import pygame

from echo_heist.infrastructure.persistence.settings import Settings
from echo_heist.ui.bootstrap import _logical_events
from echo_heist.ui.render.layout.viewport import interface_origin, logical_size_for
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.flow import GameFlow, Scene
from echo_heist.ui.scenes.menus import CHAPTER_CARD, MODE_BUTTONS, TITLE_BUTTONS
from echo_heist.ui.scenes.navigation.controls import MAP_CLOSE, PAUSE_BUTTONS
from echo_heist.ui.scenes.settings import OPTION_RECTS


def review_layout(requested: tuple[int, int], output: Path) -> dict[str, object]:
    # Independent native windows avoid a Cocoa fullscreen-space transition
    # while the previous oversized review window is still being torn down.
    pygame.display.quit()
    pygame.display.init()
    fullscreen = requested == (0, 0)
    screen = pygame.display.set_mode(
        requested, pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
    )
    actual = screen.get_size()
    logical = logical_size_for(actual)
    flow = GameFlow(logical, settings=Settings(fullscreen=fullscreen))
    canvas = opaque_surface(logical)
    origin = interface_origin(logical)
    label = "fullscreen" if fullscreen else f"{actual[0]}x{actual[1]}"
    captures = []

    def click(rect: pygame.Rect) -> None:
        window = pygame.display.get_window_size()
        pos = (
            round((rect.centerx + origin[0]) * window[0] / logical[0]),
            round((rect.centery + origin[1]) * window[1] / logical[1]),
        )
        events = [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)]
        flow.frame(_logical_events(events, window, logical), 0)

    def shot(name: str) -> None:
        pygame.event.pump()
        flow.draw(canvas)
        screen.blit(pygame.transform.smoothscale(canvas, actual), (0, 0))
        pygame.display.flip()
        path = output / label / f"{name}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(screen, str(path))
        captures.append(name)

    flow.frame([], 1200)
    shot("title")
    click(TITLE_BUTTONS[2])
    assert flow.scene == Scene.SETTINGS
    shot("settings")
    click(OPTION_RECTS[4])
    click(CHAPTER_CARD)
    assert flow.scene == Scene.MODE
    shot("briefing")
    click(MODE_BUTTONS[2])
    assert flow.scene == Scene.HEIST and flow.session is not None
    shot("gameplay")
    before = flow.session.simulation.fingerprint()
    flow.frame([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)], 0)
    shot("pause")
    click(PAUSE_BUTTONS[2])
    assert flow.scene == Scene.SETTINGS
    click(OPTION_RECTS[4])
    click(PAUSE_BUTTONS[0])
    assert not flow.session.paused
    flow.frame([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB)], 0)
    shot("map")
    click(MAP_CLOSE)
    assert not flow.session.summary
    assert flow.session.simulation.fingerprint() == before
    return {
        "requested": requested,
        "actual": actual,
        "logical": logical,
        "fullscreen": pygame.display.is_fullscreen(),
        "screens": captures,
        "click_routes": "PASS",
        "frozen_mission_preserved": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/responsive-facility/layouts"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pygame.display.init()
    pygame.font.init()
    records = [
        review_layout(requested, args.output)
        for requested in ((1280, 720), (1440, 900), (1024, 768), (1920, 820), (0, 0))
    ]
    report = {
        "video_driver": pygame.display.get_driver(),
        "layouts": records,
        "scope": (
            "Native display surfaces and shared pointer pipeline; "
            "real OS hand clicks remain a human check."
        ),
    }
    (args.output / "LAYOUTS.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
