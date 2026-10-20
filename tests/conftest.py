"""Shared real packaged rules for physics and mission scenarios."""

import pytest

from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.infrastructure.resources import load_game_rules


@pytest.fixture(scope="session")
def rules() -> GameRules:
    return load_game_rules()
