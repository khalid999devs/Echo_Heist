"""Contract/scene regressions with explicitly scripted QA, never algorithm proof."""

import pygame
import pytest

from echo_heist.core.contracts.autonomy.model import ControlMode
from echo_heist.core.contracts.autonomy.policy import Risk
from echo_heist.infrastructure.resources import load_game_rules
from echo_heist.ui.render.autonomy.protocols import RESET_BUTTONS, RESET_MEMORY
from echo_heist.ui.render.layout.viewport import interface_origin
from echo_heist.ui.scenes.design.workshop import WORKSHOP_CONTROLS
from echo_heist.ui.scenes.flow import GameFlow, Scene, load_level
from echo_heist.ui.scenes.menus import CHAPTER_CARD, MODE_BUTTONS
from echo_heist.ui.scenes.navigation.controls import PAUSE_BUTTONS
from echo_heist.ui.scenes.settings import OPTION_RECTS
from tests.fixtures.autonomy.scripted import ACTOR_ID, ScriptedGateway


def key(code: int) -> list[pygame.event.Event]:
    return [pygame.event.Event(kind, key=code) for kind in (pygame.KEYDOWN, pygame.KEYUP)]


def click(flow: GameFlow, rect: pygame.Rect) -> None:
    x, y = interface_origin(flow.view_size)
    flow.frame(
        [
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, button=1, pos=(rect.centerx + x, rect.centery + y)
            )
        ],
        0,
    )


def prepared(
    *, connected: bool = True, size: tuple[int, int] = (1280, 720)
) -> tuple[GameFlow, ScriptedGateway]:
    pygame.font.init()
    level, rules = load_level(), load_game_rules()
    gateway = ScriptedGateway(level, rules)
    flow = GameFlow(size, level=level, rules=rules, autonomy_gateway=gateway if connected else None)
    click(flow, CHAPTER_CARD)
    click(flow, MODE_BUTTONS[1])
    assert flow.scene == Scene.WORKSHOP
    return flow, gateway


@pytest.mark.parametrize("size", [(1280, 720), (1280, 1440)])
def test_unavailable_companion_never_starts_a_human_fallback(size: tuple[int, int]) -> None:
    flow, _ = prepared(connected=False, size=size)
    click(flow, WORKSHOP_CONTROLS[8])
    flow.frame(key(pygame.K_RETURN), 1000)
    assert flow.scene == Scene.WORKSHOP and flow.session is None and flow.runs_started == 0
    assert not flow.last_deployment and flow.designs.notice


def test_spectator_input_and_read_only_decision_panels_follow_the_actual_robot() -> None:
    flow, gateway = prepared()
    click(flow, WORKSHOP_CONTROLS[8])
    assert flow.session and flow.session.observer_id == ACTOR_ID and flow.session.autonomous
    assert flow.session.control_mode == ControlMode.COMPANION
    before = flow.session.simulation.fingerprint()
    flow.frame([], 700)
    assert flow.session.simulation.fingerprint() == before  # Entrance hides no simulation.
    events = [
        pygame.event.Event(pygame.KEYDOWN, key=code)
        for code in (
            pygame.K_a,
            pygame.K_q,
            pygame.K_f,
            pygame.K_SPACE,
            pygame.K_c,
            pygame.K_LSHIFT,
        )
    ]
    flow.frame(events, 34)
    run = gateway.runs[-1]
    assert run.supplied == [] and run.tick == 1
    assert run.observe(ACTOR_ID).own_status.tile == flow.level.spawn_tile
    assert flow.session.actor_motion[ACTOR_ID].moving
    flow.frame(key(pygame.K_ESCAPE), 0)
    fingerprint = run.fingerprint()
    calls = run.telemetry_calls
    for index in range(3):
        flow.session.autonomy_tab = index
        flow.draw(pygame.Surface(flow.view_size))
    flow.frame([], 5000)
    assert run.fingerprint() == fingerprint and run.telemetry_calls == calls

    # The paused map must use the robot's real ID rather than the old Human ID.
    click(flow, PAUSE_BUTTONS[0])
    flow.frame(key(pygame.K_TAB), 0)
    assert flow.session.summary
    before = run.fingerprint()
    flow.draw(pygame.Surface(flow.view_size))
    flow.frame([], 3000)
    assert run.fingerprint() == before


def test_pause_map_settings_and_review_retry_preserve_the_original_policy() -> None:
    flow, gateway = prepared(size=(1280, 1440))
    click(flow, WORKSHOP_CONTROLS[0])
    click(flow, WORKSHOP_CONTROLS[8])
    assert flow.session
    flow.frame(key(pygame.K_ESCAPE), 0)
    original = gateway.requests[-1]
    assert original.policy.risk == Risk.CAUTIOUS
    fingerprint = flow.session.simulation.fingerprint()
    click(flow, PAUSE_BUTTONS[2])
    flow.frame([], 5000)
    click(flow, OPTION_RECTS[4])
    assert flow.scene == Scene.HEIST and flow.session.paused
    assert flow.session.simulation.fingerprint() == fingerprint
    flow.frame(key(pygame.K_r), 0)
    assert flow.scene == Scene.WORKSHOP and len(gateway.requests) == 1
    click(flow, WORKSHOP_CONTROLS[8])
    assert len(gateway.requests) == 2 and gateway.requests[-1] == original
    assert flow.session.simulation.tick == 0


def test_protocol_reset_requires_confirmation_and_uses_actual_backend_results() -> None:
    flow, gateway = prepared()
    original = gateway.state
    click(flow, RESET_MEMORY)
    assert flow.designs.reset_confirmation
    click(flow, RESET_BUTTONS[1])
    assert gateway.reset_calls == 0 and gateway.state == original
    gateway.fail_reset = True
    click(flow, RESET_MEMORY)
    click(flow, RESET_BUTTONS[0])
    assert gateway.reset_calls == 1 and gateway.state == original
    assert flow.deployment.protocol_state == original and flow.designs.reset_confirmation
    gateway.fail_reset = False
    click(flow, RESET_BUTTONS[0])
    assert gateway.reset_calls == 2 and flow.deployment.protocol_state == gateway.state
    assert gateway.state.active is None and not flow.designs.reset_confirmation


@pytest.mark.parametrize("failure", ["fail_deploy", "wrong_mode"])
def test_failed_or_mismatched_runtime_does_not_create_an_attempt(failure: str) -> None:
    flow, gateway = prepared()
    setattr(gateway, failure, True)
    click(flow, WORKSHOP_CONTROLS[8])
    assert flow.scene == Scene.WORKSHOP and flow.runs_started == 0 and flow.session is None
    assert flow.designs.notice
