"""Foresight learns guard beats from sightings alone and predicts their view."""

from echo_heist.ai.companion.spacetime.foresight import HORIZON_STEPS, Foresight
from echo_heist.core.contracts.observations import EntityView, Observation, OwnStatus
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import (
    ActorKind,
    Inventory,
    MissionPhase,
    StaticMap,
    Tile,
    tile_center,
)

# A corridor along row 4 with a side corridor north at x=4 and south at x=8.
FLOOR = (
    {(x, 4) for x in range(1, 11)} | {(4, y) for y in range(1, 4)} | {(8, y) for y in range(5, 8)}
)
WALLS = frozenset((x, y) for x in range(12) for y in range(9)) - FLOOR
HALL = StaticMap("hall", 12, 9, WALLS, WALLS)
SPEED = UNIT * 6 // 100  # a Sentinel's walk: 0.06 tiles per tick
DEEP_SOUTH = (8, 7)
DEEP_NORTH = (4, 1)


def look(tick: int, guard: EntityView | None, me: Tile = (1, 1)) -> Observation:
    own = OwnStatus(me, Inventory(), position=tile_center(me))
    seen = (guard,) if guard is not None else ()
    return Observation("echo-companion", tick, HALL, MissionPhase.INFILTRATE, own, seen)


def guard_at(x: int, y: int, facing: Tile, alert: str = "PATROL") -> EntityView:
    return EntityView(
        "guard-a", ActorKind.SENTINEL, (x // UNIT, y // UNIT), (x, y), facing=facing, alert=alert
    )


def walk_east(
    eyes: Foresight,
    tick: int,
    start: int,
    end: int,
    *,
    pause_at: int | None = None,
    turn: Tile = (0, 1),
) -> int:
    """Feed sightings of the guard walking east along row 4, maybe pausing."""
    x, y = tile_center((start, 4))
    goal = tile_center((end, 4))[0]
    stop = tile_center((pause_at, 4))[0] if pause_at is not None else None
    while x < goal:
        eyes.observe(look(tick, guard_at(x, y, (1, 0))))
        tick += 1
        if stop is not None and x < stop <= x + SPEED:
            x = stop
            for _ in range(15):  # it pauses already facing the way it will leave
                eyes.observe(look(tick, guard_at(x, y, turn)))
                tick += 1
            return tick
        x += SPEED
    return tick


def ever_seen(eyes: Foresight, tick: int, tile: Tile) -> bool:
    eyes.refresh(tick)
    return any(eyes.exposed(tile, step) for step in range(HORIZON_STEPS + 1))


def test_a_pausing_guard_teaches_the_turn_it_will_take() -> None:
    eyes = Foresight(8, 56)
    walk_east(eyes, 100, 1, 9, pause_at=8)
    track = eyes.tracks["guard-a"]
    assert track.turns[((8, 4), (1, 0))] == (0, 1)
    assert (4, 4) not in {tile for tile, _ in track.turns}  # walked straight through


def test_an_unseen_junction_may_be_a_turn_but_a_walked_one_is_not() -> None:
    fresh = Foresight(8, 56)
    tick = walk_east(fresh, 100, 1, 2)
    assert ever_seen(fresh, tick, DEEP_SOUTH)  # it may turn south at x=8
    learned = Foresight(8, 56)
    tick = walk_east(learned, 100, 1, 10)  # it walked past both side corridors
    tick = walk_east(learned, tick + 300, 1, 2)
    assert not ever_seen(learned, tick, DEEP_SOUTH)
    assert not ever_seen(learned, tick, DEEP_NORTH)


def test_a_learned_turn_is_foreseen_after_the_guard_reaches_it() -> None:
    eyes = Foresight(8, 56)
    tick = walk_east(eyes, 100, 1, 9, pause_at=8)
    tick = walk_east(eyes, tick + 300, 1, 2)
    eyes.refresh(tick)
    soon = [eyes.exposed(DEEP_SOUTH, step) for step in range(HORIZON_STEPS + 1)]
    assert not soon[0] and any(soon)  # unseen now, watched once it has turned


def test_a_place_seen_empty_rules_out_a_remembered_guard_being_there() -> None:
    eyes = Foresight(8, 56)
    tick = walk_east(eyes, 100, 1, 2)
    eyes.refresh(tick + 1)
    assert eyes.exposed((6, 4), 1)
    # Later the Companion looks down the corridor and nobody is where it would be.
    eyes.observe(look(tick + 30, None, me=(9, 4)))
    eyes.refresh(tick + 30)
    assert not any(eyes.exposed((6, 4), step) for step in range(4))


def test_a_searching_guard_may_look_any_way() -> None:
    eyes = Foresight(8, 56)
    x, y = tile_center((6, 4))
    eyes.observe(look(100, guard_at(x, y, (-1, 0), alert="SEARCH")))
    eyes.refresh(100)
    assert eyes.exposed((9, 4), 0)  # behind it, yet in view of a searching guard
    calm = Foresight(8, 56)
    calm.observe(look(100, guard_at(x, y, (-1, 0))))
    calm.refresh(100)
    assert not calm.exposed((9, 4), 0)


def test_hunting_and_posted_guards_are_routed_around() -> None:
    eyes = Foresight(8, 56)
    x, y = tile_center((6, 4))
    for tick in range(100, 160):
        eyes.observe(look(tick, guard_at(x, y, (-1, 0), alert="INVESTIGATE")))
    assert eyes.blockers(160) == ((6, 4),)
    detour = eyes.detour(160)
    assert detour[(6, 4)] > detour[(9, 4)] > 0 and (1, 1) not in detour
