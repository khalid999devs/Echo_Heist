"""Reports are authoritative, attempt-specific data; they cannot be guessed by UI."""

from dataclasses import FrozenInstanceError, replace

import pytest

from echo_heist.core.contracts.experience.model import ToolUsage
from echo_heist.core.contracts.results import RunOutcome
from echo_heist.ui.presenters.reporting import ReportState
from tests.fixtures.experience.gateway import MemoryGateway, report, request


def test_default_runtime_never_fabricates_a_score_and_clears_previous_attempt() -> None:
    gateway = MemoryGateway()
    state = ReportState(gateway)
    state.capture(request())
    assert state.report == report()
    state.gateway = None
    state.capture(replace(request(), run_key="new"))
    assert state.report is None and state.request.run_key == "new"
    assert state.history() == () and state.notice


@pytest.mark.parametrize(
    "changes",
    [
        {"run_key": "old"},
        {"map_id": "old-map"},
        {"ticks_per_second": 60},
        {"tools": ToolUsage()},
        {"result": replace(report().result, mode="COMPANION")},
        {"result": replace(report().result, seed=22)},
        {"result": replace(report().result, elapsed_ticks=3601)},
    ],
)
def test_stale_report_cannot_attach_to_a_different_attempt(changes: dict[str, object]) -> None:
    gateway = MemoryGateway()
    gateway.answer = replace(report(), **changes)
    state = ReportState(gateway)
    state.capture(request())
    assert state.report is None and "different attempt" in state.notice


def test_report_validation_rejects_inconsistent_or_impossible_scores() -> None:
    r = report().result
    for bad in (
        replace(r, score=99),
        replace(r, grade="A"),
        replace(r, stealth_points=41),
        replace(r, outcome=RunOutcome.CAPTURED),
        replace(r, detection_encounters=-1),
    ):
        with pytest.raises(ValueError):
            replace(report(), result=bad)
    with pytest.raises(FrozenInstanceError):
        report().tools.melee = 7  # type: ignore[misc]


def test_provider_error_duplicate_history_and_terminal_fallback_are_honest() -> None:
    gateway = MemoryGateway()
    state = ReportState(gateway)
    gateway.fail = True
    state.capture(request())
    assert state.report is None and state.notice
    gateway.fail = False
    gateway.runs = (report(), report())
    assert state.history() == () and "recovery" in state.notice
    state.gateway = None
    state.capture(request(), report().result)
    assert state.report and state.report.result == report().result
