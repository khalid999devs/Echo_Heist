import subprocess
import sys

import pytest

from echo_heist.core.contracts.world import ActorKind, ActorSpawn, MapObject, StaticMap
from echo_heist.core.simulation.engine import Simulation
from echo_heist.infrastructure.resources import load_game_rules


def test_unseen_actor_changes_do_not_change_permitted_observation() -> None:
    world = StaticMap("same-map", 8, 8)
    own = ActorSpawn("operative", (1, 1))
    first = Simulation(
        world, (own, ActorSpawn("guard", (6, 6), ActorKind.SENTINEL)), rules=load_game_rules()
    )
    second = Simulation(
        world, (own, ActorSpawn("guard", (7, 6), ActorKind.SENTINEL)), rules=load_game_rules()
    )
    assert first.observe("operative") == second.observe("operative")
    assert first.observe("operative").visible_entities == ()
    assert first.presentation_snapshot() != second.presentation_snapshot()
    assert first.fingerprint() != second.fingerprint()


def test_map_input_collections_cannot_mutate_shared_static_knowledge() -> None:
    blocked = {(2, 2)}
    properties = [["noise_kind", "GLASS_BREAK"]]
    obj = MapObject("glass", "Prop", (1, 1), properties)
    world = StaticMap("test", 4, 4, blocked, objects=[obj])
    blocked.add((1, 1))
    properties[0][1] = "CHANGED"
    assert world.blocked_tiles == frozenset({(2, 2)})
    assert world.objects[0].properties == (("noise_kind", "GLASS_BREAK"),)
    with pytest.raises(ValueError, match="immutable scalar"):
        MapObject("bad", "Prop", (1, 1), (("mutable", []),))


def test_headless_core_and_fixture_do_not_import_pygame() -> None:
    command = (
        "import sys; "
        "from echo_heist.diagnostics.foundation import run_fixture; "
        "run_fixture(); "
        "from echo_heist.app import main; "
        "assert main(['--headless']) == 0; "
        "assert not any(m == 'pygame' or m.startswith('pygame.') for m in sys.modules)"
    )
    subprocess.run([sys.executable, "-c", command], check=True, timeout=15)
