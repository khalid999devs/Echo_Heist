"""Native all-scene review using real inputs and committed mission outcomes."""

import argparse
import json
from pathlib import Path
from statistics import median
from time import perf_counter

import pygame

from echo_heist.diagnostics.facility_routes import mission_path, walk_path
from echo_heist.diagnostics.human_driver import HumanDriver
from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.design.screens import GUIDE_CONTROLS, LAB_CONTROLS
from echo_heist.ui.scenes.design.workshop import WORKSHOP_CONTROLS
from echo_heist.ui.scenes.flow import GameFlow, Scene
from echo_heist.ui.scenes.menus import CHAPTER_CARD, MODE_BUTTONS, RESULT_STORY, TITLE_BUTTONS
from echo_heist.ui.scenes.navigation.controls import ABORT_BUTTONS, MAP_CLOSE, PAUSE_BUTTONS
from echo_heist.ui.scenes.settings import OPTION_RECTS


def key(value: int, *, release: bool = False) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYUP if release else pygame.KEYDOWN, key=value)


def click(rect: pygame.Rect) -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/scene-presentation"))
    parser.add_argument("--mute", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pygame.display.init()
    pygame.font.init()
    if not args.mute:
        pygame.mixer.init()
    screen = pygame.display.set_mode((1280, 720))
    canvas = opaque_surface((1280, 720))
    audio = AudioDirector(enabled=not args.mute)
    timings: list[float] = []
    shots: set[str] = set()
    tracks: set[str] = set()
    alarm_frames = 0
    slow_frames: list[dict[str, object]] = []

    def render(flow: GameFlow) -> None:
        nonlocal alarm_frames
        began = perf_counter()
        pygame.event.pump()
        audio.update(flow.audio_frame(), 34)
        tracks.add(str(audio.current_music))
        if audio.report()["lockdown_alarm_active"]:
            alarm_frames += 1
        mixed = perf_counter()
        flow.draw(canvas)
        drawn = perf_counter()
        screen.blit(canvas, (0, 0))
        pygame.display.flip()
        presented = perf_counter()
        timings.append((presented - began) * 1000)
        if timings[-1] > 50:
            slow_frames.append(
                {
                    "scene": flow.scene.value,
                    "frame": len(timings),
                    "audio_ms": round((mixed - began) * 1000, 2),
                    "draw_ms": round((drawn - mixed) * 1000, 2),
                    "present_ms": round((presented - drawn) * 1000, 2),
                }
            )

    def shot(flow: GameFlow, name: str) -> None:
        render(flow)
        target = args.output / "screens" / f"{name}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(canvas, str(target))
        shots.add(name)

    flow = GameFlow((1280, 720))
    # Production primes this under the resource-loading opening. This direct
    # scene harness records its separate cold cost before interactive timings.
    priming = perf_counter()
    audio.update(flow.audio_frame(), 0)
    initial_music_ms = (perf_counter() - priming) * 1000
    flow.frame([], 2300)
    shot(flow, "menus/title")
    flow.frame([click(TITLE_BUTTONS[4])], 0)
    for i, rect in enumerate(GUIDE_CONTROLS[:4]):
        flow.frame([click(rect)], 0)
        shot(flow, f"guide/tab-{i + 1}")
    flow.frame([click(GUIDE_CONTROLS[4])], 0)
    flow.frame([click(TITLE_BUTTONS[2])], 0)
    shot(flow, "menus/settings")
    flow.frame([click(OPTION_RECTS[4])], 0)
    flow.frame([click(CHAPTER_CARD)], 0)
    shot(flow, "menus/briefing")
    flow.frame([click(MODE_BUTTONS[1])], 0)
    assert flow.scene == Scene.WORKSHOP
    for i in range(3):
        flow.frame([click(WORKSHOP_CONTROLS[i])], 0)
        shot(flow, f"workshop/preset-{i + 1}")
    flow.frame([click(WORKSHOP_CONTROLS[3])], 0)
    shot(flow, "workshop/custom")
    flow.frame([click(WORKSHOP_CONTROLS[8])], 0)
    assert flow.session is None and flow.runs_started == 0
    shot(flow, "workshop/deployment-boundary")
    flow.frame([click(WORKSHOP_CONTROLS[7])], 0)
    for i in range(2):
        flow.frame([click(LAB_CONTROLS[i])], 0)
        shot(flow, f"companion/floor-{i + 1}")
    flow.frame([click(LAB_CONTROLS[2])], 0)
    flow.frame([click(WORKSHOP_CONTROLS[9])], 0)
    flow.frame([click(MODE_BUTTONS[2])], 0)
    assert flow.session is not None
    entrance_fingerprint = flow.session.simulation.fingerprint()
    shot(flow, "airlock/entry-closed")
    flow.frame([], 650)
    shot(flow, "airlock/entry-opening")
    flow.frame([], 650)
    assert flow.session.simulation.fingerprint() == entrance_fingerprint
    shot(flow, "mission/entry")
    flow.frame([key(pygame.K_TAB)], 0)
    shot(flow, "mission/map")
    flow.frame([click(MAP_CLOSE)], 0)
    flow.frame([key(pygame.K_ESCAPE)], 0)
    shot(flow, "mission/pause")
    assert flow.session is not None
    before = flow.session.simulation.fingerprint()
    flow.frame([click(PAUSE_BUTTONS[2])], 0)
    flow.frame([], 1000)
    assert flow.session.simulation.fingerprint() == before
    flow.frame([click(OPTION_RECTS[4])], 0)
    flow.frame([click(PAUSE_BUTTONS[3])], 0)
    shot(flow, "mission/confirm-abort")
    flow.frame([click(ABORT_BUTTONS[0])], 0)
    assert flow.scene == Scene.RESULTS and flow.session.mission_end is not None
    shot(flow, "ending/aborted")

    states: set[str] = set()
    rooms: set[str] = set()
    stairs: set[tuple[str, int]] = set()

    def observe(current: GameFlow) -> None:
        assert current.session is not None
        render(current)
        snap = current.session.simulation.presentation_snapshot()
        for guard in snap.guards:
            if guard.state.value not in states:
                states.add(guard.state.value)
                shot(current, f"guards/{guard.state.value.lower()}")
        for travel in snap.stairs:
            if travel.actor_id != current.level.operative_id:
                continue
            phase = round((1 - travel.remaining_ticks / travel.total_ticks) * 2)
            direction = "up" if travel.destination[0] > travel.source[0] else "down"
            marker = (direction, phase)
            if marker not in stairs:
                stairs.add(marker)
                shot(current, f"stairs/{direction}-{phase}")
        own = current.session.simulation.observe(current.level.operative_id).own_status
        room = current.level.room_at(own.tile)
        if (
            room is not None
            and room.label not in rooms
            and not own.stair_ticks_remaining
            and current.session.clock_ms - current.session.floor_changed_ms > 300
        ):
            rooms.add(room.label)
            shot(current, "rooms/" + room.label.lower().replace(" ", "-"))

    def drive(current: GameFlow, path: tuple[tuple[int, int], ...]) -> None:
        assert current.session is not None
        driver = HumanDriver(current.rules, use_tools=True)
        for tile in path:
            for _ in range(1000):
                obs = current.session.simulation.observe(current.level.operative_id)
                if driver.arrived(obs, tile):
                    break
                current.frame(driver.events(obs, tile), 34)
                observe(current)
                if current.scene == Scene.RESULTS:
                    return
            else:
                raise RuntimeError(f"Route stalled at {tile}")
        current.frame(driver.release(), 0)

    outcomes: dict[str, object] = {}
    for branch in ("upper", "lower"):
        current = GameFlow((1280, 720))
        current.frame([click(CHAPTER_CARD)], 0)
        current.frame([click(MODE_BUTTONS[2])], 0)
        drive(current, mission_path(current.level, branch))
        current.frame([key(pygame.K_e)], 34)
        for _ in range(50):
            current.frame([], 34)
            render(current)
        current.frame([key(pygame.K_e, release=True)], 0)
        shot(current, f"lockdown/{branch}-bright")
        current.frame([], 440)
        shot(current, f"lockdown/{branch}-dim")
        if branch == "upper":
            current.frame([key(pygame.K_F3)], 0)
            current.frame([key(pygame.K_F3, release=True)], 0)
            shot(current, "mission/live-diagnostics")
            current.frame([key(pygame.K_F3)], 0)
            current.frame([key(pygame.K_F3, release=True)], 0)
        drive(current, mission_path(current.level, branch, returning=True))
        assert current.session and current.session.mission_end
        end = current.session.mission_end
        assert end.outcome.value == "WIN"
        outcomes[branch] = {"outcome": end.outcome.value, "ticks": end.elapsed_ticks}
        for _ in range(10):
            current.frame([], 34)
            render(current)
        shot(current, f"airlock/{branch}-closing")
        current.frame([], 500)
        shot(current, f"airlock/{branch}-sealed")
        current.frame([], 600)
        shot(current, f"airlock/{branch}-opening")
        current.frame([], 600)
        shot(current, f"ending/{branch}-extracted")
        current.frame([click(RESULT_STORY)], 0)
        assert current.scene == Scene.EPILOGUE
        shot(current, "ending/epilogue")
    current = GameFlow((1280, 720))
    current.frame([click(CHAPTER_CARD)], 0)
    current.frame([click(MODE_BUTTONS[2])], 0)
    post = next(post for post in current.level.guards if post.guard_id == "guard-service")
    drive(current, walk_path(current.level, current.level.spawn_tile, post.tile))
    for _ in range(1200):
        current.frame([], 34)
        render(current)
        if current.scene == Scene.RESULTS:
            break
    assert current.session and current.session.mission_end
    assert current.session.mission_end.outcome.value == "CAPTURED"
    shot(current, "ending/captured")
    report = {
        "video_driver": pygame.display.get_driver(),
        "screens": len(shots),
        "outcomes": outcomes,
        "capture_ticks": current.session.mission_end.elapsed_ticks,
        "guard_states": sorted(states),
        "rooms_seen": sorted(rooms),
        "stair_views": sorted(stairs),
        "alarm_frames": alarm_frames,
        "entrance_keeps_unseen_simulation_frozen": True,
        "exit_airlock_requires_actual_win": True,
        "tracks": sorted(tracks),
        "frames": len(timings),
        "initial_music_preparation_ms": round(initial_music_ms, 2),
        "frames_over_50ms": slow_frames,
        "render_audio_display_ms": {
            "median": round(median(timings), 2),
            "p95": round(sorted(timings)[int(0.95 * len(timings))], 2),
            "max": round(max(timings), 2),
        },
        "scope": (
            "Accelerated native source input sweep; frame timings exclude simulation. "
            "AI scenes are designs; actual Human outcomes only."
        ),
    }
    (args.output / "PLAYTHROUGH.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
