"""P05-SR1 edge cases: tool/capture ordering and reach, identical for both controllers."""

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.environment.model import EnvironmentSpec, PropSpec
from echo_heist.core.contracts.environment.presentation import PropKind
from echo_heist.core.contracts.events import EventKind, GameEvent
from echo_heist.core.contracts.security.model import GuardPatrol, SecuritySpec
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, StaticMap, Tile
from echo_heist.core.simulation.engine import Simulation
from echo_heist.infrastructure.resources import load_sensor_rules

INTRUDERS = [ActorKind.OPERATIVE, ActorKind.COMPANION]


def watched(rules: GameRules, kind: ActorKind, player: Tile = (4, 3)) -> Simulation:
    border = frozenset((x, y) for x in range(12) for y in range(10) if x in (0, 11) or y in (0, 9))
    world = StaticMap("sentinel-fixture", 12, 10, border, border)
    patrol = GuardPatrol("sentinel", ((3, 3), (6, 3), (6, 6), (3, 6)))
    return Simulation(
        world,
        (ActorSpawn("intruder", player, kind), ActorSpawn("sentinel", (3, 3), ActorKind.SENTINEL)),
        rules=rules,
        security=SecuritySpec((patrol,), load_sensor_rules(), border),
    )


def act(sim: Simulation, kind: ActionKind, **fields: object) -> tuple[GameEvent, ...]:
    return sim.step((Action("intruder", kind, sim.tick, **fields),)).events  # type: ignore[arg-type]


def reasons(events: tuple[GameEvent, ...]) -> list[object]:
    return [dict(e.details)["reason"] for e in events if e.kind == EventKind.ACTION_REJECTED]


@pytest.mark.parametrize("kind", INTRUDERS)
def test_t05_emp_on_the_completion_tick_cancels_and_echo_never_erases_reports(
    rules: GameRules, kind: ActorKind
) -> None:
    sim = watched(rules, kind)
    while not sim.presentation_snapshot().captures:
        sim.step()
    report = sim.observe("sentinel").shared_reports[0]
    echo = act(sim, ActionKind.ECHO)
    assert any(e.kind == EventKind.TOOL_USED for e in echo)
    # A decoy is not a body and not a radio eraser: the grab and report continue.
    assert sim.presentation_snapshot().captures and report in sim.observe("sentinel").shared_reports
    while sim.presentation_snapshot().captures[0].remaining_ticks > 1:
        sim.step()
    result = sim.step((Action("intruder", ActionKind.EMP, sim.tick),))
    kinds = [e.kind for e in result.events]
    assert result.mission_end is None and EventKind.CAPTURE_COMPLETED not in kinds
    assert EventKind.CAPTURE_CANCELED in kinds and EventKind.GUARD_DISABLED in kinds
    assert [
        dict(e.details)["kind"] for e in result.events if e.kind == EventKind.NOISE_CREATED
    ] == ["EMP"]
    assert sim.observe("intruder").own_status.inventory.emp_charges == 0
    # Disabled for the whole window: no new grab can start or finish meanwhile.
    for _ in range(rules.emp_disable_ticks - 1):
        assert not any(e.kind == EventKind.CAPTURE_STARTED for e in sim.step().events)
    assert reasons(act(sim, ActionKind.EMP)) == ["emp_empty"]


@pytest.mark.parametrize("kind", INTRUDERS)
def test_melee_reach_is_symmetric_with_capture_from_desk_clearance(
    rules: GameRules, kind: ActorKind
) -> None:
    desk = frozenset({(3, 3), (4, 3), (5, 3)})
    world = StaticMap("under-desk", 12, 12, desk, desk, crouch_tiles=frozenset({(4, 3)}))
    sim = Simulation(
        world,
        (ActorSpawn("intruder", (4, 5), kind), ActorSpawn("guard", (6, 6), ActorKind.TRACKER)),
        rules=rules,
    )
    for _ in range(35):
        act(sim, ActionKind.MOVE, direction=(0, -1))
    act(sim, ActionKind.CROUCH)
    while not sim.observe("intruder").own_status.concealed:
        act(sim, ActionKind.MOVE, direction=(0, -1))  # just inside the desk opening
    # The guard walks to the desk's open front, adjacent to the hider.
    for _ in range(90):
        sim.step((Action("guard", ActionKind.MOVE, sim.tick, (-1, 0)),))
        position = sim.observe("guard").own_status.position
        if position is not None and position[0] <= 136_000:
            break
    for _ in range(40):
        sim.step((Action("guard", ActionKind.MOVE, sim.tick, (0, -1)),))
    assert sim.observe("guard").own_status.tile == (4, 4)
    strike = act(sim, ActionKind.MELEE, target_id="guard")
    assert any(e.kind == EventKind.GUARD_STUNNED for e in strike)


@pytest.mark.parametrize("kind", INTRUDERS)
def test_tools_from_a_locker_and_no_strike_through_a_closed_door(
    rules: GameRules, kind: ActorKind
) -> None:
    wall = frozenset((6, y) for y in range(8) if y != 3)
    spec = EnvironmentSpec(
        (
            PropSpec("door-a", PropKind.DOOR, ((6, 3),), horizontal=False),
            PropSpec("locker-a", PropKind.LOCKER, ((5, 1),)),
        )
    )
    sim = Simulation(
        StaticMap("props", 12, 8, wall, wall),
        (ActorSpawn("intruder", (5, 3), kind), ActorSpawn("guard", (7, 3), ActorKind.SENTINEL)),
        rules=rules,
        environment=spec,
    )
    act(sim, ActionKind.INTERACT, target_id="door-a")
    for _ in range(rules.simulation_hz):
        sim.step()
    blocked = act(sim, ActionKind.MELEE, target_id="guard")
    assert reasons(blocked) == ["no_reachable_guard"]
    assert sim.observe("intruder").own_status.inventory.melee_charges == 2
    assert not any(e.kind == EventKind.NOISE_CREATED for e in blocked)
    # A stale tool request is refused and spends nothing for either controller.
    stale = sim.step((Action("intruder", ActionKind.EMP, sim.tick - 1),)).events
    assert reasons(stale) == ["stale_or_future_tick"]
    for _ in range(20):
        act(sim, ActionKind.MOVE, direction=(0, -1))
    act(sim, ActionKind.HIDE, target_id="locker-a")
    assert sim.observe("intruder").own_status.hidden_in == "locker-a"
    emp = act(sim, ActionKind.EMP)
    assert any(e.kind == EventKind.TOOL_USED for e in emp)
    own = sim.observe("intruder").own_status
    assert own.hidden_in == "locker-a" and own.inventory.emp_charges == 0
    assert reasons(act(sim, ActionKind.HIDE)) == ["already_hidden"]
