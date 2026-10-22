"""P03 defenders in the real Simulation: hiding, T03/T04, radio provenance, posts, geometry."""

from collections import Counter

import pytest

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.security.model import (
    GuardPatrol,
    GuardRole,
    GuardState,
    SecuritySpec,
)
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, StaticMap, Tile, tile_center
from echo_heist.core.simulation.engine import Simulation
from echo_heist.infrastructure.resources import load_sensor_rules

KINDS = {GuardRole.SENTINEL: ActorKind.SENTINEL, GuardRole.TRACKER: ActorKind.TRACKER}


def bordered(width: int, height: int, inner: frozenset[Tile] = frozenset()) -> StaticMap:
    border = frozenset(
        (x, y)
        for x in range(width)
        for y in range(height)
        if x in (0, width - 1) or y in (0, height - 1)
    )
    return StaticMap("fixture", width, height, border | inner, border | inner)


def secured(
    world: StaticMap,
    rules: GameRules,
    operative: Tile,
    *patrols: GuardPatrol,
    kinds: dict[str, ActorKind] | None = None,
    sound_blocking: frozenset[Tile] | None = None,
) -> Simulation:
    kinds = kinds or {}
    spawns = tuple(
        ActorSpawn(
            p.actor_id, p.points[0], kinds.get(p.actor_id, KINDS.get(p.role, ActorKind.INTERCEPTOR))
        )
        for p in patrols
    )
    blockers = world.opaque_tiles if sound_blocking is None else sound_blocking
    spec = SecuritySpec(patrols, load_sensor_rules(), blockers)
    return Simulation(
        world, (ActorSpawn("operative", operative), *spawns), rules=rules, security=spec
    )


def intent(sim: Simulation, pending: list[Tile], *, sprint: bool = True) -> tuple[Action, ...]:
    """One operative MOVE toward the next waypoint, consuming reached waypoints."""
    position = sim.observe("operative").own_status.position
    assert position is not None
    while pending:
        target = tile_center(pending[0])
        dx, dy = target[0] - position[0], target[1] - position[1]
        if max(abs(dx), abs(dy)) <= 3_000:
            pending.pop(0)
            continue
        direction = ((dx > 0) - (dx < 0), 0) if abs(dx) > 3_000 else (0, (dy > 0) - (dy < 0))
        return (Action("operative", ActionKind.MOVE, sim.tick, direction, sprint=sprint),)
    return ()


def walk(sim: Simulation, path: list[Tile], ticks: int) -> Counter[str]:
    counts: Counter[str] = Counter()
    pending = list(path)
    for _ in range(ticks):
        result = sim.step(intent(sim, pending))
        counts.update(event.kind.value for event in result.events)
        if result.mission_end is not None:
            break
    return counts


def hide_fixture(rules: GameRules, patrol: GuardPatrol) -> Simulation:
    desk = frozenset({(4, 3), (5, 3), (6, 3)})
    world = StaticMap("hide", 12, 14, desk, desk, crouch_tiles=frozenset({(5, 3)}))
    sim = secured(world, rules, (5, 4), patrol)
    sim.step((Action("operative", ActionKind.CROUCH, 0),))
    return sim


def creep_into_cover(sim: Simulation, ticks: int) -> tuple[Counter[str], set[Tile]]:
    counts: Counter[str] = Counter()
    guard_tiles: set[Tile] = set()
    for _ in range(ticks):
        own = sim.observe("operative").own_status
        assert own.position is not None
        deeper = not own.concealed or own.position[1] > 3 * 30_000 + 15_000
        action = (Action("operative", ActionKind.MOVE, sim.tick, (0, -1)),) if deeper else ()
        result = sim.step(action)
        counts.update(event.kind.value for event in result.events)
        guard_tiles.add(sim.observe("guard").own_status.tile)
        if result.mission_end is not None:
            break
    return counts, guard_tiles


