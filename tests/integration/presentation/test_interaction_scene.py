"""Regression seams: concealment stays authoritative, effects stay on their deck and clock."""

from dataclasses import replace

import pygame

from echo_heist.core.contracts.environment.presentation import EnvironmentView, PropKind, PropView
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as U
from echo_heist.ui.presenters.interactions import Effect
from echo_heist.ui.render import world
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.flow import GameFlow


def test_locker_cannot_confer_concealment_and_effects_cannot_cross_decks(monkeypatch):
    pygame.font.init()
    flow = GameFlow((1280, 720))
    flow._start_run()
    session = flow.session
    base = session.simulation.presentation_snapshot()
    own = next(actor for actor in base.actors if actor.actor_id == session.observer_id)
    locker = PropView(
        "fixture-locker",
        PropKind.LOCKER,
        own.position,
        (U, U),
        occupant_id=own.actor_id,
        occupant_cover=1,
    )
    seen, drawn_effects = [], []
    monkeypatch.setattr(world.motifs, "actor", lambda *args, **kwargs: seen.append(args[1]))
    monkeypatch.setattr(
        world,
        "draw_effects",
        lambda canvas, effects, *args, **kwargs: drawn_effects.extend(effects),
    )
    effects = (Effect("same", 0, "EMP", own.position), Effect("other", 0, "EMP", (56 * U, 22 * U)))
    canvas = opaque_surface((1280, 720))
    fingerprint = session.simulation.fingerprint()
    for concealed in (False, True):
        seen.clear()
        snapshot = replace(
            base,
            actors=(replace(own, concealed=concealed),),
            guards=(),
            environment=EnvironmentView(props=(locker,)),
        )
        world.draw_world(
            canvas,
            session.level,
            session.map_surface,
            snapshot,
            session.camera,
            session.fonts,
            0.5,
            art=session.art,
            effects=effects,
        )
        assert bool(seen) is not concealed
    assert {effect.event_id for effect in drawn_effects} == {"same"}
    assert session.simulation.fingerprint() == fingerprint


def test_tool_feedback_pause_clock_and_retry_use_actual_session_state():
    pygame.font.init()
    flow = GameFlow((1280, 720))
    flow._start_run()
    session = flow.session
    initial = session.simulation.observe(session.observer_id).own_status.inventory.echo_charges
    session.input.feed([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q)])
    session.update(45)
    assert session.interactions.feedback.tool == "ECHO"
    assert (
        session.simulation.observe(session.observer_id).own_status.inventory.echo_charges
        == initial - 1
    )
    tick = session.interaction_tick
    session.paused = True
    session.update(600)
    assert session.interaction_tick == tick
    session.paused = False
    session.update(1)
    assert session.interaction_tick >= tick
    flow._start_run()
    assert flow.session.interactions is not session.interactions
    assert not flow.session.interactions.effects and not flow.session.interactions.audio
