from dataclasses import replace

from echo_heist.ai.guards.fuzzy import investigate_urgency
from echo_heist.ai.guards.sentinel import decide
from echo_heist.core.contracts.actions import ActionKind
from echo_heist.core.contracts.events import HeardCue
from echo_heist.core.contracts.observations import EntityView, Observation, OwnStatus
from echo_heist.core.contracts.security.model import GuardMemory, GuardPatrol, GuardState, VisualCue
from echo_heist.core.contracts.world import (
    ActorKind,
    Inventory,
    MissionPhase,
    StaticMap,
    tile_center,
)
from echo_heist.infrastructure.resources import load_sensor_rules


def test_sugeno_memberships_are_bounded_and_loud_near_is_more_urgent() -> None:
    quiet = investigate_urgency(0, 0, 0)
    loud = investigate_urgency(0, 1, 0)
    partial = investigate_urgency(0, 0, 0.5)
    assert quiet.urgency < partial.urgency < loud.urgency
    assert all(
        0 <= value <= 1 for value in (*quiet.activations, *loud.activations, *partial.activations)
    )


def test_unidentified_visual_cue_lures_without_fabricating_identity() -> None:
    world = StaticMap("cue", 10, 8)
    own = OwnStatus((3, 3), Inventory(), position=tile_center((3, 3)), facing=(1, 0))
    observation = Observation(
        "sentinel",
        0,
        world,
        MissionPhase.INFILTRATE,
        own,
        visual_cues=(VisualCue("motion", (6, 3), 0),),
    )
    patrol = GuardPatrol("sentinel", ((3, 3), (3, 5)))
    memory = GuardMemory()
    for tick in range(35):
        decision = decide(replace(observation, tick=tick), patrol, load_sensor_rules(), memory)
        memory = decision.memory
    assert memory.state == GuardState.INVESTIGATE and memory.target == (6, 3)
    assert memory.last_seen_tile is None and memory.identity_ticks == 0
    assert memory.expanded_nodes > 0


def test_lost_contact_search_expires_into_return_without_secret_target() -> None:
    own = OwnStatus((4, 3), Inventory(), position=tile_center((4, 3)))
    observation = Observation(
        "sentinel", 20, StaticMap("search", 10, 8), MissionPhase.INFILTRATE, own
    )
    memory = GuardMemory(
        state=GuardState.CHASE,
        identity_ticks=18,
        last_seen_tile=(4, 3),
        last_seen_tick=0,
        target=(4, 3),
    )
    patrol = GuardPatrol("sentinel", ((2, 3), (2, 5)))
    search = decide(observation, patrol, load_sensor_rules(), memory)
    assert search.memory.state == GuardState.SEARCH
    returned = decide(replace(observation, tick=200), patrol, load_sensor_rules(), search.memory)
    assert returned.memory.state == GuardState.RETURN and returned.memory.target in patrol.points


def test_fuzzy_trace_keeps_observed_origin_and_original_evaluation_time() -> None:
    cue_tile = (6, 3)
    world = StaticMap("trace", 10, 8, frozenset({cue_tile}), frozenset({cue_tile}))
    observation = Observation(
        "sentinel",
        12,
        world,
        MissionPhase.INFILTRATE,
        OwnStatus((3, 3), Inventory(), position=tile_center((3, 3))),
        heard_events=(HeardCue("step", "SPRINT", cue_tile, 9),),
    )
    patrol = GuardPatrol("sentinel", ((3, 3), (3, 5)))
    memory = decide(observation, patrol, load_sensor_rules(), GuardMemory()).memory
    trace = memory.fuzzy_trace
    assert trace is not None and trace.cue_tile == memory.evidence_tile == cue_tile
    assert trace.evaluated_tick == 12 and trace.cue_tick == memory.evidence_tick == 9
    assert memory.path_goal != cue_tile  # Solid cover needs a reachable approach.
    assert trace.distance_tiles == 3 and trace.salience == 0.75 and trace.visibility == 0
    assert dict(trace.memberships)["near"] == 0.25
    assert len(trace.activations) == len(trace.outputs) == 5
    total = sum(trace.activations)
    assert trace.urgency == round(
        sum(w * v for w, v in zip(trace.activations, trace.outputs, strict=True)) / total, 4
    )
    assert memory.identity_ticks == 0 and memory.last_seen_tile is None
    later = decide(
        replace(observation, tick=13, heard_events=()), patrol, load_sensor_rules(), memory
    )
    assert later.memory.fuzzy_trace == trace  # Drawing later must not imply fresh evidence.


def test_a_chaser_closes_on_a_quarry_hopping_between_two_rows() -> None:
    # Re-centring on a tile path used to send the chaser back and forth while a
    # thief stepped between two rows, so it never closed the gap.
    unit = tile_center((1, 0))[0] - tile_center((0, 0))[0]
    own = OwnStatus((8, 1), Inventory(), position=(8 * unit + unit // 4, unit + 3 * unit // 5))
    observation = Observation("sentinel", 0, StaticMap("hall", 12, 4), MissionPhase.LOCKDOWN, own)
    patrol = GuardPatrol("sentinel", ((9, 1), (9, 2)))
    memory = GuardMemory(
        state=GuardState.CHASE,
        identity_ticks=18,
        last_seen_tile=(5, 1),
        last_seen_tick=0,
        target=(5, 1),
    )
    for tick, (row, y) in enumerate(((1, 47), (2, 70), (1, 49), (2, 80), (1, 45), (2, 75)), 1):
        quarry = EntityView(
            "thief", ActorKind.COMPANION, (5, row), (5 * unit + 29 * unit // 30, y * unit // 50)
        )
        view = replace(observation, tick=tick, visible_entities=(quarry,))
        decision = decide(view, patrol, load_sensor_rules(), memory)
        memory = decision.memory
        assert memory.state == GuardState.CHASE
        assert decision.action.direction == (-1, 0)


def test_a_half_seen_shape_is_watched_briefly_before_it_is_checked() -> None:
    own = OwnStatus((3, 3), Inventory(), position=tile_center((3, 3)), facing=(0, 1))
    observation = Observation(
        "sentinel", 0, StaticMap("room", 12, 10), MissionPhase.INFILTRATE, own
    )
    patrol = GuardPatrol("sentinel", ((3, 3), (3, 5)))
    memory = GuardMemory(
        state=GuardState.SPOTTED,
        identity_ticks=6,
        last_seen_tile=(7, 6),
        last_seen_tick=10,
        target=(7, 6),
    )
    staring = decide(replace(observation, tick=15), patrol, load_sensor_rules(), memory)
    assert staring.memory.state == GuardState.SPOTTED
    assert staring.action.kind == ActionKind.WAIT and staring.facing == (1, 1)
    checking = decide(replace(observation, tick=21), patrol, load_sensor_rules(), staring.memory)
    assert checking.memory.state == GuardState.INVESTIGATE and checking.memory.target == (7, 6)
    # Walking over to check, it keeps its eyes on where the shape was.
    assert checking.action.kind == ActionKind.MOVE and checking.facing == (1, 1)
