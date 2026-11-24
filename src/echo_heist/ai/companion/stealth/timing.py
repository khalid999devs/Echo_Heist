"""Patience near the Core: step into a guard's view only through a gap.

Inside the Core Chamber the Companion holds on an unseen tile while its next
step lies inside the observed cone of a guard it can currently see, or right
beside a guard it saw a moment ago, and moves once the way is clear. The cone
test is the belief check, the same cone and ray test the guards use, applied to
guards in the Companion's own view or memory, so it never reads hidden state.
Without the memory it would peek at a searching guard it can see from one tile
but not the next, stepping back and forth. A bounded wait and a rest afterwards
stop a guard that never turns away from stalling the run.

The same patience decides when to take the Core. Taking it starts a lockdown
in which every guard is faster, so a theft seen by a guard almost always ends
in capture. The Companion starts the hold only when no guard has had it in
view for a while, none can see it now and none stands close and facing it.
"""

from dataclasses import dataclass

from echo_heist.ai.companion.belief import Beliefs
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.world import ActorKind, Tile

PATIENT_PHASES = frozenset({"REACH_CORE", "TAKE_CORE"})
PATIENCE_TICKS = 75  # longest single hold, 2.5 seconds
REST_TICKS = 60  # after giving up, keep moving for 2 seconds before holding again
RECENT_TICKS = 30  # a guard seen within the last second is assumed to still be there
UNSEEN_TICKS = 45  # out of every cone for 1.5 seconds before the theft
FACING_TILES = 4  # a guard this close and facing the Companion will see the theft
GUARDS = frozenset({ActorKind.SENTINEL, ActorKind.TRACKER, ActorKind.INTERCEPTOR})


def theft_window(observation: Observation, beliefs: Beliefs, last_watched: int) -> bool:
    """True when taking the Core now is unlikely to be witnessed."""
    own = observation.own_status
    if observation.tick - last_watched <= UNSEEN_TICKS:
        return False
    if beliefs.watched_by(observation, own.tile) is not None:
        return False
    for guard in observation.visible_entities:
        if guard.kind not in GUARDS or guard.disabled or guard.stunned:
            continue
        dx, dy = own.tile[0] - guard.tile[0], own.tile[1] - guard.tile[1]
        reach = max(abs(dx), abs(dy))
        facing = dx * guard.facing[0] + dy * guard.facing[1] > 0
        if reach <= 1 or (reach <= FACING_TILES and facing):
            return False
    return True


def _beside_recent_guard(beliefs: Beliefs, tick: int, tile: Tile) -> bool:
    return any(
        not sighting.incapacitated
        and tick - sighting.tick <= RECENT_TICKS
        and max(abs(sighting.tile[0] - tile[0]), abs(sighting.tile[1] - tile[1])) <= 1
        for sighting in beliefs.sightings.values()
    )


@dataclass(slots=True)
class Patience:
    since: int = -1
    resume_at: int = 0

    def hold(self, observation: Observation, beliefs: Beliefs, step: Action, phase: str) -> bool:
        """True when the Companion should wait instead of taking ``step``."""
        own = observation.own_status
        tick = observation.tick
        if (
            phase not in PATIENT_PHASES
            or step.kind != ActionKind.MOVE
            or step.direction == (0, 0)
            or own.inventory.core_held
            or own.capture_ticks_remaining is not None
            or tick < self.resume_at
            or beliefs.watched_by(observation, own.tile) is not None  # already seen: keep going
        ):
            self.since = -1
            return False
        ahead = (own.tile[0] + step.direction[0], own.tile[1] + step.direction[1])
        if beliefs.watched_by(observation, ahead) is None and not _beside_recent_guard(
            beliefs, tick, ahead
        ):
            self.since = -1
            return False
        if self.since < 0:
            self.since = tick
        if tick - self.since >= PATIENCE_TICKS:
            self.since, self.resume_at = -1, tick + REST_TICKS
            return False
        return True
