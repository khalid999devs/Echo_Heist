"""Space-time A*: the next seconds of moves and waits that stay out of sight.

The search runs over (tile, step) states, a step being a fifth of a second.
From each state the Companion may wait one step, walk to a neighbouring tile
(two steps), sprint there (one step, while it has breath, at an extra price
because running is loud) or take a stair. A move that ends where foresight
says a guard may be looking is not forbidden but costs a large penalty, so a
plan always exists and the least exposed one wins when no clean one does.
Exposure further ahead weighs less, because the plan is redone long before
then with fresher sightings. A sprint within earshot of a guard counts as
exposed. A state at the horizon finishes with its remaining walking time to
the goal, so the plan that makes the most safe progress in the time it can
foresee wins. Slipping into reachable cover is another finishing move: it
costs time but no exposure. The goal may ask for a quiet moment on arrival,
such as the time needed to lift the Core.
"""

import heapq
from collections.abc import Callable, Collection, Iterable, Mapping
from dataclasses import dataclass

from echo_heist.core.contracts.world import StaticMap, Tile

type Check = Callable[[Tile, int], bool]
type Node = tuple[Tile, int]

MAX_EXPANSIONS = 9000
WALK_STEPS = 2
SPRINT_STEPS = 1
STAIR_STEPS = 4
SURE_STEPS = 10  # exposure this close ahead costs in full
FAR_WEIGHT = 0.35  # exposure at the horizon costs this share


@dataclass(frozen=True, slots=True)
class Plan:
    tiles: tuple[Tile, ...]  # the tiles visited, starting with the current one
    steps: tuple[int, ...]  # the step at which each of those tiles is reached
    sprints: tuple[bool, ...]  # whether each move after the first tile is run
    finished: bool  # reaches the goal and its quiet moment
    hide: Tile | None  # an approach tile from which to slip into cover at the end
    exposed_steps: int
    cost: float
    expanded: int

    def next_tile(self) -> Tile | None:
        """The first tile to move to, or None while the plan starts by waiting."""
        if len(self.tiles) < 2 or self.tiles[1] == self.tiles[0]:
            return None
        return self.tiles[1]

    def runs_next(self) -> bool:
        return bool(self.sprints) and self.sprints[0]


@dataclass(frozen=True, slots=True)
class Pace:
    """How the Companion may move during this plan."""

    exposure_cost: float
    sprint_cost: float  # extra price of one running step
    breath: int  # steps it can still run from now


def distance_field(
    world_map: StaticMap,
    goals: Iterable[Tile],
    extra: Mapping[Tile, int] | None = None,
    closed: Collection[tuple[Tile, Tile]] = (),
) -> dict[Tile, int]:
    """Walking cost from every reachable tile to the nearest goal tile.

    Each tile costs one, plus any ``extra`` price for entering it (Dijkstra).
    ``closed`` stair crossings are left out.
    """
    found: dict[Tile, int] = {}
    heap: list[tuple[int, Tile]] = []
    for goal in goals:
        if world_map.can_walk(goal) and goal not in found:
            found[goal] = 0
            heap.append((0, goal))
    heapq.heapify(heap)
    extra = extra or {}
    while heap:
        cost, tile = heapq.heappop(heap)
        if cost > found[tile]:
            continue
        for nxt in world_map.connections(tile):
            if not world_map.can_walk(nxt) or (nxt, tile) in closed:
                continue
            value = cost + 1 + extra.get(nxt, 0)
            if value < found.get(nxt, value + 1):
                found[nxt] = value
                heapq.heappush(heap, (value, nxt))
    return found


