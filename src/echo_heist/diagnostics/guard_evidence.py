"""Headless P03 evidence: real default-security routes, decision traces and replay.

The route driver reads only the operative's own Observation (like a human with
the keyboard) and emits ordinary intents. It is a diagnostic QA tool, never a
gameplay controller, and it does not peek at hidden guard state.
"""

from collections import Counter
from dataclasses import dataclass, field, replace

from echo_heist.ai.navigation.grid import bfs
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.security.model import SensorRules
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import MissionPhase, Position, Tile, tile_center
from echo_heist.core.simulation.engine import Simulation
from echo_heist.core.simulation.replay import (
    ReplayLog,
    ReplayRecorder,
    build_header,
    verify_replay,
)
from echo_heist.diagnostics.facility_routes import Branch, mission_path
from echo_heist.level.model import LevelData
from echo_heist.level.security import SecurityRegistry

ARRIVE = UNIT // 8
type Step = Tile | str  # "HOLD" holds the Core interaction until lockdown


@dataclass
class RouteDriver:
    """Operative intents from its own observation: move, stairs, Core, EMP/melee."""

    rules: GameRules
    actor_id: str
    use_tools: bool = True
    sprint: bool = True
    previous: Position | None = None
    tools_used: Counter[str] = field(default_factory=Counter)

    def _bodies(self, observation: Observation) -> frozenset[Tile]:
        own = observation.own_status.tile
        return frozenset(
            entity.tile
            for entity in observation.visible_entities
            if entity.disabled or entity.stunned
        ) - {own}

    def _threat(self, observation: Observation, position: Position, reach: int) -> bool:
        return any(
            entity.position is not None
            and not entity.disabled
            and not entity.stunned
            and entity.kind.value in ("SENTINEL", "TRACKER", "INTERCEPTOR")
            and (entity.position[0] - position[0]) ** 2 + (entity.position[1] - position[1]) ** 2
            <= reach**2
            for entity in observation.visible_entities
        )

    def arrived(self, observation: Observation, goal: Tile) -> bool:
        position = observation.own_status.position
        assert position is not None
        if self.use_tools and goal in self._bodies(observation):
            return True
        return max(abs(a - b) for a, b in zip(position, tile_center(goal), strict=True)) <= ARRIVE

    def action(self, observation: Observation, goal: Tile) -> Action:
        tick, own = observation.tick, observation.own_status
        position = own.position
        assert position is not None
        if own.stair_ticks_remaining:
            return Action(self.actor_id, ActionKind.WAIT, tick)
        if self.use_tools:
            if own.inventory.emp_charges and self._threat(
                observation, position, self.rules.capture_range_units + UNIT // 8
            ):
                self.tools_used["EMP"] += 1
                return Action(self.actor_id, ActionKind.EMP, tick)
            if self._threat(observation, position, self.rules.melee_range_units):
                self.tools_used["MELEE"] += 1
                return Action(self.actor_id, ActionKind.MELEE, tick)
        stair = next(
            (
                link
                for link in observation.map_static.stairs
                if link.tile == own.tile and link.destination == goal
            ),
            None,
        )
        if stair is not None:
            return Action(self.actor_id, ActionKind.INTERACT, tick, target_id=stair.object_id)
        target = tile_center(goal)
        bodies = self._bodies(observation)
        if bodies:
            route_map = replace(
                observation.map_static, blocked_tiles=observation.map_static.blocked_tiles | bodies
            )
            path = bfs(route_map, own.tile, goal).path
            if len(path) > 1:
                target = tile_center(path[1])
                center = tile_center(own.tile)
                if path[1][0] != own.tile[0] and abs(center[1] - position[1]) > ARRIVE:
                    target = (position[0], center[1])
                elif path[1][1] != own.tile[1] and abs(center[0] - position[0]) > ARRIVE:
                    target = (center[0], position[1])
        dx, dy = target[0] - position[0], target[1] - position[1]
        direction = (
            (1 if dx > ARRIVE else -1 if dx < -ARRIVE else 0),
            0,
        )
        if direction == (0, 0):
            direction = (0, 1 if dy > ARRIVE else -1 if dy < -ARRIVE else 0)
        if self.previous == position and direction[0] and abs(dy) > ARRIVE:
            direction = (0, 1 if dy > 0 else -1)
        elif self.previous == position and direction[1] and abs(dx) > ARRIVE:
            direction = (1 if dx > 0 else -1, 0)
        self.previous = position
        if direction == (0, 0):
            return Action(self.actor_id, ActionKind.WAIT, tick)
        return Action(self.actor_id, ActionKind.MOVE, tick, direction, sprint=self.sprint)


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    name: str
    outcome: str
    ticks: int
    capture_by: str | None
    events: dict[str, int]
    algorithms: dict[str, int]
    evidence: dict[str, int]
    max_expanded: dict[str, int]
    states: dict[str, list[str]]
    tools: dict[str, int]
    log: ReplayLog


