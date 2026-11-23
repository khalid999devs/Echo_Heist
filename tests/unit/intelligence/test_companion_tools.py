"""Companion tool use under the approved two-charge, four-second melee rule.

Utility overrides and the MCTS model both read the Companion's own observed
stock and recovery; neither may plan a strike Simulation would reject.
"""

from dataclasses import replace
from random import Random

import pytest

from echo_heist.ai.companion import tactics
from echo_heist.ai.companion.belief import Sighting
from echo_heist.ai.companion.briefing import policy_weights
from echo_heist.ai.companion.stealth import lanes
from echo_heist.ai.companion.utility import emergency
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.autonomy.policy import Emergency, PolicySelection
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.observations import EntityView, Observation, OwnStatus
from echo_heist.core.contracts.world import (
    ActorKind,
    Inventory,
    MissionPhase,
    StaticMap,
    tile_center,
)

ROOM = StaticMap("melee-gate", 12, 8)


def grabbed(charges: int, recovery: int) -> Observation:
    """Grabbed by an adjacent, visible Sentinel with no EMP left."""
    own = OwnStatus(
        (4, 4),
        Inventory(echo_charges=0, emp_charges=0, melee_charges=charges),
        position=tile_center((4, 4)),
        capture_ticks_remaining=12,
        melee_cooldown_remaining=recovery,
    )
    guard = EntityView("guard-a", ActorKind.SENTINEL, (5, 4), tile_center((5, 4)))
    return Observation("echo-companion", 300, ROOM, MissionPhase.INFILTRATE, own, (guard,))


@pytest.mark.parametrize(
    ("charges", "recovery", "expected"),
    [(2, 0, "MELEE"), (1, 1, "MELEE"), (1, 2, "ESCAPE"), (0, 0, "ESCAPE")],
)
def test_grab_breaking_strike_needs_own_charge_and_finished_recovery(
    rules: GameRules, charges: int, recovery: int, expected: str
) -> None:
    """A request commits next tick, so one remaining recovery tick is already legal."""
    override = emergency(grabbed(charges, recovery), rules, Emergency.MELEE_IF_ADJACENT, {}, None)
    assert override is not None and override.kind == expected
    if expected == "MELEE":
        assert override.target_id == "guard-a"


def test_companion_saves_emp_when_a_close_guard_leaves_an_escape(rules: GameRules) -> None:
    observation = grabbed(0, 0)
    own = replace(
        observation.own_status,
        inventory=Inventory(echo_charges=0, emp_charges=1, melee_charges=0),
        capture_ticks_remaining=None,
    )
    watcher = Sighting("guard-a", ActorKind.SENTINEL, (5, 4), (-1, 0), 300, False)
    watched = replace(observation, own_status=own)
    escape = emergency(watched, rules, Emergency.EMP_IF_TRAPPED, {}, watcher)
    assert escape is not None and escape.kind == "ESCAPE"

    walls = frozenset({(3, 4), (4, 3), (4, 5)})
    trapped = replace(watched, map_static=replace(ROOM, blocked_tiles=walls))
    response = emergency(trapped, rules, Emergency.EMP_IF_TRAPPED, {}, watcher)
    assert response is not None and response.kind == "EMP"


def model(rules: GameRules, root: tactics.TacticalState) -> tactics.CompanionModel:
    return tactics.CompanionModel(
        None,  # type: ignore[arg-type]  # tool transitions never consult the briefing
        policy_weights(PolicySelection()),
        root,
        (),
        (),
        {},
        {},
        frozenset(),
        False,
        True,  # an observed guard is inside melee reach at the root
        False,
        False,
        True,
        {},
        False,
        melee_recovery=rules.melee_cooldown_ticks / rules.simulation_hz,
    )


def test_rollouts_spend_charges_and_recover_on_elapsed_simulation_time(rules: GameRules) -> None:
    guard = (("guard-a", "lab", True),)
    root = tactics.TacticalState(
        0, 0, False, 0, 0, 0.0, 0.0, 0, False, False, guard, 0, False, "lab", melee=1
    )
    tactical = model(rules, root)
    assert tactics.MELEE in tactical.actions(root)
    struck = tactical.step(root, tactics.MELEE, Random(3))
    assert struck.melee == 0 and struck.melee_wait == pytest.approx(4.0)
    assert tactics.MELEE not in tactical.actions(replace(struck, guards=guard))

    cooling = replace(struck, melee=1, guards=guard)
    assert tactics.MELEE not in tactical.actions(cooling)  # still recovering
    later = tactical.step(cooling, tactics.ALTERNATE, Random(3))  # four abstract seconds
    assert later.melee_wait == 0.0 and tactics.MELEE in tactical.actions(later)
    exhausted = replace(root, melee=0)
    assert tactics.MELEE not in tactical.actions(exhausted)


