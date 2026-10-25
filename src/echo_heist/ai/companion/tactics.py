"""Abstract tactical model for the Companion's strategic MCTS.

States are coarse: the zone the Companion is in, its chosen chokepoint route
and progress, carried Core, gadget stock, elapsed abstract time and outcome
flags, plus one *sampled* zone per guard. Guard zones are drawn from the
Companion's beliefs each iteration (determinization); actual hidden guard
positions are never available to this module. Transitions use approximate
guard rules: a guard sharing the Companion's zone may detect it, a detection
may become a capture, and guards drift between neighboring sectors.
"""

from dataclasses import dataclass, replace
from random import Random

from echo_heist.ai.companion.briefing import MissionBriefing, PolicyWeights
from echo_heist.ai.navigation.routes import ZoneRoute
from echo_heist.core.contracts.security.director import RouteGraph
from echo_heist.core.contracts.world import ActorKind

ADVANCE, ALTERNATE, WAIT, HIDE, RETREAT = "ADVANCE", "ALTERNATE", "WAIT", "HIDE", "RETREAT"
ECHO, EMP, MELEE = "ECHO", "EMP", "MELEE"
ORDER = (ADVANCE, ALTERNATE, WAIT, HIDE, RETREAT, ECHO, EMP, MELEE)
EXPOSURE = {ActorKind.SENTINEL: 0.22, ActorKind.TRACKER: 0.28, ActorKind.INTERCEPTOR: 0.25}
SECONDS_PER_STEP_TILE = 0.42  # walking ~2.4 tiles/second
RAW_FLOOR, RAW_SPAN = -120.0, 260.0
PLAYOUT_ADVANCE = 0.6
ALERT_DETECTIONS = 0.3
CONVERGE = 0.5
RESUME = 0.3
SWITCH_SECONDS = 4.0
ARRIVAL = 0.5


def _draw(belief: dict[str, float], rng: Random) -> str:
    roll, chosen = rng.random(), ""
    for candidate in sorted(belief):
        roll -= belief[candidate]
        chosen = candidate
        if roll <= 0:
            break
    return chosen


def zone_step(graph: RouteGraph, start: str, goal: str) -> str | None:
    """Next sector on a shortest zone-graph path from ``start`` toward ``goal``."""
    if start == goal or not start or not goal:
        return None
    parent: dict[str, str] = {start: start}
    frontier = [start]
    while frontier:
        following: list[str] = []
        for zone in frontier:
            for node in graph.nodes:
                if zone not in node.zones:
                    continue
                other = node.zones[1] if node.zones[0] == zone else node.zones[0]
                if other not in parent:
                    parent[other] = zone
                    following.append(other)
        frontier = sorted(following)
        if goal in parent:
            step = goal
            while parent[step] != start:
                step = parent[step]
            return step
    return None


@dataclass(frozen=True, slots=True)
class Leg:
    """A route toward the current goal, plus the zone of each segment."""

    route: ZoneRoute
    zones: tuple[str, ...]  # len(nodes) + 1 segments, the last is the goal zone
    segment_steps: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class TacticalState:
    leg: int
    progress: int  # route segments completed on the current leg
    carrying: bool
    echo: int
    emp: int
    seconds: float
    detections: float  # expected confirmed detections so far
    gadgets: int
    captured: bool
    extracted: bool
    guards: tuple[tuple[str, str, bool], ...]  # (guard ID, sampled zone, active)
    distracted: int
    hidden: bool
    zone: str
    depth: int = 0
    advanced: int = 0  # net route segments gained toward the current objective
    survival: float = 1.0  # probability of not having been grabbed on this trajectory


def legs(
    graph: RouteGraph, routes: tuple[ZoneRoute, ...], start_zone: str, goal_zone: str
) -> tuple[Leg, ...]:
    built: list[Leg] = []
    for route in routes:
        zones = [start_zone]
        for node_id in route.nodes:
            first, second = graph.node(node_id).zones
            zones.append(second if zones[-1] == first else first)
        if zones[-1] != goal_zone:
            continue
        arrivals = (*route.arrival_steps, route.total_steps)
        steps = tuple(b - a for a, b in zip((0, *arrivals[:-1]), arrivals, strict=True))
        built.append(Leg(route, tuple(zones), steps))
    return tuple(built)


