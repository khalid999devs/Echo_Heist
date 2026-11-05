"""Presentation cannot invent tool success, expose hidden targets or grow indefinitely."""

from dataclasses import FrozenInstanceError, replace

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.environment.presentation import (
    EnvironmentCue,
    EnvironmentCueKind,
    EnvironmentView,
    PropKind,
    PropView,
)
from echo_heist.core.contracts.events import EventKind, GameEvent
from echo_heist.core.contracts.observations import InteractionHint
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, StaticMap
from echo_heist.core.simulation.engine import Simulation
from echo_heist.ui.presenters.interactions import InteractionPresentation
from echo_heist.ui.presenters.objective import build_objective_view


def setup(rules):
    sim = Simulation(
        StaticMap("presentation", 12, 12),
        (
            ActorSpawn("operative", (3, 3)),
            ActorSpawn("guard", (4, 3), ActorKind.SENTINEL),
        ),
        rules=rules,
    )
    presenter = InteractionPresentation(
        "operative", rules.simulation_hz, emp_radius_units=rules.emp_radius_units
    )
    return sim, presenter


def test_actual_melee_resistance_and_rejection_are_not_success(rules):
    sim, presenter = setup(replace(rules, melee_cooldown_ticks=1))
    for expected in ("USED", "RESISTED"):
        result = sim.step((Action("operative", ActionKind.MELEE, sim.tick),))
        presenter.observe(sim.presentation_snapshot(), sim.observe("operative"), result.events)
        assert presenter.feedback.status == expected
    assert presenter.effects[-1].kind == "RESISTED"
    for expected in ("USED", "REJECTED"):
        result = sim.step((Action("operative", ActionKind.EMP, sim.tick),))
        presenter.observe(sim.presentation_snapshot(), sim.observe("operative"), result.events)
        assert presenter.feedback.status == expected
    assert sim.observe("operative").own_status.inventory.emp_charges == 0
    assert presenter.feedback.message == "OUT OF CHARGES"


def test_foreign_hidden_tool_cannot_overwrite_own_feedback_or_reveal_target(rules):
    sim, presenter = setup(rules)
    snapshot = replace(sim.presentation_snapshot(), tick=1)
    observation = replace(sim.observe("operative"), tick=1, visible_entities=())
    event = GameEvent("hidden", 1, EventKind.TOOL_USED, "guard", (("tool", "EMP"),))
    presenter.observe(snapshot, observation, (event,))
    assert not presenter.effects and presenter.feedback is None
    own = replace(
        event,
        event_id="own",
        actor_id="operative",
        details=(("tool", "MELEE"), ("target_id", "guard"), ("affected", False)),
    )
    presenter.observe(snapshot, observation, (own,))
    assert presenter.effects[-1].target is None
    assert presenter.feedback.status == "RESISTED"


def test_once_only_pause_expiry_and_bounded_event_storm(rules):
    sim, presenter = setup(rules)
    fingerprint = sim.fingerprint()
    cue = EnvironmentCue(
        "glass", 1, EnvironmentCueKind.GLASS, "panel", (90000, 90000), visible=True
    )
    snapshot = replace(
        sim.presentation_snapshot(), tick=1, environment=EnvironmentView(cues=(cue,))
    )
    obs = sim.observe("operative")
    for _ in range(50):
        presenter.observe(snapshot, obs, ())
    assert len(presenter.effects) == 1 and len(presenter.take_audio()) == 1
    assert not presenter.take_audio()
    assert sim.fingerprint() == fingerprint
    for tick in range(2, 1200):
        event = replace(cue, event_id=f"glass-{tick}", tick=tick)
        presenter.observe(
            replace(snapshot, tick=tick, environment=EnvironmentView(cues=(event,))), obs, ()
        )
    assert len(presenter.effects) <= 32 and len(presenter.audio) <= 128
    assert len(presenter._seen) <= 1024
    presenter.observe(replace(snapshot, tick=1400), obs, ())
    assert not presenter.effects
    with pytest.raises(ValueError, match="fresh"):
        presenter.observe(snapshot, obs, ())
    fresh = InteractionPresentation("operative", rules.simulation_hz, emp_radius_units=1)
    fresh.observe(snapshot, obs, ())
    assert len(fresh.effects) == 1


def test_contract_is_immutable_and_rejects_invalid_occlusion():
    prop = PropView("locker", PropKind.LOCKER, [100, 200], [300, 400])
    assert prop.position == (100, 200)
    with pytest.raises(FrozenInstanceError):
        prop.openness = 1
    with pytest.raises(ValueError):
        replace(prop, openness=float("nan"))
    with pytest.raises(ValueError):
        replace(prop, occupant_cover=1)
    with pytest.raises(ValueError):
        EnvironmentView(props=(prop, prop))


def test_interaction_prompt_uses_supplied_kind_and_progress_only(rules):
    sim, _ = setup(rules)
    obs = sim.observe("operative")
    for kind, label in (
        ("Door", "Use door"),
        ("HideSpot", "Enter cover"),
        ("LeaveHide", "Leave cover"),
        ("Canister", "Push canister"),
        ("Unknown", "Interact"),
    ):
        view = build_objective_view(
            replace(obs, interactions=(InteractionHint("target", kind, 1),)), ticks_per_second=30
        )
        assert view.interaction == "E  " + label and view.interaction_progress is None
    view = build_objective_view(
        replace(obs, interactions=(InteractionHint("core", "Core", 30, 12),)), ticks_per_second=30
    )
    assert view.interaction == "Hold E  Recover core" and view.interaction_progress == (12, 30)