@pytest.mark.parametrize("role", [GuardRole.SENTINEL, GuardRole.TRACKER])
def test_witnessed_hide_is_inspected_but_unseen_entry_stays_hidden(
    rules: GameRules, role: GuardRole
) -> None:
    witnessed = hide_fixture(rules, GuardPatrol("guard", ((5, 11), (5, 10)), role))
    counts, _ = creep_into_cover(witnessed, 400)
    assert counts["HIDE_WITNESSED"] == 1 and counts["CAPTURE_COMPLETED"] == 1
    assert witnessed.presentation_snapshot().mission_end is not None

    unseen = hide_fixture(rules, GuardPatrol("guard", ((10, 12), (10, 4), (5, 4)), role))
    counts, passed = creep_into_cover(unseen, 600)
    assert (5, 4) in passed  # the guard patrolled right beside the cover
    assert unseen.observe("operative").own_status.concealed
    assert counts["HIDE_WITNESSED"] == counts["CAPTURE_STARTED"] == 0
    assert counts["SIGHTING_CONFIRMED"] == 0
    assert not unseen.observe("guard").visible_entities


def test_t03_loud_noise_behind_opaque_wall_investigates_origin_without_identity(
    rules: GameRules,
) -> None:
    # The partition is opaque but authored as acoustically open, like thin lab walls.
    wall = frozenset((6, y) for y in range(1, 9))
    world = bordered(12, 10, wall)
    patrol = GuardPatrol("guard", ((3, 4), (3, 6)))
    sim = secured(world, rules, (8, 4), patrol, sound_blocking=world.opaque_tiles - wall)
    result = sim.step((Action("operative", ActionKind.EMP, 0),))
    assert any(event.kind == EventKind.NOISE_CREATED for event in result.events)
    heard = sim.observe("guard")
    assert not heard.visible_entities and heard.heard_events[0].tile == (8, 4)
    sim.step()
    view = sim.presentation_snapshot().guards[0]
    assert view.state == GuardState.INVESTIGATE and view.target == (8, 4)
    assert view.evidence_kind == "NOISE" and view.evidence_tick == 1
    assert view.last_seen_tile is None and view.identification_ticks == 0
    assert not sim.observe("guard").shared_reports  # sound never becomes a sighting report


def tracker_corridor(rules: GameRules) -> Simulation:
    walls = frozenset((9, y) for y in range(1, 7)) | frozenset((11, y) for y in range(2, 9))
    return secured(
        bordered(16, 10, walls),
        rules,
        (6, 4),
        GuardPatrol("tracker", ((2, 4), (3, 4)), GuardRole.TRACKER),
    )


def test_t04_tracker_searches_last_seen_then_expires_without_tracking_hidden_moves(
    rules: GameRules,
) -> None:
    first, second = tracker_corridor(rules), tracker_corridor(rules)
    for sim in (first, second):
        for _ in range(25):
            sim.step()
        assert sim.presentation_snapshot().guards[0].state == GuardState.CHASE
    escape = [(6, 7), (10, 7), (10, 1), (13, 1)]
    routes = [[*escape, (13, 8)], [*escape, (13, 4)]]  # different hidden destinations
    states: list[GuardState] = []
    algorithms: set[object] = set()
    compared = 0
    for _ in range(420):
        events = (
            *first.step(intent(first, routes[0])).events,
            *second.step(intent(second, routes[1])).events,
        )
        view = first.presentation_snapshot().guards[0]
        if not states or states[-1] != view.state:
            states.append(view.state)
        if view.state != GuardState.CHASE:
            # After contact breaks, hidden operative moves differ; Tracker knowledge cannot.
            assert first.observe("tracker") == second.observe("tracker")
            assert view == second.presentation_snapshot().guards[0]
            compared += 1
        if view.state == GuardState.SEARCH:
            last = view.last_seen_tile
            assert last is not None and view.search_tiles
            assert all(abs(x - last[0]) + abs(y - last[1]) <= 2 for x, y in view.search_tiles)
        algorithms.update(
            dict(event.details).get("algorithm")
            for event in events
            if event.kind == EventKind.POLICY_DECISION
        )
    assert compared > 150
    first_own, second_own = (sim.observe("operative").own_status.tile for sim in (first, second))
    assert first_own == (13, 8) and second_own == (13, 4)
    assert GuardState.SEARCH in states and states[-1] in (GuardState.RETURN, GuardState.PATROL)
    assert algorithms == {"A*"}
    assert first.fingerprint() != second.fingerprint()


