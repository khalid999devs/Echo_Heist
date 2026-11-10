"""Real robot movement, room lighting and service wiring at native render scale."""

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import pygame

from echo_heist.autonomy.gateway import connect_gateway
from echo_heist.core.contracts.autonomy.policy import DeploymentRequest
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as U
from echo_heist.core.contracts.world import ActorKind
from echo_heist.infrastructure.resources import load_game_rules, load_sensor_rules
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.environment.illumination.model import shadow_at
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.render.world import draw_world
from echo_heist.ui.scenes.flow import GameFlow, load_level


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--video", action="store_true", help="Requires ffmpeg on PATH")
    parser.add_argument("--frames", type=int, default=480)
    args = parser.parse_args()
    if not 60 <= args.frames <= 6000:
        parser.error("Use 60..6000 frames")
    args.output.mkdir(parents=True, exist_ok=True)
    pygame.display.init()
    pygame.font.init()
    display = pygame.display.set_mode((1024, 768))
    canvas = opaque_surface((1024, 768))
    level, rules = load_level(), load_game_rules()
    elapsed = []
    samples, fast_samples = Counter(), Counter()
    poses = {}
    shots = []
    with TemporaryDirectory(prefix="echo-robot-visuals-") as data:
        gateway = connect_gateway(level, rules, load_sensor_rules(), Path(data))
        flow = GameFlow(canvas.get_size(), level=level, rules=rules, autonomy_gateway=gateway)
        assert flow._start_run(DeploymentRequest("COMPANION", 1042, level.static_map.map_id))
        flow.airlock.skip()
        session = flow.session
        assert session
        selected = [
            actor
            for actor in session.simulation.presentation_snapshot().actors
            if actor.kind
            in (ActorKind.SENTINEL, ActorKind.TRACKER, ActorKind.INTERCEPTOR, ActorKind.COMPANION)
        ]
        selected = [
            next(a for a in selected if a.kind == kind)
            for kind in (
                ActorKind.SENTINEL,
                ActorKind.TRACKER,
                ActorKind.INTERCEPTOR,
                ActorKind.COMPANION,
            )
        ]
        encoder = (
            subprocess.Popen(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-f",
                    "rawvideo",
                    "-pixel_format",
                    "rgb24",
                    "-video_size",
                    "1024x768",
                    "-framerate",
                    "60",
                    "-i",
                    "pipe:0",
                    "-an",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "fast",
                    "-crf",
                    "19",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    str(args.output / "real-robots.mp4"),
                ],
                stdin=subprocess.PIPE,
            )
            if args.video
            else None
        )
        tile_px = level.static_map.tile_size_px

        def world(target, size=(512, 384)):
            snapshot = session.simulation.presentation_snapshot()
            camera = Camera(*size, *flow.map_surface.get_size())
            deck = level.deck_at(target.tile)
            if deck:
                camera.bounds = (
                    deck.left * tile_px,
                    deck.top * tile_px,
                    deck.width * tile_px,
                    deck.height * tile_px,
                )
            camera.follow(tuple(axis * tile_px / U for axis in target.position), 0, snap=True)
            view = opaque_surface(size)
            draw_world(
                view,
                level,
                flow.map_surface,
                snapshot,
                camera,
                flow.fonts,
                0.5,
                actor_motion=session.actor_motion,
                clock_ms=session.clock_ms,
                art=flow.art,
                furnishings=flow.furnishings,
                fraction=session.render_fraction,
                observer_id=target.actor_id,
            )
            return view

        for frame in range(args.frames):
            pygame.event.pump()
            flow.frame([], 17)
            snapshot = session.simulation.presentation_snapshot()
            actors = {actor.actor_id: actor for actor in snapshot.actors}
            began = perf_counter()
            for index, chosen in enumerate(selected):
                actor = actors[chosen.actor_id]
                motion = session.actor_motion.get(actor.actor_id)
                if motion and motion.moving:
                    samples[actor.kind.value] += 1
                    if motion.sprinting:
                        fast_samples[actor.kind.value] += 1
                    poses.setdefault(actor.kind.value, set()).add(int(motion.phase * 16) % 16)
                view = world(actor)
                canvas.blit(view, ((index % 2) * 512, (index // 2) * 384))
                label = flow.fonts.micro.render(
                    actor.kind.value + " / ACTUAL MOTION / DIAGNOSTIC CAMERA", True, (220, 240, 244)
                )
                canvas.blit(label, ((index % 2) * 512 + 8, (index // 2) * 384 + 8))
            elapsed.append((perf_counter() - began) * 1000)
            display.blit(canvas, (0, 0))
            pygame.display.flip()
            if frame in (30, 90, 150, 210, args.frames // 2, args.frames - 10):
                name = f"real-robots-{frame:03d}"
                pygame.image.save(canvas, str(args.output / f"{name}.png"))
                shots.append(name)
            if encoder and encoder.stdin:
                encoder.stdin.write(pygame.image.tobytes(canvas, "RGB"))
        if encoder and encoder.stdin:
            encoder.stdin.close()
            assert encoder.wait(timeout=60) == 0
        before = session.simulation.fingerprint()
        for room in level.rooms:
            # Architecture camera only: no actor/map/observation or outcome injection.
            room_deck = level.deck_at((room.left, room.top))
            preview_actor = next(
                actor
                for actor in session.simulation.presentation_snapshot().actors
                if level.deck_at(actor.tile) == room_deck
            )
            camera = Camera(1024, 768, *flow.map_surface.get_size())
            if room_deck:
                camera.bounds = (
                    room_deck.left * tile_px,
                    room_deck.top * tile_px,
                    room_deck.width * tile_px,
                    room_deck.height * tile_px,
                )
            camera.follow(
                ((room.left + room.width / 2) * tile_px, (room.top + room.height / 2) * tile_px),
                0,
                snap=True,
            )
            draw_world(
                canvas,
                level,
                flow.map_surface,
                session.simulation.presentation_snapshot(),
                camera,
                flow.fonts,
                0.5,
                art=flow.art,
                furnishings=flow.furnishings,
                actor_motion=session.actor_motion,
                observer_id=preview_actor.actor_id,
            )
            canvas.blit(
                flow.fonts.micro.render(
                    "ARCHITECTURE CAMERA / " + room.label, True, (240, 225, 180)
                ),
                (15, 15),
            )
            name = "room-" + room.room_id
            pygame.image.save(canvas, str(args.output / f"{name}.png"))
            shots.append(name)
        assert session.simulation.fingerprint() == before
        styles = Counter()
        for item in flow.furnishings:
            style = shadow_at(level, item.footprint.center, item.render_rect.h // 2)
            styles[f"{style.dx},{style.dy},{style.alpha}"] += 1
        report = {
            "driver": pygame.display.get_driver(),
            "frames": args.frames,
            "actual_tick": session.simulation.tick,
            "moving_frame_samples": dict(samples),
            "fast_frame_samples": dict(fast_samples),
            "actual_pose_indices": {kind: sorted(values) for kind, values in poses.items()},
            "furniture_shadow_styles": dict(styles),
            "shots": shots,
            "four_camera_draw_ms_p95": sorted(elapsed)[int(len(elapsed) * 0.95)],
            "scope": "Production AI/map, real committed movement. Four diagnostic actor cameras "
            "and room-only previews are visual QA, not ordinary player visibility or FPS.",
        }
        (args.output / "REVIEW.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
