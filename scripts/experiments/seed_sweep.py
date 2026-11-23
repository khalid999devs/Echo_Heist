"""Companion outcomes over a range of seeds, with who caught each run and when.

Usage: uv run --locked python scripts/experiments/seed_sweep.py FIRST LAST
       [--policies GHOST,BALANCED,RUSH] [--workers 8] [--rows rows.json]
Runs every seed in [FIRST, LAST) for each preset through the same Simulation,
defenders, NEXUS, props and scoring as the game, with NEXUS memory at its
reset baseline. Prints one summary line per preset. ``--rows`` also writes
each run's seed, outcome, theft tick, captor and final tile to that file.
"""

import argparse
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from echo_heist.autonomy.mission import COMPANION_ID, AutonomousMission
from echo_heist.core.contracts.autonomy.policy import PRESETS, DeploymentRequest
from echo_heist.infrastructure.resources import (
    load_environment_rules,
    load_game_rules,
    load_sensor_rules,
    resource_bytes,
)
from echo_heist.level.environment import build_environment
from echo_heist.level.io import load_tiled_map
from echo_heist.level.security import build_security_registry

LIMIT_TICKS = 9000  # five minutes of game time


def run(seed: int, policy: str) -> dict[str, Any]:
    level = load_tiled_map(resource_bytes("data/maps/vault-five-zone.json"))
    rules = load_game_rules()
    mission = AutonomousMission(
        level,
        rules,
        load_sensor_rules(),
        build_security_registry(level, rules),
        DeploymentRequest("COMPANION", seed, level.static_map.map_id, PRESETS[policy]),
        protocol=None,
        protocol_state=None,
        environment=build_environment(level, load_environment_rules()),
    )
    theft = None
    while mission.tick < LIMIT_TICKS:
        result = mission.step(())
        own = mission.observe(COMPANION_ID).own_status
        if theft is None and own.inventory.core_held:
            theft = mission.tick
        if result.mission_end:
            end, terminal = result.mission_end, result.terminal
            return {
                "seed": seed,
                "policy": policy,
                "outcome": end.outcome.value,
                "tick": mission.tick,
                "theft": theft,
                "by": end.capture_by,
                "at": list(own.tile),
                "score": terminal.score if terminal else None,
                "grade": terminal.grade if terminal else None,
            }
    return {"seed": seed, "policy": policy, "outcome": "TIMEOUT", "tick": mission.tick}


def summary(rows: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    runs = [row for row in rows if row["policy"] == policy]
    caught = [row for row in runs if row["outcome"] == "CAPTURED"]
    return {
        "policy": policy,
        "runs": len(runs),
        "wins": sum(row["outcome"] == "WIN" for row in runs),
        "thefts": sum(bool(row.get("theft")) for row in runs),
        "timeouts": sum(row["outcome"] == "TIMEOUT" for row in runs),
        "caught_before_theft": dict(Counter(r["by"] for r in caught if not r["theft"])),
        "caught_after_theft": dict(Counter(r["by"] for r in caught if r["theft"])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("first", type=int)
    parser.add_argument("last", type=int)
    parser.add_argument("--policies", default="GHOST,BALANCED,RUSH")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--rows", type=Path)
    args = parser.parse_args()
    policies = args.policies.split(",")
    jobs = [(seed, policy) for policy in policies for seed in range(args.first, args.last)]
    with ProcessPoolExecutor(args.workers) as pool:
        rows = list(pool.map(run, *zip(*jobs, strict=True), chunksize=2))
    for policy in policies:
        print(json.dumps(summary(rows, policy)))
    if args.rows:
        args.rows.write_text(json.dumps(rows), encoding="utf-8")


if __name__ == "__main__":
    main()