def test_sentinel_report_reaches_tracker_with_original_tick_only(rules: GameRules) -> None:
    sim = secured(
        bordered(30, 10),
        rules,
        (6, 4),
        GuardPatrol("sentinel", ((3, 4), (4, 4))),
        GuardPatrol("tracker", ((26, 8), (27, 8)), GuardRole.TRACKER),
    )
    sent = None
    for _ in range(40):
        for event in sim.step().events:
            if event.kind == EventKind.REPORT_SENT and sent is None:
                sent = dict(event.details)
    assert sent is not None
    tracker = next(
        view for view in sim.presentation_snapshot().guards if view.actor_id == "tracker"
    )
    assert tracker.evidence_kind == "REPORT" and tracker.state == GuardState.INVESTIGATE
    assert tracker.evidence_tick <= sim.tick - 1 and tracker.last_seen_tile is None
    assert tracker.identification_ticks == 0  # a radio lead never confirms identity
    report = sim.observe("tracker").shared_reports[0]
    assert report.source_guard == "sentinel" and report.tick == tracker.evidence_tick


def test_sensing_post_needs_current_sight_to_capture(rules: GameRules) -> None:
    post = GuardPatrol("post", ((5, 4), (6, 4)), GuardRole.POST)  # faces east
    behind = secured(bordered(12, 10), rules, (4, 4), post, kinds={"post": ActorKind.INTERCEPTOR})
    counts = walk(behind, [], 60)
    assert counts["CAPTURE_STARTED"] == 0 and behind.presentation_snapshot().mission_end is None
    ahead = secured(bordered(12, 10), rules, (6, 4), post, kinds={"post": ActorKind.INTERCEPTOR})
    counts = walk(ahead, [], 60)
    assert counts["CAPTURE_STARTED"] == 1
    view = ahead.presentation_snapshot().guards
    assert view[0].algorithm == "NONE" and view[0].state == GuardState.PATROL


def test_geometry_revision_replans_and_refuses_to_enclose_actors(rules: GameRules) -> None:
    sim = secured(
        bordered(14, 9),
        rules,
        (12, 7),
        GuardPatrol("tracker", ((2, 2), (11, 2)), GuardRole.TRACKER),
    )
    for _ in range(3):
        sim.step()
    assert sim.presentation_snapshot().guards[0].path[-1] == (11, 2)
    base = sim.observe("tracker").map_static
    barrier = frozenset((7, y) for y in range(1, 5))
    revised = StaticMap(
        base.map_id,
        base.width,
        base.height,
        base.blocked_tiles | barrier,
        base.opaque_tiles | barrier,
    )
    with pytest.raises(ValueError):
        sim.request_geometry_revision(
            StaticMap(base.map_id, base.width, base.height, base.blocked_tiles | {(12, 7)}),
            "enclose",
        )
    sim.request_geometry_revision(revised, "test barrier")
    result = sim.step()
    assert any(
        event.kind == EventKind.GEOMETRY_REVISED and dict(event.details)["revision"] == 1
        for event in result.events
    )
    sim.step()
    observation = sim.observe("tracker")
    assert observation.geometry_revision == 1 and observation.map_static.can_walk((7, 2)) is False
    path = sim.presentation_snapshot().guards[0].path
    assert path and not barrier & set(path)
    assert path[-1] == (11, 2) and (7, 5) in path
