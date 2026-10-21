from dataclasses import replace

from echo_heist.ai.guards.fuzzy import investigate_urgency
from echo_heist.ai.guards.sentinel import decide
from echo_heist.core.contracts.observations import Observation, OwnStatus
from echo_heist.core.contracts.security.model import GuardMemory, GuardPatrol, GuardState, VisualCue
from echo_heist.core.contracts.world import Inventory, MissionPhase, StaticMap, tile_center
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
