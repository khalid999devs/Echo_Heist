import pygame
import pytest

from echo_heist.core.contracts.actions import ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.results import MissionSpec
from echo_heist.core.contracts.world import ActorSpawn, MapObject, StaticMap
from echo_heist.core.simulation.engine import Simulation
from echo_heist.ui.input.human import HumanInput, KeyBindings, UiCommand
from echo_heist.ui.presenters.objective import build_objective_view


def press(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def test_input_batches_one_action_per_tick_and_filters_repeat(rules: GameRules) -> None:
    sim = Simulation(StaticMap("input", 8, 8), (ActorSpawn("operative", (3, 3)),), rules=rules)
    adapter = HumanInput("operative")
    adapter.feed([press(pygame.K_w), press(pygame.K_d), press(pygame.K_LSHIFT)])
    action = adapter.action_for(sim.observe("operative"))
    assert action.kind == ActionKind.MOVE and action.direction == (1, -1) and action.sprint
    sim.step((action,))
    adapter.feed([press(pygame.K_q), press(pygame.K_q)])
    echo = adapter.action_for(sim.observe("operative"))
    assert echo.kind == ActionKind.ECHO and not echo.sprint and echo.direction == (0, 0)
    assert adapter.action_for(sim.observe("operative")) == echo
    sim.step((echo,))
    assert adapter.action_for(sim.observe("operative")).kind == ActionKind.MOVE


def test_focus_pause_and_remap_clear_held_actions(rules: GameRules) -> None:
    sim = Simulation(StaticMap("input", 8, 8), (ActorSpawn("operative", (3, 3)),), rules=rules)
    adapter = HumanInput("operative", KeyBindings(right=(pygame.K_l,)))
    adapter.feed([press(pygame.K_l), press(pygame.K_f)])
    assert adapter.feed([pygame.event.Event(pygame.WINDOWFOCUSLOST)]) == (UiCommand.FOCUS_LOST,)
    assert adapter.action_for(sim.observe("operative")).kind == ActionKind.WAIT
    assert adapter.feed([press(pygame.K_ESCAPE)]) == (UiCommand.PAUSE,)
    assert adapter.feed([press(pygame.K_TAB), press(pygame.K_F3)]) == (
        UiCommand.OBJECTIVE,
        UiCommand.LAB,
    )
    with pytest.raises(ValueError):
        KeyBindings(right=(pygame.K_w,))


def test_interaction_and_objective_follow_committed_own_values(rules: GameRules) -> None:
    world = StaticMap(
        "input",
        8,
        8,
        objects=(MapObject("core", "Core", (4, 3)), MapObject("exit", "Exit", (1, 3))),
    )
    sim = Simulation(
        world,
        (ActorSpawn("operative", (3, 3)),),
        rules=rules,
        mission=MissionSpec("operative", "core", "exit"),
    )
    adapter = HumanInput("operative")
    adapter.feed([press(pygame.K_e)])
    original = sim.observe("operative")
    view = build_objective_view(original, ticks_per_second=rules.simulation_hz)
    assert view.interaction == "Hold E - Recover core (0%)"
    for _ in range(rules.core_interaction_ticks):
        sim.step((adapter.action_for(sim.observe("operative")),))
    updated = build_objective_view(sim.observe("operative"), ticks_per_second=rules.simulation_hz)
    assert updated.objective == "Return to Entry extraction"
    assert updated.interaction == "" and "Core YES" in updated.inventory
    assert original.own_status.inventory.core_held is False
