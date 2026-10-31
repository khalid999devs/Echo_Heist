"""A melee clang is legitimate location evidence, never a moving-target reveal."""

from dataclasses import replace

import pytest

from echo_heist.ai.guards import sentinel
from echo_heist.ai.guards.steering import evidence_expired
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.security.model import (
    GuardPatrol,
    GuardRole,
    GuardState,
    SecuritySpec,
)
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, StaticMap
from echo_heist.core.simulation.engine import Simulation
from echo_heist.infrastructure.resources import load_sensor_rules


@pytest.mark.parametrize("kind", [ActorKind.OPERATIVE, ActorKind.COMPANION])
def test_only_audible_guards_investigate_original_impact_and_memory_expires(rules, kind):
    wall = frozenset({(3, 5)})
    world = StaticMap("melee-hearing", 18, 12, wall, wall)
    patrols = (
        GuardPatrol("target", ((4, 3), (5, 3)), role=GuardRole.POST),
        GuardPatrol("near", ((3, 7), (7, 7))),
        GuardPatrol("far", ((12, 7), (16, 7))),
    )
    sensors = load_sensor_rules()
    sim = Simulation(
        world,
        (
            ActorSpawn("intruder", (3, 3), kind),
            ActorSpawn("target", (4, 3), ActorKind.SENTINEL),
            ActorSpawn("near", (3, 7), ActorKind.SENTINEL),
            ActorSpawn("far", (12, 7), ActorKind.SENTINEL),
        ),
        rules=rules,
        security=SecuritySpec(patrols, sensors, wall),
    )
    first = sim.step((Action("intruder", ActionKind.MELEE, 0),))
    noise = next(e for e in first.events if e.kind == EventKind.NOISE_CREATED)
    heard = sim.observe("near").heard_events
    assert [(cue.event_id, cue.tile, cue.tick) for cue in heard] == [(noise.event_id, (3, 3), 1)]
    assert not sim.observe("far").heard_events
    assert not any(e.kind == EventKind.SIGHTING_CONFIRMED for e in first.events)
    for _ in range(12):
        sim.step((Action("intruder", ActionKind.MOVE, sim.tick, (0, -1)),))
    guard = next(g for g in sim.presentation_snapshot().guards if g.actor_id == "near")
    assert guard.state == GuardState.INVESTIGATE
    assert guard.evidence_kind == "NOISE" and guard.evidence_tick == 1
    assert guard.evidence_tile == (3, 3) and sim.observe("intruder").own_status.tile != (3, 3)
    assert not any(
        e.kind in (ActorKind.OPERATIVE, ActorKind.COMPANION)
        for e in sim.observe("near").visible_entities
    )
    # Read the same observed provenance through the decision API at expiry boundaries.
    decision = sentinel.decide(
        sim.observe("near"), patrols[1], sensors, sim._world.guard_memories["near"]
    )
    memory = replace(decision.memory, state=GuardState.INVESTIGATE)
    observation = replace(sim.observe("near"), visible_entities=(), heard_events=(), tick=151)
    assert sensors.memory_ticks == rules.simulation_hz * 5
    assert not evidence_expired(observation, sensors, memory)
    expired = replace(observation, tick=152)
    assert evidence_expired(expired, sensors, memory)
    outcome = sentinel.decide(expired, patrols[1], sensors, memory)
    assert outcome.memory.state in (GuardState.RETURN, GuardState.PATROL)
