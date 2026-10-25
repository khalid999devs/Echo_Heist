"""P04 algorithm evidence: autonomous outcomes, real MCTS/alpha-beta/NEXUS metrics, reset.

Usage: uv run --locked python scripts/experiments/p04_evidence.py --output <file.json>
       [--seeds 24]
Writes JSON only to the given path. Every number comes from an actual run of the
packaged Simulation; nothing is estimated. Durations are wall-clock profiling
values and are excluded from the deterministic hash.
"""

import argparse
import json
import platform
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from statistics import median

from echo_heist import __version__
from echo_heist.ai.guards.interceptor import InterceptProblem, build_tree, route_hypotheses
from echo_heist.ai.navigation.grid import distances_from
from echo_heist.ai.planning.minimax import alphabeta, minimax
from echo_heist.autonomy.gateway import NexusGateway
from echo_heist.autonomy.mission import AutonomousMission
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.autonomy.model import ControlMode
from echo_heist.core.contracts.autonomy.policy import (
    DeploymentRequest,
    Emergency,
    GuardReaction,
    Navigation,
    PolicySelection,
    Risk,
)
from echo_heist.core.contracts.results import MissionEnd, RunOutcome
from echo_heist.core.contracts.security.director import NexusEvidence, NexusStatus
from echo_heist.core.simulation.replay import canonical_hash
from echo_heist.diagnostics.guard_evidence import route_steps, run_route
from echo_heist.infrastructure.persistence.protocols import FILE_NAME, ProtocolStore
from echo_heist.infrastructure.resources import load_game_rules, load_sensor_rules, resource_bytes
from echo_heist.level.io import load_tiled_map
from echo_heist.level.security import build_security_registry

PRESETS = {
    "GHOST": PolicySelection(
        Navigation.SAFEST, GuardReaction.HIDE, Emergency.ESCAPE, Risk.CAUTIOUS
    ),
    "BALANCED": PolicySelection(),
    "RUSH": PolicySelection(
        Navigation.SHORTEST, GuardReaction.CONSIDER_ECHO, Emergency.MELEE_IF_ADJACENT, Risk.BOLD
    ),
}
TICK_CAP = 9_000  # evidence-runner cap only; never an in-game deadline


def companion_run(level, rules, sensors, registry, preset: str, seed: int) -> dict[str, object]:
    request = DeploymentRequest(
        ControlMode.COMPANION, seed, level.static_map.map_id, PRESETS[preset]
    )
    run = AutonomousMission(
        level, rules, sensors, registry, request, protocol=None, protocol_state=None
    )
    events: Counter[str] = Counter()
    tasks: Counter[str] = Counter()
    decisions = alternatives = overrides = 0
    best_visits: list[int] = []
    stages = Counter()
    last = None
    seen_tasks: set[tuple[str, str, int]] = set()
    while run.tick < TICK_CAP:
        result = run.step(())
        events.update(event.kind.value for event in result.events)
        telemetry = run.telemetry()
        trace = telemetry.companion
        if trace is not None and trace.evaluated_tick != last:
            last = trace.evaluated_tick
            decisions += 1
            visited = [a for a in trace.alternatives if a.visits]
            alternatives += len(visited)
            best_visits.append(max(a.visits for a in visited))
            assert run.controller is not None and run.controller.last_result is not None
            counts = run.controller.last_result.stages
            stages.update(
                selections=counts.selections,
                expansions=counts.expansions,
                rollout_steps=counts.rollout_steps,
                backpropagations=counts.backpropagations,
            )
        if trace is not None and trace.utility_action:
            overrides += 1
        if telemetry.nexus is not None:
            for task in telemetry.nexus.tasks:
                key = (task.guard_id, task.task, task.evidence_tick)
                if key not in seen_tasks:
                    seen_tasks.add(key)
                    tasks[task.task] += 1
        if result.mission_end is not None:
            break
    end = run.presentation_snapshot().mission_end
    return {
        "preset": preset,
        "seed": seed,
        "outcome": end.outcome.value if end else "TIMEOUT",
        "ticks": run.tick,
        "capture_by": end.capture_by if end else None,
        "mcts_decisions": decisions,
        "mean_visited_alternatives": round(alternatives / max(1, decisions), 3),
        "mean_best_visits": round(sum(best_visits) / max(1, len(best_visits)), 2),
        "stages": dict(stages),
        "utility_override_ticks": overrides,
        "confirmed_sightings": events["SIGHTING_CONFIRMED"],
        "tools": events["TOOL_USED"],
        "nexus_dispatches": dict(sorted(tasks.items())),
        "fingerprint": run.fingerprint(),
    }


