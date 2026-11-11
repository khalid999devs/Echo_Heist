"""Team-wide detection encounters, owned by Simulation (SCORING.md).

An encounter starts when any guard actually confirms the real intruder while no
encounter is active, and counts once for the whole defender team. It stays
active while the newest confirmed sighting (by its original observation tick)
is fresher than the sensing memory TTL, or while any grab is in progress. Other
guards, relayed reports, stun/EMP and repeated sight ticks never add a count;
hearing, partial suspicion, Echo motion and unwitnessed cover never start one.
"""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(slots=True)
class EncounterState:
    active: bool = False
    count: int = 0
    # Original observation tick of the newest confirmed sighting (or grab start).
    last_confirmed_tick: int = -1
    started_tick: int = -1
    # Raw confirmations (guard-ticks) for analysis only; never scored.
    raw_confirmations: int = 0


def update(
    state: EncounterState,
    tick: int,
    confirmations: Iterable[int],
    *,
    grab_active: bool,
    ttl_ticks: int,
) -> bool:
    """Apply this tick's confirmed sightings; return True when a new encounter starts."""
    observed = [value for value in confirmations if 0 <= value <= tick]
    state.raw_confirmations += len(observed)
    if observed:
        state.last_confirmed_tick = max(state.last_confirmed_tick, *observed)
        if not state.active:
            state.active, state.started_tick = True, max(observed)
            state.count += 1
            return True
        return False
    if state.active and not grab_active and tick - state.last_confirmed_tick > ttl_ticks:
        state.active = False
    return False
