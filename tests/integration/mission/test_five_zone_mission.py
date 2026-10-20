"""Khalid's real Simulation on the packaged five-zone map: wins, capture, no fake exit."""

from collections import Counter

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.results import MissionEnd, RunOutcome
from echo_heist.core.contracts.world import tile_center
from echo_heist.core.simulation.engine import Simulation
from echo_heist.infrastructure.resources import resource_bytes
from echo_heist.level.io import load_tiled_map
from echo_heist.level.model import LevelData

ARRIVE = 4_000
type Step = tuple[int, int] | str
UPPER: list[Step] = [(12, 17), (23, 17), (23, 8), (43, 8), (43, 12), (58, 12), (58, 16), "HOLD"]
UPPER_BACK: list[Step] = [(58, 12), (43, 12), (43, 8), (23, 8), (23, 17), (12, 17), (2, 17)]
LOWER: list[Step] = [(12, 17), (23, 17), (23, 27), (43, 27), (43, 23), (58, 23), (58, 18), "HOLD"]
LOWER_BACK: list[Step] = [(58, 23), (43, 23), (43, 27), (23, 27), (23, 17), (12, 17), (2, 17)]
CROSS: list[Step] = [(12, 17), (23, 17), (23, 8), (36, 8), (36, 24), (43, 24), (43, 23)]


@pytest.fixture(scope="module")
def level() -> LevelData:
    return load_tiled_map(resource_bytes("data/maps/vault-five-zone.json"))


def drive(
    level: LevelData, rules: GameRules, steps: list[Step], limit: int = 3_000
) -> tuple[MissionEnd | None, Counter[str], str]:
    simulation = Simulation(
        level.static_map, level.spawns(), rules=rules, mission=level.mission(), seed=1042
    )
    pending, counts = list(steps), Counter[str]()
    while simulation.tick < limit:
        observation = simulation.observe(level.operative_id)
        position = observation.own_status.position
        assert position is not None
        if pending and pending[0] == "HOLD" and observation.phase.value == "LOCKDOWN":
            pending.pop(0)
            continue
        if pending and pending[0] == "HOLD":
            action = Action(
                level.operative_id, ActionKind.INTERACT, observation.tick, target_id=level.core_id
            )
        elif pending and isinstance(pending[0], tuple):
            target = tile_center(pending[0])
            dx, dy = target[0] - position[0], target[1] - position[1]
            if abs(dx) < ARRIVE and abs(dy) < ARRIVE:
                pending.pop(0)
                continue
            direction = ((dx > ARRIVE) - (dx < -ARRIVE), (dy > ARRIVE) - (dy < -ARRIVE))
            action = Action(
                level.operative_id, ActionKind.MOVE, observation.tick, direction, sprint=True
            )
        else:
            action = Action(level.operative_id, ActionKind.WAIT, observation.tick)
        result = simulation.step((action,))
        counts.update(event.kind.value for event in result.events)
        if result.mission_end is not None:
            return result.mission_end, counts, simulation.fingerprint()
    return None, counts, simulation.fingerprint()


@pytest.mark.parametrize(
    "route",
    [UPPER + UPPER_BACK, LOWER + LOWER_BACK, [*CROSS, (58, 23), (58, 18), "HOLD", *UPPER_BACK]],
    ids=["upper-branch", "lower-branch", "cross-link"],
)
def test_human_takes_core_once_and_extracts_at_original_exit(
    level: LevelData, rules: GameRules, route: list[Step]
) -> None:
    end, counts, _ = drive(level, rules, route)
    assert end is not None and end.outcome == RunOutcome.WIN
    assert counts["CORE_TAKEN"] == counts["LOCKDOWN_STARTED"] == counts["MISSION_ENDED"] == 1
    assert counts["ACTION_REJECTED"] == 0


def test_stationary_guard_post_captures_on_contact(level: LevelData, rules: GameRules) -> None:
    end, counts, _ = drive(level, rules, [(12, 17), (16, 17), (16, 9)], limit=600)
    assert end is not None and end.outcome == RunOutcome.CAPTURED
    assert end.capture_by == "guard-service"
    assert counts["CAPTURE_STARTED"] == counts["CAPTURE_COMPLETED"] == 1


def test_exit_without_core_never_wins(level: LevelData, rules: GameRules) -> None:
    end, counts, _ = drive(level, rules, [(12, 17), (2, 17)], limit=300)
    assert end is None and counts["MISSION_ENDED"] == 0


def test_same_seed_retry_reproduces_the_same_run(level: LevelData, rules: GameRules) -> None:
    first = drive(level, rules, UPPER + UPPER_BACK)
    assert first == drive(level, rules, UPPER + UPPER_BACK)
