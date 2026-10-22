"""Tracker: heuristic A* pursuit, last-seen memory and plausible-neighbor search.

The Tracker chases only what it actually identifies. When sight breaks it plans
with A* to its own last-seen tile, inspects a few reachable neighbors ranked by
the motion it actually observed, then returns once memory expires. Radio
SIGHTING reports from other guards become investigation leads that keep their
reporter's original tick; they never confirm identity or reveal a new position.
"""

from collections import deque
from dataclasses import replace

from echo_heist.ai.guards.steering import (
    arrived,
    distance,
    evidence_expired,
    identify,
    investigate,
    phase_rules,
    steer,
    strongest_cue,
    visible_intruder,
    witnessed_hide,
)
from echo_heist.ai.navigation.astar import astar
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.events import SecurityReport
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.security.model import (
    GuardDecision,
    GuardMemory,
    GuardPatrol,
    GuardState,
    SensorRules,
)
from echo_heist.core.contracts.world import StaticMap, Tile, tile_center

SEARCH_RADIUS = 2
SEARCH_TILES = 4


def plausible_neighbors(world_map: StaticMap, origin: Tile, heading: Tile) -> tuple[Tile, ...]:
    """Reachable tiles near the last sighting, most consistent with observed motion first.

    Uses only static geometry and the guard's own remembered heading; walls are
    respected by walking the legal graph rather than taking a radius through them.
    """
    if not world_map.can_walk(origin):
        return ()
    found: dict[Tile, int] = {origin: 0}
    pending = deque([origin])
    while pending:
        tile = pending.popleft()
        if found[tile] == SEARCH_RADIUS:
            continue
        for neighbor in world_map.connections(tile):
            if neighbor not in found and world_map.can_walk(neighbor):
                found[neighbor] = found[tile] + 1
                pending.append(neighbor)
    candidates = [tile for tile in found if tile != origin]
    candidates.sort(
        key=lambda tile: (
            -((tile[0] - origin[0]) * heading[0] + (tile[1] - origin[1]) * heading[1]),
            found[tile],
            tile,
        )
    )
    return tuple(candidates[:SEARCH_TILES])


def report_lead(observation: Observation, memory: GuardMemory) -> SecurityReport | None:
    """Newest unexpired SIGHTING from another guard that is newer than current evidence."""
    leads = [
        report
        for report in observation.shared_reports
        if report.source_guard != observation.agent_id
        and report.report_kind == "SIGHTING"
        and observation.tick <= report.expires_at_tick
        and report.tick > max(memory.evidence_tick, memory.last_seen_tick)
    ]
    return max(leads, key=lambda report: (report.tick, report.event_id)) if leads else None


def _return(observation: Observation, patrol: GuardPatrol, memory: GuardMemory) -> GuardMemory:
    index = min(
        range(len(patrol.points)),
        key=lambda value: (distance(observation.own_status.tile, patrol.points[value]), value),
    )
    return replace(
        memory,
        state=GuardState.RETURN,
        target=patrol.points[index],
        patrol_index=index,
        identity_ticks=0,
        search_tiles=(),
    )


def _search(observation: Observation, rules: SensorRules, memory: GuardMemory) -> GuardMemory:
    origin = memory.target or observation.own_status.tile
    tiles = plausible_neighbors(observation.map_static, origin, memory.last_seen_heading)
    return replace(
        memory,
        state=GuardState.SEARCH,
        search_origin=origin,
        search_index=0,
        search_tiles=tiles,
        search_until=observation.tick + rules.search_ticks,
    )


def decide(
    observation: Observation, patrol: GuardPatrol, rules: SensorRules, memory: GuardMemory
) -> GuardDecision:
    own = observation.own_status
    position = own.position or tile_center(own.tile)
    wait = Action(observation.agent_id, ActionKind.WAIT, observation.tick)
    if own.stair_ticks_remaining:
        return GuardDecision(wait, memory, own.facing)
    rules = phase_rules(observation, rules)
    if own.disabled or own.stunned:
        return GuardDecision(wait, replace(memory, identity_ticks=0), own.facing)
    intruder = visible_intruder(observation)
    if intruder is not None:
        memory = replace(identify(observation, rules, memory, intruder), search_tiles=())
    else:
        memory = replace(memory, identity_ticks=max(0, memory.identity_ticks - 2))
        sight_expired = (
            memory.last_seen_tick >= 0
            and observation.tick - memory.last_seen_tick > rules.memory_ticks
        )
        if memory.state == GuardState.CHASE and sight_expired:
            memory = _return(observation, patrol, memory)
        elif memory.state == GuardState.SPOTTED:
            memory = replace(memory, state=GuardState.INVESTIGATE, target=memory.last_seen_tile)
        elif memory.state in (
            GuardState.INVESTIGATE,
            GuardState.SEARCH,
        ) and evidence_expired(observation, rules, memory):
            memory = _return(observation, patrol, memory)
        hidden = witnessed_hide(observation, memory)
        if memory.state == GuardState.CHASE and hidden is not None:
            memory = replace(memory, target=hidden)
        if memory.state != GuardState.CHASE:
            lead = report_lead(observation, memory)
            cue = strongest_cue(observation)
            if lead is not None and (cue is None or lead.tick >= cue.tick):
                memory = replace(
                    memory,
                    state=GuardState.INVESTIGATE,
                    target=lead.tile,
                    urgency=lead.confidence,
                    search_tiles=(),
                    evidence_kind="REPORT",
                    evidence_id=lead.event_id,
                    evidence_tick=lead.tick,
                )
            elif cue is not None and memory.state != GuardState.SEARCH:
                memory = replace(investigate(observation, rules, memory), search_tiles=())
    target = memory.target
    if memory.state == GuardState.PATROL:
        target = patrol.points[memory.patrol_index]
        if arrived(position, target):
            index = (memory.patrol_index + 1) % len(patrol.points)
            target = patrol.points[index]
            memory = replace(
                memory, patrol_index=index, wait_until=observation.tick + rules.patrol_pause_ticks
            )
    elif (
        memory.state in (GuardState.CHASE, GuardState.INVESTIGATE)
        and intruder is None
        and target is not None
        and (arrived(position, target) or (not memory.path and memory.path_goal == target))
    ):
        # Reached the last evidence (or its nearest legal edge): search nearby.
        memory = _search(observation, rules, memory)
    elif memory.state == GuardState.RETURN and arrived(position, target):
        memory = replace(
            memory,
            state=GuardState.PATROL,
            last_seen_tile=None,
            last_seen_tick=-1,
            last_seen_heading=(0, 0),
        )
    if memory.state == GuardState.SEARCH:
        index = memory.search_index
        if index < len(memory.search_tiles) and arrived(position, memory.search_tiles[index]):
            index += 1
        if observation.tick >= memory.search_until or index >= len(memory.search_tiles):
            memory = _return(observation, patrol, memory)
            target = memory.target
        else:
            memory = replace(memory, search_index=index)
            target = memory.search_tiles[index]
    return steer(observation, memory, target, astar, intruder)
