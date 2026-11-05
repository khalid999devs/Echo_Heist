"""Limited emergency melee: exact ticks, fair costs, shared controller rules and capture order."""

from dataclasses import replace

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, StaticMap
from echo_heist.core.simulation.engine import Simulation


def arena(rules, kind=ActorKind.OPERATIVE):
    return Simulation(
        StaticMap("melee-budget", 16, 10),
        (ActorSpawn("intruder", (3, 3), kind), ActorSpawn("guard", (4, 3), ActorKind.SENTINEL)),
        rules=replace(rules, capture_windup_ticks=1000),
    )


def strike(sim):
    return sim.step((Action("intruder", ActionKind.MELEE, sim.tick),))


def impacts(result):
    return [event for event in result.events if event.kind == EventKind.NOISE_CREATED]


@pytest.mark.parametrize("kind", [ActorKind.OPERATIVE, ActorKind.COMPANION])
def test_two_charges_exact_four_second_recovery_and_no_refill(rules, kind):
    assert rules.melee_cooldown_ticks == rules.simulation_hz * 4
    sim = arena(rules, kind)
    first = strike(sim)
    own = sim.observe("intruder").own_status
    assert own.inventory.melee_charges == 1 and own.melee_cooldown_remaining == 120
    assert len(impacts(first)) == 1 and dict(impacts(first)[0].details)["radius_tiles"] == 6
    ready = dict(next(e for e in first.events if e.kind == EventKind.TOOL_USED).details)[
        "ready_at_tick"
    ]
    rejected = strike(sim)
    assert rejected.events[0].details == (("reason", "melee_cooldown"),)
    assert not impacts(rejected)
    assert sim.observe("intruder").own_status.inventory.melee_charges == 1
    while sim.tick < ready - 2:
        sim.step()
    early = strike(sim)
    assert early.events[0].details == (("reason", "melee_cooldown"),)
    assert sim.tick == ready - 1
    second = strike(sim)  # Validate at the action's commit tick, exactly ready_at.
    assert second.tick == ready and len(impacts(second)) == 1
    assert sim.observe("intruder").own_status.inventory.melee_charges == 0
    empty = strike(sim)
    assert empty.events[0].details == (("reason", "melee_empty"),) and not impacts(empty)
    for _ in range(rules.melee_cooldown_ticks * 2):
        sim.step()
    own = sim.observe("intruder").own_status
    assert own.inventory.melee_charges == 0 and own.melee_cooldown_remaining == 0
    reset = arena(rules, kind).observe("intruder").own_status
    assert reset.inventory.melee_charges == 2 and reset.melee_cooldown_remaining == 0


@pytest.mark.parametrize("invalid", ["range", "stale", "multiple", "direction"])
def test_illegal_strikes_do_not_spend_charge_or_start_recovery_or_make_noise(rules, invalid):
    sim = arena(rules)
    action = Action("intruder", ActionKind.MELEE, 0)
    if invalid == "range":
        action = replace(action, target_id="missing")
    elif invalid == "stale":
        action = replace(action, tick_issued=-1)
    elif invalid == "direction":
        action = replace(action, direction=(1, 0))
    result = sim.step((action, action) if invalid == "multiple" else (action,))
    assert any(e.kind == EventKind.ACTION_REJECTED for e in result.events)
    assert not impacts(result)
    own = sim.observe("intruder").own_status
    assert own.inventory.melee_charges == 2 and own.melee_cooldown_remaining == 0


def test_resisted_contact_consumes_each_attackers_charge_and_noise_without_extending_stun(rules):
    sim = Simulation(
        StaticMap("two-attackers", 12, 10),
        (
            ActorSpawn("human", (3, 3)),
            ActorSpawn("robot", (5, 3), ActorKind.COMPANION),
            ActorSpawn("guard", (4, 3), ActorKind.SENTINEL),
        ),
        rules=rules,
    )
    result = sim.step(tuple(Action(actor, ActionKind.MELEE, 0) for actor in ("human", "robot")))
    uses = [dict(e.details) for e in result.events if e.kind == EventKind.TOOL_USED]
    assert [use["affected"] for use in uses] == [True, False]
    assert len(impacts(result)) == 2
    assert sum(e.kind == EventKind.GUARD_STUNNED for e in result.events) == 1
    for actor in ("human", "robot"):
        own = sim.observe(actor).own_status
        assert own.inventory.melee_charges == 1 and own.melee_cooldown_remaining == 120
    until = next(
        dict(e.details)["until_tick"] for e in result.events if e.kind == EventKind.GUARD_STUNNED
    )
    assert until == result.tick + rules.melee_stun_ticks


def test_last_moment_melee_interrupts_capture_before_completion(rules):
    sim = arena(rules)
    # Use normal capture timing for this precedence check.
    sim = Simulation(
        sim.presentation_snapshot().world_map,
        (
            ActorSpawn("intruder", (3, 3)),
            ActorSpawn("guard", (4, 3), ActorKind.SENTINEL),
        ),
        rules=rules,
    )
    for _ in range(rules.capture_windup_ticks):
        sim.step()
    result = strike(sim)
    assert result.mission_end is None
    assert any(e.kind == EventKind.CAPTURE_CANCELED for e in result.events)
    assert not any(e.kind == EventKind.CAPTURE_COMPLETED for e in result.events)
    assert sim.observe("intruder").own_status.inventory.melee_charges == 1
