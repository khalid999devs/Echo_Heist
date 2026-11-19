"""Interceptor: bounded minimax/alpha-beta over chokepoint posts and route hypotheses.

On a meaningful new report (a radio SIGHTING, a NEXUS INTERCEPT order such as
the public Core alarm, or its own lost sighting) it infers two or three
plausible intruder routes from that evidence's tile and original tick to the
current mission goal, searches post choices against them, then physically walks
to the chosen chokepoint with A*. Hypotheses are an estimated distribution over
the static route graph; the real intruder position or future input is never
read. A wrong hypothesis sends it to the wrong post.
"""

from dataclasses import dataclass, replace

from echo_heist.ai.guards.steering import (
    DISPATCH,
    arrived,
    distance,
    identify,
    phase_rules,
    steer,
    visible_intruder,
)
from echo_heist.ai.navigation.astar import astar
from echo_heist.ai.navigation.grid import distances_from
from echo_heist.ai.navigation.routes import ZoneRoute as Hypothesis
from echo_heist.ai.navigation.routes import zone_routes as route_hypotheses
from echo_heist.ai.planning.minimax import GameTree, SearchResult, alphabeta
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.security.director import (
    DirectorRules,
    ProtocolId,
    RouteGraph,
)
from echo_heist.core.contracts.security.model import (
    GuardDecision,
    GuardMemory,
    GuardPatrol,
    GuardState,
    InterceptPlan,
    SensorRules,
)
from echo_heist.core.contracts.world import MissionPhase, Tile, tile_center

BLOCK_HORIZON_TICKS = 300


@dataclass(frozen=True, slots=True)
class InterceptProblem:
    """Everything the search needs; built only from evidence and static geometry."""

    hypotheses: tuple[Hypothesis, ...]
    posts: tuple[str, ...]
    guard_steps: tuple[tuple[str, int], ...]
    graph: RouteGraph
    evidence_age_ticks: int
    guard_ticks_per_tile: int
    intruder_ticks_per_tile: int

    def steps_to(self, post: str) -> int | None:
        return next((steps for node, steps in self.guard_steps if node == post), None)


type Node = tuple[str | None, int | None, str | None]  # (post, hypothesis index, final post)


def build_tree(problem: InterceptProblem, depth: int) -> GameTree[Node, str | int]:
    """MIN Interceptor picks a post, MAX intruder picks a branch, MIN may redeploy."""

    def moves(node: Node, maximizing: bool) -> tuple[str | int, ...]:
        post, route, _ = node
        if post is None:
            return tuple(p for p in problem.posts if problem.steps_to(p) is not None)
        if route is None:
            return tuple(range(len(problem.hypotheses)))
        if depth < 3:
            return ()
        on_route = problem.hypotheses[route].nodes
        return (post, *(n for n in on_route if n != post))

    def child(node: Node, move: str | int, maximizing: bool) -> Node:
        post, route, _ = node
        if post is None:
            return (str(move), None, None)
        if route is None:
            return (post, int(move), None)
        return (post, route, str(move))

    def evaluate(node: Node) -> float:
        post, route, final = node
        if post is None or route is None:
            return 1.0
        final = final or post
        hypothesis = problem.hypotheses[route]
        reach = problem.steps_to(post)
        if reach is None:
            return hypothesis.weight
        travel = reach
        if final != post:
            leg = problem.graph.distance(post, final)
            if leg is None:
                return hypothesis.weight
            travel += leg
        if final not in hypothesis.nodes:
            return hypothesis.weight  # every gate on this branch left open
        index = hypothesis.nodes.index(final)
        intruder = max(
            0,
            hypothesis.arrival_steps[index] * problem.intruder_ticks_per_tile
            - problem.evidence_age_ticks,
        )
        margin = intruder - travel * problem.guard_ticks_per_tile
        if margin >= 0:
            quality = 0.1 + 0.2 * (1 - min(1.0, margin / BLOCK_HORIZON_TICKS))
        else:
            quality = 0.6 + 0.4 * min(1.0, -margin / BLOCK_HORIZON_TICKS)
        return hypothesis.weight * quality

    return GameTree(moves, child, evaluate)


def plan_intercept(
    observation: Observation,
    graph: RouteGraph,
    director: DirectorRules,
    evidence_tile: Tile,
    evidence_tick: int,
    home_zone: str,
) -> tuple[InterceptPlan, SearchResult[str | int]] | None:
    """Alpha-beta over this guard's own registry gates (its home-zone chokepoints).

    Posts are limited to the route-level gates it defends, so a shared exit
    articulation point is never sealed and every branch keeps a counterplay.
    """
    world_map = observation.map_static
    goals = graph.exit_tiles if observation.phase == MissionPhase.LOCKDOWN else (graph.core_tile,)
    steps = distances_from(world_map, evidence_tile)
    hypotheses = tuple(
        route for goal in goals for route in route_hypotheses(graph, evidence_tile, goal, steps)
    )
    if not hypotheses:
        return None
    posts = tuple(
        sorted(
            {
                node
                for item in hypotheses
                for node in item.nodes
                if home_zone in graph.node(node).zones
            }
        )
    )
    if not posts:
        return None
    own = distances_from(world_map, observation.own_status.tile)
    problem = InterceptProblem(
        hypotheses,
        posts,
        tuple((post, own[tile]) for post in posts if (tile := graph.node(post).tile) in own),
        graph,
        max(0, observation.tick - evidence_tick),
        director.guard_ticks_per_tile,
        director.intruder_ticks_per_tile,
    )
    depth = director.interceptor_depth
    result = alphabeta(build_tree(problem, depth), (None, None, None), depth, False)
    if result.move is None:
        return None
    post = str(result.move)
    return (
        InterceptPlan(
            observation.tick,
            evidence_tick,
            post,
            graph.node(post).tile,
            depth,
            result.evaluated,
            result.pruned,
            round(result.value, 6),
            tuple(item.label for item in hypotheses),
        ),
        result,
    )


