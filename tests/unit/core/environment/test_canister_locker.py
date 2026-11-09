"""Canister travel/impact and locker hiding are committed, fair and once-only."""

from dataclasses import replace
from itertools import pairwise

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.environment.model import EnvironmentSpec, PropSpec
from echo_heist.core.contracts.environment.presentation import EnvironmentCueKind, PropKind
from echo_heist.core.contracts.events import EventKind, GameEvent
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, StaticMap
from echo_heist.core.simulation.engine import Simulation

WALL = frozenset((9, y) for y in range(8))
SPEC = EnvironmentSpec(
    (
        PropSpec("can-a", PropKind.CANISTER, ((3, 3),)),
        PropSpec("locker-a", PropKind.LOCKER, ((4, 1),)),
    )
)


def world(rules: GameRules, *spawns: ActorSpawn) -> Simulation:
    return Simulation(StaticMap("props", 12, 8, WALL, WALL), spawns, rules=rules, environment=SPEC)


def step(sim: Simulation, *actions: Action) -> tuple[GameEvent, ...]:
    return sim.step(
        tuple(
            Action(a.actor_id, a.kind, sim.tick, a.direction, target_id=a.target_id)
            for a in actions
        )
    ).events


def noises(events: list[GameEvent], kind: str) -> list[dict[str, object]]:
    return [
        dict(e.details)
        for e in events
        if e.kind == EventKind.NOISE_CREATED and dict(e.details)["kind"] == kind
    ]


def test_bumped_canister_rolls_then_clangs_once_where_it_stops(rules: GameRules) -> None:
    sim = world(rules, ActorSpawn("operative", (2, 3)))
    events: list[GameEvent] = []
    samples = []
    for index in range(60):
        move = Action("operative", ActionKind.MOVE, 0, (1, 0)) if index < 8 else None
        events.extend(step(sim, *(move,) if move else ()))
        can = next(
            p for p in sim.presentation_snapshot().environment.props if p.kind == PropKind.CANISTER
        )
        samples.append(can.position[0])
    clang = noises(events, "METAL")
    # Four tiles from (3, 3), the rolling budget; one cue/noise at the final tile.
    assert clang == [{"kind": "METAL", "x": 7, "y": 3, "radius_tiles": 4}]
    cues = [
        c
        for c in sim.presentation_snapshot().environment.cues
        if c.kind == EnvironmentCueKind.CANISTER_IMPACT
    ]
    noise_id = next(
        e.event_id
        for e in events
        if e.kind == EventKind.NOISE_CREATED and dict(e.details)["kind"] == "METAL"
    )
    assert len(cues) == 1 and cues[0].noise_event_id == noise_id
    assert samples == sorted(samples)  # monotone committed travel, no teleport back
    assert max(b - a for a, b in pairwise(samples)) <= 30_000 // 5


def test_kick_into_a_wall_is_one_immediate_clang_and_interaction_kicks_away(
    rules: GameRules,
) -> None:
    sim = world(rules, ActorSpawn("operative", (2, 3)))
    hints = sim.observe("operative").interactions
    assert [h.kind for h in hints] == ["Canister"]
    events = list(step(sim, Action("operative", ActionKind.INTERACT, 0, target_id="can-a")))
    for _ in range(60):
        events.extend(step(sim))
    assert len(noises(events, "METAL")) == 1
    blocked = Simulation(
        StaticMap("props", 12, 8, WALL | {(4, 3)}, WALL),
        (ActorSpawn("operative", (2, 3)),),
        rules=rules,
        environment=SPEC,
    )
    kicked = step(blocked, Action("operative", ActionKind.INTERACT, 0, target_id="can-a"))
    assert noises(list(kicked), "METAL") == [{"kind": "METAL", "x": 3, "y": 3, "radius_tiles": 4}]


def test_locker_conceals_only_unseen_entry_and_move_or_e_leaves(rules: GameRules) -> None:
    sim = world(
        rules, ActorSpawn("operative", (4, 2)), ActorSpawn("guard", (8, 6), ActorKind.SENTINEL)
    )
    assert [h.kind for h in sim.observe("operative").interactions] == ["HideSpot"]
    enter = step(sim, Action("operative", ActionKind.HIDE, 0))
    assert not noises(list(enter), "DOOR")
    own = sim.observe("operative").own_status
    assert own.concealed and own.hidden_in == "locker-a" and own.tile == (4, 1)
    assert [h.kind for h in sim.observe("operative").interactions] == ["LeaveHide"]
    crouch = step(sim, Action("operative", ActionKind.CROUCH, 0))
    assert dict(crouch[0].details) == {"reason": "hidden"}
    locker = next(
        p for p in sim.presentation_snapshot().environment.props if p.kind == PropKind.LOCKER
    )
    assert locker.occupant_id == "operative" and locker.occupant_cover == 1.0
    actor = next(a for a in sim.presentation_snapshot().actors if a.actor_id == "operative")
    assert actor.concealed
    # An unregistered guard pressed against the locker still cannot grab it.
    for _ in range(3 * rules.capture_windup_ticks):
        step(sim)
    assert sim.presentation_snapshot().mission_end is None
    leave = step(sim, Action("operative", ActionKind.MOVE, 0, (1, 0)))
    assert any(e.kind == EventKind.ACTOR_MOVED for e in leave)
    assert not sim.observe("operative").own_status.concealed
    # Re-enter with E, then leave with E: exactly one enter/leave cue each.
    step(sim, Action("operative", ActionKind.MOVE, 0, (-1, 0)))
    step(sim, Action("operative", ActionKind.INTERACT, 0, target_id="locker-a"))
    step(sim, Action("operative", ActionKind.INTERACT, 0, target_id="locker-a"))
    kinds = [c.kind for c in sim.presentation_snapshot().environment.cues]
    assert kinds.count(EnvironmentCueKind.HIDE_ENTER) == 2
    assert kinds.count(EnvironmentCueKind.HIDE_LEAVE) == 2


def test_locker_holds_one_occupant_and_hidden_intruder_is_not_contact_captured(
    rules: GameRules,
) -> None:
    sim = world(
        rules,
        ActorSpawn("operative", (4, 2)),
        ActorSpawn("guard", (5, 1), ActorKind.SENTINEL),
    )
    step(sim, Action("operative", ActionKind.HIDE, 0, target_id="locker-a"))
    for _ in range(3 * rules.capture_windup_ticks):
        assert not any(e.kind == EventKind.CAPTURE_STARTED for e in step(sim))
    second = Simulation(
        StaticMap("props", 12, 8, WALL, WALL),
        (ActorSpawn("operative", (4, 2)), ActorSpawn("companion", (3, 1), ActorKind.COMPANION)),
        rules=replace(rules),
        environment=SPEC,
    )
    step(second, Action("operative", ActionKind.HIDE, 0))
    taken = step(second, Action("companion", ActionKind.HIDE, 0, target_id="locker-a"))
    assert {
        dict(e.details).get("reason") for e in taken if e.kind == EventKind.ACTION_REJECTED
    } == {"no_hide_spot"}
