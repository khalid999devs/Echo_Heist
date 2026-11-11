"""The approved scoring specification, checked against its own examples and boundaries."""

import pytest

from echo_heist.core.contracts.config.scoring import ScoringRules
from echo_heist.core.contracts.experience.model import Achievement, RunReport
from echo_heist.core.contracts.results import RunOutcome
from echo_heist.core.scoring.score import achievements, grade, pace_points, score_run
from echo_heist.infrastructure.resources import load_scoring_rules

RULES = ScoringRules()
REF = RULES.pace_reference_ticks


def win(encounters: int, ticks: int, mode: str = "HUMAN") -> tuple[int, str]:
    result = score_run(
        mode=mode,
        seed=1,
        outcome=RunOutcome.WIN,
        elapsed_ticks=ticks,
        detection_encounters=encounters,
        rules=RULES,
    )
    return result.score, result.grade


@pytest.mark.parametrize(
    ("encounters", "at_reference", "at_twice"),
    [
        (0, (100, "S"), (95, "S")),
        (1, (88, "A"), (83, "A")),
        (2, (76, "A"), (71, "B")),
        (3, (64, "B"), (59, "C")),
        (4, (60, "B"), (55, "C")),
        (9, (60, "B"), (55, "C")),
    ],
)
def test_published_example_table(encounters, at_reference, at_twice) -> None:
    assert win(encounters, REF) == at_reference
    assert win(encounters, 2 * REF) == at_twice


def test_rank_boundaries_and_every_success_grade_reachable() -> None:
    for score, expected in ((59, "C"), (60, "B"), (74, "B"), (75, "A"), (89, "A"), (90, "S")):
        assert grade(RunOutcome.WIN, score) == expected
    reached = {win(e, t)[1] for e in range(6) for t in (REF, 2 * REF, 10 * REF, 10**6)}
    assert reached == {"S", "A", "B", "C"}
    # Scores stay within 50-100 for any valid metrics.
    for e in range(8):
        for t in (0, 1, REF - 1, REF, REF + 1, 3 * REF, 10**7):
            score, _ = win(e, t)
            assert 50 <= score <= 100


def test_pace_bounds_zero_duration_and_monotonic() -> None:
    assert pace_points(0, RULES) == 10 and pace_points(REF, RULES) == 10
    assert pace_points(2 * REF, RULES) == 5 and pace_points(10**9, RULES) == 0
    values = [pace_points(t, RULES) for t in range(0, 5 * REF, REF // 7)]
    assert values == sorted(values, reverse=True)
    # More time or more encounters never raise the score; a clean win is >= 90.
    assert win(0, 10**9)[0] >= 90 and win(1, 1)[0] == 88


@pytest.mark.parametrize("outcome", [RunOutcome.CAPTURED, RunOutcome.ABORTED])
def test_failures_are_zero_f_with_no_subtotals(outcome: RunOutcome) -> None:
    result = score_run(
        mode="COMPANION",
        seed=3,
        outcome=outcome,
        elapsed_ticks=100,
        detection_encounters=0,
        rules=RULES,
    )
    assert (result.score, result.grade) == (0, "F")
    assert result.completion_points == result.stealth_points == result.pace_points == 0
    assert achievements(result, RULES) == ()


def test_modes_share_the_function_and_achievements_never_add_points() -> None:
    human = score_run(
        mode="HUMAN",
        seed=1,
        outcome=RunOutcome.WIN,
        elapsed_ticks=500,
        detection_encounters=0,
        rules=RULES,
    )
    robot = score_run(
        mode="COMPANION",
        seed=1,
        outcome=RunOutcome.WIN,
        elapsed_ticks=500,
        detection_encounters=0,
        rules=RULES,
    )
    assert (human.score, human.grade) == (robot.score, robot.grade) == (100, "S")
    assert achievements(robot, RULES) == (
        Achievement.GHOST,
        Achievement.AI_MASTER,
        Achievement.SPEEDRUNNER,
    )
    assert achievements(human, RULES) == (Achievement.GHOST, Achievement.SPEEDRUNNER)
    # The UI contract accepts the backend result as authoritative.
    RunReport("run", "map", robot, 30, achievements=achievements(robot, RULES))


def test_packaged_rules_are_the_approved_version() -> None:
    assert load_scoring_rules() == RULES
    with pytest.raises(ValueError):
        ScoringRules(encounter_penalty=10)