def _evidence(observation: Observation, memory: GuardMemory) -> tuple[Tile, int, str, str] | None:
    """Newest report or order newer than the last searched evidence."""
    searched = memory.intercept.evidence_tick if memory.intercept else -1
    leads = [
        report
        for report in observation.shared_reports
        if report.source_guard != observation.agent_id
        and observation.tick <= report.expires_at_tick
        and (
            report.report_kind == "SIGHTING"
            or (report.report_kind == DISPATCH and report.recipient == observation.agent_id)
        )
        and report.tick > searched
        and report.tick >= memory.last_seen_tick
    ]
    if not leads:
        return None
    lead = max(leads, key=lambda report: (report.tick, report.event_id))
    return lead.tile, lead.tick, lead.event_id, "REPORT"


def _return(observation: Observation, patrol: GuardPatrol, memory: GuardMemory) -> GuardMemory:
    index = min(
        range(len(patrol.points)),
        key=lambda value: (distance(observation.own_status.tile, patrol.points[value]), value),
    )
    return replace(memory, state=GuardState.RETURN, target=patrol.points[index], patrol_index=index)


def standing_post(graph: RouteGraph, director: DirectorRules, patrol: GuardPatrol) -> Tile | None:
    """REINFORCE_ROUTE: hold the home-zone chokepoint joining the reinforced sector."""
    protocol = director.protocol
    if protocol is None or protocol.protocol_id != ProtocolId.REINFORCE_ROUTE:
        return None
    home = graph.zone_of(patrol.points[0])
    matches = [
        node
        for node in graph.nodes
        if home in node.zones and protocol.sector in node.zones and home != protocol.sector
    ]
    return min(matches, key=lambda node: node.node_id).tile if matches else None


def decide(
    observation: Observation,
    patrol: GuardPatrol,
    rules: SensorRules,
    memory: GuardMemory,
    *,
    graph: RouteGraph | None,
    director: DirectorRules,
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
        return steer(observation, memory, memory.target, astar, intruder)
    memory = replace(memory, identity_ticks=max(0, memory.identity_ticks - 2))
    if memory.state == GuardState.SPOTTED:
        memory = replace(memory, state=GuardState.INVESTIGATE, target=memory.last_seen_tile)
    lead = _evidence(observation, memory) if graph is not None else None
    own_loss = (
        graph is not None
        and memory.state == GuardState.CHASE
        and memory.last_seen_tile is not None
        and (memory.intercept is None or memory.intercept.evidence_tick < memory.last_seen_tick)
    )
    if graph is not None and (lead is not None or own_loss):
        tile, tick, key, kind = (
            lead
            if lead is not None
            else (
                memory.last_seen_tile,
                memory.last_seen_tick,
                memory.evidence_id,
                memory.evidence_kind,
            )
        )
        assert tile is not None
        home = graph.zone_of(patrol.points[0])
        planned = plan_intercept(observation, graph, director, tile, tick, home)
        if planned is not None:
            plan, _ = planned
            memory = replace(
                memory,
                state=GuardState.INVESTIGATE,
                target=plan.post_tile,
                intercept=plan,
                search_tiles=(),
                evidence_kind=kind,
                evidence_id=key,
                evidence_tick=tick,
                evidence_tile=tile,
                wait_until=0,
            )
        elif memory.state == GuardState.CHASE:
            memory = replace(memory, state=GuardState.INVESTIGATE, target=memory.last_seen_tile)
    if memory.state == GuardState.INVESTIGATE:
        hold = observation.phase == MissionPhase.LOCKDOWN
        age = observation.tick - max(memory.evidence_tick, memory.last_seen_tick)
        if not hold and age > 2 * rules.memory_ticks:
            memory = _return(observation, patrol, memory)
    target = memory.target
    if memory.state in (GuardState.PATROL, GuardState.SEARCH):
        post = standing_post(graph, director, patrol) if graph is not None else None
        if post is not None:
            target = post
            memory = replace(memory, state=GuardState.PATROL)
        else:
            target = patrol.points[memory.patrol_index]
            if arrived(position, target):
                index = (memory.patrol_index + 1) % len(patrol.points)
                target = patrol.points[index]
                memory = replace(
                    memory,
                    state=GuardState.PATROL,
                    patrol_index=index,
                    wait_until=observation.tick + rules.patrol_pause_ticks,
                )
    elif memory.state == GuardState.RETURN and arrived(position, target):
        memory = replace(memory, state=GuardState.PATROL, last_seen_tile=None, last_seen_tick=-1)
    return steer(observation, memory, target, astar, None)
