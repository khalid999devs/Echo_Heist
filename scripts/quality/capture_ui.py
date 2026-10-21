"""Capture actual scene/input states for a native visual review; no forced outcomes."""

import argparse
import json
from collections.abc import Callable
from pathlib import Path

import pygame

from echo_heist.core.contracts.results import RunOutcome
from echo_heist.diagnostics.facility_routes import mission_path, walk_path
from echo_heist.diagnostics.human_driver import HumanDriver
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.flow import GameFlow, Scene
from echo_heist.ui.scenes.menus import MODE_BUTTONS, TITLE_BUTTONS


def key(value: int, *, release: bool = False) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYUP if release else pygame.KEYDOWN, key=value)


def mission() -> GameFlow:
    flow = GameFlow((1280, 720))
    flow.frame([key(pygame.K_RETURN)], 16)
    flow.frame([key(pygame.K_RETURN)], 16)
    assert flow.scene == Scene.HEIST
    return flow


def drive(
    flow: GameFlow,
    route: tuple[tuple[int, int], ...],
    *,
    use_tools: bool = False,
    observer: Callable[[GameFlow], None] | None = None,
) -> None:
    assert flow.session is not None
    driver = HumanDriver(flow.rules, use_tools=use_tools)
    for destination in route:
        for _ in range(1000):
            observation = flow.session.simulation.observe(flow.level.operative_id)
            if driver.arrived(observation, destination):
                break
            flow.frame(driver.events(observation, destination), 34)
            if observer is not None:
                observer(flow)
            if flow.scene == Scene.RESULTS:
                return
        else:
            raise RuntimeError(f"Input route failed at {destination}")
    flow.frame(driver.release(), 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/phase02/ui-polish"))
    args = parser.parse_args()
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    canvas = opaque_surface((1280, 720))

    def shot(flow: GameFlow, path: str) -> None:
        flow.draw(canvas)
        width, height = screen.get_size()
        scale = min(width / 1280, height / 720)
        target_size = round(1280 * scale), round(720 * scale)
        offset = (width - target_size[0]) // 2, (height - target_size[1]) // 2
        screen.fill((4, 11, 18))
        screen.blit(pygame.transform.smoothscale(canvas, target_size), offset)
        pygame.display.flip()
        target = args.output / f"{path}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        # Cocoa's display buffer can contain unused zero-alpha bytes. Export
        # explicit RGB so documentation previews are opaque on every viewer.
        rgb = pygame.image.frombytes(pygame.image.tobytes(screen, "RGB"), screen.get_size(), "RGB")
        pygame.image.save(rgb, str(target))

    def click(rect: pygame.Rect) -> pygame.event.Event:
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)

    flow = GameFlow((1280, 720))
    flow.frame([], 2400)
    shot(flow, "menus/01-title")
    flow.frame([pygame.event.Event(pygame.MOUSEMOTION, pos=TITLE_BUTTONS[3].center)], 16)
    shot(flow, "menus/02-title-quit-selected")
    flow.frame([click(TITLE_BUTTONS[2])], 16)
    shot(flow, "menus/05-settings")
    flow.frame([key(pygame.K_RIGHT), key(pygame.K_DOWN), key(pygame.K_LEFT)], 16)
    shot(flow, "menus/06-settings-adjusted")
    flow.frame([key(pygame.K_ESCAPE)], 16)
    flow.frame([click(TITLE_BUTTONS[1])], 16)
    assert flow.scene == Scene.TITLE and flow.notice
    shot(flow, "unavailable/empty-report")
    flow.frame([click(TITLE_BUTTONS[0])], 16)
    assert flow.scene == Scene.MODE
    shot(flow, "menus/03-human-briefing")
    flow.frame([click(MODE_BUTTONS[1])], 16)
    assert flow.scene == Scene.MODE and flow.runs_started == 0 and flow.mode_choice == 0
    shot(flow, "menus/04-companion-unavailable")

    flow = mission()
    shot(flow, "gameplay/01-entry")
    flow.frame([key(pygame.K_TAB)], 16)
    shot(flow, "gameplay/02-route-guide")
    flow.frame([key(pygame.K_TAB)], 0)
    flow.frame([key(pygame.K_ESCAPE)], 16)
    shot(flow, "gameplay/03-paused")
    flow.frame([key(pygame.K_x)], 16)
    shot(flow, "gameplay/04-confirm-abort")
    flow.frame([key(pygame.K_x)], 16)
    assert flow.session is not None and flow.session.mission_end is not None
    assert flow.session.mission_end.outcome == RunOutcome.ABORTED
    shot(flow, "outcomes/03-aborted")

    flow = mission()
    for code, label in ((pygame.K_q, "echo"), (pygame.K_f, "emp"), (pygame.K_SPACE, "melee")):
        flow.frame([key(code)], 34)
        shot(flow, f"feedback/{label}")
        flow.frame([key(code, release=True)], 34)
    flow.frame([key(pygame.K_F3)], 16)
    shot(flow, "feedback/live-ai-lab")

    flow = mission()
    captured_states: set[str] = set()
    captured_rooms: set[str] = set()
    room_views = {
        (27, 11): "01-service-servers",
        (32, 11): "02-security-gangway",
        (44, 13): "03-security-control",
        (56, 21): "04-core-chamber",
        (32, 34): "05-research-gangway",
        (44, 30): "06-biology-lab",
    }

    def observe_guard(current: GameFlow) -> None:
        assert current.session is not None
        snapshot = current.session.simulation.presentation_snapshot()
        tile = current.session.simulation.observe(current.level.operative_id).own_status.tile
        room_view = room_views.get(tile)
        if room_view is not None and room_view not in captured_rooms:
            captured_rooms.add(room_view)
            shot(current, f"rooms/{room_view}")
        guard = snapshot.guards[0]
        actor = next(actor for actor in snapshot.actors if actor.actor_id == guard.actor_id)
        state = "DISABLED" if actor.disabled else guard.state.value
        if state not in captured_states:
            captured_states.add(state)
            group = "awareness" if state in ("PATROL", "SPOTTED", "INVESTIGATE") else "response"
            shot(current, f"stealth/{group}/{state.lower()}")

    observe_guard(flow)
    drive(flow, mission_path(flow.level, "upper"), use_tools=True, observer=observe_guard)
    flow.frame([key(pygame.K_e)], 34)
    for _ in range(15):
        flow.frame([], 34)
    shot(flow, "gameplay/05-core-link")
    for _ in range(35):
        flow.frame([], 34)
    shot(flow, "gameplay/06-lockdown")
    flow.frame([key(pygame.K_e, release=True)], 0)
    drive(
        flow,
        mission_path(flow.level, "upper", returning=True),
        use_tools=True,
        observer=observe_guard,
    )
    assert flow.session is not None and flow.session.mission_end is not None
    assert flow.session.mission_end.outcome == RunOutcome.WIN
    shot(flow, "outcomes/01-win")
    upper_ticks = flow.session.mission_end.elapsed_ticks
    flow.frame([key(pygame.K_RETURN)], 0)
    shot(flow, "outcomes/06-report-unlocked")
    flow.frame([click(TITLE_BUTTONS[1])], 0)
    assert flow.scene == Scene.RESULTS and flow.session.mission_end.outcome == RunOutcome.WIN

    flow = mission()
    drive(flow, mission_path(flow.level, "lower"), use_tools=True, observer=observe_guard)
    flow.frame([key(pygame.K_e)], 34)
    for _ in range(50):
        flow.frame([], 34)
    flow.frame([key(pygame.K_e, release=True)], 0)
    drive(
        flow,
        mission_path(flow.level, "lower", returning=True),
        use_tools=True,
        observer=observe_guard,
    )
    assert flow.session is not None and flow.session.mission_end is not None
    assert flow.session.mission_end.outcome == RunOutcome.WIN
    lower_ticks = flow.session.mission_end.elapsed_ticks
    assert captured_rooms == set(room_views.values())

    flow = mission()
    post = next(post for post in flow.level.guards if post.guard_id == "guard-service")
    drive(flow, walk_path(flow.level, flow.level.spawn_tile, post.tile))
    for _ in range(1200):
        flow.frame([], 34)
        if flow.scene == Scene.RESULTS:
            break
    assert flow.session is not None and flow.session.mission_end is not None
    assert flow.session.mission_end.outcome == RunOutcome.CAPTURED
    capture_ticks = flow.session.mission_end.elapsed_ticks
    shot(flow, "outcomes/02-captured")
    flow.frame([pygame.event.Event(pygame.MOUSEMOTION, pos=(700, 610))], 16)
    shot(flow, "outcomes/04-retry-hover")
    flow.frame([pygame.event.Event(pygame.MOUSEMOTION, pos=(700, 670))], 16)
    shot(flow, "outcomes/05-menu-hover")

    flow = GameFlow((1280, 720))
    flow.frame([], 2800)
    screen = pygame.display.set_mode((960, 540), pygame.RESIZABLE)
    shot(flow, "display/01-small-window")
    screen = pygame.display.set_mode((1024, 800), pygame.RESIZABLE)
    shot(flow, "display/02-tall-window-letterbox")
    report = {
        "video_driver": pygame.display.get_driver(),
        "seed": flow.seed,
        "input": "real HumanInput keyboard events; EMP and melee when needed",
        "upper": {"outcome": "WIN", "ticks": upper_ticks},
        "lower": {"outcome": "WIN", "ticks": lower_ticks},
        "contact": {"outcome": "CAPTURED", "ticks": capture_ticks},
        "rooms_captured": sorted(captured_rooms),
        "guard_states_captured": sorted(captured_states),
        "screenshots": len(list(args.output.rglob("*.png"))),
    }
    (args.output / "playthrough.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"Captured all scene states to {args.output}; video driver: {pygame.display.get_driver()}"
    )
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
