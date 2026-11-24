"""The stealth agent: MCTS picks the way, space-time A* times every step.

Each tick the Companion

1. learns from what it sees: every guard's position, facing and state label,
   and from those each guard's beat (see ``foresight``);
2. breaks a grab with a stun or the EMP when a guard has hold of it;
3. asks Monte Carlo tree search, at real decision points, which route to take
   and whether a decoy Echo would help (``tactics``);
4. plans the next seconds of moves and waits with space-time A* against the
   guards' predicted sight (``planner``): it walks while the way stays out of
   view, waits where it is safe, backs off or slips into cover where it is
   not, and lifts the Core only in a quiet window long enough to finish.

It reads only its own observation and memory, like every other character.
"""

from math import hypot

from echo_heist.ai.companion import tactics
from echo_heist.ai.companion.controller import ARRIVE, CompanionController, _sign
from echo_heist.ai.companion.spacetime.foresight import HORIZON_STEPS, POSTED_TICKS, STEP_TICKS
from echo_heist.ai.companion.spacetime.planner import Pace, Plan, distance_field, plan
from echo_heist.ai.companion.stealth import lanes
from echo_heist.ai.companion.stealth.cover import approaches
from echo_heist.ai.companion.tactics import Directive
from echo_heist.ai.companion.utility import active_guards, emergency
from echo_heist.ai.navigation.grid import unsnag
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import MissionPhase, Tile, tile_center

ALERTED = frozenset({"INVESTIGATE", "SPOTTED", "CHASE", "SEARCH"})
REPLAN_TICKS = 4
TAKE_STEPS = 4  # lifting the Core takes 24 ticks
FLEE_TICKS = 60  # seen this recently: run, do not walk
HIDE_LIMIT_TICKS = 600
HIDE_MIN_TICKS = 30  # once in cover, stay at least a second
BURN_TILES = 6
BURN_TICKS = 1500  # a junction where it was seen stays suspect for fifty seconds
BURN_COST = (16, 16, 12, 8, 4)
COVER_REST_TICKS = 300  # after a fruitless long hide, keep moving for ten seconds
LEAVE_STEPS = 9  # leave cover only when the way out stays unseen this long
PATIENCE_TICKS = {"GHOST": 600, "BALANCED": 420, "RUSH": 240}
BOLD_TICKS = 150  # how long a lost patience lowers the price of exposure
STRATEGY_STALL_TICKS = 450
HUNT_MEMORY_TICKS = 90
HUNT_TILES = 12
HUNTED_HIDE_COST = 8.0  # with a guard on the hunt, cover beats being found
GATE_BIAS = (8, 8, 4)  # route cost near the junctions of routes MCTS passed over
EXIT_SWITCH_COST = 15
EXIT_COMMIT_TICKS = 150
STAIR_CLOSED_TICKS = 300  # a stair whose landing was held is avoided for ten seconds


