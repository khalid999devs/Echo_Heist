"""P05 SR evidence: real prop lifecycles on the packaged facility, both modes.

Usage: uv run --locked python scripts/experiments/p05_evidence.py --output <file.json>
       [--seeds 12]
Every number comes from an actual run of the packaged Simulation through the
same gateway the game uses. Companion attempts are run with and without the
authored props on the same seeds so the prop effect is visible, not estimated.
Durations are wall-clock profiling values excluded from the deterministic hash.
"""

import argparse
import json
import platform
import sys
import time
from collections import Counter
from pathlib import Path

from echo_heist import __version__
from echo_heist.ai.navigation.grid import bfs
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
from echo_heist.core.contracts.environment.model import EnvironmentSpec
from echo_heist.core.contracts.events import EventKind
from echo_heist.core.contracts.world import tile_center
from echo_heist.core.simulation.replay import canonical_hash
from echo_heist.diagnostics.guard_evidence import route_steps, run_route
from echo_heist.infrastructure.resources import load_game_rules, load_sensor_rules, resource_bytes
from echo_heist.level.io import load_tiled_map

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


def companion(gateway: NexusGateway, preset: str, seed: int, props: bool) -> dict[str, object]:
    level = gateway.level
    request = DeploymentRequest(
        ControlMode.COMPANION, seed, level.static_map.map_id, PRESETS[preset]
    )
    run = AutonomousMission(
        level,
        gateway.rules,
        gateway.sensors,
        gateway.registry,
        request,
        protocol=None,
        protocol_state=None,
        environment=gateway.environment if props else None,
    )
    changes: Counter[str] = Counter()
    noises: Counter[str] = Counter()
    while run.tick < TICK_CAP:
        result = run.step(())
        for event in result.events:
            details = dict(event.details)
            if event.kind == EventKind.PROP_CHANGED:
                changes[str(details.get("state") or details.get("cue"))] += 1
            elif event.kind == EventKind.NOISE_CREATED and details["kind"] in (
                "DOOR",
                "GLASS",
                "METAL",
            ):
                noises[str(details["kind"])] += 1
        if result.mission_end is not None:
            break
    end = run.presentation_snapshot().mission_end
    return {
        "preset": preset,
        "seed": seed,
        "props": props,
        "outcome": end.outcome.value if end else "TIMEOUT",
        "ticks": run.tick,
        "prop_changes": dict(sorted(changes.items())),
        "prop_noises": dict(sorted(noises.items())),
        "fingerprint": run.fingerprint()[:16],
    }


