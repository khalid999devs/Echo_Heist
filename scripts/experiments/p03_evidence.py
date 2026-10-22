"""P03 defender evidence: default-security route outcomes, guard traces and replay checks.

Usage: uv run --locked python scripts/experiments/p03_evidence.py --output <file.json>
Writes ignored output only; compare its hashes across machines/commits.
"""

import argparse
import json
import platform
import sys
import time
from dataclasses import asdict
from pathlib import Path

from echo_heist import __version__
from echo_heist.core.simulation.replay import canonical_hash
from echo_heist.diagnostics.guard_evidence import replay_matches, route_steps, run_route
from echo_heist.infrastructure.resources import load_game_rules, load_sensor_rules, resource_bytes
from echo_heist.level.io import load_tiled_map
from echo_heist.level.security import build_security_registry

SCENARIOS = (
    ("upper-tools", "upper", "upper", True),
    ("lower-tools", "lower", "lower", True),
    ("cross-tools", "cross", "upper", True),
    ("upper-no-tools", "upper", "upper", False),
    ("lower-no-tools", "lower", "lower", False),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=1042)
    args = parser.parse_args()
    level = load_tiled_map(resource_bytes("data/maps/vault-five-zone.json"))
    rules, sensors = load_game_rules(), load_sensor_rules()
    registry = build_security_registry(level, rules)
    results = []
    for name, branch, back, tools in SCENARIOS:
        started = time.perf_counter()
        result = run_route(
            name,
            level,
            rules,
            sensors,
            registry,
            route_steps(level, branch, back),
            seed=args.seed,
            use_tools=tools,
        )
        elapsed = time.perf_counter() - started
        replayed = replay_matches(level, rules, sensors, registry, result)
        results.append(
            {
                "name": name,
                "outcome": result.outcome,
                "ticks": result.ticks,
                "capture_by": result.capture_by,
                "tools": result.tools,
                "events": result.events,
                "decisions_by_algorithm": result.algorithms,
                "decisions_by_evidence": result.evidence,
                "max_expanded_nodes": result.max_expanded,
                "state_trails": result.states,
                "event_chain_hash": canonical_hash(list(result.log.tick_hashes)),
                "final_fingerprint": result.log.final_fingerprint,
                "replay_matched": replayed,
                "wall_seconds": round(elapsed, 3),
            }
        )
        print(f"{name}: {result.outcome} at {result.ticks} ticks, replay={replayed}")
    first = run_route("header", level, rules, sensors, registry, [], seed=args.seed)
    report = {
        "version": __version__,
        "python": platform.python_version(),
        "machine": platform.machine(),
        "system": platform.platform(),
        "replay_header": asdict(first.log.header),
        "registry": [
            {
                "guard": value.guard_id,
                "kind": value.kind.value,
                "role": value.role.value,
                "zone": value.zone_id,
                "chokepoints": value.chokepoint_ids,
            }
            for value in registry.assignments
        ],
        "scenarios": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    expected = {"upper-tools": "WIN", "lower-tools": "WIN", "cross-tools": "WIN"}
    ok = all(
        item["replay_matched"] and expected.get(item["name"], item["outcome"]) == item["outcome"]
        for item in results
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
