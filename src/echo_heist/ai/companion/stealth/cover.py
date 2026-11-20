"""Find reachable cover using public floor geometry and the Companion's observations."""

from echo_heist.ai.companion.belief import Beliefs
from echo_heist.ai.companion.briefing import MissionBriefing
from echo_heist.ai.navigation.grid import distances_from, neighbors
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.world import Tile


def approaches(briefing: MissionBriefing, tile: Tile) -> tuple[Tile, ...]:
    if tile in briefing.locker_tiles:
        return neighbors(tile)
    return ((tile[0], tile[1] + 1),)


def safe_cover(
    observation: Observation,
    briefing: MissionBriefing,
    beliefs: Beliefs,
    *,
    max_steps: int = 6,
) -> tuple[Tile, Tile] | None:
    """Return the cover and its unwatched approach, with ties favoring lockers."""
    feet = observation.own_status.tile
    steps = distances_from(observation.map_static, feet, max_steps=max_steps)
    occupied = {entity.tile for entity in observation.visible_entities}
    choices = [
        (steps[approach], tile not in briefing.locker_tiles, tile, approach)
        for tile in (*briefing.locker_tiles, *briefing.hide_tiles)
        for approach in approaches(briefing, tile)
        if steps.get(approach, max_steps + 1) <= max_steps
        and approach not in occupied
        and tile not in occupied
        and beliefs.watched_by(observation, approach) is None
    ]
    closest = min(choices, default=None)
    return (closest[2], closest[3]) if closest is not None else None
