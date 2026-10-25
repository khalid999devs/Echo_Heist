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
from dataclasses import dataclass

from echo_heist.ai.companion import tactics
from echo_heist.ai.companion.belief import Beliefs
from echo_heist.ai.companion.briefing import MissionBriefing, PolicyWeights, policy_weights
from echo_heist.ai.companion.utility import Override, active_guards, emergency
from echo_heist.ai.navigation.astar import astar
from echo_heist.ai.navigation.grid import distances_from
from echo_heist.ai.navigation.routes import ZoneRoute, zone_routes
from echo_heist.ai.planning.mcts import MctsResult, search
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.autonomy.model import Alternative, CompanionTrace
from echo_heist.core.contracts.autonomy.policy import PolicySelection
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import MissionPhase, Position, Tile, tile_center
from echo_heist.core.simulation.randomness import seeded_rng

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
BLOCK_TILES = 4
JAM_TICKS = 90
FLEE_LIMIT_TICKS = 180
JAM_COST = 400
ALERT_TICKS = 150
FLEE_TICKS = 75


@dataclass(frozen=True, slots=True)
class Directive:
    """The strategic choice being executed and how long it holds."""

    action: str
    until_tick: int = 0
    goal: Tile | None = None


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
        seed: int,
        sight_range_tiles: int,
        half_angle_degrees: int,
    ) -> None:
        self.actor_id, self.briefing, self.rules = actor_id, briefing, rules
        self.policy = policy
        self.weights: PolicyWeights = policy_weights(policy)
        self.beliefs = Beliefs(briefing, sight_range_tiles, half_angle_degrees)
        self.rng = seeded_rng(seed, "companion-mcts")
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
        self.last_result: MctsResult[str] | None = None
        self.trace: CompanionTrace | None = None
        self.reason = ""
        self.trigger = "deployment"
        self.pending = ""
        self.last_kind: ActionKind | None = None
        self.last_tick = -1
        self.last_watched = -10_000
        self.jammed: dict[Tile, int] = {}
        self.flee_started = -1
        self.previous: Position | None = None
        self.still_ticks = 0
        self.crumbs: deque[Tile] = deque(maxlen=BREADCRUMBS)
        self.melee_ready_at: dict[str, int] = {}
        self.echo_ready_at = 0
        self.hide_tile: Tile | None = None
        self.hidden_since = -1
        self.utility = ("", "")
        self.geometry_revision = 0
        self.homeward = self._legs_from(briefing.core_tile, briefing.exit_tile, None)

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
        name = "CORE" if start == self.briefing.core_tile else "EXIT"
        steps: dict[Tile, int] = {}
        for node in graph.nodes:
            value = graph.distance(node.node_id, name)
            if value is not None:
                steps[node.tile] = value
        return steps

    def _goal(self, observation: Observation) -> Tile:
        carrying = observation.own_status.inventory.core_held
        return self.briefing.exit_tile if carrying else self.briefing.core_tile

    def _strategize(self, observation: Observation) -> None:
        own = observation.own_status
        carrying = own.inventory.core_held
        remaining = self.legs[0].route.nodes[self.progress :] if self.legs else ()
        legs = self._legs_from(own.tile, self._goal(observation), observation)
        # Keep the branch being followed first so ADVANCE means "continue".
        legs = tuple(sorted(legs, key=lambda leg: leg.route.nodes != remaining))
        self.legs, self.progress = legs, 0
        guards = {brief.guard_id: brief for brief in self.briefing.guards}
        threats = active_guards(observation)
        position = own.position or tile_center(own.tile)

        def within(reach: int) -> bool:
            return any(
                (lambda p: (p[0] - position[0]) ** 2 + (p[1] - position[1]) ** 2 <= reach**2)(
                    entity.position or tile_center(entity.tile)
                )
                for entity in threats
            )

        zone = self.briefing.graph.zone_of(own.tile)
        hide_zones = frozenset(
            self.briefing.graph.zone_of(tile) for tile in self.briefing.hide_tiles
        )
        root = tactics.TacticalState(
            leg=0,
            progress=0,
            carrying=carrying,
            echo=own.inventory.echo_charges,
            emp=own.inventory.emp_charges,
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
            own.inventory.emp_charges > 0 and within(self.rules.emp_radius_units * 8 // 10),
            within(self.rules.melee_range_units),
            len(self.crumbs) > 8,
            not self.beliefs.visible
            and any(observation.tick - seen.tick <= 150 for seen in self.beliefs.sightings.values())
            and self._hide_spot(observation) is not None,
            bool(threats),
            {gid: self.beliefs.prior(brief) for gid, brief in guards.items()},
            self._branch_threatened(observation, legs),
        )
        result = search(model, iterations=ITERATIONS, max_depth=MAX_DEPTH, rng=self.rng)
        self.last_result, self.last_search_tick = result, observation.tick
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
            self.legs = (*legs[1:], legs[0])
            self.directive = Directive(tactics.ADVANCE)
        elif choice == tactics.WAIT:
            self.directive = Directive(tactics.WAIT, observation.tick + WAIT_TICKS)
        elif choice == tactics.HIDE:
            self.directive = Directive(
                tactics.HIDE, observation.tick + HIDE_MAX_TICKS, self._hide_spot(observation)
            )
        elif choice == tactics.RETREAT:
            self.directive = Directive(
                tactics.RETREAT,
                observation.tick + WAIT_TICKS * 2,
                self._safe_crumb(observation.tick),
            )
        else:
            self.directive = Directive(choice)
        self.path_goal = None  # replan the physical path for the new directive
        self._record(observation)

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

    def _hide_spot(self, observation: Observation) -> Tile | None:
        steps = distances_from(observation.map_static, observation.own_status.tile)
        best: tuple[int, Tile] | None = None
        for tile in self.briefing.hide_tiles:
            for x, y in (
                (tile[0], tile[1] - 1),
                (tile[0] + 1, tile[1]),
                (tile[0], tile[1] + 1),
                (tile[0] - 1, tile[1]),
            ):
                if (x, y) in steps and (best is None or (steps[(x, y)], tile) < best):
                    best = (steps[(x, y)], tile)
        return best[1] if best is not None and best[0] <= 14 else None

    def _safe_crumb(self, tick: int, *, far: bool = False) -> Tile | None:
        """A remembered tile some steps back that no observed cone covers."""
        danger = self.beliefs.danger(tick)
        trail = list(self.crumbs)[: -(14 if far else 6)]
        for tile in reversed(trail):
            if danger.get(tile, 0) == 0:
                return tile
        return trail[0] if trail else None

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
            self.trigger = f"reaching junction {node.node_id}"
        return self._goal(observation)

    def _plan_path(self, observation: Observation, goal: Tile) -> None:
        own = observation.own_status
        stale = (
            goal != self.path_goal
            or observation.geometry_revision != self.geometry_revision
            or not self.path
            or (self.beliefs.visible and observation.tick - self.path_tick >= 15)
            or self.still_ticks >= 4
        )
        if not stale:
            return
        danger = self.beliefs.danger(observation.tick)
        weight = self.weights.risk_weight
        # Observed bodies are physical obstacles (every policy routes around them).
        bodies = {
            entity.tile
            for entity in observation.visible_entities
            if entity.actor_id != self.actor_id
        } - {own.tile}

        jammed = {tile for tile, until in self.jammed.items() if until > observation.tick}

        def penalty(tile: Tile) -> int:
            return (
                weight * danger.get(tile, 0) // 2
                + (BODY_COST if tile in bodies else 0)
                + (JAM_COST if tile in jammed else 0)
            )

        result = astar(observation.map_static, own.tile, goal, penalty=penalty)
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
        if self.still_ticks >= 2:
            # Pressed against a body: side-step into an open parallel lane.
            bodies = {e.tile for e in observation.visible_entities if e.actor_id != self.actor_id}
            world_map = observation.map_static
            sides = [(direction[1], direction[0]), (-direction[1], -direction[0])]
            if (self.still_ticks // 6) % 2:
                sides.reverse()
            for side in sides:
                lane = (own.tile[0] + side[0], own.tile[1] + side[1])
                if world_map.can_walk(lane) and lane not in bodies:
                    return Action(self.actor_id, ActionKind.MOVE, tick, side, sprint=sprint)
            # A body fills a one-tile corridor: treat the way ahead as jammed and re-route.
            ahead = (own.tile[0] + direction[0], own.tile[1] + direction[1])
            for tile in (ahead, *(self.path[:1])):
                self.jammed[tile] = tick + JAM_TICKS
            self.path_goal = None
        return Action(self.actor_id, ActionKind.MOVE, tick, direction, sprint=sprint)

    def _escape(self, observation: Observation, away: Position) -> Action:
        own = observation.own_status
        position = own.position or tile_center(own.tile)
        options = []
        for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            tile = (own.tile[0] + direction[0], own.tile[1] + direction[1])
            if not observation.map_static.can_walk(tile, crouched=own.crouched):
                continue
            point = tile_center(tile)
            gain = (point[0] - away[0]) ** 2 + (point[1] - away[1]) ** 2
            options.append((-gain, direction))
        if not options:
            return Action(self.actor_id, ActionKind.WAIT, observation.tick)
        options.sort()
        direction = options[0][1]
        del position
        return Action(
            self.actor_id, ActionKind.MOVE, observation.tick, direction, sprint=not own.crouched
        )

    def _hide(self, observation: Observation) -> Action | None:
        own = observation.own_status
        tile = self.directive.goal
        if tile is None:
            return None
        if own.concealed:
            if self.hidden_since < 0:
                self.hidden_since = observation.tick
            clear = (
                not self.beliefs.visible
                and observation.tick
                - max((s.tick for s in self.beliefs.sightings.values()), default=-10_000)
                > CLEAR_TICKS
            )
            if not clear and observation.tick < self.directive.until_tick:
                return Action(self.actor_id, ActionKind.WAIT, observation.tick)
            self.directive = Directive(tactics.ADVANCE)
            self.hidden_since = -1
            self.pending = "leaving cover"
            return None
        approach = min(
            (
                (abs(n[0] - own.tile[0]) + abs(n[1] - own.tile[1]), n)
                for n in (
                    (tile[0], tile[1] - 1),
                    (tile[0] + 1, tile[1]),
                    (tile[0], tile[1] + 1),
                    (tile[0] - 1, tile[1]),
                )
                if observation.map_static.can_walk(n)
            ),
            default=None,
        )
        if approach is None:
            return None
        if own.tile != approach[1] and own.tile != tile:
            return self._steer(observation, approach[1], False)
        if not own.crouched:
            return Action(self.actor_id, ActionKind.CROUCH, observation.tick)
        position = own.position or tile_center(own.tile)
        point = tile_center(tile)
        dx, dy = point[0] - position[0], point[1] - position[1]
        direction = (_sign(dx), 0) if abs(dx) > ARRIVE else (0, _sign(dy))
        if direction == (0, 0):
            return Action(self.actor_id, ActionKind.WAIT, observation.tick)
        return Action(self.actor_id, ActionKind.MOVE, observation.tick, direction)

    def _stand(self, observation: Observation, goal: Tile) -> Action:
        """Stand at a tile centre clear of the desk; low headroom moves one tile further."""
        own = observation.own_status
        tick = observation.tick
        position = own.position or tile_center(own.tile)
        center = tile_center(own.tile)
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

    def act(self, observation: Observation) -> Action:
        own = observation.own_status
        tick = observation.tick
        position = own.position or tile_center(own.tile)
        appeared = self.beliefs.update(observation)
        if not self.crumbs or self.crumbs[-1] != own.tile:
            self.crumbs.append(own.tile)
        phase = self._phase(observation)
        changed = phase != self.state
        self.state = phase
        if own.stair_ticks_remaining or phase in ("WIN", "CAPTURED"):
            return Action(self.actor_id, ActionKind.WAIT, tick)
        self.still_ticks = self.still_ticks + 1 if self.previous == position else 0
        watched = self.beliefs.watched_by(observation, own.tile)
        if watched is not None:
            self.last_watched = tick
        override = emergency(
            observation, self.rules, self.weights.emergency, self.melee_ready_at, watched
        )
        action = self._override(observation, override) if override else None
        self.utility = (override.kind, override.reason) if override and action else ("", "")
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
                else "being stuck"
                if self.still_ticks >= STUCK_TICKS and self.directive.action == tactics.ADVANCE
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
        self.previous = position
        self.last_kind, self.last_tick = action.kind, tick
        self._record(observation)
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
            return self._escape(observation, override.away_from)
        if override.kind == "REACT" and self.directive.action != FLEE:
            # Seen in a cone: break line of sight now. Sentinels are slower than
            # a walking intruder, so moving away beats freezing or hiding in view.
            if (
                self.weights.preferred == "ECHO"
                and own.inventory.echo_charges > 0
                and tick >= self.echo_ready_at
            ):
                self.directive = Directive(FLEE, tick + FLEE_TICKS)
                return Action(self.actor_id, ActionKind.ECHO, tick)
            watcher = self.beliefs.watched_by(observation, own.tile)
            ahead = self._route_goal(observation)
            # Only turn back when the watcher stands close ahead on the way.
            blocked = (
                watcher is not None
                and abs(watcher.tile[0] - own.tile[0]) + abs(watcher.tile[1] - own.tile[1])
                <= BLOCK_TILES
                and abs(watcher.tile[0] - ahead[0]) + abs(watcher.tile[1] - ahead[1])
                < abs(own.tile[0] - ahead[0]) + abs(own.tile[1] - ahead[1])
            )
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
            if kind == ActionKind.MELEE:
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
            if self.still_ticks >= STUCK_TICKS // 2 and directive.goal is None:
                # The way forward stays jammed: turn back along remembered tiles.
                self.directive = directive = Directive(
                    FLEE, directive.until_tick, self._safe_crumb(tick, far=True)
                )
            running = tick - self.flee_started < FLEE_LIMIT_TICKS
            if running and (self.beliefs.visible or tick < directive.until_tick - FLEE_TICKS // 2):
                self.directive = Directive(
                    FLEE, max(directive.until_tick, tick + 30), directive.goal
                )
                target = directive.goal if directive.goal not in (None, own.tile) else goal
                return self._steer(observation, target, not own.crouched)
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
        return self.weights.sprint_always or (self.weights.sprint and own.inventory.core_held)

    # --------------------------------------------------------------- telemetry
    def _record(self, observation: Observation) -> None:
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
            self.directive.action
            if self.directive.action in legal
            else result.best or tactics.WAIT,
            self.reason,
            result.simulations,
            tuple(alternatives),
            self.path,
            self.path_cost,
            self.expanded,
            self.utility[0],
            self.utility[1],
        )
