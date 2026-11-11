"""Prevent misleading search numbers and mutable nested presentation records."""

import pytest

from echo_heist.core.contracts.autonomy.model import Alternative, CompanionTrace


def test_unknown_reward_is_distinct_from_zero_and_invalid_metrics_are_rejected() -> None:
    assert Alternative("WAIT", 0, None).mean_reward is None
    assert Alternative("WAIT", 1, 0).mean_reward == 0
    for visits, reward in ((0, 0.5), (1, float("nan")), (1, 1.5), (-1, None)):
        with pytest.raises(ValueError):
            Alternative("WAIT", visits, reward)
    with pytest.raises(ValueError, match="exceed"):
        CompanionTrace(
            "echo", 0, "INFILTRATE", "WAIT", "actual decision", 1, (Alternative("WAIT", 2, 0.5),)
        )


def test_nested_decision_values_are_detached_from_mutable_inputs() -> None:
    path = [(1, 1), (1, 2)]
    choices = [Alternative("WAIT", 1, 0.5)]
    trace = CompanionTrace("echo", 0, "INFILTRATE", "WAIT", "actual decision", 1, choices, path)
    path.clear()
    choices.clear()
    assert trace.path == ((1, 1), (1, 2)) and len(trace.alternatives) == 1


def test_workshop_presets_match_the_backend_presets() -> None:
    from echo_heist.core.contracts.autonomy.policy import PRESETS
    from echo_heist.ui.scenes.companion.deployment import selection
    from echo_heist.ui.scenes.design.model import PRESETS as NAMES
    from echo_heist.ui.scenes.design.model import WorkshopDraft

    for index, name in enumerate(NAMES):
        draft = WorkshopDraft()
        draft.select_preset(index)
        assert selection(draft) == PRESETS[name]
