"""Small seeded MOVE/WAIT trace used by --headless and packaging smoke checks."""

import json
from dataclasses import asdict
from hashlib import sha256

from echo_heist import __version__
from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.world import ActorSpawn, StaticMap
from echo_heist.core.simulation.engine import Simulation
from echo_heist.core.simulation.randomness import seeded_rng


def run_fixture(seed: int = 1042) -> dict[str, object]:
    world_map = StaticMap("foundation-diagnostic", 4, 4, frozenset({(3, 3)}))
    simulation = Simulation(world_map, (ActorSpawn("operative", (0, 0)),), seed=seed)
    trace: list[dict[str, object]] = []
    for direction in ((1, 0), (0, 1), (-1, 0), (0, -1), (0, 0)):
        kind = ActionKind.WAIT if direction == (0, 0) else ActionKind.MOVE
        result = simulation.step((Action("operative", kind, simulation.tick, direction),))
        trace.extend(asdict(event) for event in result.events)
    canonical = json.dumps(trace, sort_keys=True, separators=(",", ":"))
    return {
        "diagnostic": "phase-1-tile-fixture",
        "schema_version": 1,
        "version": __version__,
        "seed": seed,
        "tick": simulation.tick,
        "ticks_per_second": simulation.ticks_per_second,
        "final_tile": list(simulation.observe("operative").own_status.tile),
        "events": len(trace),
        "state_hash": simulation.fingerprint(),
        "event_hash": sha256(canonical.encode("utf-8")).hexdigest(),
        "world_rng_sample": seeded_rng(seed, "world").randrange(1_000_000),
    }
