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


def test_decision_panel_keeps_a_chosen_action_beyond_the_first_four_rows(monkeypatch) -> None:
    import pygame

    from echo_heist.core.contracts.autonomy.model import (
        Alternative,
        AutonomyTelemetry,
        CompanionTrace,
    )
    from echo_heist.ui.render.autonomy import panel
    from echo_heist.ui.render.theme import Fonts

    pygame.font.init()
    original = panel.render
    labels = []

    def recorded(font, text, color):
        labels.append(text)
        return original(font, text, color)

    monkeypatch.setattr(panel, "render", recorded)
    trace = CompanionTrace(
        "robot",
        10,
        "INFILTRATE",
        "EMP",
        "Real chosen action",
        64,
        (
            *(Alternative(name, 1, 0.1) for name in ("ADVANCE", "WAIT", "ALTERNATE", "HIDE")),
            Alternative("EMP", 60, 0.8),
        ),
    )
    panel.draw_telemetry(
        pygame.Surface((1280, 720)), Fonts(), AutonomyTelemetry(companion=trace), 0, 10, 30
    )
    assert "EMP" in labels and "60" in labels and "0.80" in labels
