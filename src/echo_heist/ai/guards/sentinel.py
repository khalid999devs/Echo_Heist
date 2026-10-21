"""A real Sentinel: BFS patrol, visual identification, cue investigation and finite search."""

from dataclasses import replace

from echo_heist.ai.guards.fuzzy import investigate_urgency
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
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import ActorKind, Tile, tile_center


def distance(first: Tile, second: Tile) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


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

    def arrived(tile: Tile | None) -> bool:
        return (
            tile is not None
            and max(abs(a - b) for a, b in zip(position, tile_center(tile), strict=True))
            <= UNIT // 10
        )

    wait = Action(observation.agent_id, ActionKind.WAIT, observation.tick)
    if own.disabled or own.stunned:
        return GuardDecision(wait, replace(memory, identity_ticks=0), own.facing)
    intruder = next(
        (
            entity
            for entity in observation.visible_entities
            if entity.kind in (ActorKind.OPERATIVE, ActorKind.COMPANION)
        ),
        None,
    )
    if intruder is not None:
        near = distance(own.tile, intruder.tile) <= 1
        threshold = rules.near_identification_ticks if near else rules.identification_ticks
        identity = min(rules.identification_ticks, memory.identity_ticks + 1)
        remembered = (
            memory.state == GuardState.CHASE
            and observation.tick - memory.last_seen_tick <= rules.memory_ticks
        )
        confirmed = remembered or identity >= threshold
        memory = replace(
            memory,
            state=GuardState.CHASE if confirmed else GuardState.SPOTTED,
            identity_ticks=rules.identification_ticks if confirmed else identity,
            last_seen_tile=intruder.tile,
            last_seen_tick=observation.tick,
            target=intruder.tile,
            wait_until=0,
        )
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
        if memory.state not in (GuardState.CHASE, GuardState.SEARCH):
            cue_tile: Tile | None = None
            salience, visibility = 0.0, 0.0
            if observation.heard_events:
                heard = max(observation.heard_events, key=lambda cue: (cue.tick, cue.event_id))
                cue_tile = heard.tile
                salience = {"FOOTSTEP": 0.25, "SPRINT": 0.75, "EMP": 1.0, "MELEE": 1.0}.get(
                    heard.kind, 0.5
                )
            elif observation.visual_cues:
                cue_tile = observation.visual_cues[-1].tile
                visibility = 0.5
            if cue_tile is not None:
                fuzzy = investigate_urgency(distance(own.tile, cue_tile), salience, visibility)
                memory = replace(
                    memory,
                    state=GuardState.INVESTIGATE,
                    target=cue_tile,
                    urgency=fuzzy.urgency,
                    search_until=observation.tick + rules.search_ticks,
                )
    target = memory.target
    if memory.state == GuardState.PATROL:
        target = patrol.points[memory.patrol_index]
        if arrived(target):
            index = (memory.patrol_index + 1) % len(patrol.points)
            target = patrol.points[index]
            memory = replace(
                memory, patrol_index=index, wait_until=observation.tick + rules.patrol_pause_ticks
            )
    elif (
        memory.state in (GuardState.CHASE, GuardState.INVESTIGATE)
        and arrived(target)
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
    elif memory.state == GuardState.RETURN and arrived(target):
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
                index = memory.search_index + int(arrived(target))
                target = options[index % len(options)]
                memory = replace(memory, search_index=index)
    memory = replace(memory, target=target)
    if target is None:
        return GuardDecision(wait, memory, own.facing)
    path = memory.path
    if target != memory.path_goal or (not path and not arrived(target)):
        result = bfs(observation.map_static, own.tile, target)
        path = result.path[1:]
        memory = replace(memory, expanded_nodes=result.expanded, path_goal=target)
        if not result.path:
            return GuardDecision(wait, replace(memory, path=()), own.facing)
    while path:
        point = tile_center(path[0])
        if max(abs(point[0] - position[0]), abs(point[1] - position[1])) > UNIT // 10:
            break
        path = path[1:]
    memory = replace(memory, path=path)
    point = tile_center(path[0] if path else target)
    dx, dy = point[0] - position[0], point[1] - position[1]
    direction = (
        ((1 if dx > 0 else -1), 0)
        if abs(dx) > UNIT // 10
        else (0, (1 if dy > 0 else -1))
        if abs(dy) > UNIT // 10
        else (0, 0)
    )
    facing = direction if direction != (0, 0) else own.facing
    if memory.state == GuardState.SPOTTED and intruder is not None:
        look = intruder.position or tile_center(intruder.tile)
        facing = (
            1 if look[0] > position[0] else -1 if look[0] < position[0] else 0,
            1 if look[1] > position[1] else -1 if look[1] < position[1] else 0,
        )
        facing = facing if facing != (0, 0) else own.facing
    if (
        observation.tick < memory.wait_until
        or memory.state == GuardState.SPOTTED
        or arrived(target)
    ):
        return GuardDecision(wait, memory, facing)
    return GuardDecision(
        Action(observation.agent_id, ActionKind.MOVE, observation.tick, direction), memory, facing
    )
