"""Native 60 Hz Human walk/run review; security disabled only for this visual fixture."""

import argparse
import json
from pathlib import Path
from statistics import median
from time import perf_counter

import pygame

from echo_heist.diagnostics.human_driver import HumanDriver
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.environment.furnishings.catalogue import draw_instrument
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.flow import GameFlow


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/close-camera/motion"))
    parser.add_argument("--realtime", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    frames = args.output / "frames"
    frames.mkdir(exist_ok=True)
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((1280, 720))
    canvas = opaque_surface((1280, 720))
    flow = GameFlow((1280, 720), security_enabled=False)
    confirm = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
    flow.frame([confirm], 0)
    flow.frame([confirm], 0)
    assert flow.session is not None
    clock = pygame.time.Clock()
    timings: list[float] = []
    phases: dict[str, set[int]] = {"walk": set(), "run": set()}
    directions: set[tuple[int, int]] = set()
    frame_number = 0
    # All four facings, turns, passing poses, rest and sprint recharge on real
    # collision geometry. Inputs never write positions or bypass Simulation.
    for label, sprint in (("walk", False), ("run", True)):
        driver = HumanDriver(flow.rules, sprint=sprint)
        for target in ((7, 23), (7, 25), (4, 25), (4, 23)):
            for _ in range(600):
                observation = flow.session.simulation.observe(flow.level.operative_id)
                if driver.arrived(observation, target):
                    break
                dt = 17 if frame_number % 3 else 16
                flow.frame(driver.events(observation, target), dt)
                began = perf_counter()
                pygame.event.pump()
                before = flow.session.simulation.fingerprint()
                flow.draw(canvas)
                assert flow.session.simulation.fingerprint() == before
                timings.append((perf_counter() - began) * 1000)
                screen.blit(canvas, (0, 0))
                pygame.display.flip()
                motion = flow.session.actor_motion.get(flow.level.operative_id)
                if motion is not None and motion.moving:
                    phases[label].add(int(motion.phase * 8) % 8)
                    directions.add(motion.direction)
                pygame.image.save(canvas, str(frames / f"{frame_number:05d}.png"))
                frame_number += 1
                if args.realtime:
                    clock.tick(60)
            else:
                raise RuntimeError(f"Human input stalled before {target}")
        flow.frame(driver.release(), 100)
        for _ in range(250):
            flow.frame([], 17)
        flow.draw(canvas)
        pygame.image.save(canvas, str(args.output / f"{label}-rest.png"))
    # Architectural inspection uses presentation-only camera views. These are
    # explicitly previews, not evidence that the operative visited each room.
    room_output = args.output / "room-previews"
    room_output.mkdir(exist_ok=True)
    size = flow.level.static_map.tile_size_px
    for room in flow.level.rooms:
        camera = Camera(1280, 720, *flow.map_surface.get_size())
        camera.follow(
            ((room.left + room.width / 2) * size, (room.top + room.height / 2) * size), 0, snap=True
        )
        canvas.blit(flow.map_surface, camera.to_screen((0, 0)))
        for item in flow.furnishings:
            feet = camera.to_screen(item.footprint.midbottom)
            canvas.blit(
                item.shadow.surface,
                (feet[0] - item.shadow.pivot[0], feet[1] - item.shadow.pivot[1]),
            )
        for item in flow.furnishings:
            draw_instrument(canvas, item, camera, 0)
        canvas.blit(
            flow.fonts.small.render("ROOM ART REVIEW / " + room.label, True, (230, 244, 247)),
            (24, 24),
        )
        screen.blit(canvas, (0, 0))
        pygame.display.flip()
        pygame.image.save(canvas, str(room_output / f"{room.room_id}.png"))
    report = {
        "video_driver": pygame.display.get_driver(),
        "frames": frame_number,
        "animation_frames_seen": {key: sorted(value) for key, value in phases.items()},
        "directions": sorted(directions),
        "simulation_fingerprint_preserved_on_every_draw": True,
        "tile_size_px": flow.level.static_map.tile_size_px,
        "viewport_tiles": [1280 / size, 720 / size],
        "architectural_preview_rooms": len(flow.level.rooms),
        "draw_ms": {"median": round(median(timings), 2), "max": round(max(timings), 2)},
        "scope": "Native visual fixture with security disabled; mission wins use capture_scenes.",
    }
    (args.output / "MOTION.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