def build_simulation(
    level: LevelData, rules: GameRules, sensors: SensorRules, registry: SecurityRegistry, seed: int
) -> Simulation:
    return Simulation(
        level.static_map,
        level.spawns(),
        rules=rules,
        mission=level.mission(),
        seed=seed,
        security=registry.spec(sensors),
    )


def run_route(
    name: str,
    level: LevelData,
    rules: GameRules,
    sensors: SensorRules,
    registry: SecurityRegistry,
    steps: list[Step],
    *,
    seed: int = 1042,
    limit: int = 9_000,
    use_tools: bool = True,
    sprint: bool = True,
) -> ScenarioResult:
    simulation = build_simulation(level, rules, sensors, registry, seed)
    header = build_header(
        level.static_map, rules, sensors, registry_revision=registry.revision, seed=seed
    )
    recorder = ReplayRecorder(simulation, header)
    driver = RouteDriver(rules, level.operative_id, use_tools=use_tools, sprint=sprint)
    pending = list(steps)
    counts: Counter[str] = Counter()
    algorithms: Counter[str] = Counter()
    evidence: Counter[str] = Counter()
    expanded: dict[str, int] = {}
    states: dict[str, list[str]] = {}
    end = None
    while simulation.tick < limit:
        observation = simulation.observe(level.operative_id)
        if pending and pending[0] == "HOLD":
            if observation.phase == MissionPhase.LOCKDOWN:
                pending.pop(0)
                continue
            action = Action(
                level.operative_id, ActionKind.INTERACT, observation.tick, target_id=level.core_id
            )
        elif pending and isinstance(pending[0], tuple):
            if driver.arrived(observation, pending[0]):
                pending.pop(0)
                continue
            action = driver.action(observation, pending[0])
        else:
            action = Action(level.operative_id, ActionKind.WAIT, observation.tick)
        result = recorder.step((action,))
        for event in result.events:
            counts[event.kind.value] += 1
            if event.kind == EventKind.POLICY_DECISION:
                details = dict(event.details)
                algorithm = str(details["algorithm"])
                algorithms[algorithm] += 1
                # NOISE/MOTION goals carry the Sentinel's Sugeno urgency.
                evidence[str(details.get("evidence_kind") or "ROUTINE")] += 1
                nodes = details.get("expanded_nodes")
                if isinstance(nodes, int):
                    expanded[algorithm] = max(expanded.get(algorithm, 0), nodes)
                trail = states.setdefault(event.actor_id, [])
                if not trail or trail[-1] != details["state"]:
                    trail.append(str(details["state"]))
        if result.mission_end is not None:
            end = result.mission_end
            break
        if not pending:
            break
    return ScenarioResult(
        name,
        end.outcome.value if end else "UNFINISHED",
        simulation.tick,
        end.capture_by if end else None,
        dict(sorted(counts.items())),
        dict(sorted(algorithms.items())),
        dict(sorted(evidence.items())),
        dict(sorted(expanded.items())),
        {key: value[:24] for key, value in sorted(states.items())},
        dict(driver.tools_used),
        recorder.log(),
    )


def route_steps(level: LevelData, branch: Branch, back: Branch) -> list[Step]:
    return [*mission_path(level, branch), "HOLD", *mission_path(level, back, returning=True)]


def replay_matches(
    level: LevelData,
    rules: GameRules,
    sensors: SensorRules,
    registry: SecurityRegistry,
    result: ScenarioResult,
) -> bool:
    fresh = build_simulation(level, rules, sensors, registry, result.log.header.seed)
    header = build_header(
        level.static_map,
        rules,
        sensors,
        registry_revision=registry.revision,
        seed=result.log.header.seed,
    )
    return verify_replay(fresh, result.log, header).matched
