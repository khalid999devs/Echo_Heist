"""Space-time A*: wait out a watched tile, run a closing gap, hide when cornered."""

from echo_heist.ai.companion.spacetime.planner import Pace, distance_field, plan
from echo_heist.core.contracts.world import StairLink, StaticMap, Tile

# One open row of floor, ten tiles long, walled above and below.
ROW = StaticMap(
    "row",
    10,
    3,
    blocked_tiles=frozenset({(x, y) for x in range(10) for y in (0, 2)}),
    opaque_tiles=frozenset({(x, y) for x in range(10) for y in (0, 2)}),
)
WALK = Pace(exposure_cost=60.0, sprint_cost=3.0, breath=0)


def never(tile: Tile, step: int) -> bool:
    return False


def arrives(goal: Tile) -> object:
    return lambda tile, step: tile == goal


def test_a_clear_way_is_walked_straight_to_the_goal() -> None:
    field = distance_field(ROW, [(6, 1)])
    route = plan(ROW, (1, 1), field, never, never, WALK, horizon=30, finish=arrives((6, 1)))
    assert route.finished and route.exposed_steps == 0
    assert route.tiles == ((1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1))
    assert route.steps == (0, 2, 4, 6, 8, 10) and route.next_tile() == (2, 1)


def test_a_watched_tile_is_crossed_only_once_the_view_has_passed() -> None:
    def watched(tile: Tile, step: int) -> bool:
        return tile == (3, 1) and step <= 9

    field = distance_field(ROW, [(6, 1)])
    route = plan(ROW, (1, 1), field, watched, never, WALK, horizon=30, finish=arrives((6, 1)))
    assert route.finished and route.exposed_steps == 0
    crossing = route.steps[route.tiles.index((3, 1))]
    assert crossing > 9


def test_running_beats_a_closing_gap_that_walking_would_miss() -> None:
    def closing(tile: Tile, step: int) -> bool:
        return tile == (3, 1) and step >= 3

    field = distance_field(ROW, [(3, 1)])
    walking = plan(ROW, (1, 1), field, closing, never, WALK, horizon=6, finish=arrives((3, 1)))
    assert not walking.finished  # four steps on foot: the view closes first
    running = Pace(exposure_cost=60.0, sprint_cost=0.5, breath=10)
    route = plan(ROW, (1, 1), field, closing, never, running, horizon=6, finish=arrives((3, 1)))
    assert route.finished and route.exposed_steps == 0 and all(route.sprints)


def test_a_sprint_a_guard_would_hear_counts_as_being_seen() -> None:
    def closing(tile: Tile, step: int) -> bool:
        return tile == (3, 1) and step >= 3

    def heard(tile: Tile, step: int) -> bool:
        return True

    running = Pace(exposure_cost=60.0, sprint_cost=0.5, breath=10)
    field = distance_field(ROW, [(3, 1)])
    route = plan(ROW, (1, 1), field, closing, heard, running, horizon=6, finish=arrives((3, 1)))
    assert not any(route.sprints) or route.exposed_steps > 0


def test_cornered_it_slips_into_cover_instead_of_waiting_in_view() -> None:
    def everywhere(tile: Tile, step: int) -> bool:
        return step >= 2

    field = distance_field(ROW, [(8, 1)])
    route = plan(
        ROW,
        (1, 1),
        field,
        everywhere,
        never,
        WALK,
        horizon=12,
        finish=arrives((8, 1)),
        covers={(1, 1)},
    )
    assert route.hide == (1, 1) and route.tiles == ((1, 1),) and route.exposed_steps == 0


def test_a_stair_that_failed_is_left_out_of_routes_and_plans() -> None:
    link = StairLink("up", (1, 1), "down", (8, 1))
    back = StairLink("down", (8, 1), "up", (1, 1))
    wall = frozenset({(x, y) for x in range(10) for y in (0, 2)} | {(4, 1), (5, 1)})
    split = StaticMap("split", 10, 3, wall, wall, stairs=(link, back))
    assert distance_field(split, [(9, 1)])[(1, 1)] == 2
    closed = {((1, 1), (8, 1)), ((8, 1), (1, 1))}
    assert (1, 1) not in distance_field(split, [(9, 1)], closed=closed)
    route = plan(
        split,
        (1, 1),
        distance_field(split, [(9, 1)]),
        never,
        never,
        WALK,
        horizon=20,
        finish=arrives((9, 1)),
        closed=closed,
    )
    assert not route.finished and (8, 1) not in route.tiles


def test_extra_route_costs_bend_the_distance_field_around_a_held_post() -> None:
    open_floor = StaticMap("open", 7, 5)
    plain = distance_field(open_floor, [(6, 2)])
    held = distance_field(open_floor, [(6, 2)], extra={(3, 2): 12, (3, 1): 12, (3, 3): 12})
    assert plain[(0, 2)] == 6
    assert held[(0, 2)] == 10  # around through row 0 or 4 is cheaper than past the post
