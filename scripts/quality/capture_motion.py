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
    phases: dict[str, set[int]] = {"walk": set(), "run": set(), "crouch": set()}
    directions: set[tuple[int, int]] = set()
    frame_number = 0
    # All four facings, turns, passing poses, rest and sprint recharge on real
    # collision geometry. Inputs never write positions or bypass Simulation.
    for label, sprint in (("walk", False), ("run", True), ("crouch", False)):
        if label == "crouch":
            flow.frame([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c)], 34)
            flow.frame([pygame.event.Event(pygame.KEYUP, key=pygame.K_c)], 34)
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
                    count = (
                        len(
                            flow.session.art.operative_crouch
                            if label == "crouch"
                            else flow.session.art.operative_run
                            if label == "run"
                            else flow.session.art.operative_walk
                        )
                        // 4
                    )
                    phases[label].add(int(motion.phase * count) % count)
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
    driver = HumanDriver(flow.rules)
    for target in ((3, 23), (3, 22), (3, 21)):
        for _ in range(600):
            observation = flow.session.simulation.observe(flow.level.operative_id)
            if driver.arrived(observation, target):
                break
            flow.frame(driver.events(observation, target), 17)
        else:
            raise RuntimeError(f"Crouch input stalled before {target}")
    flow.frame(driver.release(), 34)
    assert flow.session.simulation.observe(flow.level.operative_id).own_status.concealed
    flow.draw(canvas)
    pygame.image.save(canvas, str(args.output / "under-desk.png"))
    flow.frame([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c)], 34)
    flow.frame([pygame.event.Event(pygame.KEYUP, key=pygame.K_c)], 34)
    assert flow.session.simulation.observe(flow.level.operative_id).own_status.crouched
    flow.draw(canvas)
    pygame.image.save(canvas, str(args.output / "low-headroom.png"))
    for _ in range(100):
        observation = flow.session.simulation.observe(flow.level.operative_id)
        flow.frame(driver.events(observation, (3, 23)), 17)
    flow.frame(driver.release(), 34)
    flow.frame([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c)], 34)
    flow.frame([pygame.event.Event(pygame.KEYUP, key=pygame.K_c)], 34)
    assert not flow.session.simulation.observe(flow.level.operative_id).own_status.crouched
    # Architectural inspection uses presentation-only camera views. These are
    # explicitly previews, not evidence that the operative visited each room.
    room_output = args.output / "room-previews"
    room_output.mkdir(exist_ok=True)
    size = flow.level.static_map.tile_size_px
    preview_targets = [
        (room.room_id, room.label, room.left + room.width / 2, room.top + room.height / 2)
        for room in flow.level.rooms
    ]
    preview_targets.extend(
        (marker.marker_id, "Prepared hiding recess / P05 interaction pending", *marker.tile)
        for marker in flow.level.markers
        if marker.kind == "HideSpot"
    )
    for preview_id, label, x, y in preview_targets:
        camera = Camera(1280, 720, *flow.map_surface.get_size())
        camera.follow((x * size, y * size), 0, snap=True)
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
            flow.fonts.small.render("ROOM ART REVIEW / " + label, True, (230, 244, 247)),
            (24, 24),
        )
        screen.blit(canvas, (0, 0))
        pygame.display.flip()
        pygame.image.save(canvas, str(room_output / f"{preview_id}.png"))
    report = {
        "video_driver": pygame.display.get_driver(),
        "frames": frame_number,
        "animation_frames_seen": {key: sorted(value) for key, value in phases.items()},
        "directions": sorted(directions),
        "simulation_fingerprint_preserved_on_every_draw": True,
        "under_desk_input_entry_concealed": True,
        "standing_refused_beneath_desk_and_allowed_after_exit": True,
        "tile_size_px": flow.level.static_map.tile_size_px,
        "viewport_tiles": [1280 / size, 720 / size],
        "architectural_preview_rooms": len(flow.level.rooms),
        "prepared_hiding_previews": len(preview_targets) - len(flow.level.rooms),
        "draw_ms": {"median": round(median(timings), 2), "max": round(max(timings), 2)},
        "scope": "Native visual fixture with security disabled; mission wins use capture_scenes.",
    }
    (args.output / "MOTION.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
