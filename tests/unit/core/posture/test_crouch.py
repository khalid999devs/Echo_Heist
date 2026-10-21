"""Authoritative posture, low headroom, acoustic cadence and filtered guard knowledge."""

from dataclasses import replace

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.security.model import GuardPatrol, SecuritySpec
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, StaticMap
from echo_heist.core.simulation.engine import Simulation
from echo_heist.infrastructure.resources import load_sensor_rules


def desk_map() -> StaticMap:
    desk = frozenset({(3, 3), (4, 3), (5, 3)})
    return StaticMap("under-desk", 12, 12, desk, desk, crouch_tiles=frozenset({(4, 3)}))


def intent(sim: Simulation, kind: ActionKind, direction: tuple[int, int] = (0, 0)) -> None:
    sim.step((Action("operative", kind, sim.tick, direction),))


def test_low_headroom_requires_crouch_and_refuses_standing_until_clear(rules: GameRules) -> None:
    sim = Simulation(desk_map(), (ActorSpawn("operative", (4, 5)),), rules=rules)
    for _ in range(35):
        intent(sim, ActionKind.MOVE, (0, -1))
    assert sim.observe("operative").own_status.tile == (4, 4)
    intent(sim, ActionKind.CROUCH)
    for _ in range(23):
        intent(sim, ActionKind.MOVE, (0, -1))
    own = sim.observe("operative").own_status
    assert own.crouched and own.concealed and own.tile == (4, 3)
    refused = sim.step((Action("operative", ActionKind.CROUCH, sim.tick),))
    assert any(dict(e.details).get("reason") == "low_headroom" for e in refused.events)
    assert sim.observe("operative").own_status.crouched
    for _ in range(30):
        intent(sim, ActionKind.MOVE, (0, 1))
    intent(sim, ActionKind.CROUCH)
    own = sim.observe("operative").own_status
    assert not own.crouched and not own.concealed
    assert not desk_map().can_walk((3, 3), crouched=True)


def test_crouch_is_slower_quieter_and_cannot_spend_sprint(rules: GameRules) -> None:
    world = StaticMap("open-floor", 30, 12)
    sim = Simulation(world, (ActorSpawn("operative", (3, 4)),), rules=rules)
    intent(sim, ActionKind.CROUCH)
    before = sim.observe("operative").own_status.position
    assert before is not None
    events = []
    for _ in range(60):
        events.extend(
            sim.step((Action("operative", ActionKind.MOVE, sim.tick, (1, 0), sprint=True),)).events
        )
    own = sim.observe("operative").own_status
    assert own.position is not None
    expected = (
        rules.walk_speed_units_per_second // rules.simulation_hz * rules.crouch_speed_percent // 100
    )
    assert own.position[0] - before[0] == expected * 60
    assert own.sprint_ticks_remaining == rules.sprint_duration_ticks and not own.sprinting
    noises = [e for e in events if e.kind == EventKind.NOISE_CREATED]
    assert len(noises) == 3 and all(dict(e.details)["kind"] == "CROUCH" for e in noises)
    assert all(dict(e.details)["radius_tiles"] == 1 for e in noises)
    assert not own.concealed  # posture alone never grants invisibility


def test_crouch_does_not_erase_a_guards_legitimate_last_sighting(rules: GameRules) -> None:
    world = desk_map()
    spec = SecuritySpec(
        (GuardPatrol("sentinel", ((1, 5), (2, 5))),), load_sensor_rules(), world.opaque_tiles
    )
    sim = Simulation(
        world,
        (ActorSpawn("operative", (4, 5)), ActorSpawn("sentinel", (1, 5), ActorKind.SENTINEL)),
        rules=replace(rules, sentinel_speed_units_per_second=300),
        security=spec,
    )
    assert any(e.actor_id == "operative" for e in sim.observe("sentinel").visible_entities)
    intent(sim, ActionKind.CROUCH)
    assert any(e.crouched for e in sim.observe("sentinel").visible_entities)
    for _ in range(40):
        intent(sim, ActionKind.MOVE, (0, -1))
    assert sim.observe("operative").own_status.concealed
    assert not any(e.actor_id == "operative" for e in sim.observe("sentinel").visible_entities)
    memory = sim.presentation_snapshot().guards[0]
    assert memory.last_seen_tile is not None and memory.last_seen_tile != (4, 3)
    assert memory.last_seen_tick < sim.tick


def test_guard_cannot_use_intruder_posture_and_replay_is_repeatable(rules: GameRules) -> None:
    def run() -> list[str]:
        sim = Simulation(
            desk_map(),
            (ActorSpawn("operative", (4, 5)), ActorSpawn("guard", (7, 6), ActorKind.TRACKER)),
            rules=rules,
        )
        result = sim.step((Action("guard", ActionKind.CROUCH, 0),))
        assert any(dict(e.details).get("reason") == "intruder_only_action" for e in result.events)
        hashes = [sim.fingerprint()]
        for kind, direction in [(ActionKind.CROUCH, (0, 0)), *[(ActionKind.MOVE, (0, -1))] * 35]:
            intent(sim, kind, direction)
            hashes.append(sim.fingerprint())
        return hashes

    assert run() == run()


def test_under_desk_movement_is_still_audible_and_has_a_reachable_investigation(
    rules: GameRules,
) -> None:
    world = desk_map()
    spec = SecuritySpec(
        (GuardPatrol("sentinel", ((4, 2), (5, 2))),), load_sensor_rules(), world.opaque_tiles
    )
    sim = Simulation(
        world,
        (ActorSpawn("operative", (4, 4)), ActorSpawn("sentinel", (4, 2), ActorKind.SENTINEL)),
        rules=replace(rules, sentinel_speed_units_per_second=300),
        security=spec,
    )
    intent(sim, ActionKind.CROUCH)
    for _ in range(25):
        intent(sim, ActionKind.MOVE, (0, -1))
    assert sim.observe("operative").own_status.concealed
    cues = sim.observe("sentinel").heard_events
    assert any(cue.kind == "CROUCH" and cue.tile == (4, 3) for cue in cues)
    sim.step()
    guard = sim.presentation_snapshot().guards[0]
    assert guard.target is not None and world.can_walk(guard.target)
    assert guard.last_seen_tile is None  # noise is not visual identification
