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
from echo_heist.ai.companion.utility import emergency
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
