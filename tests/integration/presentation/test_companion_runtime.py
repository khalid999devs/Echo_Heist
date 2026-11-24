"""The real NEXUS gateway behind Khalid's Workshop: a first-launch Companion deploys,
moves under its own controller and publishes actual search telemetry."""

from pathlib import Path

import pygame

from echo_heist.autonomy.gateway import connect_gateway
from echo_heist.autonomy.mission import COMPANION_ID
from echo_heist.core.contracts.autonomy.model import ControlMode
from echo_heist.core.contracts.results import StairView
from echo_heist.infrastructure.persistence.protocols import FILE_NAME
from echo_heist.infrastructure.resources import load_game_rules, load_sensor_rules
from echo_heist.ui.render.layout.viewport import interface_origin
from echo_heist.ui.scenes.design.workshop import WORKSHOP_CONTROLS
from echo_heist.ui.scenes.flow import GameFlow, Scene, load_level
from echo_heist.ui.scenes.menus import CHAPTER_CARD, MODE_BUTTONS


def click(flow: GameFlow, rect: pygame.Rect) -> None:
    x, y = interface_origin(flow.view_size)
    position = (rect.centerx + x, rect.centery + y)
    flow.frame([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position)], 0)


def test_first_launch_deploys_the_real_companion_through_the_workshop(tmp_path: Path) -> None:
    pygame.font.init()
    level, rules = load_level(), load_game_rules()
    gateway = connect_gateway(level, rules, load_sensor_rules(), tmp_path)
    availability = gateway.availability()
    assert ControlMode.COMPANION in availability.modes and availability.protocols
    assert gateway.protocols().active is None  # a fresh profile starts at baseline
    flow = GameFlow((1280, 720), level=level, rules=rules, autonomy_gateway=gateway)
    click(flow, CHAPTER_CARD)
    click(flow, MODE_BUTTONS[1])
    assert flow.scene == Scene.WORKSHOP
    click(flow, WORKSHOP_CONTROLS[8])  # Deploy with the default (Balanced) policy

    session = flow.session
    assert session is not None and session.autonomous and session.observer_id == COMPANION_ID
    assert session.control_mode == ControlMode.COMPANION
    start = session.simulation.observe(COMPANION_ID).own_status.tile
    flow.frame([], 700)  # pressure-door entrance
    for _ in range(120):
        flow.frame([], 100)
    run = session.simulation
    assert run.presentation_snapshot().tick >= 300
    own = run.observe(COMPANION_ID).own_status
    assert own.tile != start  # moved by its own controller, not by input
    trace = run.telemetry().companion
    assert trace is not None and trace.actor_id == COMPANION_ID and trace.simulations == 64
    assert sum(item.visits for item in trace.alternatives) == 64
    # Moving, it shows its planned tiles; holding still, it says why.
    assert trace.path or trace.utility_action in ("WAIT", "HOLD", "HIDE", "COVER")
    assert not (tmp_path / FILE_NAME).exists()  # evidence is written once, at attempt end


def test_stair_overlay_clears_if_travel_ends_without_arrival() -> None:
    pygame.font.init()
    flow = GameFlow((1280, 720))
    flow._start_run()
    assert flow.session is not None
    session = flow.session
    overlay = session.stairwell
    canvas = pygame.Surface(flow.view_size)
    travel = StairView(COMPANION_ID, (28, 11), (32, 11), 3, 24)
    overlay.draw(
        canvas,
        travel,
        flow.art.companion,
        flow.fonts,
        10,
        observer_tile=travel.source,
        reduced_motion=False,
    )
    assert overlay.active == travel
    overlay.draw(
        canvas,
        None,
        flow.art.companion,
        flow.fonts,
        20,
        observer_tile=travel.source,
        reduced_motion=False,
    )
    assert overlay.active is None
