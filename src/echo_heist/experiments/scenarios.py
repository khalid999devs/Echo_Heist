"""Versioned 24-scenario registry for paired policy comparisons (P07-SR2).

Scenarios share the canonical map, rules, defenders and props. Each one only
varies the Companion's start tile, deployment hold, tool stock or an already
stolen Core, plus its seed; those differences are recorded in run metadata.
"""

import json
from dataclasses import dataclass

from echo_heist.core.contracts.autonomy.policy import PolicySelection
from echo_heist.core.contracts.config.scenario import IntruderStart
from echo_heist.infrastructure.persistence.experience import decode_policy
from echo_heist.infrastructure.resources import resource_bytes

CATEGORIES = (
    "patrol-timing",
    "route-upper",
    "route-lower",
    "junction",
    "partial-vision",
    "heard-only",
    "stale-sighting",
    "capture-threat",
    "scarce-tools",
    "core-theft",
    "lockdown-return",
)


@dataclass(frozen=True, slots=True)
class Scenario:
    scenario_id: str
    category: str
    seed: int
    start: IntruderStart
    hold_ticks: int = 0


@dataclass(frozen=True, slots=True)
class Suite:
    suite_id: str
    map_id: str
    tick_cap: int
    policies: tuple[tuple[str, PolicySelection], ...]
    scenarios: tuple[Scenario, ...]


def _scenario(item: object) -> Scenario:
    if not isinstance(item, dict):
        raise ValueError("A scenario must be an object")
    tile = item.get("tile")
    category = str(item["category"])
    if category not in CATEGORIES:
        raise ValueError(f"Unknown scenario category {category!r}")
    start = IntruderStart(
        None if tile is None else (int(tile[0]), int(tile[1])),
        int(item.get("echo", 3)),
        int(item.get("emp", 1)),
        int(item.get("melee", 2)),
        bool(item.get("core_held", False)),
    )
    seed, hold = item["seed"], item.get("hold", 0)
    if type(seed) is not int or type(hold) is not int:
        raise ValueError("Scenario seed and hold must be integers")
    return Scenario(str(item["id"]), category, seed, start, hold)


def load_suite(path: str = "data/experiments/scenarios.json") -> Suite:
    payload = json.loads(resource_bytes(path))
    if not isinstance(payload, dict) or payload.get("schema") != 1:
        raise ValueError("Unsupported scenario registry")
    policies = tuple(
        (str(name), decode_policy(value)) for name, value in payload["policies"].items()
    )
    scenarios = tuple(_scenario(item) for item in payload["scenarios"])
    ids = [scenario.scenario_id for scenario in scenarios]
    if len(set(ids)) != len(ids) or len(scenarios) != 24 or len(policies) != 4:
        raise ValueError("The registry needs 24 unique scenarios and four policies")
    if len({policy for _, policy in policies}) != 4:
        raise ValueError("The four compared policies must differ")
    return Suite(
        str(payload["suite"]), str(payload["map_id"]), int(payload["tick_cap"]), policies, scenarios
    )