def human_lifecycle(gateway: NexusGateway, delay: int = 240) -> dict[str, object]:
    """A scripted Human on the packaged map: kick a canister, then use a locker."""
    level = gateway.level
    run = gateway.deploy(DeploymentRequest(ControlMode.HUMAN, 1042, level.static_map.map_id))
    actor = level.operative_id
    locker = next(p for p in gateway.environment.props if p.object_id == "hide-2")
    can = next(p for p in gateway.environment.props if p.object_id == "canister-service-1")
    noises: Counter[str] = Counter()
    cues: list[str] = []

    def step(action: Action) -> None:
        result = run.step((action,))
        noises.update(
            str(dict(e.details)["kind"]) for e in result.events if e.kind == EventKind.NOISE_CREATED
        )
        for cue in run.presentation_snapshot().environment.cues:
            if f"{cue.event_id}:{cue.kind.value}" not in cues:
                cues.append(f"{cue.event_id}:{cue.kind.value}")

    def walk_to(tile: tuple[int, int]) -> None:
        """Follow a BFS route tile by tile with plain MOVE intents (no shortcuts)."""
        own = run.observe(actor).own_status
        for waypoint in bfs(run.observe(actor).map_static, own.tile, tile).path[1:]:
            for _ in range(120):
                own = run.observe(actor).own_status
                position = own.position or tile_center(own.tile)
                goal = tile_center(waypoint)
                dx, dy = goal[0] - position[0], goal[1] - position[1]
                if abs(dx) <= 3_000 and abs(dy) <= 3_000:
                    break
                direction = ((dx > 3_000) - (dx < -3_000), (dy > 3_000) - (dy < -3_000))
                step(Action(actor, ActionKind.MOVE, run.tick, direction))

    for _ in range(delay):  # let the service patrol pass before crossing its corridor
        step(Action(actor, ActionKind.WAIT, run.tick))
    walk_to((can.tile[0], can.tile[1] - 1))
    for _ in range(14):  # step down onto it: a bump kicks it along that step
        step(Action(actor, ActionKind.MOVE, run.tick, (0, 1)))
    rolled = next(
        p for p in run.presentation_snapshot().environment.props if p.object_id == can.object_id
    )
    walk_to(locker.tile)
    offered = [h.kind for h in run.observe(actor).interactions]
    step(Action(actor, ActionKind.HIDE, run.tick, target_id=locker.object_id))
    hidden = run.observe(actor).own_status.hidden_in
    for _ in range(30):
        step(Action(actor, ActionKind.WAIT, run.tick))
    step(Action(actor, ActionKind.INTERACT, run.tick, target_id=locker.object_id))
    end = run.presentation_snapshot().mission_end
    return {
        "canister_rest_tile": (rolled.position[0] // 30_000, rolled.position[1] // 30_000),
        "offered_at_locker": offered,
        "hidden_in": hidden,
        "left_locker": run.observe(actor).own_status.hidden_in is None,
        "prop_noises": {k: noises[k] for k in ("DOOR", "GLASS", "METAL")},
        "cues": cues,
        "ended": end.outcome.value if end else None,
        "tick": run.tick,
        "fingerprint": run.fingerprint()[:16],
    }


def inventory(spec: EnvironmentSpec) -> list[dict[str, object]]:
    return [
        {
            "id": p.object_id,
            "kind": p.kind.value,
            "tiles": list(p.tiles),
            "horizontal": p.horizontal,
        }
        for p in spec.props
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=12)
    args = parser.parse_args()
    began = time.perf_counter()
    level = load_tiled_map(resource_bytes("data/maps/vault-five-zone.json"))
    rules, sensors = load_game_rules(), load_sensor_rules()
    gateway = NexusGateway(level, rules, sensors, None)
    runs = [
        companion(gateway, preset, seed, props)
        for preset in PRESETS
        for seed in range(args.seeds)
        for props in (True, False)
    ]
    summary = {}
    for preset in PRESETS:
        for props in (True, False):
            rows = [r for r in runs if r["preset"] == preset and r["props"] is props]
            summary[f"{preset}/{'props' if props else 'no-props'}"] = dict(
                Counter(str(r["outcome"]) for r in rows)
            )
    used = Counter[str]()
    for row in runs:
        if row["props"]:
            used.update(row["prop_changes"])  # type: ignore[arg-type]
    repeat = companion(gateway, "BALANCED", 1, True)
    routes = {
        name: run_route(
            name,
            level,
            rules,
            sensors,
            gateway.registry,
            route_steps(level, a, b),
            environment=gateway.environment,
        ).outcome
        for name, a, b in (
            ("upper-upper", "upper", "upper"),
            ("lower-upper", "lower", "upper"),
            ("cross-upper", "cross", "upper"),
            ("lower-lower", "lower", "lower"),
        )
    }
    deterministic = {
        "props": inventory(gateway.environment),
        "rules": {
            key: getattr(gateway.environment.rules, key)
            for key in gateway.environment.rules.__dataclass_fields__
        },
        "runs": runs,
        "summary": summary,
        "companion_prop_changes": dict(sorted(used.items())),
        "repeat_balanced_seed_1_matches": repeat["fingerprint"]
        == next(
            r["fingerprint"]
            for r in runs
            if r["preset"] == "BALANCED" and r["seed"] == 1 and r["props"]
        ),
        "human_routes_with_props": routes,
        "human_lifecycle": human_lifecycle(gateway),
    }
    report = {
        "evidence": "p05-suhita",
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
    print(
        json.dumps(
            {
                "summary": summary,
                "routes": routes,
                "lifecycle": deterministic["human_lifecycle"],
                "hash": report["deterministic_hash"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