class StealthAgent(CompanionController):
    """The Companion's mission loop; see the module description."""

    HOLDS_AT_ROOT = False  # waits, hides and retreats are timed by the planner

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.plan: Plan | None = None
        self.plan_tick = -REPLAN_TICKS
        self.plan_key: tuple[object, ...] = ()
        self.fields: dict[tuple[object, ...], dict[Tile, int]] = {}
        self.closed_stairs: dict[tuple[Tile, Tile], int] = {}
        self.burned: dict[Tile, int] = {}
        self.plan_goals: tuple[Tile, ...] = ()
        self.cover_at: dict[Tile, Tile] = {}
        self.best_remaining: int | None = None
        self.progress_at = 0
        self.bold_until = 0
        self.take_tiles: tuple[Tile, ...] = ()
        self.stay, self.stay_tick = False, -1
        self.geometry_known = False

    def act(self, observation: Observation) -> Action:
        own, tick = observation.own_status, observation.tick
        position = own.position or tile_center(own.tile)
        appeared = self.beliefs.update(observation)
        self.foresight.observe(observation)
        if not self.crumbs or self.crumbs[-1] != own.tile:
            self.crumbs.append(own.tile)
            self.visited.add(own.tile)
        phase = self._phase(observation)
        changed, self.state = phase != self.state, phase
        if own.stair_ticks_remaining or phase in ("WIN", "CAPTURED"):
            return self._done(Action(self.actor_id, ActionKind.WAIT, tick), position)
        if not self.geometry_known:
            self._learn_geometry(observation)
        self._remember_stair(observation)
        self.still_ticks = self.still_ticks + 1 if self.previous == position else 0
        self.tile_ticks = self.tile_ticks + 1 if self.last_tile == own.tile else 0
        self.last_tile = own.tile
        watched = self.beliefs.watched_by(observation, own.tile)
        if watched is not None:
            self.last_watched = tick
            self._burn_gate(observation)
        self._track_progress(observation)
        action = self._break_grab(observation, watched)
        if action is None:
            self._think(observation, appeared, changed)
            action = (
                self._gadget(observation)
                or self._keep_hiding(observation)
                or self._move(observation)
            )
        return self._done(action, position)

    # ------------------------------------------------------------ decisions
    def _break_grab(self, observation: Observation, watched: object) -> Action | None:
        own = observation.own_status
        override = emergency(
            observation,
            self.rules,
            self.weights.emergency,
            self.melee_ready_at,
            self.beliefs.watched_by(observation, own.tile),
            stalled=self.still_ticks >= 40,
        )
        if override is None or override.kind == "REACT":
            return None
        if own.capture_ticks_remaining is None and override.kind == "ESCAPE":
            return None  # not grabbed: the planner already runs out of sight
        self.utility = (override.kind, override.reason)
        return self._override(observation, override)

    def _think(self, observation: Observation, appeared: frozenset[str], changed: bool) -> None:
        """Ask MCTS for the route and gadget at real decision points."""
        tick = observation.tick
        junction = self.progress
        self._route_goal(observation)
        trigger = (
            "deployment"
            if self.last_result is None
            else f"objective {self.state}"
            if changed and self.state in ("EXTRACT", "REACH_CORE")
            else f"seeing {sorted(appeared)[0]}"
            if appeared
            else self.trigger
            if self.progress != junction
            else "inability to progress"
            if tick - self.progress_at >= STRATEGY_STALL_TICKS
            and tick - self.last_search_tick >= STRATEGY_STALL_TICKS
            else ""
        )
        hiding = observation.own_status.concealed or self.directive.action == tactics.HIDE
        if trigger and not hiding and (tick - self.last_search_tick >= 12 or changed):
            self.trigger = trigger
            self._strategize(observation)
            self.plan_tick = -REPLAN_TICKS  # the way may have changed

    def _gadget(self, observation: Observation) -> Action | None:
        directive = self.directive.action
        if directive not in (tactics.ECHO, tactics.EMP, tactics.MELEE):
            return None
        self.directive = Directive(tactics.ADVANCE)
        if directive == tactics.ECHO and observation.own_status.inventory.echo_charges > 0:
            self.utility = ("ECHO", "Send a decoy back along the trail")
            self.echo_ready_at = observation.tick + 120
            return Action(self.actor_id, ActionKind.ECHO, observation.tick)
        return None

    def _keep_hiding(self, observation: Observation) -> Action | None:
        """Stay in cover while the planner would hide here again, then leave."""
        own, tick = observation.own_status, observation.tick
        if own.concealed:
            approach = self.hide_approach or self._way_out(observation)
            if self.hidden_since < 0:
                self.hidden_since = tick
            held = tick - self.hidden_since
            if held < HIDE_LIMIT_TICKS and (
                held < HIDE_MIN_TICKS or self._hide_again(observation, approach)
            ):
                self.utility = ("HIDE", "Stay in cover until the guards have passed")
                self.still_ticks = self.tile_ticks = 0
                return Action(self.actor_id, ActionKind.WAIT, tick)
            if held >= HIDE_LIMIT_TICKS:
                self.cover_ready_at = tick + COVER_REST_TICKS  # hiding here leads nowhere
            self.directive, self.hidden_since = Directive(tactics.ADVANCE), -1
            self.hide_approach = None
            self.utility = ("LEAVE", "The guards have passed: leave cover")
            if own.hidden_in is not None:
                return Action(self.actor_id, ActionKind.INTERACT, tick, target_id=own.hidden_in)
            return self._crawl_out(observation, approach)
        self.hidden_since = -1
        if self.directive.action != tactics.HIDE:
            return None
        action = self._hide(observation)  # walk to the approach, then slip in
        if action is not None:
            self.utility = ("COVER", "Slip into cover out of sight")
            self.still_ticks = self.tile_ticks = 0
        return action

    def _hide_again(self, observation: Observation, approach: Tile) -> bool:
        """Would the planner, standing outside, choose this cover again?"""
        if self._fleeing(observation):
            return True
        tick = observation.tick
        if self.stay_tick >= 0 and tick - self.stay_tick < REPLAN_TICKS:
            return self.stay
        self.foresight.refresh(tick)
        outside = self._search(observation, approach, self.plan_goals or self._goals(observation))
        self.stay = outside.hide == approach and outside.tiles == (approach,)
        self.stay = self.stay or not self.foresight.clear_for(approach, 1, LEAVE_STEPS)
        self.stay_tick = tick
        return self.stay

    def _crawl_out(self, observation: Observation, approach: Tile) -> Action:
        """Crawl from under a desk onto its approach tile before standing up."""
        own, tick = observation.own_status, observation.tick
        position = own.position or tile_center(own.tile)
        target = tile_center(approach)
        dx, dy = target[0] - position[0], target[1] - position[1]
        direction = (_sign(dx), 0) if abs(dx) > abs(dy) else (0, _sign(dy))
        if direction == (0, 0):
            return Action(self.actor_id, ActionKind.WAIT, tick)
        return Action(self.actor_id, ActionKind.MOVE, tick, direction)

    def _way_out(self, observation: Observation) -> Tile:
        own = observation.own_status.tile
        options = [tile for tile, cover in self.cover_at.items() if cover == own]
        return min(options, default=own)

    def _move(self, observation: Observation) -> Action:
        own, tick = observation.own_status, observation.tick
        if own.inventory.core_held and tick >= self.exit_replan_at:
            self.exit_replan_at = tick + 45
            self._choose_exit(observation)
        if own.crouched or not observation.map_static.can_walk(own.tile):
            return self._stand(observation, self._goal(observation))
        self.foresight.refresh(tick)
        core = next((hint for hint in observation.interactions if hint.kind == "Core"), None)
        if core is not None and not own.inventory.core_held:
            busy = own.interaction_progress_ticks > 0
            if (busy and self.beliefs.watched_by(observation, own.tile) is None) or (
                self.foresight.clear_for(own.tile, 0, TAKE_STEPS)
            ):
                self.utility = ("TAKE", "No guard will look here before the Core is out")
                return Action(self.actor_id, ActionKind.INTERACT, tick, target_id=core.target_id)
        current = self._plan(observation)
        cover = self.cover_at.get(own.tile)
        if current.hide == own.tile and current.tiles == (own.tile,) and cover is not None:
            self._begin_hide((cover, own.tile), tick)
            hidden = self._keep_hiding(observation)
            if hidden is not None:
                return hidden
        step = current.next_tile()
        fleeing = self._fleeing(observation)
        if step is None and current.finished:
            # At the goal: stand square on the tile so the Core is within reach.
            self.utility = ("ADVANCE", "Step up to the Core")
            return self._walk(observation, (own.tile,), False)
        if step is None:
            self.still_ticks = self.tile_ticks = 0  # a deliberate hold is not being stuck
            self.utility = (
                ("WAIT", "Hold here: the way ahead is watched")
                if current.exposed_steps == 0
                else ("HOLD", "Every way is watched: keep the least exposed place")
            )
            return Action(self.actor_id, ActionKind.WAIT, tick)
        self.utility = (
            ("EVADE", "Out of the guard's sight, fast")
            if fleeing
            else ("COVER", "Head for cover before the guard looks")
            if current.hide is not None
            else ("ADVANCE", "The way ahead stays out of sight")
            if current.exposed_steps == 0
            else ("RISK", "No unseen way: take the least watched one")
        )
        return self._walk(observation, current.tiles[1:], fleeing or current.runs_next())

    # -------------------------------------------------------------- planning
    def _plan(self, observation: Observation) -> Plan:
        own, tick = observation.own_status, observation.tick
        goals = self._goals(observation)
        key = (own.tile, goals, self.directive.action, tick >= self.bold_until)
        if self.plan is not None and key == self.plan_key and tick - self.plan_tick < REPLAN_TICKS:
            return self.plan
        self.plan = self._search(observation, own.tile, goals)
        self.plan_key, self.plan_tick, self.plan_goals = key, tick, goals
        self.path, self.path_cost = self.plan.tiles[1:], round(self.plan.cost)
        self.expanded = self.plan.expanded
        return self.plan

    def _search(self, observation: Observation, start: Tile, goals: tuple[Tile, ...]) -> Plan:
        field = self._field(observation, goals)
        taking = goals == self.take_tiles

        def finish(tile: Tile, step: int) -> bool:
            if field.get(tile) != 0:
                return False
            return not taking or self.foresight.clear_for(tile, step, TAKE_STEPS)

        own = observation.own_status
        return plan(
            observation.map_static,
            start,
            field,
            self.foresight.exposed,
            self.foresight.loud,
            self._pace(observation),
            horizon=HORIZON_STEPS,
            finish=finish,
            covers=self.cover_at if observation.tick >= self.cover_ready_at else (),
            hide_cost=HUNTED_HIDE_COST if self._hunted(observation) else HORIZON_STEPS + 5.0,
            blocked={guard.tile for guard in active_guards(observation)} - {own.tile},
            closed=self._closed(observation.tick),
        )

    def _pace(self, observation: Observation) -> Pace:
        """Prices from the policy: caution makes exposure dear and running dearer."""
        own, tick = observation.own_status, observation.tick
        cost = 40.0 + 5.0 * self.weights.risk_weight
        if tick < self.bold_until:
            cost /= 3  # patience ran out: accept being glimpsed to get on
        running = 1.0 if self.weights.sprint_always else 2.0 if self.weights.sprint else 3.0
        if observation.phase == MissionPhase.LOCKDOWN:
            running = 0.5  # the alarm is up: speed now beats quiet feet
        breath = 0
        if not own.crouched and not own.sprint_recharge_remaining:
            breath = own.sprint_ticks_remaining // STEP_TICKS
        return Pace(cost, running, breath)

    def _field(self, observation: Observation, goals: tuple[Tile, ...]) -> dict[Tile, int]:
        """Route costs to the goals: wide of hunting or posted guards, and
        through the junction of the route MCTS prefers."""
        tick = observation.tick
        blockers = self.foresight.blockers(tick)
        others = self._other_gates(tick)
        closed = self._closed(tick)
        burned = self._burned_gates(tick)
        key = (goals, observation.geometry_revision, blockers, others, closed, burned)
        field = self.fields.get(key)
        if field is None:
            if len(self.fields) > 64:
                self.fields.clear()
            extra = self.foresight.detour(tick) if blockers else {}
            for prices, gates in ((GATE_BIAS, others), (BURN_COST, burned)):
                reach = len(prices) - 1
                for x, y in gates:
                    for dx in range(-reach, reach + 1):
                        for dy in range(-reach, reach + 1):
                            tile = (x + dx, y + dy)
                            price = prices[max(abs(dx), abs(dy))]
                            extra[tile] = max(extra.get(tile, 0), price)
            field = self.fields[key] = distance_field(observation.map_static, goals, extra, closed)
        return field

    def _closed(self, tick: int) -> tuple[tuple[Tile, Tile], ...]:
        """Stair crossings that failed lately (someone holds the far landing)."""
        return tuple(
            sorted(crossing for crossing, until in self.closed_stairs.items() if until > tick)
        )

    def _remember_stair(self, observation: Observation) -> None:
        attempt = self.stair_attempt
        super()._remember_stair(observation)
        if attempt is not None and observation.own_status.tile != attempt.destination:
            until = observation.tick + STAIR_CLOSED_TICKS
            self.closed_stairs[(attempt.tile, attempt.destination)] = until
            self.closed_stairs[(attempt.destination, attempt.tile)] = until

    def _burn_gate(self, observation: Observation) -> None:
        """Seen near a junction: treat it as watched, and the routes through it as
        spent, for a while (a person spotted at a door tries the other one)."""
        own, tick = observation.own_status.tile, observation.tick
        graph = self.briefing.graph
        near = [
            node
            for node in graph.nodes
            if abs(node.tile[0] - own[0]) + abs(node.tile[1] - own[1]) <= BURN_TILES
        ]
        for node in near:
            self.burned[node.tile] = tick + BURN_TICKS
            for leg in self.legs:
                if node.node_id in leg.route.nodes:
                    self.abandoned[leg.route.nodes] = tick + BURN_TICKS

    def _burned_gates(self, tick: int) -> tuple[Tile, ...]:
        return tuple(sorted(tile for tile, until in self.burned.items() if until > tick))

    def _other_gates(self, tick: int) -> tuple[Tile, ...]:
        """First junctions of the routes MCTS did not pick, or gave up on."""
        graph = self.briefing.graph
        chosen = set(self.legs[0].route.nodes) if self.legs else set()
        gates = {
            graph.node(leg.route.nodes[0]).tile
            for leg in self.legs[1:]
            if leg.route.nodes and leg.route.nodes[0] not in chosen
        }
        gates |= {
            graph.node(nodes[0]).tile
            for nodes, until in self.abandoned.items()
            if until > tick and nodes and nodes[0] not in chosen
        }
        return tuple(sorted(gates))

    def _choose_exit(self, observation: Observation) -> None:
        """The exit whose route costs least now, held for a while once chosen."""
        own, tick = observation.own_status, observation.tick
        options = []
        for exit_tile in self.briefing.graph.exit_tiles:
            cost = self._field(observation, (exit_tile,)).get(own.tile)
            if cost is not None:
                switch = 0 if exit_tile == self.extraction_goal else EXIT_SWITCH_COST
                options.append((cost + switch, exit_tile))
        if not options:
            return
        choice = min(options)[1]
        if choice != self.extraction_goal and tick >= self.exit_locked_until:
            self.extraction_goal, self.exit_locked_until = choice, tick + EXIT_COMMIT_TICKS

    def _branch_threatened(self, observation: Observation, legs: tuple[tactics.Leg, ...]) -> bool:
        """Weigh the other routes at the start, after the theft, and whenever a
        guard holds the next junction."""
        if super()._branch_threatened(observation, legs):
            return True
        if self.trigger in ("deployment", "objective EXTRACT"):
            return len(legs) > 1
        if len(legs) < 2 or not legs[0].route.nodes:
            return False
        gate = self.briefing.graph.node(legs[0].route.nodes[0]).tile
        return any(
            max(abs(tile[0] - gate[0]), abs(tile[1] - gate[1])) <= 3
            for tile in self.foresight.blockers(observation.tick)
        )

    def _goals(self, observation: Observation) -> tuple[Tile, ...]:
        own = observation.own_status
        directive = self.directive
        if directive.action == tactics.RETREAT and directive.goal is not None:
            if own.tile != directive.goal and observation.tick < directive.until_tick:
                return (directive.goal,)
            self.directive = Directive(tactics.ADVANCE)
        if own.inventory.core_held:
            return (self.extraction_goal,)
        return self.take_tiles

    def _learn_geometry(self, observation: Observation) -> None:
        """Cover approaches and the tiles from which the Core can be lifted."""
        world_map = observation.map_static
        for tile in (*self.briefing.locker_tiles, *self.briefing.hide_tiles):
            for approach in approaches(self.briefing, tile):
                if world_map.can_walk(approach):
                    self.cover_at.setdefault(approach, tile)
        cx, cy = self.briefing.core_tile
        core = tile_center((cx, cy))
        reach = self.rules.interaction_range_units - UNIT // 30
        self.take_tiles = tuple(
            tile
            for tile in ((cx + dx, cy + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1))
            if world_map.can_walk(tile)
            and hypot(tile_center(tile)[0] - core[0], tile_center(tile)[1] - core[1]) <= reach
        )
        self.geometry_known = True

    def _track_progress(self, observation: Observation) -> None:
        """Lose patience after waiting long without getting any closer."""
        own, tick = observation.own_status, observation.tick
        field = self._field(observation, self.plan_goals) if self.plan_goals else None
        remaining = field.get(own.tile) if field else None
        if remaining is None:
            return
        if self.best_remaining is None or remaining < self.best_remaining:
            self.best_remaining, self.progress_at = remaining, tick
        policy = self.weights.policy_id
        patience = PATIENCE_TICKS[
            "GHOST" if "CAUTIOUS" in policy else "RUSH" if "BOLD" in policy else "BALANCED"
        ]
        if self._hunted(observation):
            self.progress_at = tick  # never lose patience with a guard on the hunt
        elif tick - self.progress_at >= patience and tick >= self.bold_until:
            self.bold_until, self.progress_at = tick + BOLD_TICKS, tick
            self.best_remaining = None

    def _hunted(self, observation: Observation) -> bool:
        """Is a guard nearby moving about checking, searching or chasing?

        A guard holding a post is routed around instead (see ``_field``).
        """
        tick = observation.tick
        own = observation.own_status.tile
        return any(
            track.alert in ALERTED
            and tick - track.tick <= HUNT_MEMORY_TICKS
            and (track.still_since < 0 or track.tick - track.still_since < POSTED_TICKS)
            and abs(track.tile[0] - own[0]) + abs(track.tile[1] - own[1]) <= HUNT_TILES
            for track in self.foresight.tracks.values()
        )

    def _fleeing(self, observation: Observation) -> bool:
        if observation.tick - self.last_watched <= FLEE_TICKS:
            return True
        return any(
            entity.alert in ("SPOTTED", "CHASE") and entity.actor_id in self.beliefs.visible
            for entity in active_guards(observation)
        )

    # ------------------------------------------------------------- execution
    def _walk(self, observation: Observation, path: tuple[Tile, ...], sprint: bool) -> Action:
        """Follow the planned tiles: stairs, bodies and corners, nothing else."""
        own, tick = observation.own_status, observation.tick
        position = own.position or tile_center(own.tile)
        while (
            path
            and max(abs(a - b) for a, b in zip(tile_center(path[0]), position, strict=True))
            <= ARRIVE
        ):
            path = path[1:]
        if not path:
            return Action(self.actor_id, ActionKind.WAIT, tick)
        stair = next(
            (
                link
                for link in observation.map_static.stairs
                if link.tile == own.tile and link.destination == path[0]
            ),
            None,
        )
        if stair is not None:
            backoff = self.stair_backoff
            if backoff is not None and backoff.blocked and stair == backoff.link:
                return Action(self.actor_id, ActionKind.WAIT, tick)
            self.stair_attempt = stair
            return Action(self.actor_id, ActionKind.INTERACT, tick, target_id=stair.object_id)
        target = tile_center(path[0])
        center = tile_center(own.tile)
        if path[0][0] != own.tile[0] and abs(center[1] - position[1]) > ARRIVE:
            target = (position[0], center[1])
        elif path[0][1] != own.tile[1] and abs(center[0] - position[0]) > ARRIVE:
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
        if self.still_ticks >= 2:  # pressed against a body: try a parallel lane
            side = lanes.side_lane(observation, self.actor_id, direction, self.still_ticks)
            if side is not None:
                return Action(self.actor_id, ActionKind.MOVE, tick, side)
        sprint = sprint and not own.crouched
        return Action(self.actor_id, ActionKind.MOVE, tick, direction, sprint=sprint)

    def _done(self, action: Action, position: tuple[int, int]) -> Action:
        tick = action.tick_issued
        if action.kind == ActionKind.MELEE and action.target_id:
            self.melee_ready_at[action.target_id] = (
                tick + self.rules.melee_stun_ticks + self.rules.melee_immunity_ticks
            )
        self.previous, self.last_action = position, action
        self.last_kind, self.last_tick = action.kind, tick
        self._record()
        return action
