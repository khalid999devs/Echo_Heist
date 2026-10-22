"""Seen versus unseen hiding over the existing posture/under-desk clearance contract.

Concealment is authoritative posture plus authored clearance, never an art or
render effect. A guard that saw the entry receives a cue naming that cover and
may inspect it from an adjacent tile; nobody else can see the hidden actor.
"""

from echo_heist.core.contracts.security.model import VisualCue
from echo_heist.core.contracts.world import StaticMap, Tile

HIDE_ENTRY = "HIDE_ENTRY"


def is_concealed(world_map: StaticMap, tile: Tile, crouched: bool) -> bool:
    return crouched and tile in world_map.crouch_tiles


def witnessed_entry(guard_id: str, cover: Tile, tick: int) -> VisualCue:
    return VisualCue(f"hide:{guard_id}:{tick}", cover, tick, HIDE_ENTRY)


def inspection_reveals(
    guard_tile: Tile, cover: Tile, witnesses: tuple[VisualCue, ...], tick: int, ttl: int
) -> bool:
    """Only a still-valid witnessed entry lets a guard inspect that exact cover."""
    adjacent = abs(guard_tile[0] - cover[0]) + abs(guard_tile[1] - cover[1]) <= 1
    return adjacent and any(
        cue.kind == HIDE_ENTRY and cue.tile == cover and tick - cue.tick <= ttl for cue in witnesses
    )
