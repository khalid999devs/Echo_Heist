"""P03 native gate: ordinary Human input, live diagnostics and both-deck evidence.

Screens and traces are ignored output. No actor position, guard memory or outcome
is injected. Off-screen room inspection moves only a diagnostic Camera.
"""

import argparse
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from statistics import median
from time import perf_counter

import pygame

from echo_heist.core.contracts.world import MissionPhase
from echo_heist.diagnostics.facility_routes import mission_path, walk_path
from echo_heist.diagnostics.human_driver import HumanDriver
from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.bootstrap import _logical_events
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.environment.furnishings.catalogue import draw_instrument
from echo_heist.ui.render.layout.viewport import interface_origin, logical_size_for
from echo_heist.ui.render.security.lab import GUARD_TABS
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.flow import GameFlow, Scene


def key(code: int) -> list[pygame.event.Event]:
    return [pygame.event.Event(kind, key=code) for kind in (pygame.KEYDOWN, pygame.KEYUP)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/phase03-integration"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pygame.display.init()
    pygame.font.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1280, 720))
    canvas = opaque_surface(screen.get_size())
    flow = GameFlow(canvas.get_size())
    audio = AudioDirector(enabled=True)
    frames = []
    shots: set[str] = set()
    states: set[str] = set()
    traces: dict[str, object] = {}
    decks: set[str] = set()
    captures = Counter()

    def render() -> None:
        started = perf_counter()
        pygame.event.pump()
        audio.update(flow.audio_frame(), 34)
        flow.draw(canvas)
        screen.blit(pygame.transform.smoothscale(canvas, screen.get_size()), (0, 0))
        pygame.display.flip()
        frames.append((perf_counter() - started) * 1000)

    def shot(name: str) -> None:
        render()
        path = args.output / "screens" / (name + ".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(screen, str(path))
        shots.add(name)

    def inspect() -> None:
        assert flow.session is not None
        session = flow.session
        snapshot = session.simulation.presentation_snapshot()
        actors = {actor.actor_id: actor for actor in snapshot.actors}
        own = actors[flow.level.operative_id]
        deck = flow.level.deck_at(own.tile)
        if deck:
            decks.add(deck.deck_id)
        for guard in snapshot.guards:
            marker = f"{guard.actor_id}/{guard.state}"
            states.add(marker)
            actor = actors[guard.actor_id]
            visible = deck is None or deck.contains(actor.tile)
            position = actor.position
            if position is not None:
                point = session.camera.to_screen(
                    tuple(axis * flow.level.static_map.tile_size_px / 30000 for axis in position)
                )
                visible = visible and canvas.get_rect().inflate(-120, -180).collidepoint(point)
            name = f"guards/{guard.actor_id}-{guard.state.lower()}"
            if visible and name not in shots:
                shot(name)
                before = session.simulation.fingerprint()
                if not session.lab_note:
                    flow.frame(key(pygame.K_F3), 0)
                index = snapshot.guards.index(guard)
                flow.frame(key(pygame.K_1 + index), 0)
                shot(name + "-lab")
                if guard.fuzzy_trace is not None:
                    traces[name] = {
                        "urgency": guard.fuzzy_trace.urgency,
                        "evaluated_tick": guard.fuzzy_trace.evaluated_tick,
                        "cue_tile": guard.fuzzy_trace.cue_tile,
                        "evidence_tile": guard.evidence_tile,
                    }
                flow.frame(key(pygame.K_F3), 0)
                assert session.simulation.fingerprint() == before
        for capture in snapshot.captures:
            captures[capture.guard_id] += 1
            if "capture/wind-up" not in shots:
                shot("capture/wind-up")
        render()

    def drive(path: tuple[tuple[int, int], ...], *, tools: bool = True) -> None:
        assert flow.session is not None
        driver = HumanDriver(flow.rules, use_tools=tools)
        for tile in path:
            for _ in range(1000):
                observation = flow.session.simulation.observe(flow.level.operative_id)
                if driver.arrived(observation, tile):
                    break
                flow.frame(driver.events(observation, tile), 34)
                inspect()
                if flow.session.mission_end is not None:
                    return
            else:
                raise RuntimeError(f"Human route stalled at {tile}")
        flow.frame(driver.release(), 0)

    outcomes = {}
    for branch in ("upper", "lower"):
        flow._start_run()  # Actual restart factory; default registry and seed.
        flow.frame([], 1300)
        drive(mission_path(flow.level, branch))
        flow.frame([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)], 34)
        for _ in range(50):
            flow.frame([], 34)
            inspect()
        flow.frame([pygame.event.Event(pygame.KEYUP, key=pygame.K_e)], 0)
        assert (
            flow.session
            and flow.session.simulation.observe(flow.level.operative_id).phase
            == MissionPhase.LOCKDOWN
        )
        shot(f"routes/{branch}-lockdown")
        drive(mission_path(flow.level, branch, returning=True))
        assert flow.session and flow.session.mission_end
        assert flow.session.mission_end.outcome.value == "WIN"
        outcomes[branch] = {"outcome": "WIN", "ticks": flow.session.mission_end.elapsed_ticks}
        print(f"{branch}: WIN at {flow.session.mission_end.elapsed_ticks}", flush=True)
        flow.frame([], 2200)
        shot(f"routes/{branch}-win")

    flow._start_run()
    flow.frame([], 1300)
    desk = (3, 21)
    drive(walk_path(flow.level, flow.level.spawn_tile, (3, 22)), tools=False)
    flow.frame(key(pygame.K_c), 34)
    drive((desk,), tools=False)
    for _ in range(60):
        flow.frame([], 34)
    assert (
        flow.session
        and flow.session.simulation.observe(flow.level.operative_id).own_status.concealed
    )
    assert not flow.session.mission_end
    shot("hiding/unseen-under-desk")
    drive(((3, 22),), tools=False)
    flow.frame(key(pygame.K_c), 34)
    assert not flow.session.simulation.observe(flow.level.operative_id).own_status.crouched

    # A timed, ordinary approach from behind the patrol gives a real uncertain
    # sound evaluation, rather than filling the teaching panel with sample data.
    flow._start_run()
    flow.frame([], 1300)
    assert flow.session
    while flow.session.simulation.tick < 270:
        flow.frame([], 33)
    drive(walk_path(flow.level, flow.level.spawn_tile, (22, 20)), tools=False)
    emp_tick = flow.session.simulation.tick + 1
    flow.frame(key(pygame.K_f), 34)
    for _ in range(12):
        flow.frame([], 17)
        snapshot = flow.session.simulation.presentation_snapshot()
        guard = next(guard for guard in snapshot.guards if guard.actor_id == "guard-service")
        if (
            guard.fuzzy_trace
            and guard.fuzzy_trace.evaluated_tick >= emp_tick
            and guard.evidence_kind == "NOISE"
        ):
            break
    assert guard.fuzzy_trace and sum(guard.fuzzy_trace.activations) > 0
    assert guard.identification_ticks < guard.identification_required_ticks
    flow.frame(key(pygame.K_F3), 0)
    flow.frame(key(pygame.K_4), 0)
    traces["fuzzy/actual-emp"] = asdict(guard.fuzzy_trace)
    shot("fuzzy/actual-emp")
    print(
        f"Fuzzy hearing: urgency {guard.fuzzy_trace.urgency}, ID {guard.identification_ticks}",
        flush=True,
    )

    # Inspect the actual F3 pointer mapping at laptop, tall and native fullscreen sizes.
    layouts = []
    for requested in ((1366, 768), (1440, 900), (0, 0)):
        flags = pygame.FULLSCREEN if requested == (0, 0) else pygame.RESIZABLE
        screen = pygame.display.set_mode(requested, flags)
        actual = screen.get_size()
        logical = logical_size_for(actual)
        flow.resize(logical)
        canvas = opaque_surface(logical)
        origin = interface_origin(logical)
        flow.session.paused = False
        if not flow.session.lab_note:
            flow.frame(key(pygame.K_F3), 0)
        fingerprint = flow.session.simulation.fingerprint()
        for index, tab in enumerate(GUARD_TABS):
            logical_pos = (tab.centerx + origin[0], tab.centery + origin[1])
            window = pygame.display.get_window_size()
            pos = (
                round(logical_pos[0] * window[0] / logical[0]),
                round(logical_pos[1] * window[1] / logical[1]),
            )
            events = [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)]
            flow.frame(_logical_events(events, window, logical), 0)
            assert flow.session.lab_selected == index
            shot(f"layouts/{actual[0]}x{actual[1]}-guard-{index + 1}")
        assert flow.session.simulation.fingerprint() == fingerprint
        layouts.append(
            {
                "actual": actual,
                "logical": logical,
                "fullscreen": pygame.display.is_fullscreen(),
                "guard_clicks": 4,
            }
        )

    screen = pygame.display.set_mode((1280, 720))
    canvas = opaque_surface((1280, 720))
    flow.resize(canvas.get_size())
    flow._start_run()
    flow.frame([], 1300)
    service = next(post for post in flow.level.guards if post.guard_id == "guard-service")
    drive(walk_path(flow.level, flow.level.spawn_tile, service.tile), tools=False)
    for _ in range(1200):
        if flow.scene == Scene.RESULTS:
            break
        flow.frame([], 34)
        inspect()
    assert (
        flow.session
        and flow.session.mission_end
        and flow.session.mission_end.outcome.value == "CAPTURED"
    )
    shot("capture/result")
    outcomes["careless"] = {"outcome": "CAPTURED", "ticks": flow.session.mission_end.elapsed_ticks}

    # Physical fixture/route inspection uses unmodified live state and a separate camera.
    for room in flow.level.rooms:
        size = flow.level.static_map.tile_size_px
        camera = Camera(1280, 720, *flow.map_surface.get_size())
        camera.follow(
            ((room.left + room.width / 2) * size, (room.top + room.height / 2) * size), 0, snap=True
        )
        canvas.blit(flow.map_surface, camera.to_screen((0, 0)))
        for item in sorted(flow.furnishings, key=lambda item: item.depth):
            draw_instrument(canvas, item, camera, 0)
        for obstacle in flow.level.static_map.obstacles:
            origin = camera.to_screen((obstacle.left * size / 30000, obstacle.top * size / 30000))
            rect = pygame.Rect(
                origin,
                (
                    (obstacle.right - obstacle.left) * size / 30000,
                    (obstacle.bottom - obstacle.top) * size / 30000,
                ),
            )
            pygame.draw.rect(canvas, (37, 226, 235), rect, 1)
        path = args.output / "geometry" / (room.room_id + ".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(canvas, str(path))

    report = {
        "driver": pygame.display.get_driver(),
        "outcomes": outcomes,
        "decks": sorted(decks),
        "states": sorted(states),
        "traces": traces,
        "capture_frames": dict(captures),
        "screens": sorted(shots),
        "layouts": layouts,
        "unseen_hiding": "PASS",
        "diagnostics_read_only": "PASS",
        "frames": len(frames),
        "render_audio_present_ms": {
            "median": round(median(frames), 2),
            "p95": round(sorted(frames)[int(0.95 * len(frames))], 2),
            "max": round(max(frames), 2),
        },
        "scope": (
            "Accelerated native Human input, default four-guard security. "
            "Timing excludes simulation; room cameras are diagnostic only."
        ),
    }
    (args.output / "GATE.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
