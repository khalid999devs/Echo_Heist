"""Source, wheel and frozen builds share one package-owned resource tree."""

import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import PurePosixPath

from echo_heist.core.contracts.config.gameplay import GameRules


def load_game_rules() -> GameRules:
    return GameRules.from_payload(json.loads(resource_bytes("data/gameplay/phase02.json")))


def resource_bytes(relative_path: str) -> bytes:
    path = PurePosixPath(relative_path)
    if path.is_absolute() or ".." in path.parts or "\\" in relative_path:
        raise ValueError("Resource paths must be relative to package resources")
    return files("echo_heist").joinpath("resources", *path.parts).read_bytes()


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
