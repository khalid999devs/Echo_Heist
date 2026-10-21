"""Capture actual scene/input states for a native visual review; no forced outcomes."""

import argparse
from pathlib import Path

import pygame

from echo_heist.core.contracts.results import RunOutcome
from echo_heist.core.contracts.world import tile_center
from echo_heist.ui.scenes.flow import GameFlow, Scene

UPPER = ((12, 17), (23, 17), (23, 8), (43, 8), (43, 12), (58, 12), (58, 16))
RETURN = ((58, 12), (43, 12), (43, 8), (23, 8), (23, 17), (12, 17), (2, 17))


def key(value: int, *, release: bool = False) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYUP if release else pygame.KEYDOWN, key=value)


def mission() -> GameFlow:
    flow = GameFlow((1280, 720))
    flow.frame([key(pygame.K_RETURN)], 16)
    flow.frame([key(pygame.K_RETURN)], 16)
    assert flow.scene == Scene.HEIST
    return flow


def drive(flow: GameFlow, route: tuple[tuple[int, int], ...]) -> None:
    assert flow.session is not None
    held: set[int] = set()
    for destination in route:
        target = tile_center(destination)
        for _ in range(1000):
            own = flow.session.simulation.observe(flow.level.operative_id).own_status
            assert own.position is not None
            dx, dy = target[0] - own.position[0], target[1] - own.position[1]
            if abs(dx) < 4_000 and abs(dy) < 4_000:
                break
            direction = (
                pygame.K_d
                if dx > 4_000
                else pygame.K_a
                if dx < -4_000
                else pygame.K_s
                if dy > 4_000
                else pygame.K_w
            )
            desired = {direction, pygame.K_LSHIFT}
            events = [key(code, release=True) for code in sorted(held - desired)]
            events.extend(key(code) for code in sorted(desired - held))
            held = desired
            flow.frame(events, 34)
            if flow.scene == Scene.RESULTS:
                return
        else:
            raise RuntimeError(f"Input route failed at {destination}")
    flow.frame([key(code, release=True) for code in sorted(held)], 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/phase02/ui-polish"))
    args = parser.parse_args()
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    canvas = pygame.Surface((1280, 720))

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
        pygame.image.save(screen, str(target))

    flow = GameFlow((1280, 720))
    flow.frame([], 2400)
    shot(flow, "menus/01-title")
    flow.frame([key(pygame.K_DOWN)], 16)
    shot(flow, "menus/02-title-quit-selected")
    flow.frame([key(pygame.K_UP), key(pygame.K_RETURN)], 16)
    shot(flow, "menus/03-human-briefing")
    flow.frame([key(pygame.K_DOWN), key(pygame.K_RETURN)], 16)
    shot(flow, "menus/04-companion-unavailable")

    flow = mission()
    shot(flow, "gameplay/01-entry")
    flow.frame([key(pygame.K_TAB)], 16)
    shot(flow, "gameplay/02-route-guide")
    flow.frame([key(pygame.K_TAB), key(pygame.K_ESCAPE)], 16)
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
    shot(flow, "feedback/lab-unavailable")

    flow = mission()
    drive(flow, UPPER)
    flow.frame([key(pygame.K_e)], 34)
    for _ in range(15):
        flow.frame([], 34)
    shot(flow, "gameplay/05-core-link")
    for _ in range(35):
        flow.frame([], 34)
    shot(flow, "gameplay/06-lockdown")
    flow.frame([key(pygame.K_e, release=True)], 0)
    drive(flow, RETURN)
    assert flow.session is not None and flow.session.mission_end is not None
    assert flow.session.mission_end.outcome == RunOutcome.WIN
    shot(flow, "outcomes/01-win")

    flow = mission()
    drive(flow, ((12, 17), (16, 17), (16, 9)))
    for _ in range(30):
        flow.frame([], 34)
        if flow.scene == Scene.RESULTS:
            break
    assert flow.session is not None and flow.session.mission_end is not None
    assert flow.session.mission_end.outcome == RunOutcome.CAPTURED
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
    print(
        f"Captured all scene states to {args.output}; video driver: {pygame.display.get_driver()}"
    )
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