def test_flip_flopping_moves_hold_the_heading_but_a_sustained_turn_wins() -> None:
    east = Action("echo-companion", ActionKind.MOVE, 0, (1, 0))
    west = Action("echo-companion", ActionKind.MOVE, 1, (-1, 0))
    # Alternating requests (flee vs. step away) keep the current heading: no wiggle.
    kept, votes = lanes.damp_reversal(west, east, 0, exempt=False)
    assert kept.direction == (1, 0) and votes == 1
    again, votes = lanes.damp_reversal(east, kept, votes, exempt=False)
    assert again.direction == (1, 0) and votes == 0
    # Asking to turn around several ticks running is honoured; a grab or blocked
    # step may turn back at once.
    action, votes = west, 0
    for _ in range(lanes.REVERSAL_TICKS):
        result, votes = lanes.damp_reversal(action, east, votes, exempt=False)
    assert result.direction == (-1, 0) and votes == 0
    assert lanes.damp_reversal(west, east, 0, exempt=True)[0].direction == (-1, 0)


def test_fleeing_never_steps_toward_a_close_guard_and_a_cornered_robot_stands() -> None:
    own = OwnStatus((4, 4), Inventory(), position=tile_center((4, 4)))
    guard = EntityView("guard-a", ActorKind.SENTINEL, (6, 4), tile_center((6, 4)))
    open_room = Observation("echo-companion", 9, ROOM, MissionPhase.LOCKDOWN, own, (guard,))
    assert lanes.closing_threat(open_room, (1, 0)) == tile_center((6, 4))
    assert lanes.closing_threat(open_room, (-1, 0)) is None
    assert lanes.escape_steps(open_room, "echo-companion", tile_center((6, 4)))[0] == (-1, 0)
    # A dead end with the guard at the mouth: no step gains distance, so it holds.
    walls = frozenset((x, y) for x in range(12) for y in range(8) if not (y == 4 and 2 <= x <= 7))
    corridor = replace(ROOM, blocked_tiles=walls, opaque_tiles=walls)
    trapped = replace(
        open_room,
        map_static=corridor,
        own_status=replace(own, tile=(2, 4), position=tile_center((2, 4))),
        visible_entities=(replace(guard, tile=(4, 4), position=tile_center((4, 4))),),
    )
    assert lanes.escape_steps(trapped, "echo-companion", tile_center((4, 4))) == []


def test_a_diagonal_escape_keeps_its_heading_instead_of_flickering() -> None:
    own = OwnStatus((5, 5), Inventory(), position=tile_center((5, 5)))
    guard = EntityView("guard-a", ActorKind.SENTINEL, (3, 3), tile_center((3, 3)))
    room = Observation("echo-companion", 9, ROOM, MissionPhase.LOCKDOWN, own, (guard,))
    away = tile_center((3, 3))
    # Right and down gain the same distance; the step already being taken wins.
    for heading in ((1, 0), (0, 1)):
        last = Action("echo-companion", ActionKind.MOVE, 8, heading)
        assert lanes.escape_steps(room, "echo-companion", away, last)[0] == heading


def test_a_guard_standing_in_a_one_tile_corridor_makes_the_robot_back_off() -> None:
    walls = frozenset((x, y) for x in range(12) for y in range(8) if not (y == 4 and 1 <= x <= 10))
    corridor = replace(ROOM, blocked_tiles=walls, opaque_tiles=walls)
    own = OwnStatus((5, 4), Inventory(), position=tile_center((5, 4)))
    guard = EntityView("guard-a", ActorKind.SENTINEL, (6, 4), tile_center((6, 4)), facing=(0, -1))
    blocked = Observation("echo-companion", 9, corridor, MissionPhase.LOCKDOWN, own, (guard,))
    # Pushing on into the guard's back read as walking into a wall: step back two tiles.
    assert lanes.side_lane(blocked, "echo-companion", (1, 0), 2) is None
    assert lanes.backoff(blocked, "echo-companion", (1, 0)) == (3, 4)
    # A slumped guard is stepped past, so there is nothing to back away from.
    slumped = replace(blocked, visible_entities=(replace(guard, stunned=True),))
    assert lanes.backoff(slumped, "echo-companion", (1, 0)) is None


def test_a_flee_goal_past_the_close_guard_is_swapped_for_one_behind_the_robot() -> None:
    guard = tile_center((6, 3))
    trail = [(1, 4), (2, 4), (3, 4), (4, 4)]
    # Heading back past the guard paced the robot in front of it.
    assert lanes.away_goal((7, 2), trail, (5, 4), guard) == (4, 4)
    assert lanes.away_goal((2, 4), trail, (5, 4), guard) == (2, 4)
    assert lanes.away_goal((7, 2), [(6, 4), (7, 4)], (5, 4), guard) is None