@dataclass(slots=True)
class CompanionModel:
    """TacticalModel implementation; every input comes from beliefs or the briefing."""

    briefing: MissionBriefing
    weights: PolicyWeights
    root: TacticalState
    outbound: tuple[Leg, ...]
    homeward: tuple[Leg, ...]
    beliefs: dict[str, dict[str, float]]
    kinds: dict[str, ActorKind]
    hide_zones: frozenset[str]
    emp_ready: bool  # a visible guard is inside EMP range now (observed)
    melee_ready: bool  # a visible guard is inside melee reach now (observed)
    can_retreat: bool  # the Companion has a remembered path back
    hide_ready: bool  # authored cover is reachable from here (observed geometry)
    echo_useful: bool  # an active guard is in view now, so a decoy is plausible
    priors: dict[str, dict[str, float]]  # briefed home-sector prior per guard
    reroute_ready: bool  # observed danger on the current branch justifies a switch
    committed: bool = False  # no progress for long: holds are excluded at the root

    def _legs(self, state: TacticalState) -> tuple[Leg, ...]:
        return self.homeward if state.carrying else self.outbound

    def sample(self, rng: Random) -> TacticalState:
        guards = [
            (guard_id, _draw(self.beliefs[guard_id], rng), True)
            for guard_id in sorted(self.beliefs)
        ]
        return replace(self.root, guards=tuple(guards))

    def actions(self, state: TacticalState) -> tuple[str, ...]:
        if self.terminal(state):
            return ()
        legal = [ADVANCE, WAIT]
        root = state.depth == 0
        if len(self._legs(state)) > 1 and state.progress == 0 and (not root or self.reroute_ready):
            legal.append(ALTERNATE)
        root = state.depth == 0
        if not state.hidden and (self.hide_ready if root else state.zone in self.hide_zones):
            legal.append(HIDE)
        if state.progress > 0 or (state.depth == 0 and self.can_retreat):
            legal.append(RETREAT)
        threat = any(zone == state.zone and active for _, zone, active in state.guards)
        if state.echo > 0 and (self.echo_useful if root else threat):
            legal.append(ECHO)
        if state.emp > 0 and (self.emp_ready if root else threat):
            legal.append(EMP)
        if root and self.melee_ready:
            legal.append(MELEE)
        if root and self.committed:
            legal = [action for action in legal if action not in (WAIT, HIDE, RETREAT)]
        preferred = self.weights.preferred
        return tuple(sorted(legal, key=lambda action: (action != preferred, ORDER.index(action))))

    def terminal(self, state: TacticalState) -> bool:
        return state.captured or state.extracted

    def _exposed(
        self, state: TacticalState, zone: str, factor: float, rng: Random
    ) -> TacticalState:
        """Approximate guard rules: a co-located active guard may detect, then grab."""
        for guard_id, guard_zone, active in state.guards:
            if not active or guard_zone != zone:
                continue
            # Observed-risk routing keeps a cautious path out of more cones.
            care = 1.0
            chance = (
                EXPOSURE.get(self.kinds.get(guard_id, ActorKind.SENTINEL), 0.25) * factor * care
            )
            if state.distracted:
                chance *= 0.4
            if state.hidden:
                chance *= 0.1
            # Expected-value exposure (no Bernoulli draw): far lower rollout variance.
            grab = 0.45
            if state.emp > 0 and chance >= 0.2:
                state = replace(state, emp=state.emp - 1, gadgets=state.gadgets + 1)
                grab = 0.1
            survival = state.survival * (1 - chance * grab)
            state = replace(state, detections=state.detections + chance, survival=survival)
            if survival < 0.02:
                return replace(state, captured=True)
        return state

    def _drift(self, state: TacticalState, rng: Random, follow: str | None) -> TacticalState:
        """Patrols wander between neighbouring sectors; once the intruder has been
        detected (or the Core alarm sounds) defenders converge on its sector."""
        graph = self.briefing.graph
        alert = state.carrying or state.detections >= ALERT_DETECTIONS
        moved = []
        for guard_id, zone, active in state.guards:
            if follow is not None and zone == state.zone and active:
                moved.append((guard_id, follow, active))
                continue
            toward = zone_step(graph, zone, state.zone)
            if alert and active and toward is not None and rng.random() < CONVERGE:
                zone = toward
            elif not alert and rng.random() < RESUME:
                # An unalerted patrol resumes its briefed sector: waiting lets a
                # guard that was seen ahead move on, but cannot clear an unseen one.
                zone = _draw(self.priors.get(guard_id, {zone: 1.0}), rng) or zone
            moved.append((guard_id, zone, active))
        return replace(state, guards=tuple(moved), distracted=max(0, state.distracted - 1))

    def step(self, state: TacticalState, action: str, rng: Random) -> TacticalState:
        return replace(self._transition(state, action, rng), depth=state.depth + 1)

    def _transition(self, state: TacticalState, action: str, rng: Random) -> TacticalState:
        legs_now = self._legs(state)
        leg = legs_now[state.leg % len(legs_now)] if legs_now else None
        if action == ADVANCE and leg is not None:
            index = min(state.progress, len(leg.zones) - 1)
            seconds = (
                leg.segment_steps[min(index, len(leg.segment_steps) - 1)] * SECONDS_PER_STEP_TILE
            )
            state = replace(state, seconds=state.seconds + seconds, hidden=False)
            state = self._exposed(state, leg.zones[index], 1.0, rng)
            if state.captured:
                return state
            progress = state.progress + 1
            state = replace(state, advanced=state.advanced + 1)
            if progress >= len(leg.zones):
                if state.carrying:
                    return replace(state, extracted=True, progress=progress)
                # Reach and take the Core (lockdown follows), then start the way home.
                state = replace(state, carrying=True, leg=0, progress=0, seconds=state.seconds + 1)
                return self._drift(replace(state, zone=leg.zones[-1]), rng, leg.zones[-1])
            next_zone = leg.zones[progress]
            # Stepping through the gate exposes the Companion to whoever holds the next sector.
            state = self._exposed(
                replace(state, progress=progress, zone=next_zone), next_zone, ARRIVAL, rng
            )
            if state.captured:
                return state
            return self._drift(state, rng, None)
        if action == ALTERNATE:
            return replace(state, leg=state.leg + 1, seconds=state.seconds + SWITCH_SECONDS)
        if action == RETREAT and leg is not None:
            back = max(0, state.progress - 1)
            factor = 0.6 if state.progress else 0.3  # backing out of view in the same sector
            state = replace(
                state,
                progress=back,
                zone=leg.zones[back],
                seconds=state.seconds + 3,
                # Backing off always gives up ground that must be re-crossed later.
                advanced=state.advanced - 1,
            )
            return self._drift(self._exposed(state, state.zone, factor, rng), rng, None)
        if action == HIDE:
            state = replace(state, hidden=True, seconds=state.seconds + 4)
            return self._drift(self._exposed(state, state.zone, 1.0, rng), rng, None)
        if action == ECHO:
            state = replace(
                state,
                echo=state.echo - 1,
                gadgets=state.gadgets + 1,
                distracted=2,
                seconds=state.seconds + 1,
            )
            return self._drift(state, rng, None)
        if action in (EMP, MELEE):
            calm = tuple(
                (guard_id, zone, active and zone != state.zone)
                for guard_id, zone, active in state.guards
            )
            state = replace(
                state,
                guards=calm,
                emp=state.emp - (action == EMP),
                gadgets=state.gadgets + 1,
                seconds=state.seconds + 1,
            )
            return state
        state = replace(state, seconds=state.seconds + 3)  # WAIT
        return self._drift(self._exposed(state, state.zone, 0.35, rng), rng, None)

    def raw(self, state: TacticalState) -> float:
        """Blueprint trial reward: +100 extraction, +30 per objective step (zone
        gained or Core taken), -capture, -detection, -5 per gadget, -time."""
        gained = 100.0 * state.extracted + 30.0 * (
            state.advanced + state.carrying - self.root.carrying
        )
        return (
            state.survival * (gained - self.ahead(state))
            - self.weights.capture_penalty * (1.0 - state.survival)
            - self.weights.detection_penalty * state.detections
            - 5.0 * state.gadgets
            - self.weights.time_cost * (state.seconds - self.root.seconds)
        )

    def ahead(self, state: TacticalState) -> float:
        """Leaf heuristic: briefed baseline risk of the sectors still to cross.

        Without it a depth-4 horizon would prefer waiting forever, because a
        delayed crossing simply falls outside the lookahead. Waiting therefore
        only pays when observed danger now exceeds the briefed baseline.
        """
        if state.extracted:
            return 0.0
        legs_now = self._legs(state)
        zones: list[str] = []
        if legs_now:
            zones.extend(legs_now[state.leg % len(legs_now)].zones[state.progress :])
        if not state.carrying and self.homeward:
            zones.extend(self.homeward[0].zones[1:])
        care = 1.0
        cost = 0.0
        for zone in zones:
            for guard_id, prior in self.priors.items():
                chance = (
                    prior.get(zone, 0.0)
                    * EXPOSURE.get(self.kinds.get(guard_id, ActorKind.SENTINEL), 0.25)
                    * care
                )
                cost += chance * (
                    self.weights.detection_penalty + 0.45 * self.weights.capture_penalty
                )
        return cost

    def playout(self, state: TacticalState, legal: tuple[str, ...], rng: Random) -> str:
        """Default rollout policy: usually keep moving, otherwise a random legal reply."""
        if ADVANCE in legal and rng.random() < PLAYOUT_ADVANCE:
            return ADVANCE
        return legal[rng.randrange(len(legal))]

    def reward(self, state: TacticalState) -> float:
        return min(1.0, max(0.0, (self.raw(state) - RAW_FLOOR) / RAW_SPAN))
