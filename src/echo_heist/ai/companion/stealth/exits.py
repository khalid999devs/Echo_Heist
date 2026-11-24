"""Exit choice by risk: distance, observed danger and the way already travelled.

The Companion remembers every tile it has walked this mission. A route it has
already crossed is evidence of a survivable path, while unexplored floor is an
open question, so each exit's A* path pays one per step, the observed danger
from recent sightings, a cost for standing bodies and jammed gates, and an
extra cost on every tile it has never walked. Everything here comes from its
own observations; it never reads where a guard really is.
"""

from collections.abc import Collection, Mapping

from echo_heist.ai.navigation.astar import astar
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.world import Tile

BODY_COST = 60
JAM_COST = 400
UNKNOWN_COST = 1  # an unexplored tile costs twice a walked one
EXIT_SWITCH_COST = 40  # A* cost an alternative exit must save to win
EXIT_COMMIT_TICKS = 180


def choose_exit(
    observation: Observation,
    exits: tuple[Tile, ...],
    danger: Mapping[Tile, int],
    risk_weight: int,
    bodies: Collection[Tile],
    jammed: Mapping[Tile, int],
    visited: Collection[Tile],
    current: Tile,
    locked_until: int,
) -> tuple[Tile, int]:
    """The exit to head for and the tick until which that choice is held."""
    if len(exits) < 2:
        return current, locked_until
    tick = observation.tick
    blocked = {tile for tile, until in jammed.items() if until > tick}

    def penalty(tile: Tile) -> int:
        return (
            risk_weight * danger.get(tile, 0) // 2
            + (BODY_COST if tile in bodies else 0)
            + (JAM_COST if tile in blocked else 0)
            + (0 if tile in visited else UNKNOWN_COST)
        )

    options = []
    for tile in exits:
        path = astar(observation.map_static, observation.own_status.tile, tile, penalty=penalty)
        if path.path:
            # Switching exits turns the escape around; demand a clear gain.
            options.append((path.cost + (EXIT_SWITCH_COST if tile != current else 0), tile))
    known = any(tile == current for _, tile in options)
    if not options or (known and tick < locked_until):
        return current, locked_until
    choice = min(options)[1]
    # Commit: re-deciding every search bounced between the two escapes.
    return choice, (tick + EXIT_COMMIT_TICKS if choice != current else locked_until)
