"""Fixed-seed Companion harness: one real attempt per scenario/policy (P07-SR1).

Each record has a deterministic part (decisions, outcome, score, algorithm
metrics, fingerprint) and a separate ``timing`` part with wall-clock profiling
that is excluded from any comparison hash. NEXUS memory is the reset baseline
for every run (no protocol). The tick cap is a runner limit only: hitting it is
reported as TIMEOUT, never as an in-game deadline.
"""

from collections import Counter
from dataclasses import dataclass
from statistics import median
from time import perf_counter_ns

from echo_heist.autonomy.mission import AutonomousMission
from echo_heist.core.contracts.autonomy.model import ControlMode
from echo_heist.core.contracts.autonomy.policy import DeploymentRequest, PolicySelection
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.config.scoring import ScoringRules
from echo_heist.core.contracts.environment.model import EnvironmentSpec
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.security.model import SensorRules
from echo_heist.experiments.scenarios import Scenario
from echo_heist.level.model import LevelData
from echo_heist.level.security import SecurityRegistry


@dataclass(frozen=True, slots=True)
class Facility:
    level: LevelData
    rules: GameRules
    sensors: SensorRules
    registry: SecurityRegistry
    environment: EnvironmentSpec
    scoring: ScoringRules


def _quantiles(values: list[float]) -> dict[str, float]:
    if not values:
        return {"p50": 0.0, "p95": 0.0, "max": 0.0}
    ordered = sorted(values)
    return {
        "p50": round(median(ordered), 4),
        "p95": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 4),
        "max": round(ordered[-1], 4),
    }


def run_scenario(
    facility: Facility,
    scenario: Scenario,
    policy_name: str,
    policy: PolicySelection,
    tick_cap: int,
) -> dict[str, object]:
    level = facility.level
    request = DeploymentRequest(
        ControlMode.COMPANION, scenario.seed, level.static_map.map_id, policy
    )
    run = AutonomousMission(
        level,
        facility.rules,
        facility.sensors,
        facility.registry,
        request,
        protocol=None,
        protocol_state=None,
        environment=facility.environment,
        scoring=facility.scoring,
        start=scenario.start,
        hold_ticks=scenario.hold_ticks,
    )
    actor = run.actor_id
    events: Counter[str] = Counter()
    chosen: Counter[str] = Counter()
    zones: list[str] = []
    stairs: list[str] = []
    interceptor = {"searches": 0, "evaluated_leaves": 0, "pruned_branches": 0}
    posts: list[str] = []
    fuzzy_evaluations = transitions = 0
    decisions = visited = best = overrides = expanded = no_path = 0
    still = longest_still = 0
    last_trace = last_search = -1
    previous = run.observe(actor).own_status.position
    tick_ms: list[float] = []
    while run.tick < tick_cap:
        started = perf_counter_ns()
        result = run.step(())
        tick_ms.append((perf_counter_ns() - started) / 1e6)
        for event in result.events:
            events[event.kind.value] += 1
            details = dict(event.details)
            if event.kind == EventKind.POLICY_DECISION:
                transitions += 1
                fuzzy_evaluations += details.get("fuzzy_urgency") is not None
            elif event.kind == EventKind.STAIR_USED and event.actor_id == actor:
                stairs.append(str(details["stair_id"]))
        own = run.observe(actor).own_status
        zone = level.zone_at(own.tile)
        if zone is not None and (not zones or zones[-1] != zone.zone_id):
            zones.append(zone.zone_id)
        still = still + 1 if own.position == previous else 0
        longest_still, previous = max(longest_still, still), own.position
        telemetry = run.telemetry()
        trace = telemetry.companion
        if trace is not None and trace.evaluated_tick != last_trace:
            last_trace = trace.evaluated_tick
            decisions += 1
            chosen[trace.chosen_action] += 1
            used = [a for a in trace.alternatives if a.visits]
            visited += len(used)
            best += max((a.visits for a in used), default=0)
            expanded += trace.expanded_nodes
            no_path += not trace.path
        if trace is not None and trace.utility_action:
            overrides += 1
        plan = telemetry.nexus.interceptor if telemetry.nexus else None
        if plan is not None and plan.evaluated_tick != last_search:
            last_search = plan.evaluated_tick
            interceptor["searches"] += 1
            interceptor["evaluated_leaves"] += plan.evaluated_nodes
            interceptor["pruned_branches"] += plan.pruned_nodes
            if not posts or posts[-1] != plan.post_id:
                posts.append(plan.post_id)
        if result.mission_end is not None:
            break
    end = run.presentation_snapshot().mission_end
    terminal = run.terminal
    capture_zone = None
    if end is not None and end.capture_by is not None:
        where = level.zone_at(run.observe(actor).own_status.tile)
        capture_zone = where.zone_id if where else "corridor"
    return {
        "scenario": scenario.scenario_id,
        "category": scenario.category,
        "policy": policy_name,
        "seed": scenario.seed,
        "outcome": end.outcome.value if end else "TIMEOUT",
        "ticks": run.tick,
        "capture_by": end.capture_by if end else None,
        "capture_zone": capture_zone,
        "score": terminal.score if terminal else None,
        "grade": terminal.grade if terminal else None,
        "detection_encounters": run.simulation.detection_encounters(),
        "raw_confirmed_sightings": events["SIGHTING_CONFIRMED"],
        "completion_stealth_pace": [
            terminal.completion_points,
            terminal.stealth_points,
            terminal.pace_points,
        ]
        if terminal
        else None,
        "tools": [run.tools.echo, run.tools.emp, run.tools.melee],
        "route_zones": zones,
        "stairs": stairs,
        "longest_still_ticks": longest_still,
        "mcts": {
            "decisions": decisions,
            "mean_visited_alternatives": round(visited / max(1, decisions), 3),
            "mean_best_visits": round(best / max(1, decisions), 2),
            "chosen": dict(sorted(chosen.items())),
            "utility_override_ticks": overrides,
        },
        "astar": {"expanded_nodes": expanded, "plans_without_path": no_path},
        "sentinel": {"fuzzy_evaluations": fuzzy_evaluations, "fsm_decisions": transitions},
        "interceptor": {**interceptor, "posts": posts},
        "decisive": [e.kind.value for e in (terminal.decisive_events if terminal else ())],
        "fingerprint": run.fingerprint()[:16],
        "timing": {"tick_ms": _quantiles(tick_ms)},
    }