def interceptor_parity(level, rules, registry) -> list[dict[str, object]]:
    """Minimax vs alpha-beta on the real lockdown search from several guard tiles."""
    graph, director = registry.graph, registry.director
    hypotheses = route_hypotheses(
        graph, graph.core_tile, graph.exit_tile, distances_from(level.static_map, graph.core_tile)
    )
    posts = tuple(
        sorted({n for h in hypotheses for n in h.nodes if "core-chamber" in graph.node(n).zones})
    )
    rows = []
    for tile in ((59, 26), (50, 29), (50, 13), (55, 18)):
        own = distances_from(level.static_map, tile)
        problem = InterceptProblem(
            hypotheses,
            posts,
            tuple((post, own[graph.node(post).tile]) for post in posts),
            graph,
            0,
            director.guard_ticks_per_tile,
            director.intruder_ticks_per_tile,
        )
        tree = build_tree(problem, director.interceptor_depth)
        plain = minimax(tree, (None, None, None), director.interceptor_depth, False)
        fast = alphabeta(tree, (None, None, None), director.interceptor_depth, False)
        rows.append(
            {
                "guard_tile": tile,
                "hypotheses": [h.label for h in hypotheses],
                "minimax": {
                    "value": round(plain.value, 6),
                    "post": plain.move,
                    "leaves": plain.evaluated,
                },
                "alphabeta": {
                    "value": round(fast.value, 6),
                    "post": fast.move,
                    "leaves": fast.evaluated,
                    "pruned": fast.pruned,
                },
                "agree": (plain.value, plain.move) == (fast.value, fast.move),
            }
        )
    return rows


def reset_check(level, rules, sensors) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as folder:
        service = NexusGateway(level, rules, sensors, ProtocolStore(Path(folder) / FILE_NAME))

        def waited() -> str:
            run = service.deploy(DeploymentRequest(ControlMode.HUMAN, 7, level.static_map.map_id))
            for _ in range(240):
                run.step((Action(level.operative_id, ActionKind.WAIT, run.tick),))
            return run.fingerprint()

        baseline = waited()
        end = MissionEnd(RunOutcome.CAPTURED, 1, level.operative_id, None)
        for _ in range(2):
            service._attempt_ended(
                end, NexusStatus(1, (), "", None, NexusEvidence(0, (("security-control", 1),), 0))
            )
        state = service.protocols()
        adapted = waited()
        service.reset_protocols()
        return {
            "protocol": state.active.protocol_id if state.active else None,
            "reason": state.active.reason if state.active else None,
            "adapted_differs": adapted != baseline,
            "reset_matches_baseline": waited() == baseline,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=24)
    args = parser.parse_args()
    began = time.perf_counter()
    level = load_tiled_map(resource_bytes("data/maps/vault-five-zone.json"))
    rules, sensors = load_game_rules(), load_sensor_rules()
    registry = build_security_registry(level, rules)
    runs = [
        companion_run(level, rules, sensors, registry, preset, seed)
        for preset in PRESETS
        for seed in range(args.seeds)
    ]
    repeat = companion_run(level, rules, sensors, registry, "BALANCED", 6)
    summary = {}
    for preset in PRESETS:
        rows = [row for row in runs if row["preset"] == preset]
        wins = [int(row["ticks"]) for row in rows if row["outcome"] == "WIN"]
        summary[preset] = {
            "outcomes": dict(Counter(str(row["outcome"]) for row in rows)),
            "median_win_ticks": median(wins) if wins else None,
            "mean_confirmed_sightings": round(
                sum(int(r["confirmed_sightings"]) for r in rows) / len(rows), 2
            ),
            "mean_tools": round(sum(int(r["tools"]) for r in rows) / len(rows), 2),
        }
    routes = {
        name: run_route(name, level, rules, sensors, registry, route_steps(level, a, b)).outcome
        for name, a, b in (
            ("upper-upper", "upper", "upper"),
            ("lower-upper", "lower", "upper"),
            ("cross-upper", "cross", "upper"),
            ("lower-lower", "lower", "lower"),
        )
    }
    deterministic = {
        "runs": runs,
        "summary": summary,
        "repeat_balanced_seed_6_matches": repeat["fingerprint"]
        == next(r["fingerprint"] for r in runs if r["preset"] == "BALANCED" and r["seed"] == 6),
        "interceptor_parity": interceptor_parity(level, rules, registry),
        "protocol_reset": reset_check(level, rules, sensors),
        "human_routes": routes,
        "registry_revision": registry.revision,
    }
    report = {
        "evidence": "p04-suhita",
        "version": __version__,
        "python": platform.python_version(),
        "machine": platform.machine(),
        "system": platform.system(),
        "seeds_per_preset": args.seeds,
        "tick_cap": TICK_CAP,
        "deterministic": deterministic,
        "deterministic_hash": canonical_hash(deterministic),
        "seconds": round(time.perf_counter() - began, 1),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"summary": summary, "routes": routes, "hash": report["deterministic_hash"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
