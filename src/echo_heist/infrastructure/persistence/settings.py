"""Settings schema 1: missing fields default; future versions are preserved."""

import json
from dataclasses import asdict, dataclass
from math import isfinite
from pathlib import Path
from time import time_ns

from echo_heist.infrastructure.persistence.atomic import atomic_write_json

SCHEMA_VERSION = 1
MIN_WINDOW_SIZE = (640, 360)
MAX_WINDOW_SIZE = (7680, 4320)


class FutureSettingsVersion(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Settings:
    window_width: int = 1280
    window_height: int = 720
    fullscreen: bool = False
    music_volume: float = 0.5
    sfx_volume: float = 0.7
    reduced_flashing: bool = False

    def __post_init__(self) -> None:
        for value, low, high in zip(
            (self.window_width, self.window_height), MIN_WINDOW_SIZE, MAX_WINDOW_SIZE, strict=True
        ):
            if type(value) is not int or not low <= value <= high:
                raise ValueError("Window dimensions are outside the supported range")
        if type(self.fullscreen) is not bool or type(self.reduced_flashing) is not bool:
            raise ValueError("Settings toggles must be booleans")
        for volume in (self.music_volume, self.sfx_volume):
            if type(volume) not in (int, float) or not isfinite(volume) or not 0 <= volume <= 1:
                raise ValueError("Volumes must be finite numbers from 0 to 1")


@dataclass(frozen=True, slots=True)
class SettingsLoad:
    settings: Settings
    can_write: bool = True
    notice: str | None = None


@dataclass(frozen=True, slots=True)
class SettingsSave:
    saved: bool
    notice: str | None = None


def decode_settings(payload: object) -> Settings:
    if not isinstance(payload, dict):
        raise ValueError("Settings must be a JSON object")
    version = payload.get("schema_version", SCHEMA_VERSION)
    if type(version) is not int or version < 1:
        raise ValueError("Invalid settings schema version")
    if version > SCHEMA_VERSION:
        raise FutureSettingsVersion(f"Settings schema {version} is newer; preserving this file")
    defaults = asdict(Settings())
    values = {key: payload.get(key, default) for key, default in defaults.items()}
    return Settings(**values)


class SettingsStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> SettingsLoad:
        try:
            # Windows may report a missing file when an ancestor is a regular file.
            for directory in self.path.parents:
                if directory.exists():
                    if not directory.is_dir():
                        raise NotADirectoryError(f"Settings directory is blocked: {directory}")
                    break
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            settings = decode_settings(payload)
        except FileNotFoundError:
            return SettingsLoad(Settings())
        except FutureSettingsVersion as error:
            return SettingsLoad(Settings(), can_write=False, notice=str(error))
        except (ValueError, UnicodeError) as error:
            try:
                backup = self.path.with_name(f"settings.corrupt-{time_ns()}.json")
                self.path.replace(backup)
                backups = sorted(self.path.parent.glob("settings.corrupt-*.json"))
                for old in backups[:-3]:
                    old.unlink(missing_ok=True)
            except OSError as backup_error:
                return SettingsLoad(
                    Settings(),
                    can_write=False,
                    notice=f"Cannot preserve invalid settings: {backup_error}",
                )
            return SettingsLoad(
                Settings(), notice=f"Recovered invalid settings ({error}); backup kept"
            )
        except OSError as error:
            return SettingsLoad(
                Settings(), can_write=False, notice=f"Cannot read settings: {error}"
            )
        return SettingsLoad(settings)

    def save(self, settings: Settings) -> SettingsSave:
        current = self.load()
        if not current.can_write:
            return SettingsSave(False, current.notice)
        try:
            atomic_write_json(self.path, {"schema_version": SCHEMA_VERSION, **asdict(settings)})
        except OSError as error:
            return SettingsSave(False, f"Cannot save settings: {error}")
        return SettingsSave(True)
