"""One integer scoring function for both modes; only actual run metrics go in."""

from echo_heist.core.contracts.config.scoring import ScoringRules
from echo_heist.core.contracts.events import GameEvent
from echo_heist.core.contracts.experience.model import Achievement
from echo_heist.core.contracts.results import RunOutcome, RunResult


def pace_points(elapsed_ticks: int, rules: ScoringRules) -> int:
    """10 at or below the reference, 5 at twice it; never negative, never above 10."""
    reference = rules.pace_reference_ticks
    return (rules.pace_points * reference) // max(max(0, elapsed_ticks), reference)


def grade(outcome: RunOutcome, score: int) -> str:
    if outcome != RunOutcome.WIN:
        return "F"
    if score >= 90:
        return "S"
    if score >= 75:
        return "A"
    return "B" if score >= 60 else "C"


def score_run(
    *,
    mode: str,
    seed: int,
    outcome: RunOutcome,
    elapsed_ticks: int,
    detection_encounters: int,
    rules: ScoringRules,
    policy_id: str | None = None,
    decisive_events: tuple[GameEvent, ...] = (),
) -> RunResult:
    """Approved score: 50 + max(0, 40 - 12 * encounters) + pace on a real extraction.

    A capture or abort is 0/F with no extraction or stealth/pace subtotals.
    Tool use, noise and lockdown carry no direct deduction by design.
    """
    if elapsed_ticks < 0 or detection_encounters < 0:
        raise ValueError("Run metrics must be nonnegative")
    if outcome == RunOutcome.WIN:
        completion = rules.completion_points
        stealth = max(0, rules.stealth_points - rules.encounter_penalty * detection_encounters)
        pace = pace_points(elapsed_ticks, rules)
    else:
        completion = stealth = pace = 0
    score = completion + stealth + pace
    if outcome == RunOutcome.WIN and not 50 <= score <= 100:
        raise AssertionError("Approved successful scores stay within 50-100")
    return RunResult(
        mode,
        seed,
        outcome,
        elapsed_ticks,
        score,
        grade(outcome, score),
        detection_encounters,
        completion,
        stealth,
        pace,
        rules.scoring_version,
        rules.pace_reference_ticks,
        policy_id,
        decisive_events,
    )


def achievements(result: RunResult, rules: ScoringRules) -> tuple[Achievement, ...]:
    """Win-only labels; they never change the score or grade."""
    if result.outcome != RunOutcome.WIN:
        return ()
    earned = []
    if result.detection_encounters == 0:
        earned.append(Achievement.GHOST)
    if result.mode == "COMPANION":
        earned.append(Achievement.AI_MASTER)
    if result.elapsed_ticks <= rules.speedrunner_ticks:
        earned.append(Achievement.SPEEDRUNNER)
    return tuple(earned)
