"""Real menu/input/scene composition against the packaged five-zone mission."""

import pygame

from echo_heist.core.contracts.results import RunOutcome
from echo_heist.core.contracts.world import MissionPhase
from echo_heist.diagnostics.facility_routes import mission_path, walk_path
from echo_heist.diagnostics.human_driver import HumanDriver
from echo_heist.ui.bootstrap import _logical_events
from echo_heist.ui.scenes.flow import GameFlow, Scene
from echo_heist.ui.scenes.menus import LAUNCH_BUTTON, MODE_BUTTONS, TITLE_BUTTONS


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
    use_tools: bool = False,
) -> None:
    assert flow.session is not None
    driver = HumanDriver(flow.rules, use_tools=use_tools)
    pending = list(route)
    until = flow.session.steps + 4_000
    while pending and flow.session.steps < until:
        observation = flow.session.simulation.observe(flow.level.operative_id)
        if driver.arrived(observation, pending[0]):
            pending.pop(0)
            continue
        flow.frame(driver.events(observation, pending[0]), 34)
        if flow.scene == Scene.RESULTS:
            assert expected_end is not None
            assert flow.session.mission_end is not None
            assert flow.session.mission_end.outcome == expected_end
            return
        assert flow.scene == Scene.HEIST, "Unexpected mission end before reaching waypoint"
    assert not pending, "The real input adapter did not reach the route"
    flow.frame(driver.release(), 0)
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
    drive(flow, list(mission_path(flow.level, "upper")), take_core=True)
    drive(
        flow, list(mission_path(flow.level, "upper", returning=True)), expected_end=RunOutcome.WIN
    )
    assert flow.scene == Scene.RESULTS
    assert flow.session.mission_end is not None
    assert flow.session.mission_end.outcome == RunOutcome.WIN
    assert flow.outcomes["WIN"] == 1
    flow.frame([key(pygame.KEYDOWN, pygame.K_RETURN)], 0)
    assert flow.scene == Scene.TITLE


def test_real_scene_capture_reaches_result_and_retry() -> None:
    flow = start()
    post = next(post for post in flow.level.guards if post.guard_id == "guard-service")
    drive(
        flow,
        list(walk_path(flow.level, flow.level.spawn_tile, post.tile)),
        expected_end=RunOutcome.CAPTURED,
    )
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
    target = TITLE_BUTTONS[0].center
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(target[0], target[1] + 360))
    mapped = _logical_events([click], (1280, 1440), (1280, 720))
    assert mapped[0].pos == target
    flow.frame(mapped, 0)
    assert flow.scene == Scene.MODE
    flow.frame([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=LAUNCH_BUTTON.center)], 0)
    assert flow.scene == Scene.HEIST


def test_art_and_gait_follow_committed_movement_without_changing_simulation() -> None:
    flow = start()
    assert flow.session is not None
    art = flow.session.art
    assert art.operative[0].get_width() <= flow.level.static_map.tile_size_px + 4
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
    route = list(mission_path(flow.level, "lower"))
    back = list(mission_path(flow.level, "lower", returning=True))
    drive(flow, route, take_core=True, use_tools=True)
    guard = flow.session.simulation.presentation_snapshot().guards[0]
    # Actual pursuit has finite memory; it does not track the hidden carrier forever.
    assert guard.last_seen_tick == -1
    drive(flow, back, expected_end=RunOutcome.WIN, use_tools=True)
    assert flow.session.mission_end is not None
    assert flow.session.mission_end.outcome == RunOutcome.WIN


def test_facility_map_freezes_time_and_clears_held_movement() -> None:
    flow = start(security_enabled=True)
    assert flow.session is not None
    flow.frame([key(pygame.KEYDOWN, pygame.K_d), key(pygame.KEYDOWN, pygame.K_LSHIFT)], 34)
    flow.frame([key(pygame.KEYDOWN, pygame.K_TAB)], 34)
    before = flow.session.simulation.presentation_snapshot()
    clock = flow.session.clock_ms
    sprint_before = flow.session.simulation.observe(flow.level.operative_id).own_status
    flow.frame([key(pygame.KEYDOWN, pygame.K_w)], 5_000)
    assert flow.session.summary and not flow.session.paused
    assert flow.session.simulation.presentation_snapshot() == before
    assert flow.session.clock_ms == clock
    assert flow.session.simulation.observe(flow.level.operative_id).own_status == sprint_before
    flow.frame([key(pygame.KEYDOWN, pygame.K_ESCAPE)], 0)
    assert not flow.session.summary and not flow.session.paused
    flow.frame([], 34)
    after = flow.session.simulation.presentation_snapshot()
    assert after.tick > before.tick
    old_player = next(actor for actor in before.actors if actor.actor_id == flow.level.operative_id)
    new_player = next(actor for actor in after.actors if actor.actor_id == flow.level.operative_id)
    assert new_player.position == old_player.position


def test_mode_selection_does_not_launch_and_back_does_not_start_a_run() -> None:
    pygame.font.init()
    flow = GameFlow((1280, 720))

    def click(rect: pygame.Rect) -> None:
        flow.frame([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)], 0)

    click(TITLE_BUTTONS[0])
    assert flow.scene == Scene.MODE and flow.selected == 2
    click(MODE_BUTTONS[1])
    assert flow.notice and flow.scene == Scene.MODE
    assert flow.mode_choice == 0 and flow.runs_started == 0
    click(MODE_BUTTONS[0])
    assert flow.mode_choice == 0 and flow.selected == 2
    assert flow.scene == Scene.MODE and flow.session is None
    click(MODE_BUTTONS[3])
    assert flow.scene == Scene.TITLE and flow.runs_started == 0
    click(TITLE_BUTTONS[0])
    click(LAUNCH_BUTTON)
    assert flow.scene == Scene.HEIST and flow.runs_started == 1


def test_layered_actor_alpha_keeps_background_and_opaque_destination() -> None:
    from echo_heist.core.contracts.world import ActorKind
    from echo_heist.ui.render import motifs
    from echo_heist.ui.render.surfaces.formats import opaque_surface
    from echo_heist.ui.render.world import WorldArt

    pygame.font.init()
    canvas = opaque_surface((100, 100))
    background = (100, 140, 155)
    canvas.fill(background)
    motifs.light_pool(canvas, (50, 50), (130, 170, 190), 40)
    before = canvas.copy()
    motifs.actor(
        canvas,
        (50, 50),
        ActorKind.OPERATIVE,
        disabled=False,
        stunned=False,
        carries_core=False,
        pulse=0.5,
        motion=motifs.ActorMotion(),
        clock_ms=0,
        sprites=WorldArt.load().operative,
    )
    # Transparent sprite corners must preserve prior light/floor layers, even
    # when the native display offers alpha masks on otherwise opaque surfaces.
    assert canvas.get_masks()[3] == 0
    assert canvas.get_at((32, 27)) == before.get_at((32, 27))
    assert canvas.get_at((35, 35)) == before.get_at((35, 35))
    assert canvas.get_at((50, 50)) != before.get_at((50, 50))
    assert all(canvas.get_at((x, y)).a == 255 for x in range(100) for y in range(100))
