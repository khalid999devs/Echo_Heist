"""A real Sentinel: BFS patrol, visual identification, cue investigation and finite search."""

from dataclasses import replace

from echo_heist.ai.guards.steering import (
    arrived,
    distance,
    evidence_expired,
    identify,
    investigate,
    phase_rules,
    steer,
    visible_intruder,
    witnessed_hide,
)
from echo_heist.ai.navigation.grid import bfs, neighbors
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.security.model import (
    GuardDecision,
    GuardMemory,
    GuardPatrol,
    GuardState,
    SensorRules,
)
from echo_heist.core.contracts.world import tile_center


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
        memory = identify(observation, rules, memory, intruder)
    else:
        memory = replace(memory, identity_ticks=max(0, memory.identity_ticks - 2))
        expired = (
            memory.last_seen_tick >= 0
            and observation.tick - memory.last_seen_tick > rules.memory_ticks
        )
        if memory.state in (GuardState.CHASE, GuardState.SEARCH) and expired:
            memory = _return(observation, patrol, memory)
        elif memory.state == GuardState.SPOTTED:
            memory = replace(memory, state=GuardState.INVESTIGATE, target=memory.last_seen_tile)
        elif memory.state == GuardState.INVESTIGATE and evidence_expired(
            observation, rules, memory
        ):
            # A cue is checked for a bounded time from its original tick; an
            # unreachable or stale origin cannot hold the guard forever.
            memory = _return(observation, patrol, memory)
        hidden = witnessed_hide(observation, memory)
        if memory.state == GuardState.CHASE and hidden is not None:
            memory = replace(memory, target=hidden)
        if memory.state not in (GuardState.CHASE, GuardState.SEARCH):
            memory = investigate(observation, rules, memory)
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
        and arrived(position, target)
        and intruder is None
    ):
        duration = round(rules.search_ticks * (0.5 + memory.urgency / 2))
        memory = replace(
            memory,
            state=GuardState.SEARCH,
            search_origin=target,
            search_index=0,
            search_until=observation.tick + duration,
        )
    elif memory.state == GuardState.RETURN and arrived(position, target):
        memory = replace(memory, state=GuardState.PATROL, last_seen_tile=None, last_seen_tick=-1)
    if memory.state == GuardState.SEARCH:
        if observation.tick >= memory.search_until:
            memory = _return(observation, patrol, memory)
            target = memory.target
        else:
            origin = memory.search_origin or own.tile
            options = tuple(
                tile for tile in neighbors(origin) if observation.map_static.can_walk(tile)
            )
            if options:
                index = memory.search_index + int(arrived(position, target))
                target = options[index % len(options)]
                memory = replace(memory, search_index=index, search_tiles=options)
    return steer(observation, memory, target, bfs, intruder)