def plan(
    world_map: StaticMap,
    start: Tile,
    field: Mapping[Tile, int],
    exposed: Check,
    loud: Check,
    pace: Pace,
    *,
    horizon: int,
    finish: Check,
    covers: Collection[Tile] = (),
    hide_cost: float = 20.0,
    blocked: Collection[Tile] = (),
    closed: Collection[tuple[Tile, Tile]] = (),
) -> Plan:
    """Best receding-horizon plan from ``start`` toward ``field``'s goals."""
    far = max(field.values(), default=0) + 1

    def remaining(tile: Tile) -> float:
        return float(field.get(tile, far) * WALK_STEPS)

    def penalty(step: int) -> float:
        if step <= SURE_STEPS:
            return pace.exposure_cost
        share = (step - SURE_STEPS) / max(1, horizon - SURE_STEPS)
        return pace.exposure_cost * (1.0 - (1.0 - FAR_WEIGHT) * min(1.0, share))

    counter = 0
    heap: list[tuple[float, int, int, Tile, int, float, int, str]] = []
    parents: dict[Node, tuple[Node, bool] | None] = {(start, 0): None}
    costs: dict[Node, float] = {(start, 0): 0.0}
    hits: dict[Node, int] = {(start, 0): 0}
    heapq.heappush(heap, (remaining(start), 0, counter, start, 0, 0.0, 0, "state"))
    expanded = 0
    best: tuple[float, int, Tile] | None = None
    while heap:
        _, _, _, tile, step, cost, hit, kind = heapq.heappop(heap)
        if kind != "state":
            return _plan(parents, tile, step, kind, hit, cost, expanded)
        if cost > costs.get((tile, step), float("inf")):
            continue
        expanded += 1
        if best is None or (remaining(tile) + cost, -step) < (best[0], best[1]):
            best = (remaining(tile) + cost, -step, tile)
        if finish(tile, step):
            return _plan(parents, tile, step, "finish", hit, cost, expanded)
        if expanded >= MAX_EXPANSIONS:
            break
        if step >= horizon:
            counter += 1
            total = cost + remaining(tile)
            heapq.heappush(heap, (total, -step, counter, tile, step, cost, hit, "horizon"))
            continue
        if tile in covers and not exposed(tile, step):
            counter += 1
            total = cost + hide_cost + remaining(tile)
            heapq.heappush(heap, (total, -step, counter, tile, step, total, hit, "hide"))
        moves: list[tuple[Tile, int, bool]] = [(tile, 1, False)]
        for nxt in world_map.connections(tile):
            if not world_map.can_walk(nxt) or nxt in blocked or (tile, nxt) in closed:
                continue
            if abs(nxt[0] - tile[0]) + abs(nxt[1] - tile[1]) > 1:
                moves.append((nxt, STAIR_STEPS, False))
                continue
            moves.append((nxt, WALK_STEPS, False))
            if step < pace.breath:
                moves.append((nxt, SPRINT_STEPS, True))
        for nxt, duration, run in moves:
            later = step + duration
            seen = any(exposed(nxt, at) for at in range(step + 1, later + 1))
            if run and not seen:
                seen = loud(nxt, later)
            total = (
                cost
                + duration
                + (pace.sprint_cost if run else 0.0)
                + (penalty(later) if seen else 0.0)
            )
            key = (nxt, later)
            if total >= costs.get(key, float("inf")):
                continue
            costs[key], parents[key], hits[key] = total, ((tile, step), run), hit + seen
            counter += 1
            estimate = total + remaining(nxt)
            heapq.heappush(
                heap, (estimate, -later, counter, nxt, later, total, hit + seen, "state")
            )
    assert best is not None
    _, negative, tile = best
    node = (tile, -negative)
    return _plan(parents, tile, node[1], "horizon", hits[node], costs[node], expanded)


def _plan(
    parents: Mapping[Node, tuple[Node, bool] | None],
    tile: Tile,
    step: int,
    kind: str,
    hits: int,
    cost: float,
    expanded: int,
) -> Plan:
    tiles: list[Tile] = []
    steps: list[int] = []
    sprints: list[bool] = []
    node: Node | None = (tile, step)
    while node is not None:
        tiles.append(node[0])
        steps.append(node[1])
        link = parents[node]
        if link is None:
            break
        node, run = link
        sprints.append(run)
    tiles.reverse()
    steps.reverse()
    sprints.reverse()
    return Plan(
        tuple(tiles),
        tuple(steps),
        tuple(sprints),
        kind == "finish",
        tile if kind == "hide" else None,
        hits,
        cost,
        expanded,
    )
