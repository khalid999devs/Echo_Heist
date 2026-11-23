"""The Companion controller: mission FSM, utility, MCTS and observed-risk A*.

One controller turns the Companion's own Observation into one legal Action per
tick. The mission FSM (INFILTRATE -> REACH_CORE -> TAKE_CORE -> EXTRACT) fixes
the legal goal; utility overrides handle immediate danger; a bounded
belief-only MCTS chooses a strategic response at important events (new
sighting, junction, objective change, being stuck, a finished hold); A* with
observed-danger step penalties executes it physically. The Simulation applies
the same movement, tool and mission rules as for the Human operative.
"""

from collections import deque
from dataclasses import dataclass, replace
from itertools import pairwise
from random import Random

from echo_heist.ai.companion import tactics
from echo_heist.ai.companion.belief import Beliefs
from echo_heist.ai.companion.briefing import MissionBriefing, PolicyWeights, policy_weights
from echo_heist.ai.companion.stealth import lanes
from echo_heist.ai.companion.stealth.cover import safe_cover
from echo_heist.ai.companion.utility import (
    Override,
    active_guards,
    emergency,
    escape_available,
    melee_available,
)
from echo_heist.ai.navigation.astar import astar
from echo_heist.ai.navigation.grid import distances_from, unsnag
from echo_heist.ai.navigation.routes import ZoneRoute, zone_routes
from echo_heist.ai.planning.mcts import MctsResult, search
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.autonomy.model import Alternative, CompanionTrace
from echo_heist.core.contracts.autonomy.policy import PolicySelection
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import (
    MissionPhase,
    Position,
    StairLink,
    Tile,
    tile_center,
)

ITERATIONS = 64
MAX_DEPTH = 4
ARRIVE = UNIT // 8
SEARCH_GAP_TICKS = 12
STUCK_TICKS = 40
WAIT_TICKS = 45
HIDE_MAX_TICKS = 240
CLEAR_TICKS = 60
BREADCRUMBS = 150
FLEE = "FLEE"
BODY_COST = 60
JAM_TICKS = 90
FLEE_LIMIT_TICKS = 180
JAM_COST = 400
ALERT_TICKS = 150
STALL_TICKS = 600
FLEE_TICKS = 75
BLOCK_TILES = 4
EXIT_SWITCH_COST = 40  # A* cost an alternative exit must save to win
EXIT_COMMIT_TICKS = 180
GATE_HOLD_TICKS = 45
GATE_ABANDON_TICKS = 600
ESCAPE_HOLD_TICKS = 15
ABANDON_TICKS = 180
RECOVERY_TICKS = 900  # time without getting closer to the actual objective
STAIR_COMMIT_SECONDS = 2
STAIR_RETRY_TICKS = 12


@dataclass(frozen=True, slots=True)
class Directive:
    """The strategic choice being executed and how long it holds."""

    action: str
    until_tick: int = 0
    goal: Tile | None = None


@dataclass(frozen=True, slots=True)
class StairBackoff:
    link: StairLink
    until_tick: int
    blocked: bool


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)


