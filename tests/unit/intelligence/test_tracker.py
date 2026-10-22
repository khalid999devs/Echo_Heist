"""Tracker decisions from one filtered Observation: A*, search order, leads, expiry."""

from dataclasses import replace

from echo_heist.ai.guards.tracker import decide, plausible_neighbors
from echo_heist.core.contracts.events import SecurityReport
from echo_heist.core.contracts.observations import EntityView, Observation, OwnStatus
from echo_heist.core.contracts.security.model import (
    GuardMemory,
    GuardPatrol,
    GuardRole,
    GuardState,
)
from echo_heist.core.contracts.world import (
    ActorKind,
    Inventory,
    MissionPhase,
    StaticMap,
    Tile,
    tile_center,
)
from echo_heist.infrastructure.resources import load_sensor_rules

PATROL = GuardPatrol("tracker", ((2, 2), (2, 6)), GuardRole.TRACKER)
RULES = load_sensor_rules()


def observe(tile: Tile, tick: int, world: StaticMap, **values: object) -> Observation:
    own = OwnStatus(tile, Inventory(), position=tile_center(tile), facing=(1, 0))
    return Observation("tracker", tick, world, MissionPhase.INFILTRATE, own, **values)  # type: ignore[arg-type]


def test_lost_contact_plans_with_astar_then_searches_in_observed_direction() -> None:
    world = StaticMap("search", 14, 10)
    memory = GuardMemory()
    intruder = (7, 4)
    # Two real sightings establish motion toward +x.
    for tick, seen in ((0, (6, 4)), (1, intruder)):
        view = EntityView("operative", ActorKind.OPERATIVE, seen, tile_center(seen))
        memory = decide(
            observe((3, 4), tick, world, visible_entities=(view,)), PATROL, RULES, memory
        ).memory
    assert memory.last_seen_heading == (1, 0)
    lost = decide(observe((3, 4), 2, world), PATROL, RULES, memory)
    assert lost.memory.target == intruder and lost.memory.path[-1] == intruder
    assert lost.memory.path_cost == 4 and lost.memory.expanded_nodes > 0
    arrived = decide(observe(intruder, 30, world), PATROL, RULES, lost.memory)
    assert arrived.memory.state == GuardState.SEARCH
    assert arrived.memory.search_tiles[0] == (9, 4)  # furthest along observed heading first
    assert all(abs(x - 7) + abs(y - 4) <= 2 for x, y in arrived.memory.search_tiles)
    expired = decide(
        observe(intruder, 1 + RULES.memory_ticks + 1, world), PATROL, RULES, arrived.memory
    )
    assert expired.memory.state == GuardState.RETURN and expired.memory.target in PATROL.points


def test_search_respects_walls_rather_than_radius_through_them() -> None:
    wall = frozenset((5, y) for y in range(10))
    world = StaticMap("wall", 10, 10, wall, wall)
    tiles = plausible_neighbors(world, (4, 4), (1, 0))
    assert tiles and all(x < 5 for x, _ in tiles)


def test_radio_report_is_a_lead_with_original_tick_not_identity() -> None:
    world = StaticMap("radio", 14, 10)
    report = SecurityReport("sentinel", "SIGHTING", (10, 5), 40, 1.0, "sight:sentinel:40", 130)
    first = decide(
        observe((2, 2), 50, world, shared_reports=(report,)), PATROL, RULES, GuardMemory()
    )
    memory = first.memory
    assert memory.state == GuardState.INVESTIGATE and memory.target == (10, 5)
    assert (memory.evidence_kind, memory.evidence_id, memory.evidence_tick) == (
        "REPORT",
        report.event_id,
        40,
    )
    assert memory.last_seen_tile is None and memory.identity_ticks == 0
    again = decide(observe((2, 2), 90, world, shared_reports=(report,)), PATROL, RULES, memory)
    assert again.memory.evidence_tick == 40  # duplicate delivery cannot refresh its age
    stale = decide(observe((6, 6), 40 + RULES.memory_ticks + 1, world), PATROL, RULES, again.memory)
    assert stale.memory.state == GuardState.RETURN and stale.memory.target in PATROL.points
    own = SecurityReport("tracker", "SIGHTING", (9, 9), 60, 1.0, "sight:tracker:60", 150)
    ignored = decide(
        observe((2, 2), 61, world, shared_reports=(own,)), PATROL, RULES, GuardMemory()
    )
    assert ignored.memory.state == GuardState.PATROL


def test_decision_depends_only_on_its_observation() -> None:
    world = StaticMap("pure", 12, 8)
    observation = observe((3, 3), 5, world, shared_reports=())
    memory = replace(GuardMemory(), state=GuardState.CHASE, last_seen_tile=(8, 3), last_seen_tick=1)
    first = decide(observation, PATROL, RULES, memory)
    second = decide(observation, PATROL, RULES, memory)
    assert first == second
