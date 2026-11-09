"""T03 with real props: a guard hears glass/metal at its source, never the hidden intruder."""

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.environment.model import EnvironmentSpec, PropSpec
from echo_heist.core.contracts.environment.presentation import PropKind
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.security.model import GuardPatrol, GuardState, SecuritySpec
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, StaticMap
from echo_heist.core.simulation.engine import Simulation
from echo_heist.infrastructure.resources import load_sensor_rules

# An opaque, sound-blocking wall at x=6 with one gap at (6, 4).
BORDER = frozenset((x, y) for x in range(14) for y in range(10) if x in (0, 13) or y in (0, 9))
WALL = frozenset((6, y) for y in range(1, 9) if y != 4)
SOLID = BORDER | WALL


def facility(rules: GameRules, kind: ActorKind, player: tuple[int, int]) -> Simulation:
    patrol = GuardPatrol("sentinel", ((9, 4), (11, 4)))
    return Simulation(
        StaticMap("hearing", 14, 10, SOLID, SOLID),
        (ActorSpawn("intruder", player, kind), ActorSpawn("sentinel", (9, 4), ActorKind.SENTINEL)),
        rules=rules,
        security=SecuritySpec((patrol,), load_sensor_rules(), SOLID),
        environment=EnvironmentSpec(
            (
                PropSpec("glass-a", PropKind.GLASS, ((3, 4),)),
                PropSpec("can-a", PropKind.CANISTER, ((2, 6),)),
            )
        ),
    )


@pytest.mark.parametrize("kind", [ActorKind.OPERATIVE, ActorKind.COMPANION])
def test_glass_behind_a_wall_is_investigated_at_its_tile_without_contact(
    rules: GameRules, kind: ActorKind
) -> None:
    sim = facility(rules, kind, (3, 3))  # standing beside the pane
    assert [h.kind for h in sim.observe("intruder").interactions] == ["Glass"]
    smash = sim.step((Action("intruder", ActionKind.INTERACT, sim.tick, target_id="glass-a"),))
    noise = next(e for e in smash.events if e.kind == EventKind.NOISE_CREATED)
    assert dict(noise.details) == {"kind": "GLASS", "x": 3, "y": 4, "radius_tiles": 6}
    heard = sim.observe("sentinel").heard_events
    assert [(cue.event_id, cue.kind, cue.tile) for cue in heard] == [
        (noise.event_id, "GLASS", (3, 4))
    ]
    events = []
    for _ in range(3):
        events.extend(sim.step().events)
    guard = next(g for g in sim.presentation_snapshot().guards if g.actor_id == "sentinel")
    assert guard.state == GuardState.INVESTIGATE
    assert guard.evidence_kind == "NOISE" and guard.evidence_tile == (3, 4)
    assert guard.last_seen_tile is None
    assert not any(e.kind == EventKind.SIGHTING_CONFIRMED for e in events)
    # Once-only: the shattered pane is never offered or heard again.
    assert all(h.kind != "Glass" for h in sim.observe("intruder").interactions)


def test_out_of_reach_canister_clang_is_not_heard(rules: GameRules) -> None:
    sim = facility(rules, ActorKind.OPERATIVE, (2, 5))
    for _ in range(60):  # walk down onto the canister: kicks it south into the border
        result = sim.step((Action("intruder", ActionKind.MOVE, sim.tick, (0, 1)),))
        if any(dict(e.details).get("kind") == "METAL" for e in result.events):
            break
    clang = next(
        e
        for e in result.events
        if e.kind == EventKind.NOISE_CREATED and dict(e.details)["kind"] == "METAL"
    )
    assert dict(clang.details)["radius_tiles"] == 4
    # Through the gap the sentinel is more than four acoustic tiles away.
    assert not sim.observe("sentinel").heard_events
