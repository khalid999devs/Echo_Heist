"""P08 policy comparison: every registry scenario under all four policies.

Usage: uv run --locked python scripts/experiments/comparison.py --output-dir <dir>
       [--only s01-patrol-early,s02-patrol-3s] [--policies GHOST,BALANCED]
Writes runs.json (full records), runs.csv and summary.md to the given folder.
Every value comes from a real Simulation run through the same Companion,
defenders, props and scoring the game uses, with NEXUS memory at its reset
baseline. Wall-clock timing is reported separately and excluded from the hash.
"""

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from statistics import median
from typing import Any

from echo_heist import __version__
from echo_heist.core.simulation.replay import canonical_hash, map_hash
from echo_heist.experiments.harness import Facility, run_scenario
from echo_heist.experiments.scenarios import Suite, load_suite
from echo_heist.infrastructure.resources import (
    load_environment_rules,
    load_game_rules,
    load_scoring_rules,
    load_sensor_rules,
    resource_bytes,
)
from echo_heist.level.environment import build_environment
from echo_heist.level.io import load_tiled_map
from echo_heist.level.security import build_security_registry

ROOT = Path(__file__).resolve().parents[2]


def metadata(facility: Facility, suite: Suite) -> dict[str, Any]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"
    lock = ROOT / "uv.lock"
    return {
        "suite": suite.suite_id,
        "version": __version__,
        "commit": commit,
        "uv_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest() if lock.exists() else None,
        "map_hash": map_hash(facility.level.static_map),
        "rules_hash": canonical_hash(asdict(facility.rules)),
        "sensors_hash": canonical_hash(asdict(facility.sensors)),
        "environment_hash": canonical_hash(asdict(facility.environment)),
        "scoring": canonical_hash(asdict(facility.scoring)),
        "scoring_version": facility.scoring.scoring_version,
        "pace_reference_ticks": facility.scoring.pace_reference_ticks,
        "registry_revision": facility.registry.revision,
        "nexus_memory": "reset baseline (no protocol)",
        "rng": "seeded per scenario (companion-mcts stream)",
        "tick_cap": suite.tick_cap,
    }


def summarize(runs: list[dict[str, Any]], policies: list[str]) -> dict[str, Any]:
    table: dict[str, Any] = {}
    for name in policies:
        rows = [r for r in runs if r["policy"] == name]
        wins = [r for r in rows if r["outcome"] == "WIN"]
        table[name] = {
            "runs": len(rows),
            "outcomes": dict(Counter(str(r["outcome"]) for r in rows)),
            "win_rate": round(len(wins) / max(1, len(rows)), 3),
            "median_win_ticks": median(int(r["ticks"]) for r in wins) if wins else None,
            "mean_encounters": round(
                sum(int(r["detection_encounters"]) for r in rows) / max(1, len(rows)),
                2,
            ),
            "grades": dict(Counter(str(r["grade"]) for r in rows)),
            "mean_tools": [
                round(sum(r["tools"][i] for r in rows) / max(1, len(rows)), 2) for i in range(3)
            ],
        }
    return table


def write_csv(path: Path, runs: list[dict[str, Any]]) -> None:
    columns = [
        "scenario",
        "category",
        "policy",
        "seed",
        "outcome",
        "ticks",
        "score",
        "grade",
        "detection_encounters",
        "raw_confirmed_sightings",
        "capture_by",
        "capture_zone",
        "longest_still_ticks",
        "fingerprint",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow([*columns, "echo", "emp", "melee", "mcts_decisions", "tick_ms_p95"])
        for r in runs:
            tools = r["tools"]
            mcts, timing = r["mcts"], r["timing"]
            assert isinstance(tools, list) and isinstance(mcts, dict) and isinstance(timing, dict)
            writer.writerow(
                [
                    *(r[c] for c in columns),
                    *tools,
                    mcts["decisions"],
                    timing["tick_ms"]["p95"],
                ]
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--only", default="", help="comma-separated scenario IDs")
    parser.add_argument("--policies", default="", help="comma-separated policy names")
    args = parser.parse_args()
    began = time.perf_counter()
    level = load_tiled_map(resource_bytes("data/maps/vault-five-zone.json"))
    rules = load_game_rules()
    facility = Facility(
        level,
        rules,
        load_sensor_rules(),
        build_security_registry(level, rules),
        build_environment(level, load_environment_rules()),
        load_scoring_rules(),
    )
    suite = load_suite()
    chosen = {s for s in args.only.split(",") if s}
    names = [n for n in args.policies.split(",") if n] or [n for n, _ in suite.policies]
    policies = [(n, p) for n, p in suite.policies if n in names]
    scenarios = [s for s in suite.scenarios if not chosen or s.scenario_id in chosen]
    runs = []
    for scenario in scenarios:
        for name, policy in policies:
            record = run_scenario(facility, scenario, name, policy, suite.tick_cap)
            runs.append(record)
            print(scenario.scenario_id, name, record["outcome"], record["ticks"], flush=True)
    first = runs[0] if runs else None
    repeat = (
        run_scenario(
            facility,
            next(s for s in scenarios if s.scenario_id == first["scenario"]),
            str(first["policy"]),
            dict(policies)[str(first["policy"])],
            suite.tick_cap,
        )
        if first
        else None
    )
    deterministic = {
        "metadata": metadata(facility, suite),
        "summary": summarize(runs, names),
        "runs": [{k: v for k, v in r.items() if k != "timing"} for r in runs],
        "repeat_first_run_matches": bool(repeat and repeat["fingerprint"] == first["fingerprint"]),
    }
    tick_p95 = [r["timing"]["tick_ms"]["p95"] for r in runs]
    report = {
        **deterministic,
        "deterministic_hash": canonical_hash(deterministic),
        "profiling": {
            "python": platform.python_version(),
            "machine": platform.machine(),
            "system": platform.system(),
            "processor": platform.processor(),
            "seconds": round(time.perf_counter() - began, 1),
            "tick_ms_p95_median_across_runs": median(tick_p95) if tick_p95 else None,
            "tick_ms_p95_max_across_runs": max(tick_p95) if tick_p95 else None,
            "per_run_timing": {f"{r['scenario']}/{r['policy']}": r["timing"] for r in runs},
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "runs.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    write_csv(args.output_dir / "runs.csv", runs)
    print(json.dumps({"summary": deterministic["summary"], "hash": report["deterministic_hash"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
