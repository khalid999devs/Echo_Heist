"""P05 props on the packaged facility, deployed exactly as the game does, in both modes."""

from collections import Counter

import pytest

from echo_heist.autonomy.gateway import NexusGateway
from echo_heist.core.contracts.autonomy.policy import PRESETS, DeploymentRequest
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.environment.presentation import PropKind
from echo_heist.core.contracts.results import RunOutcome
from echo_heist.core.contracts.security.model import SensorRules
from echo_heist.diagnostics.guard_evidence import route_steps, run_route
from echo_heist.infrastructure.resources import load_sensor_rules, resource_bytes
from echo_heist.level.io import load_tiled_map
from echo_heist.level.model import LevelData

COMPANION_WIN, COMPANION_CAPTURE = 44, 18


@pytest.fixture(scope="module")
def level() -> LevelData:
    return load_tiled_map(resource_bytes("data/maps/vault-five-zone.json"))


@pytest.fixture(scope="module")
def sensors() -> SensorRules:
    return load_sensor_rules()


@pytest.fixture(scope="module")
def gateway(level: LevelData, rules: GameRules, sensors: SensorRules) -> NexusGateway:
    return NexusGateway(level, rules, sensors, None)


def test_every_authored_prop_is_live_from_tick_zero(
    level: LevelData, gateway: NexusGateway
) -> None:
    run = gateway.deploy(DeploymentRequest("HUMAN", 1042, level.static_map.map_id))
    props = run.presentation_snapshot().environment.props
    assert Counter(prop.kind for prop in props) == {
        PropKind.DOOR: 3,
        PropKind.GLASS: 2,
        PropKind.CANISTER: 3,
        PropKind.LOCKER: 8,
    }
    assert all(p.openness == 1.0 for p in props if p.kind == PropKind.DOOR)
    assert not any(p.broken or p.occupant_id for p in props)
    world_map = run.observe(level.operative_id).map_static
    glass = {
        tile
        for spec in gateway.environment.props
        if spec.kind == PropKind.GLASS
        for tile in spec.tiles
    }
    doors = {
        tile
        for spec in gateway.environment.props
        if spec.kind == PropKind.DOOR
        for tile in spec.tiles
    }
    assert glass <= world_map.blocked_tiles and not glass & world_map.opaque_tiles
    assert doors == world_map.door_tiles and not doors & world_map.blocked_tiles
    assert not run.presentation_snapshot().environment.cues


@pytest.mark.parametrize(
    ("first", "second", "outcome"),
    [("upper", "upper", RunOutcome.WIN), ("lower", "lower", RunOutcome.CAPTURED)],
)
def test_human_routes_keep_their_outcomes_with_props(
    level: LevelData,
    rules: GameRules,
    sensors: SensorRules,
    gateway: NexusGateway,
    first: str,
    second: str,
    outcome: RunOutcome,
) -> None:
    result = run_route(
        f"{first}-{second}",
        level,
        rules,
        sensors,
        gateway.registry,
        route_steps(level, first, second),
        environment=gateway.environment,
    )
    assert result.outcome == outcome


@pytest.mark.parametrize(
    ("seed", "outcome"),
    [(COMPANION_WIN, RunOutcome.WIN), (COMPANION_CAPTURE, RunOutcome.CAPTURED)],
)
def test_companion_plays_the_prop_facility_deterministically(
    level: LevelData, rules: GameRules, sensors: SensorRules, seed: int, outcome: RunOutcome
) -> None:
    def attempt() -> tuple[RunOutcome | None, str]:
        # A fresh gateway each time: NEXUS memory adapts after every attempt.
        fresh = NexusGateway(level, rules, sensors, None)
        run = fresh.deploy(
            DeploymentRequest("COMPANION", seed, level.static_map.map_id, PRESETS["RUSH"])
        )
        used_cover = set()
        while run.tick < 9_000:
            if run.step(()).mission_end is not None:
                break
            status = run.observe(run.actor_id).own_status
            if status.concealed:
                used_cover.add(status.hidden_in or status.tile)
        assert len(used_cover) >= 2
        end = run.presentation_snapshot().mission_end
        return (end.outcome if end else None), run.fingerprint()

    first = attempt()
    assert first[0] == outcome
    assert attempt() == first
