"""Native labeled P05 presentation fixture; never evidence of environment physics.

Run with --interactive to review motion/sound; Space pauses, R reduces effects,
Escape closes. Default saves native frames and a bounded render workload report.
"""

import argparse
import json
from dataclasses import replace
from pathlib import Path
from statistics import median
from time import perf_counter

import pygame

from echo_heist.core.contracts.environment.presentation import (
    EnvironmentCue,
    EnvironmentCueKind,
    EnvironmentView,
    PropKind,
    PropView,
)
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as U
from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.audio.model import AudioFrame
from echo_heist.ui.presenters.interactions import Effect, InteractionPresentation
from echo_heist.ui.render import theme
from echo_heist.ui.render.actors.draw import draw_actor
from echo_heist.ui.render.actors.model import ActorMotion
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.interactions.effects import draw_effects
from echo_heist.ui.render.interactions.props import draw_prop, footprint
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.render.world import draw_world
from echo_heist.ui.scenes.flow import GameFlow


def props(tick: int) -> tuple[PropView, ...]:
    t = (tick % 120) / 120
    openness = max(0, min(1, (t - 0.12) * 4, (0.95 - t) * 4))
    points = ((1.35, 2.45), (4.5, 2.45), (7.6, 2.45), (10.75, 2.45))
    sizes = ((2.4, 0.9), (2.5, 0.25), (0.45, 0.65), (1, 0.6))
    result = []
    for i, (kind, point, size) in enumerate(zip(PropKind, points, sizes, strict=True)):
        position = (round(point[0] * U), round(point[1] * U))
        previous = None
        if kind == PropKind.CANISTER:
            position = (round((point[0] + min(t * 2, 1) * 0.5) * U), position[1])
            previous = (position[0] - (round(U * 0.5 / 60) if t < 0.5 else 0), position[1])
        result.append(
            PropView(
                f"fixture-{i}",
                kind,
                position,
                (round(size[0] * U), round(size[1] * U)),
                openness=openness,
                broken=t >= 0.5,
                locked=t < 0.12,
                previous_position=previous,
                roll_degrees=min(t * 2, 1) * 180,
                occupant_id="operative" if kind == PropKind.LOCKER and 0.35 < t < 0.8 else None,
                occupant_cover=1 if kind == PropKind.LOCKER and 0.35 < t < 0.8 else 0,
            )
        )
    return tuple(result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/phase05-visuals/fixture"))
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pygame.display.init()
    pygame.font.init()
    pygame.mixer.init()
    display = pygame.display.set_mode((1280, 720))
    screen = opaque_surface((1280, 720))
    pygame.display.set_caption("ECHO HEIST / P05 presentation fixture")
    flow = GameFlow(screen.get_size())
    flow._start_run()
    session = flow.session
    assert session is not None
    audio = AudioDirector(enabled=True)
    camera = Camera(1280, 720, 1280, 720, x=-60, y=-70)
    floor = pygame.transform.smoothscale(session.art.floor, (96, 96))
    stats = []
    shots = []
    reduced = paused = False
    tick = 0
    clock = pygame.time.Clock()
    before = session.simulation.fingerprint()
    base = session.simulation.presentation_snapshot()
    presenter = InteractionPresentation(
        "operative", 30, emp_radius_units=session.rules.emp_radius_units
    )
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                pygame.quit()
                return 0
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                paused = not paused
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                reduced = not reduced
        phase = tick % 120
        cycle = tick // 120
        items = props(tick)
        cues = []
        for offset, kind, i in (
            (15, EnvironmentCueKind.DOOR, 0),
            (60, EnvironmentCueKind.GLASS, 1),
            (60, EnvironmentCueKind.CANISTER_IMPACT, 2),
            (45, EnvironmentCueKind.HIDE_ENTER, 3),
            (100, EnvironmentCueKind.HIDE_LEAVE, 3),
        ):
            if phase == offset:
                cues.append(
                    EnvironmentCue(
                        f"fixture:{cycle}:{kind}",
                        tick,
                        kind,
                        items[i].object_id,
                        items[i].position,
                        actor_id="operative",
                        visible=True,
                    )
                )
        snapshot = replace(base, tick=tick, environment=EnvironmentView(items, tuple(cues)))
        presenter.observe(snapshot, session.simulation.observe("operative"), ())
        audio.update(
            AudioFrame(
                "HEIST",
                "fixture",
                1,
                paused=paused,
                tick=tick,
                listener_position=(12 * U, 4 * U),
                environment_cues=presenter.take_audio(),
            ),
            33,
        )
        started = perf_counter()
        screen.fill(theme.BACKGROUND)
        for y in range(150, 355, 96):
            for x in range(0, 1280, 96):
                screen.blit(floor, (x, y))
        for item in items:
            if item.kind == PropKind.LOCKER and item.occupant_id is None:
                pos = camera.to_screen((item.position[0] * 96 / U, item.position[1] * 96 / U))
                draw_actor(
                    screen,
                    (pos[0] + 58, pos[1] + 24),
                    session.art.operative,
                    ActorMotion(),
                    0,
                    disabled=False,
                    stunned=False,
                    carries_core=False,
                    pulse=0.5,
                    crouch=session.art.operative_crouch,
                )
            draw_prop(
                screen,
                item,
                camera,
                session.level.static_map.tile_size_px,
                1,
                session.art.props[46],
            )
        draw_effects(
            screen,
            tuple(presenter.effects),
            camera,
            session.level.static_map.tile_size_px,
            tick,
            30,
            reduced_motion=reduced,
        )
        title = session.fonts.heading.render(
            "INTERACTIVE ENVIRONMENT / PRESENTATION REVIEW", True, theme.TEXT
        )
        screen.blit(title, (40, 35))
        label = session.fonts.small.render(
            "SCRIPTED FIXTURE / NO DOOR, GLASS OR HIDING LOGIC", True, theme.WARNING
        )
        screen.blit(label, (40, 83))
        for i, (name, state) in enumerate(
            (
                ("PRESSURE DOOR", "LOCKED" if items[0].locked else "OPENING / CLOSING"),
                ("GLASS PARTITION", "BROKEN" if items[1].broken else "INTACT"),
                ("LOOSE CANISTER", "ROLL / IMPACT"),
                ("HIDING LOCKER", "OCCUPIED" if items[3].occupant_id else "EMPTY"),
            )
        ):
            x = 40 + i * 300
            screen.blit(session.fonts.small.render(name, True, theme.TEXT), (x, 120))
            screen.blit(session.fonts.micro.render(state, True, theme.ACCENT), (x, 380))
        tool_effects = tuple(
            Effect(
                f"tool-{i}",
                cycle * 120,
                name,
                (round((2 + i * 6) * U), 10 * U),
                target=(round((3 + i * 6) * U), 10 * U),
                radius_units=session.rules.emp_radius_units if name == "EMP" else 0,
            )
            for i, name in enumerate(("ECHO", "EMP", "MELEE", "RESISTED"))
        )
        # Cycle tool samples independently so each effect remains easy to inspect.
        tool_effects = tuple(replace(effect, tick=tick - phase % 30) for effect in tool_effects)
        draw_effects(screen, tool_effects, camera, 48, tick, 30, reduced_motion=reduced)
        for i, name in enumerate(("ECHO DEPLOY", "EMP RADIUS", "MELEE CONTACT", "GUARD RESISTED")):
            screen.blit(session.fonts.micro.render(name, True, theme.MUTED), (40 + i * 300, 625))
        screen.blit(
            session.fonts.micro.render(
                "SPACE Pause   R Reduced effects   ESC Close", True, theme.MUTED
            ),
            (40, 680),
        )
        display.blit(screen, (0, 0))
        pygame.display.flip()
        stats.append((perf_counter() - started) * 1000)
        if tick in (0, 30, 60, 70, 90, 110, 170, 180):
            path = args.output / f"props-{tick:03}.png"
            pygame.image.save(screen, str(path))
            shots.append(path.name)
        if tick == 150 and not args.interactive:
            reduced = True
        if not paused:
            tick += 1
        if args.interactive:
            clock.tick(30)
        elif tick >= 240:
            break
    # Exercise the actual world renderer with fixture-only immutable snapshots.
    size = session.level.static_map.tile_size_px
    for turn, deck in enumerate(session.level.decks):
        anchor = session.level.exit_id if turn == 0 else session.level.core_id
        tile = next(obj.tile for obj in session.level.static_map.objects if obj.object_id == anchor)
        offset = ((tile[0] - 2) * U, (tile[1] - 4) * U)
        placed = tuple(
            replace(
                item,
                position=(item.position[0] + offset[0], item.position[1] + offset[1]),
                previous_position=None,
            )
            for item in props(60)
        )
        actors = tuple(
            replace(actor, tile=tile, position=(tile[0] * U + U // 2, tile[1] * U + U // 2))
            if actor.actor_id == session.observer_id
            else actor
            for actor in base.actors
        )
        view = replace(base, actors=actors, environment=EnvironmentView(props=placed))
        session.camera.follow((tile[0] * size, tile[1] * size), 0, snap=True)
        session.camera.bounds = (
            deck.left * size,
            deck.top * size,
            deck.width * size,
            deck.height * size,
        )
        session.camera.follow((tile[0] * size, tile[1] * size), 0, snap=True)
        draw_world(
            screen,
            session.level,
            session.map_surface,
            view,
            session.camera,
            session.fonts,
            0.5,
            art=session.art,
            furnishings=session.furnishings,
        )
        screen.blit(label, (30, 20))
        name = f"world-deck-{turn + 1}.png"
        pygame.image.save(screen, str(args.output / name))
        shots.append(name)
    assert session.simulation.fingerprint() == before
    # Check committed fixed-point interpolation, independent of camera/view size.
    canister = props(30)[2]
    assert footprint(canister, 48, 0).centerx <= footprint(canister, 48, 1).centerx
    # These HUD captures use real ordinary Human tool actions, not injected tool results.
    session._follow(0, snap=True)
    for key, name in (
        (pygame.K_q, "human-echo"),
        (pygame.K_f, "human-emp"),
        (pygame.K_f, "human-emp-empty"),
        (pygame.K_SPACE, "human-melee-out-of-range"),
    ):
        session.input.feed(
            [pygame.event.Event(kind, key=key) for kind in (pygame.KEYDOWN, pygame.KEYUP)]
        )
        session.update(40)
        session.draw(screen)
        display.blit(screen, (0, 0))
        pygame.display.flip()
        pygame.image.save(screen, str(args.output / (name + ".png")))
        shots.append(name + ".png")
    report = {
        "kind": "scripted presentation fixture, NOT environment behavior proof",
        "driver": pygame.display.get_driver(),
        "audio_ready": pygame.mixer.get_init() is not None,
        "shots": shots,
        "frames": len(stats),
        "render_ms_median": round(median(stats), 3),
        "render_ms_p95": round(sorted(stats)[int(len(stats) * 0.95)], 3),
        "effects_max": 32,
        "fixture_simulation_unchanged": True,
        "human_tool_capture_ticks": session.simulation.presentation_snapshot().tick,
        "audio": audio.report(),
    }
    (args.output / "REVIEW.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
