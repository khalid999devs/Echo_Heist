"""Door and glass lifecycles change collision, sight and routing together, once."""

from echo_heist.ai.navigation.grid import bfs
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.environment.model import EnvironmentSpec, PropSpec
from echo_heist.core.contracts.environment.presentation import EnvironmentCueKind, PropKind
from echo_heist.core.contracts.events import EventKind, GameEvent
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, StaticMap
from echo_heist.core.perception.sensors import line_of_sight
from echo_heist.core.simulation.engine import Simulation

# A wall at x=6 with a one-tile doorway at (6, 3); free-standing glass at (3, 6).
WALL = frozenset((6, y) for y in range(8) if y != 3)
DOOR = PropSpec("door-a", PropKind.DOOR, ((6, 3),), horizontal=False)
GLASS = PropSpec("glass-a", PropKind.GLASS, ((3, 6),))
SPEC = EnvironmentSpec((DOOR, GLASS))


def world(rules: GameRules, *spawns: ActorSpawn) -> Simulation:
    return Simulation(StaticMap("props", 14, 8, WALL, WALL), spawns, rules=rules, environment=SPEC)


def details(events: tuple[GameEvent, ...], kind: EventKind) -> list[dict[str, object]]:
    return [dict(event.details) for event in events if event.kind == kind]


def run(sim: Simulation, ticks: int, *actions: Action) -> list[GameEvent]:
    events: list[GameEvent] = []
    for _ in range(ticks):
        events.extend(
            sim.step(
                tuple(
                    Action(a.actor_id, a.kind, sim.tick, a.direction, sprint=a.sprint)
                    for a in actions
                )
            ).events
        )
    return events


def test_closed_door_blocks_body_and_sight_but_still_routes_and_reopens_on_push(
    rules: GameRules,
) -> None:
    sim = world(
        rules, ActorSpawn("operative", (5, 3)), ActorSpawn("guard", (9, 3), ActorKind.SENTINEL)
    )
    first = sim.step((Action("operative", ActionKind.INTERACT, 0, target_id="door-a"),))
    noise = details(first.events, EventKind.NOISE_CREATED)
    assert noise == [{"kind": "DOOR", "x": 6, "y": 3, "radius_tiles": 2}]
    cue = sim.presentation_snapshot().environment.cues[0]
    assert cue.kind == EnvironmentCueKind.DOOR and cue.noise_event_id == first.events[0].event_id
    events = run(sim, rules.simulation_hz)
    revisions = [e for e in events if e.kind == EventKind.GEOMETRY_REVISED]
    assert len(revisions) == 1 and dict(revisions[0].details)["reason"] == "door-closed:door-a"
    closed = sim.observe("operative").map_static
    assert (6, 3) in closed.blocked_tiles and (6, 3) in closed.opaque_tiles
    guard, operative = (sim.observe(a).own_status.position for a in ("guard", "operative"))
    assert guard is not None and operative is not None
    assert not line_of_sight(closed, operative, guard)
    # A controlled passage still routes: whoever pushes into it opens it.
    assert bfs(closed, (5, 3), (9, 3)).path
    # The guard walks up and its own push opens the door silently; geometry
    # follows at the next tick start, then it actually walks through.
    events = run(sim, 4 * rules.simulation_hz, Action("guard", ActionKind.MOVE, 0, (-1, 0)))
    assert not [d for d in details(tuple(events), EventKind.NOISE_CREATED) if d["kind"] == "DOOR"]
    assert [dict(e.details)["reason"] for e in events if e.kind == EventKind.GEOMETRY_REVISED] == [
        "door-open:door-a"
    ]
    assert sim.observe("guard").own_status.tile[0] < 6


def test_door_never_closes_on_a_body(rules: GameRules) -> None:
    sim = world(
        rules, ActorSpawn("operative", (5, 3)), ActorSpawn("guard", (6, 3), ActorKind.TRACKER)
    )
    blocked = sim.step((Action("operative", ActionKind.INTERACT, 0, target_id="door-a"),))
    assert details(blocked.events, EventKind.ACTION_REJECTED) == [{"reason": "door_obstructed"}]
    assert not details(blocked.events, EventKind.NOISE_CREATED)
    # The guard steps out, the door starts closing, then the guard steps back in.
    run(sim, 20, Action("guard", ActionKind.MOVE, 0, (1, 0)))
    sim.step((Action("operative", ActionKind.INTERACT, sim.tick, target_id="door-a"),))
    events = run(sim, 40, Action("guard", ActionKind.MOVE, 0, (-1, 0)))
    states = [dict(e.details).get("state") for e in events if e.kind == EventKind.PROP_CHANGED]
    assert "REOPENING" in states or "OPENING" in states
    assert "CLOSED" not in states
    assert not any(e.kind == EventKind.GEOMETRY_REVISED for e in events)


def test_glass_breaks_once_by_sprint_or_interaction_and_opens_the_tile(rules: GameRules) -> None:
    walker = world(rules, ActorSpawn("operative", (3, 5)))
    walked = run(walker, 10, Action("operative", ActionKind.MOVE, 0, (0, 1)))
    assert not any(e.kind == EventKind.PROP_CHANGED for e in walked)  # walking only bumps it
    sim = world(rules, ActorSpawn("operative", (3, 5)))
    smash = run(sim, 2, Action("operative", ActionKind.MOVE, 0, (0, 1), sprint=True))
    glass = [d for d in details(tuple(smash), EventKind.NOISE_CREATED) if d["kind"] == "GLASS"]
    assert glass == [{"kind": "GLASS", "x": 3, "y": 6, "radius_tiles": 6}]
    pane = next(
        p for p in sim.presentation_snapshot().environment.props if p.object_id == "glass-a"
    )
    assert pane.broken
    later = run(sim, 30, Action("operative", ActionKind.MOVE, 0, (0, 1), sprint=True))
    assert not [d for d in details(tuple(later), EventKind.NOISE_CREATED) if d["kind"] == "GLASS"]
    assert sim.observe("operative").own_status.tile[1] >= 6  # walked through the shattered pane
    assert (3, 6) not in sim.observe("operative").map_static.blocked_tiles
    # An explicit interaction breaks a fresh pane; it is then no longer offered.
    other = world(rules, ActorSpawn("operative", (3, 5)))
    assert [h.kind for h in other.observe("operative").interactions] == ["Glass"]
    other.step((Action("operative", ActionKind.INTERACT, 0, target_id="glass-a"),))
    assert not other.observe("operative").interactions


def test_same_inputs_give_the_same_fingerprint(rules: GameRules) -> None:
    def scripted() -> str:
        sim = world(rules, ActorSpawn("operative", (5, 3)))
        sim.step((Action("operative", ActionKind.INTERACT, 0, target_id="door-a"),))
        run(sim, 20, Action("operative", ActionKind.MOVE, 0, (1, 0)))
        return sim.fingerprint()

    assert scripted() == scripted()
