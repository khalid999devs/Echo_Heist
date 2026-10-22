"""Deterministic replay: a versioned header, recorded intents and per-tick hashes.

A seed alone cannot reproduce a run. The header pins the build, map, rules,
sensor config and guard registry; the log holds every external action by tick.
Replaying feeds the same actions to a fresh Simulation and compares the
committed event stream tick by tick, then the privileged final fingerprint.
"""

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from hashlib import sha256

from echo_heist import __version__
from echo_heist.core.contracts.actions import Action
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import GameEvent
from echo_heist.core.contracts.results import StepResult
from echo_heist.core.contracts.security.model import SensorRules
from echo_heist.core.contracts.world import StaticMap
from echo_heist.core.simulation.engine import Simulation

REPLAY_SCHEMA = 1
FINGERPRINT_SCHEMA = 8


def canonical_hash(value: object) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False, default=list)
    return sha256(text.encode()).hexdigest()


def map_hash(world_map: StaticMap) -> str:
    return canonical_hash(
        {
            "id": world_map.map_id,
            "size": (world_map.width, world_map.height, world_map.tile_size_px),
            "blocked": sorted(world_map.blocked_tiles),
            "opaque": sorted(world_map.opaque_tiles),
            "crouch": sorted(world_map.crouch_tiles),
            "obstacles": [
                (o.object_id, o.left, o.top, o.right, o.bottom, sorted(o.reserved_tiles), o.opaque)
                for o in world_map.obstacles
            ],
            "objects": [asdict(obj) for obj in world_map.objects],
            "stairs": [asdict(link) for link in world_map.stairs],
        }
    )


def events_hash(events: Iterable[GameEvent]) -> str:
    return canonical_hash([asdict(event) for event in events])


@dataclass(frozen=True, slots=True)
class ReplayHeader:
    replay_schema: int
    game_version: str
    fingerprint_schema: int
    map_id: str
    map_hash: str
    rules_hash: str
    sensor_hash: str
    registry_revision: str
    seed: int
    simulation_hz: int
    mode: str


def build_header(
    world_map: StaticMap,
    rules: GameRules,
    sensors: SensorRules,
    *,
    registry_revision: str,
    seed: int,
    mode: str = "HUMAN",
) -> ReplayHeader:
    return ReplayHeader(
        REPLAY_SCHEMA,
        __version__,
        FINGERPRINT_SCHEMA,
        world_map.map_id,
        map_hash(world_map),
        canonical_hash(asdict(rules)),
        canonical_hash(asdict(sensors)),
        registry_revision,
        seed,
        rules.simulation_hz,
        mode,
    )


@dataclass(frozen=True, slots=True)
class ReplayLog:
    header: ReplayHeader
    actions: tuple[tuple[Action, ...], ...]
    tick_hashes: tuple[str, ...]
    final_fingerprint: str


@dataclass(frozen=True, slots=True)
class ReplayCheck:
    matched: bool
    ticks: int
    first_divergent_tick: int | None


class ReplayRecorder:
    """Steps a Simulation while recording its external intents and event hashes."""

    def __init__(self, simulation: Simulation, header: ReplayHeader) -> None:
        self.simulation, self.header = simulation, header
        self._actions: list[tuple[Action, ...]] = []
        self._hashes: list[str] = []

    def step(self, actions: Iterable[Action] = ()) -> StepResult:
        supplied = tuple(actions)
        result = self.simulation.step(supplied)
        self._actions.append(supplied)
        self._hashes.append(events_hash(result.events))
        return result

    def log(self) -> ReplayLog:
        return ReplayLog(
            self.header,
            tuple(self._actions),
            tuple(self._hashes),
            self.simulation.fingerprint(),
        )


def verify_replay(simulation: Simulation, log: ReplayLog, header: ReplayHeader) -> ReplayCheck:
    """Re-run ``log`` on a fresh ``simulation`` built from an identical ``header``."""
    if header != log.header:
        return ReplayCheck(False, 0, 0)
    for index, (actions, expected) in enumerate(zip(log.actions, log.tick_hashes, strict=True)):
        if events_hash(simulation.step(actions).events) != expected:
            return ReplayCheck(False, index + 1, index + 1)
    matched = simulation.fingerprint() == log.final_fingerprint
    ticks = len(log.actions)
    return ReplayCheck(matched, ticks, None if matched else ticks)
