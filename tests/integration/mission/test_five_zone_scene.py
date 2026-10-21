"""Real menu/input/scene composition against the packaged five-zone mission."""

import pygame

from echo_heist.core.contracts.results import RunOutcome
from echo_heist.core.contracts.world import MissionPhase, tile_center
from echo_heist.ui.bootstrap import _logical_events
from echo_heist.ui.scenes.flow import GameFlow, Scene

UPPER = [(12, 17), (23, 17), (23, 8), (43, 8), (43, 12), (58, 12), (58, 16)]
RETURN = [(58, 12), (43, 12), (43, 8), (23, 8), (23, 17), (12, 17), (2, 17)]
ARRIVE = 4_000


def key(event_type: int, value: int) -> pygame.event.Event:
    return pygame.event.Event(event_type, key=value)


def start(*, security_enabled: bool = False) -> GameFlow:
    pygame.font.init()
    flow = GameFlow((1280, 720), security_enabled=security_enabled)
    flow.frame([key(pygame.KEYDOWN, pygame.K_RETURN)], 0)
    assert flow.scene == Scene.MODE
    flow.frame([key(pygame.KEYDOWN, pygame.K_RETURN)], 0)
    assert flow.scene == Scene.HEIST and flow.session is not None
    return flow


def drive(
    flow: GameFlow,
    route: list[tuple[int, int]],
    *,
    take_core: bool = False,
    expected_end: RunOutcome | None = None,
) -> None:
    assert flow.session is not None
    held: set[int] = set()
    pending = list(route)
    until = flow.session.steps + 3_000
    while pending and flow.session.steps < until:
        observation = flow.session.simulation.observe(flow.level.operative_id)
        position = observation.own_status.position
        assert position is not None
        destination = tile_center(pending[0])
        dx, dy = destination[0] - position[0], destination[1] - position[1]
        if abs(dx) < ARRIVE and abs(dy) < ARRIVE:
            pending.pop(0)
            continue
        direction = (
            pygame.K_d
            if dx > ARRIVE
            else pygame.K_a
            if dx < -ARRIVE
            else pygame.K_s
            if dy > ARRIVE
            else pygame.K_w
        )
        desired = {direction, pygame.K_LSHIFT}
        events = [key(pygame.KEYUP, code) for code in sorted(held - desired)]
        events.extend(key(pygame.KEYDOWN, code) for code in sorted(desired - held))
        held = desired
        flow.frame(events, 34)
        if flow.scene == Scene.RESULTS:
            assert expected_end is not None and len(pending) == 1
            assert flow.session.mission_end is not None
            assert flow.session.mission_end.outcome == expected_end
            return
        assert flow.scene == Scene.HEIST, "Unexpected mission end before reaching waypoint"
    assert not pending, "The real input adapter did not reach the route"
    flow.frame([key(pygame.KEYUP, code) for code in sorted(held)], 0)
    if take_core:
        for count in range(50):
            events = [key(pygame.KEYDOWN, pygame.K_e)] if count == 0 else []
            flow.frame(events, 34)
            observation = flow.session.simulation.observe(flow.level.operative_id)
            if observation.phase == MissionPhase.LOCKDOWN:
                break
        assert observation.phase == MissionPhase.LOCKDOWN
        flow.frame([key(pygame.KEYUP, pygame.K_e)], 0)


def test_keyboard_scene_pause_retry_and_full_win() -> None:
    flow = start()
    assert flow.session is not None
    flow.frame([key(pygame.KEYDOWN, pygame.K_ESCAPE)], 34)
    paused_tick = flow.session.simulation.tick
    flow.frame([], 5_000)
    assert flow.session.paused and flow.session.simulation.tick == paused_tick
    flow.frame([key(pygame.KEYDOWN, pygame.K_r)], 0)
    assert flow.scene == Scene.HEIST and flow.runs_started == 2
    assert flow.session.simulation.tick == 0
    drive(flow, UPPER, take_core=True)
    drive(flow, RETURN, expected_end=RunOutcome.WIN)
    assert flow.scene == Scene.RESULTS
    assert flow.session.mission_end is not None
    assert flow.session.mission_end.outcome == RunOutcome.WIN
    assert flow.outcomes["WIN"] == 1
    flow.frame([key(pygame.KEYDOWN, pygame.K_RETURN)], 0)
    assert flow.scene == Scene.TITLE


def test_real_scene_capture_reaches_result_and_retry() -> None:
    flow = start()
    drive(flow, [(12, 17), (16, 17), (16, 9)], expected_end=RunOutcome.CAPTURED)
    for _ in range(30):
        if flow.scene == Scene.RESULTS:
            break
        flow.frame([], 34)
    assert flow.scene == Scene.RESULTS and flow.session is not None
    assert flow.session.mission_end is not None
    assert flow.session.mission_end.capture_by == "guard-service"
    retry_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(700, 610))
    flow.frame([retry_click], 0)
    assert flow.scene == Scene.HEIST and flow.session.simulation.tick == 0


def test_mouse_menu_and_letterbox_coordinates() -> None:
    pygame.font.init()
    flow = GameFlow((1280, 720))
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(88, 784))
    mapped = _logical_events([click], (1280, 1440), (1280, 720))
    assert mapped[0].pos == (88, 424)
    flow.frame(mapped, 0)
    assert flow.scene == Scene.MODE
    flow.frame([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(70, 640))], 0)
    assert flow.scene == Scene.HEIST


def test_art_and_gait_follow_committed_movement_without_changing_simulation() -> None:
    flow = start()
    assert flow.session is not None
    art = flow.session.art
    assert art.operative[0].get_size() == (52, 66)
    assert pygame.image.tobytes(art.operative[0], "RGBA") != pygame.image.tobytes(
        art.operative[3], "RGBA"
    )
    first_tick = flow.session.simulation.tick
    flow.frame([key(pygame.KEYDOWN, pygame.K_d), key(pygame.KEYDOWN, pygame.K_LSHIFT)], 34)
    assert flow.session.simulation.tick == first_tick + 1
    assert flow.session.actor_motion[flow.level.operative_id].sprinting
    tick_after_move = flow.session.simulation.tick
    canvas = pygame.Surface((1280, 720))
    flow.draw(canvas)
    assert flow.session.simulation.tick == tick_after_move


def test_default_live_guard_allows_actual_lower_route_core_and_extraction() -> None:
    flow = start(security_enabled=True)
    assert flow.session is not None
    first = flow.session.simulation.presentation_snapshot()
    assert first.guards and first.guards[0].actor_id == "guard-service"
    route = [(12, 17), (23, 17), (23, 27), (43, 27), (43, 23), (58, 23), (58, 18)]
    back = [(58, 23), (43, 23), (43, 27), (23, 27), (23, 17), (12, 17), (2, 17)]
    drive(flow, route, take_core=True)
    guard = flow.session.simulation.presentation_snapshot().guards[0]
    # Actual pursuit has finite memory; it does not track the hidden carrier forever.
    assert guard.last_seen_tick == -1
    drive(flow, back, expected_end=RunOutcome.WIN)
    assert flow.session.mission_end is not None
    assert flow.session.mission_end.outcome == RunOutcome.WIN
