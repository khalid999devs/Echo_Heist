"""Source, wheel and frozen builds share one package-owned resource tree."""

import json
from dataclasses import dataclass
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path, PurePosixPath

from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.config.scoring import ScoringRules
from echo_heist.core.contracts.environment.model import EnvironmentRules
from echo_heist.core.contracts.security.model import SensorRules


def load_game_rules() -> GameRules:
    return GameRules.from_payload(json.loads(resource_bytes("data/gameplay/phase02.json")))


def load_sensor_rules() -> SensorRules:
    return SensorRules.from_payload(json.loads(resource_bytes("data/gameplay/security.json")))


def load_environment_rules() -> EnvironmentRules:
    return EnvironmentRules.from_payload(
        json.loads(resource_bytes("data/gameplay/environment.json"))
    )


def load_scoring_rules() -> ScoringRules:
    return ScoringRules.from_payload(json.loads(resource_bytes("data/gameplay/scoring.json")))


def _resource(relative_path: str) -> Traversable:
    path = PurePosixPath(relative_path)
    if path.is_absolute() or ".." in path.parts or "\\" in relative_path:
        raise ValueError("Resource paths must be relative to package resources")
    return files("echo_heist").joinpath("resources", *path.parts)


def resource_bytes(relative_path: str) -> bytes:
    return _resource(relative_path).read_bytes()


def resource_path(relative_path: str) -> Path:
    """Installed and frozen data files that native libraries open themselves."""
    resource = _resource(relative_path)
    if not isinstance(resource, Path) or not resource.is_file():
        raise FileNotFoundError(f"Expected a bundled resource file: {relative_path}")
    return resource


@dataclass(frozen=True, slots=True)
class BootstrapConfig:
    title: str
    stage: str
    logical_width: int
    logical_height: int
    target_fps: int
    background: str
    foreground: str
    muted: str
    accent: str


def load_bootstrap_config() -> BootstrapConfig:
    data = json.loads(resource_bytes("data/bootstrap.json"))
    if not isinstance(data, dict):
        raise ValueError("Bootstrap config must be a JSON object")

    def text(key: str) -> str:
        value = data.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"Bootstrap {key} must be nonempty text")
        return value

    def positive_int(key: str) -> int:
        value = data.get(key)
        if type(value) is not int or value <= 0:
            raise ValueError(f"Bootstrap {key} must be a positive integer")
        return value

    return BootstrapConfig(
        title=text("title"),
        stage=text("stage"),
        logical_width=positive_int("logical_width"),
        logical_height=positive_int("logical_height"),
        target_fps=positive_int("target_fps"),
        background=text("background"),
        foreground=text("foreground"),
        muted=text("muted"),
        accent=text("accent"),
    )