class CompanionController:
    def __init__(
        self,
        actor_id: str,
        briefing: MissionBriefing,
        policy: PolicySelection,
        rules: GameRules,
        *,
        rng: Random,
        sight_range_tiles: int,
        half_angle_degrees: int,
    ) -> None:
        self.actor_id, self.briefing, self.rules = actor_id, briefing, rules
        self.policy = policy
        self.weights: PolicyWeights = policy_weights(policy)
        self.beliefs = Beliefs(briefing, sight_range_tiles, half_angle_degrees)
        self.rng = rng  # a dedicated, seeded decision stream supplied by the runtime
        self.state = "INFILTRATE"
        self.directive = Directive(tactics.ADVANCE)
        self.legs: tuple[tactics.Leg, ...] = ()
        self.progress = 0
        self.path: tuple[Tile, ...] = ()
        self.path_goal: Tile | None = None
        self.path_cost: int | None = None
        self.expanded = 0
        self.path_tick = -1
        self.last_search_tick = -10_000
        self.last_search_trigger = ""
        self.last_result: MctsResult[str] | None = None
        self.trace: CompanionTrace | None = None
        self.reason = ""
        self.trigger = "deployment"
        self.pending = ""
        self.last_kind: ActionKind | None = None
        self.last_tick = -1
        self.last_watched = -10_000
        self.jammed: dict[Tile, int] = {}
        # Routes given up by ALTERNATE stay excluded briefly, so the choice commits.
        self.abandoned: dict[tuple[str, ...], int] = {}
        self.flee_started = -1
        self.progress_tick = 0
        self.previous: Position | None = None
        self.still_ticks = 0
        self.tile_ticks = 0  # ticks spent on the current tile (survives body jitter)
        self.last_tile: Tile | None = None
        self.crumbs: deque[Tile] = deque(maxlen=BREADCRUMBS)
        self.melee_ready_at: dict[str, int] = {}
        self.echo_ready_at = 0
        self.hidden_since = -1
        self.cover_ready_at = 0
        self.hide_approach: Tile | None = None
        self.utility = ("", "")
        self.geometry_revision = 0
        self.objective_key: tuple[bool, int] | None = None
        self.objective_steps: dict[Tile, int] = {}
        self.objective_best: int | None = None
        self.objective_progress_at = 0
        self.exit_replan_at = 0
        self.exit_locked_until = self.hold_ticks = 0
        self.escape_from: Position | None = None
        self.escape_until = self.turns = 0
        self.last_action: Action | None = None
        self.stair_attempt: StairLink | None = None
        self.last_stair_crossing: tuple[StairLink, int] | None = None
        self.stair_backoff: StairBackoff | None = None
        self.extraction_goal = briefing.exit_tile
        graph = briefing.graph
        return_legs = [
            (self._legs_from(briefing.core_tile, exit_tile, None), exit_tile)
            for exit_tile in graph.exit_tiles
        ]
        self.homeward, self.extraction_goal = min(
            return_legs, key=lambda item: item[0][0].route.total_steps
        )

    # ----------------------------------------------------------------- planning
    def _legs_from(
        self, start: Tile, goal: Tile, observation: Observation | None
    ) -> tuple[tactics.Leg, ...]:
        graph = self.briefing.graph
        start_zone, goal_zone = graph.zone_of(start), graph.zone_of(goal)
        world_map = observation.map_static if observation else None
        if world_map is None:
            # Homeward legs at deployment come from the static distance table.
            routes = zone_routes(graph, start, goal, self._anchor_steps(start))
        else:
            routes = zone_routes(graph, start, goal, distances_from(world_map, start))
        if start_zone == goal_zone or not routes:
            return (tactics.Leg(ZoneRoute((), (), 0, 1.0), (start_zone or goal_zone,), (0,)),)
        return tactics.legs(graph, routes, start_zone, goal_zone)

    def _anchor_steps(self, start: Tile) -> dict[Tile, int]:
        graph = self.briefing.graph
        name = graph.anchor_name(start)
        steps: dict[Tile, int] = {}
        for node in graph.nodes:
            value = graph.distance(node.node_id, name)
            if value is not None:
                steps[node.tile] = value
        return steps

    def _goal(self, observation: Observation) -> Tile:
        carrying = observation.own_status.inventory.core_held
        return self.extraction_goal if carrying else self.briefing.core_tile

    def _choose_exit(self, observation: Observation) -> None:
        exits = self.briefing.graph.exit_tiles
        self.exit_replan_at = observation.tick + SEARCH_GAP_TICKS
        if len(exits) < 2:
            return
        danger = self.beliefs.danger(observation.tick)
        bodies = {guard.tile for guard in active_guards(observation)}
        own = observation.own_status.tile

        jammed = {tile for tile, until in self.jammed.items() if until > observation.tick}

        def penalty(tile: Tile) -> int:
            return (
                self.weights.risk_weight * danger.get(tile, 0) // 2
                + (BODY_COST if tile in bodies else 0)
                + (JAM_COST if tile in jammed else 0)
            )

        options = []
        for tile in exits:
            path = astar(observation.map_static, own, tile, penalty=penalty)
            if path.path:
                # Switching exits turns the escape around; demand a clear gain.
                options.append(
                    (path.cost + (EXIT_SWITCH_COST if tile != self.extraction_goal else 0), tile)
                )
        current = any(tile == self.extraction_goal for _, tile in options)
        if options and (not current or observation.tick >= self.exit_locked_until):
            choice = min(options)[1]
            if choice != self.extraction_goal:
                # Commit: re-deciding every search bounced between the two escapes.
                self.exit_locked_until = observation.tick + EXIT_COMMIT_TICKS
            self.extraction_goal = choice

    def _needs_recovery(self, observation: Observation) -> bool:
        own = observation.own_status
        carrying = own.inventory.core_held
        key = (carrying, observation.geometry_revision)
        if self.objective_key != key:
            # Public walkable geometry only; cache reverse distances until it changes.
            goals = self.briefing.graph.exit_tiles if carrying else (self.briefing.core_tile,)
            steps: dict[Tile, int] = {}
            for goal in goals:
                for tile, distance in distances_from(observation.map_static, goal).items():
                    steps[tile] = min(steps.get(tile, distance), distance)
            if self.objective_key is None or self.objective_key[0] != carrying:
                self.objective_best, self.objective_progress_at = None, observation.tick
            self.objective_key, self.objective_steps = key, steps
        remaining = self.objective_steps.get(own.tile)
        if remaining is not None and (
            self.objective_best is None or remaining < self.objective_best
        ):
            self.objective_best, self.objective_progress_at = remaining, observation.tick
        return observation.tick - self.objective_progress_at >= RECOVERY_TICKS

    def _strategize(self, observation: Observation) -> None:
        own = observation.own_status
        carrying = own.inventory.core_held
        if carrying:
            self._choose_exit(observation)
        remaining = self.legs[0].route.nodes[self.progress :] if self.legs else ()
        legs = self._legs_from(own.tile, self._goal(observation), observation)
        tick = observation.tick
        open_legs = tuple(leg for leg in legs if self.abandoned.get(leg.route.nodes, -1) < tick)
        legs = open_legs or legs
        # Keep the branch being followed first so ADVANCE means "continue".
        legs = tuple(sorted(legs, key=lambda leg: leg.route.nodes != remaining))
        self.legs, self.progress = legs, 0
        guards = {brief.guard_id: brief for brief in self.briefing.guards}
        threats = active_guards(observation)
        watched_recently = tick - self.last_watched <= CLEAR_TICKS
        cover = safe_cover(observation, self.briefing, self.beliefs) if watched_recently else None
        zone = self.briefing.graph.zone_of(own.tile)
        hide_zones = frozenset(
            self.briefing.graph.zone_of(tile)
            for tile in (*self.briefing.hide_tiles, *self.briefing.locker_tiles)
        )
        root = tactics.TacticalState(
            leg=0,
            progress=0,
            carrying=carrying,
            echo=own.inventory.echo_charges,
            emp=own.inventory.emp_charges,
            melee=own.inventory.melee_charges,
            melee_wait=own.melee_cooldown_remaining / self.rules.simulation_hz,
            seconds=0.0,
            # Recently seen in a cone: the defenders are alerted and converging.
            detections=tactics.ALERT_DETECTIONS
            if observation.tick - self.last_watched <= ALERT_TICKS
            else 0.0,
            gadgets=0,
            captured=False,
            extracted=False,
            guards=(),
            distracted=0,
            hidden=own.concealed,
            zone=zone,
        )
        model = tactics.CompanionModel(
            self.briefing,
            self.weights,
            root,
            legs,
            self.homeward if not carrying else legs,
            {
                gid: self.beliefs.zone_belief(brief, observation.tick)
                for gid, brief in guards.items()
            },
            {gid: brief.kind for gid, brief in guards.items()},
            hide_zones,
            False,  # EMP and melee are handled by immediate-danger utility.
            False,
            len(self.crumbs) > 8,
            cover is not None and tick >= self.cover_ready_at,
            bool(threats)
            and watched_recently
            and cover is None
            and tick >= self.echo_ready_at
            and self.tile_ticks >= STUCK_TICKS
            and not escape_available(observation, self.rules),
            {gid: self.beliefs.prior(brief) for gid, brief in guards.items()},
            self._branch_threatened(observation, legs),
            observation.tick - self.progress_tick >= STALL_TICKS,
            melee_recovery=self.rules.melee_cooldown_ticks / self.rules.simulation_hz,
        )
        result: MctsResult[str] = search(
            model, iterations=ITERATIONS, max_depth=MAX_DEPTH, rng=self.rng
        )
        self.last_result, self.last_search_tick = result, observation.tick
        self.last_search_trigger = self.trigger
        choice = result.best or tactics.WAIT
        ranked = sorted(
            (item for item in result.alternatives if item.visits),
            key=lambda item: (-item.visits, item.action),
        )
        runner = next((item for item in ranked if item.action != choice), None)
        best = next(item for item in ranked if item.action == choice) if ranked else None
        self.reason = (
            f"MCTS preferred {choice} ({best.visits if best else 0} visits)"
            + (f" over {runner.action} ({runner.visits})" if runner else "")
            + f" after {self.trigger}"
        )
        if choice == tactics.ALTERNATE and len(legs) > 1:
            self.abandoned[legs[0].route.nodes] = observation.tick + ABANDON_TICKS
            self.legs = (*legs[1:], legs[0])
            self.directive = Directive(tactics.ADVANCE)
        elif choice == tactics.WAIT:
            self.directive = Directive(tactics.WAIT, observation.tick + WAIT_TICKS)
        elif choice == tactics.HIDE and cover is not None:
            self._begin_hide(cover, tick)
        elif choice == tactics.RETREAT:
            self.directive = Directive(
                tactics.RETREAT,
                observation.tick + WAIT_TICKS * 2,
                self._safe_crumb(observation.tick),
            )
        elif not (
            self.directive.action == tactics.RETREAT
            and observation.tick < self.directive.until_tick
        ):
            # A back-off out of a patrol's lane finishes first; advancing (or
            # using a gadget) straight back into it is exactly what it avoids.
            self.directive = Directive(choice)
        self.path_goal = None  # replan the physical path for the new directive

    def _branch_threatened(self, observation: Observation, legs: tuple[tactics.Leg, ...]) -> bool:
        """Switch branches only on observed danger: a recent sighting in the sector
        the current branch enters next, or an alert after being seen."""
        if len(legs) < 2:
            return False
        if observation.tick - self.last_watched <= ALERT_TICKS:
            return True
        upcoming = set(legs[0].zones[1:3])
        return any(
            observation.tick - seen.tick <= ALERT_TICKS
            and self.briefing.graph.zone_of(seen.tile) in upcoming
            for seen in self.beliefs.sightings.values()
        )

    def _safe_crumb(self, tick: int, *, far: bool = False) -> Tile | None:
        return lanes.safe_crumb(self.beliefs.danger(tick), self.crumbs, far=far)

    # --------------------------------------------------------------- execution
    def _route_goal(self, observation: Observation) -> Tile:
        if not self.legs:
            return self._goal(observation)
        leg = self.legs[0]
        own = observation.own_status.tile
        graph = self.briefing.graph
        while self.progress < len(leg.route.nodes):
            node = graph.node(leg.route.nodes[self.progress])
            passed = own == node.tile or graph.zone_of(own) == leg.zones[self.progress + 1]
            if not passed:
                return node.tile
            self.progress += 1
            self.progress_tick = observation.tick
            self.trigger = f"reaching junction {node.node_id}"
        return self._goal(observation)

    def _plan_path(self, observation: Observation, goal: Tile) -> None:
        own = observation.own_status
        recovering = observation.tick - self.objective_progress_at >= RECOVERY_TICKS
        backoff = self.stair_backoff
        if backoff is not None and backoff.link.tile != own.tile:
            backoff = None
        stale = (
            goal != self.path_goal
            or observation.geometry_revision != self.geometry_revision
            or not self.path
            or (backoff is not None and backoff.link.destination in self.path[:2])
            # Recovery commits to a route through changing patrol risk. Real
            # geometry changes and blocked motion can still force a replan.
            or (not recovering and self.beliefs.visible and observation.tick - self.path_tick >= 15)
            or self.still_ticks >= 4
        )
        if not stale:
            return
        danger = self.beliefs.danger(observation.tick)
        weight = self.weights.risk_weight
        # Observed bodies are physical obstacles (every policy routes around them).
        bodies = lanes.bodies(observation, self.actor_id) - {own.tile}

        jammed = {tile for tile, until in self.jammed.items() if until > observation.tick}

        def penalty(tile: Tile) -> int:
            return (
                weight * danger.get(tile, 0) // 2
                + (BODY_COST if tile in bodies else 0)
                + (JAM_COST if tile in jammed else 0)
            )

        world_map = observation.map_static
        result = astar(world_map, own.tile, goal, penalty=penalty)
        if backoff is not None and (backoff.link.tile, backoff.link.destination) in pairwise(
            result.path
        ):
            # A room-scale detour can cost less than another stair transition or
            # running straight back into the same patrol. Keep the other stairway.
            avoided = {backoff.link.object_id, backoff.link.destination_id}
            alternate_map = replace(
                world_map,
                stairs=tuple(link for link in world_map.stairs if link.object_id not in avoided),
            )
            alternative = astar(alternate_map, own.tile, goal, penalty=penalty)
            if alternative.path:
                result = alternative
        self.path = result.path[1:] if result.path else ()
        self.path_goal, self.path_tick = goal, observation.tick
        self.path_cost = result.cost if result.path else None
        self.expanded = result.expanded
        self.geometry_revision = observation.geometry_revision

    def _steer(self, observation: Observation, goal: Tile, sprint: bool) -> Action:
        own = observation.own_status
        tick = observation.tick
        position = own.position or tile_center(own.tile)
        self._plan_path(observation, goal)
        while (
            self.path
            and max(abs(a - b) for a, b in zip(tile_center(self.path[0]), position, strict=True))
            <= ARRIVE
        ):
            self.path = self.path[1:]
        stair = next(
            (
                link
                for link in observation.map_static.stairs
                if link.tile == own.tile and self.path and link.destination == self.path[0]
            ),
            None,
        )
        if stair is not None:
            backoff = self.stair_backoff
            if backoff is not None and backoff.blocked and stair == backoff.link:
                return Action(self.actor_id, ActionKind.WAIT, tick)
            self.stair_attempt = stair
            return Action(self.actor_id, ActionKind.INTERACT, tick, target_id=stair.object_id)
        target = tile_center(self.path[0] if self.path else goal)
        center = tile_center(own.tile)
        if self.path and self.path[0][0] != own.tile[0] and abs(center[1] - position[1]) > ARRIVE:
            target = (position[0], center[1])
        elif self.path and self.path[0][1] != own.tile[1] and abs(center[0] - position[0]) > ARRIVE:
            target = (center[0], position[1])
        dx, dy = target[0] - position[0], target[1] - position[1]
        direction = (_sign(dx) if abs(dx) > ARRIVE else 0, 0)
        if direction == (0, 0):
            direction = (0, _sign(dy) if abs(dy) > ARRIVE else 0)
        if self.previous == position and direction[0] and abs(dy) > ARRIVE:
            direction = (0, _sign(dy))
        elif self.previous == position and direction[1] and abs(dx) > ARRIVE:
            direction = (_sign(dx), 0)
        if direction == (0, 0):
            return Action(self.actor_id, ActionKind.WAIT, tick)
        direction = unsnag(observation.map_static, position, direction, (dx, dy))
        ahead = (own.tile[0] + direction[0], own.tile[1] + direction[1])
        if (
            self.directive.action == tactics.ADVANCE
            and self.weights.risk_weight > 0
            and tick - self.last_watched > self.rules.pursuit_grace_ticks
            and self.tile_ticks < self.rules.simulation_hz * 3
        ):
            closing, exposed = lanes.lane_pressure(
                observation, self.beliefs, own.tile, ahead, self.rules.simulation_hz
            )
            if self.beliefs.watched_by(observation, ahead) is not None or closing:
                crumb = self._safe_crumb(tick) if exposed else None
                if crumb is not None and crumb != own.tile:
                    # Standing in the patrol's lane is no cover: back off first.
                    self.directive = Directive(tactics.RETREAT, tick + WAIT_TICKS, crumb)
                    self.path_goal = None
                    self.utility = ("HOLD", "Back out of the patrol's lane and let it pass")
                    return self._steer(observation, crumb, False)
                if self.hold_ticks >= GATE_HOLD_TICKS and lanes.gate_guarded(
                    observation, self.briefing.graph, self.legs, self.progress
                ):  # a guard planted on the gate never turns away: reroute
                    self._avoid_gate(observation)
                self.utility = ("HOLD", "Wait at cover until the patrol turns")
                return Action(self.actor_id, ActionKind.WAIT, tick)
        if self.still_ticks >= 2:  # pressed against a body: side-step into a parallel lane
            side = lanes.side_lane(observation, self.actor_id, direction, self.still_ticks)
            if side is not None:
                return Action(self.actor_id, ActionKind.MOVE, tick, side, sprint=sprint)
            # A body fills a one-tile corridor: jam the way ahead and re-route. If a guard
            # stands in the only way on, back off out of its reach and let it move.
            ahead = (own.tile[0] + direction[0], own.tile[1] + direction[1])
            for tile in (ahead, *(self.path[:1])):
                self.jammed[tile] = tick + JAM_TICKS
            self.path_goal = None
            back = lanes.backoff(observation, self.actor_id, direction)
            if back is not None and self.directive.action != tactics.RETREAT:
                self.directive = Directive(tactics.RETREAT, tick + WAIT_TICKS, back)
                self.utility = ("HOLD", "A guard blocks the way: back off and let it move")
                return self._steer(observation, back, False)
        return Action(self.actor_id, ActionKind.MOVE, tick, direction, sprint=sprint)

    def _avoid_gate(self, observation: Observation) -> None:
        tick = observation.tick
        leg = self.legs[0]
        gate = self.briefing.graph.node(leg.route.nodes[self.progress]).tile
        self.abandoned[leg.route.nodes] = tick + GATE_ABANDON_TICKS
        lanes.jam_around(self.jammed, gate, tick + GATE_ABANDON_TICKS)
        self.exit_locked_until = 0  # the committed exit may lie behind this gate
        self.pending, self.path_goal = "guarded gate", None

    def _avoid(self, guard: Position, tick: int) -> None:
        lanes.jam_around(self.jammed, (guard[0] // UNIT, guard[1] // UNIT), tick + JAM_TICKS)
        self.path_goal = None

    def _escape(self, observation: Observation, away: Position) -> Action:
        own = observation.own_status
        position = own.position or tile_center(own.tile)
        options = lanes.escape_steps(observation, self.actor_id, away, self.last_action)
        if not options:
            return Action(self.actor_id, ActionKind.WAIT, observation.tick)
        # A rejected step (a body or an exact fixture edge) rotates to the next option.
        choice = (self.still_ticks // 3) % len(options) if self.previous == position else 0
        direction = options[choice]
        return Action(
            self.actor_id, ActionKind.MOVE, observation.tick, direction, sprint=not own.crouched
        )

    def _begin_hide(self, cover: tuple[Tile, Tile], tick: int) -> None:
        tile, self.hide_approach = cover
        self.directive = Directive(tactics.HIDE, tick + HIDE_MAX_TICKS, tile)
        self.path_goal = None

    def _hide(self, observation: Observation) -> Action | None:
        own, tick = observation.own_status, observation.tick
        tile, approach = self.directive.goal, self.hide_approach
        if tile is None or approach is None:
            return None
        watching_cover = self.beliefs.watched_by(observation, approach)
        if own.concealed:
            if self.hidden_since < 0:
                self.hidden_since = tick
            held = tick - self.hidden_since
            guard_near = any(
                abs(guard.tile[0] - approach[0]) + abs(guard.tile[1] - approach[1]) <= 3
                for guard in active_guards(observation)
            )
            if held < self.rules.simulation_hz * 5 or (
                (watching_cover is not None or guard_near) and held < HIDE_MAX_TICKS
            ):
                return Action(self.actor_id, ActionKind.WAIT, tick)
            if own.hidden_in is None:
                return Action(self.actor_id, ActionKind.MOVE, tick, (0, 1))
        elif self.hidden_since >= 0:
            # Keep a single outward heading until fully clear of the desk.
            self.directive = Directive(tactics.ADVANCE)
            self.hidden_since = -1
            self.cover_ready_at = tick + self.rules.simulation_hz * 4
            self.pending = "leaving cover"
            return None
        elif tick < self.directive.until_tick and watching_cover is None:
            if tile in self.briefing.locker_tiles:
                locker = next(
                    (
                        obj
                        for obj in observation.map_static.objects
                        if obj.tile == tile and obj.kind == "HideSpot"
                    ),
                    None,
                )
                if locker and any(
                    hint.kind == "HideSpot" and hint.target_id == locker.object_id
                    for hint in observation.interactions
                ):
                    return Action(self.actor_id, ActionKind.HIDE, tick, target_id=locker.object_id)
                if own.tile != approach:
                    return self._steer(observation, approach, False)
            else:
                if own.tile != approach:
                    return self._steer(observation, approach, False)
                position = own.position or tile_center(own.tile)
                dx = tile_center(tile)[0] - position[0]
                if abs(dx) > ARRIVE:
                    return Action(self.actor_id, ActionKind.MOVE, tick, (_sign(dx), 0))
                if not own.crouched:
                    return Action(self.actor_id, ActionKind.CROUCH, tick)
                return Action(self.actor_id, ActionKind.MOVE, tick, (0, -1))
        self.directive = Directive(tactics.ADVANCE)
        self.hidden_since = -1
        self.cover_ready_at = tick + self.rules.simulation_hz * 4
        self.pending = "leaving cover" if own.concealed else "cover approach exposed"
        if own.hidden_in is not None:
            return Action(self.actor_id, ActionKind.INTERACT, tick, target_id=own.hidden_in)
        return None

    def _cover_response(self, observation: Observation) -> Action | None:
        tick = observation.tick
        if self.directive.action == tactics.HIDE:
            return self._hide(observation)
        if tick < self.cover_ready_at or tick - self.last_watched > CLEAR_TICKS:
            return None
        limit = 3 if self.weights.sprint_always else 6
        cover = safe_cover(observation, self.briefing, self.beliefs, max_steps=limit)
        if cover is None:
            self.cover_ready_at = tick + SEARCH_GAP_TICKS
            return None
        self._begin_hide(cover, tick)
        return self._hide(observation)

    def _stand(self, observation: Observation, goal: Tile) -> Action:
        """Stand at a tile centre clear of the desk; low headroom moves one tile further."""
        own, tick = observation.own_status, observation.tick
        position, center = own.position or tile_center(own.tile), tile_center(own.tile)
        failed = self.last_kind == ActionKind.CROUCH and self.last_tick == tick - 1
        if not failed and max(abs(a - b) for a, b in zip(center, position, strict=True)) <= ARRIVE:
            return Action(self.actor_id, ActionKind.CROUCH, tick)
        if not failed:
            dx, dy = center[0] - position[0], center[1] - position[1]
            direction = (_sign(dx), 0) if abs(dx) > ARRIVE else (0, _sign(dy))
            return Action(self.actor_id, ActionKind.MOVE, tick, direction)
        world_map = observation.map_static
        covers = self.briefing.hide_tiles
        options = [
            tile
            for tile in world_map.connections(own.tile)[:4]
            if world_map.can_walk(tile) and tile not in covers
        ]
        if not options:
            return Action(self.actor_id, ActionKind.WAIT, tick)
        best = max(
            options,
            key=lambda t: (
                min(abs(t[0] - c[0]) + abs(t[1] - c[1]) for c in covers) if covers else 0,
                -(abs(t[0] - goal[0]) + abs(t[1] - goal[1])),
                t,
            ),
        )
        direction = (_sign(best[0] - own.tile[0]), _sign(best[1] - own.tile[1]))
        return Action(self.actor_id, ActionKind.MOVE, tick, direction)

    def _phase(self, observation: Observation) -> str:
        own = observation.own_status
        if observation.phase == MissionPhase.WON:
            return "WIN"
        if observation.phase == MissionPhase.CAPTURED:
            return "CAPTURED"
        if own.inventory.core_held:
            return "EXTRACT"
        if any(hint.kind == "Core" for hint in observation.interactions):
            return "TAKE_CORE"
        if self.briefing.graph.zone_of(own.tile) == self.briefing.graph.zone_of(
            self.briefing.core_tile
        ):
            return "REACH_CORE"
        return "INFILTRATE"

    def _remember_stair(self, observation: Observation) -> None:
        if self.stair_backoff is not None and observation.tick >= self.stair_backoff.until_tick:
            self.stair_backoff = None
        attempt, self.stair_attempt = self.stair_attempt, None
        if attempt is None:
            return
        if observation.own_status.tile == attempt.destination:
            commit_ticks = self.rules.simulation_hz * STAIR_COMMIT_SECONDS
            previous = self.last_stair_crossing
            self.last_stair_crossing = attempt, observation.tick
            if (
                previous is not None
                and previous[0].object_id == attempt.destination_id
                and observation.tick - previous[1] < commit_ticks
            ):
                # An immediate retreat can be legitimate. The third trip across
                # the same stairs should give the other route a chance.
                self.stair_backoff = StairBackoff(
                    previous[0], observation.tick + commit_ticks, False
                )
        else:
            # The controller sees its own unchanged landing, never who blocked it.
            self.stair_backoff = StairBackoff(attempt, observation.tick + STAIR_RETRY_TICKS, True)
            self.path_goal = None
            self.pending = "blocked stair landing"

    def act(self, observation: Observation) -> Action:
        own = observation.own_status
        tick = observation.tick
        position = own.position or tile_center(own.tile)
        appeared = self.beliefs.update(observation)
        if not self.crumbs or self.crumbs[-1] != own.tile:
            self.crumbs.append(own.tile)
        phase = self._phase(observation)
        changed = phase != self.state
        if changed:
            self.progress_tick = tick
        self.state = phase
        if own.stair_ticks_remaining or phase in ("WIN", "CAPTURED"):
            return Action(self.actor_id, ActionKind.WAIT, tick)
        self._remember_stair(observation)
        self.still_ticks = self.still_ticks + 1 if self.previous == position else 0
        self.tile_ticks = self.tile_ticks + 1 if self.last_tile == own.tile else 0
        self.last_tile = own.tile
        watched = self.beliefs.watched_by(observation, own.tile)
        if watched is not None:
            self.last_watched = tick
        override = emergency(
            observation,
            self.rules,
            self.weights.emergency,
            self.melee_ready_at,
            watched,
            stalled=self.still_ticks >= STUCK_TICKS,
        )
        recover = self._needs_recovery(observation)
        grabbed = own.capture_ticks_remaining is not None
        if recover and not grabbed and override and override.kind in ("REACT", "ESCAPE"):
            # Repeated retreats can create a stable loop at a guarded gate.
            # Commit to the observed-risk path until progress resumes.
            override = None
        if override is not None and override.kind == "ESCAPE" and override.away_from:
            if grabbed or self.tile_ticks >= STUCK_TICKS:
                # Remember where this guard stands so the route stops leading back
                # into its reach (otherwise grab/escape can alternate forever).
                self._avoid(override.away_from, tick)
            if not grabbed and self.tile_ticks >= STUCK_TICKS:
                # Backing off gains nothing and the guard is not grabbing (e.g. it
                # holds a gate): let the strategy pick another way out.
                self.pending, override = "escape blocked", None
        action = self._cover_response(observation) if not grabbed and not recover else None
        if action is not None:
            self.utility = ("COVER", "Break line of sight and wait in cover")
        else:
            action = self._override(observation, override) if override else None
            self.utility = (override.kind, override.reason) if override and action else ("", "")
        if action is None and recover:
            if own.inventory.core_held and tick >= self.exit_replan_at:
                self._choose_exit(observation)
            self.directive = Directive(tactics.ADVANCE)
            self.flee_started = -1
            self.utility = ("REPLAN", "Stalled: commit to the safest available objective path")
            action = self._execute(observation, self._goal(observation))
        if action is None:
            trigger = (
                ""
                if self.directive.action == FLEE
                else "deployment"
                if self.last_result is None
                else self.pending
                if self.pending
                else f"objective {phase}"
                if changed and phase in ("EXTRACT", "REACH_CORE")
                else f"seeing {sorted(appeared)[0]}"
                if appeared
                else "inability to progress"
                if tick - self.progress_tick == STALL_TICKS
                else "being stuck"
                if (self.still_ticks >= STUCK_TICKS or self.tile_ticks >= 2 * STUCK_TICKS)
                and self.directive.action == tactics.ADVANCE
                else "finishing a hold"
                if self.directive.until_tick and tick >= self.directive.until_tick
                else ""
            )
            junction_before = self.progress
            goal = self._route_goal(observation)
            if self.progress != junction_before and not trigger:
                trigger = self.trigger
            if trigger and (tick - self.last_search_tick >= SEARCH_GAP_TICKS or changed):
                self.trigger, self.pending = trigger, ""
                self._strategize(observation)
                goal = self._route_goal(observation)
                self.still_ticks = 0
            action = self._execute(observation, goal)
        if action.kind == ActionKind.MELEE and action.target_id:
            self.melee_ready_at[action.target_id] = (
                tick + self.rules.melee_stun_ticks + self.rules.melee_immunity_ticks
            )
        if action.kind == ActionKind.ECHO:
            self.echo_ready_at = tick + 120
        self.hold_ticks = self.hold_ticks + 1 if self.utility[0] == "HOLD" else 0
        free = grabbed or self.previous == position or self.utility[0] == "ESCAPE"  # turn now
        action, self.turns = lanes.damp_reversal(action, self.last_action, self.turns, free)
        self.previous, self.last_action = position, action
        self.last_kind, self.last_tick = action.kind, tick
        self._record()
        return action

    def _override(self, observation: Observation, override: Override) -> Action | None:
        tick = observation.tick
        own = observation.own_status
        if override.kind == "MELEE":
            return Action(self.actor_id, ActionKind.MELEE, tick, target_id=override.target_id)
        if override.kind == "EMP" and own.inventory.emp_charges > 0:
            self.directive = Directive(FLEE, tick + FLEE_TICKS)  # slip past while disabled
            self.path_goal = None
            return Action(self.actor_id, ActionKind.EMP, tick)
        if override.kind == "ESCAPE" and override.away_from is not None:
            fleeing = self.directive.action == FLEE
            aim = self.directive.goal if fleeing else self._safe_crumb(tick, far=True)
            # Commit to a flee (dropping it walked back into reach), never past the guard.
            aim = lanes.away_goal(aim, self.crumbs, own.tile, override.away_from)
            if own.capture_ticks_remaining is None and (not fleeing or aim != self.directive.goal):
                until = self.directive.until_tick if fleeing else tick + FLEE_TICKS
                self.directive, self.path_goal = Directive(FLEE, until, aim), None
            return self._escape(observation, override.away_from)
        if override.kind == "REACT" and self.directive.action != FLEE:
            if self.weights.sprint:
                # Bolder policies keep their route if they have no safe nearby
                # cover. Actual grab danger is handled by the utility override.
                return None
            watcher = self.beliefs.watched_by(observation, own.tile)
            ahead = self._route_goal(observation)
            # Only a watcher standing close ahead on the way blocks the route.
            blocked = (
                watcher is not None
                and abs(watcher.tile[0] - own.tile[0]) + abs(watcher.tile[1] - own.tile[1])
                <= BLOCK_TILES
                and abs(watcher.tile[0] - ahead[0]) + abs(watcher.tile[1] - ahead[1])
                < abs(own.tile[0] - ahead[0]) + abs(own.tile[1] - ahead[1])
            )
            # Cautious policy: break line of sight, backing off if the watcher blocks.
            self.directive = Directive(
                FLEE, tick + FLEE_TICKS, self._safe_crumb(tick, far=True) if blocked else None
            )
            self.path_goal = None
            return None  # execute the reaction through the normal path follower
        return None

    def _execute(self, observation: Observation, goal: Tile) -> Action:
        own = observation.own_status
        tick = observation.tick
        directive = self.directive
        if directive.action in (tactics.ECHO, tactics.EMP, tactics.MELEE):
            self.directive = Directive(tactics.ADVANCE)
            kind = {
                tactics.ECHO: ActionKind.ECHO,
                tactics.EMP: ActionKind.EMP,
                tactics.MELEE: ActionKind.MELEE,
            }[directive.action]
            stock = {
                ActionKind.ECHO: own.inventory.echo_charges,
                ActionKind.EMP: own.inventory.emp_charges,
            }
            if stock.get(kind, 1) > 0 and kind != ActionKind.MELEE:
                return Action(self.actor_id, kind, tick)
            if kind == ActionKind.MELEE and melee_available(observation):
                target = min(
                    active_guards(observation),
                    key=lambda e: abs(e.tile[0] - own.tile[0]) + abs(e.tile[1] - own.tile[1]),
                    default=None,
                )
                if target is not None:
                    return Action(self.actor_id, ActionKind.MELEE, tick, target_id=target.actor_id)
            # A stale or illegal choice falls back to waiting and re-planning.
            return Action(self.actor_id, ActionKind.WAIT, tick)
        if directive.action == tactics.HIDE:
            hidden = self._hide(observation)
            if hidden is not None:
                return hidden
        world_map = observation.map_static
        if self.directive.action != tactics.HIDE and not world_map.can_walk(own.tile):
            if lanes.guard_near(observation, self.beliefs):  # stay hidden while it passes
                return Action(self.actor_id, ActionKind.WAIT, tick)
            # Crawl out from under cover toward the goal before standing up.
            exits = [
                tile
                for tile in observation.map_static.connections(own.tile)[:4]
                if world_map.can_walk(tile)
            ]
            if exits:
                out = min(exits, key=lambda t: (abs(t[0] - goal[0]) + abs(t[1] - goal[1]), t))
                direction = (_sign(out[0] - own.tile[0]), _sign(out[1] - own.tile[1]))
                return Action(self.actor_id, ActionKind.MOVE, tick, direction)
        if own.crouched and self.directive.action != tactics.HIDE:
            return self._stand(observation, goal)
        if directive.action == FLEE:
            if self.flee_started < 0:
                self.flee_started = tick
            if (
                self.still_ticks >= STUCK_TICKS // 2 or self.tile_ticks >= STUCK_TICKS
            ) and directive.goal is None:
                # The way forward stays jammed: turn back along remembered tiles.
                self.directive = directive = Directive(
                    FLEE, directive.until_tick, self._safe_crumb(tick, far=True)
                )
            running = tick - self.flee_started < FLEE_LIMIT_TICKS
            if running and (self.beliefs.visible or tick < directive.until_tick - FLEE_TICKS // 2):
                self.directive = Directive(
                    FLEE, max(directive.until_tick, tick + 30), directive.goal
                )
                # Hold at a reached crumb; re-aiming at the goal there jittered.
                aim = directive.goal if directive.goal is not None else goal
                step = self._steer(observation, aim, not own.crouched)
                threat = lanes.closing_threat(observation, step.direction)
                if threat is not None:  # hold the escape briefly instead of dithering
                    self.escape_from, self.escape_until = threat, tick + ESCAPE_HOLD_TICKS
                if tick < self.escape_until and self.escape_from is not None:
                    return self._escape(observation, self.escape_from)
                return step
            self.directive = Directive(tactics.ADVANCE)
            self.flee_started = -1
            self.pending = "breaking line of sight"  # re-plan now that contact is broken
        if directive.action == tactics.WAIT and tick < directive.until_tick:
            return Action(self.actor_id, ActionKind.WAIT, tick)
        if directive.action == tactics.RETREAT and directive.goal is not None:
            if own.tile == directive.goal:
                if tick < directive.until_tick:
                    return Action(self.actor_id, ActionKind.WAIT, tick)
                self.directive = Directive(tactics.ADVANCE)
            else:
                return self._steer(observation, directive.goal, self._sprinting(observation))
        core = next((hint for hint in observation.interactions if hint.kind == "Core"), None)
        if core is not None and not own.inventory.core_held:
            return Action(self.actor_id, ActionKind.INTERACT, tick, target_id=core.target_id)
        return self._steer(observation, goal, self._sprinting(observation))

    def _sprinting(self, observation: Observation) -> bool:
        own = observation.own_status
        if own.crouched:
            return False
        if self.directive.action in (FLEE, tactics.RETREAT):
            return True  # breaking contact outweighs the louder footsteps
        if self.weights.sprint_always:
            return True
        if not self.weights.sprint:
            return False
        if observation.tick - self.last_watched <= CLEAR_TICKS:
            return True
        # Keep footfalls light when a known patrol is near enough to hear them.
        return (own.inventory.core_held or self.state == "INFILTRATE") and not any(
            abs(guard.tile[0] - own.tile[0]) + abs(guard.tile[1] - own.tile[1]) <= 4
            for guard in active_guards(observation)
        )

    # --------------------------------------------------------------- telemetry
    def _record(self) -> None:
        result = self.last_result
        if result is None:
            return
        legal = set(result.root_legal)
        alternatives = [
            Alternative(
                item.action,
                item.visits,
                round(item.mean_reward, 6) if item.mean_reward is not None else None,
            )
            for item in result.alternatives
        ]
        alternatives += [
            Alternative(action, 0, None, legal=False)
            for action in tactics.ORDER
            if action not in legal
        ]
        self.trace = CompanionTrace(
            self.actor_id,
            self.last_search_tick,
            self.state,
            result.best or tactics.WAIT,
            self.reason,
            result.simulations,
            tuple(alternatives),
            self.path,
            self.path_cost,
            self.expanded,
            self.utility[0],
            self.utility[1],
            search_trigger=self.last_search_trigger,
            search_depth=MAX_DEPTH,
            path_goal=self.path_goal,
        )
