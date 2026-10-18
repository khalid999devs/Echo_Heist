import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from echo_heist.infrastructure.paths import application_data_dir
from echo_heist.infrastructure.persistence.atomic import atomic_write_json
from echo_heist.infrastructure.persistence.settings import Settings, SettingsStore


def test_settings_round_trip_and_explicit_data_directory(tmp_path: Path) -> None:
    directory = application_data_dir(tmp_path / "isolated-profile")
    store = SettingsStore(directory / "settings.json")
    assert store.load().settings == Settings()
    chosen = replace(Settings(), music_volume=0.2, reduced_flashing=True, window_width=1366)
    assert store.save(chosen).saved
    assert store.load().settings == chosen
    assert json.loads(store.path.read_text())["schema_version"] == 1


@pytest.mark.parametrize(
    "content",
    ["{broken", "[]", '{"music_volume": 4}', '{"window_width": true}', '{"sfx_volume": NaN}'],
)
def test_corrupt_or_invalid_settings_are_backed_up_and_recover(
    tmp_path: Path, content: str
) -> None:
    path = tmp_path / "settings.json"
    path.write_text(content, encoding="utf-8")
    store = SettingsStore(path)
    loaded = store.load()
    assert loaded.settings == Settings()
    assert loaded.can_write
    assert loaded.notice is not None
    backups = list(tmp_path.glob("settings.corrupt-*.json"))
    assert len(backups) == 1
    assert backups[0].read_text() == content
    assert store.save(loaded.settings).saved
    assert store.load().notice is None


def test_missing_settings_fields_use_backward_safe_defaults(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"schema_version": 1, "music_volume": 0.25}')
    loaded = SettingsStore(path).load()
    assert loaded.settings.music_volume == 0.25
    assert loaded.settings.window_width == Settings().window_width
    assert loaded.can_write


def test_future_settings_are_never_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    original = '{"schema_version": 99, "new_feature": "keep me"}'
    path.write_text(original)
    store = SettingsStore(path)
    assert not store.load().can_write
    assert not store.save(Settings()).saved
    assert path.read_text() == original
    assert not list(tmp_path.glob("settings.corrupt-*.json"))


def test_failed_atomic_replace_keeps_previous_settings_and_cleans_temporary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "settings.json"
    atomic_write_json(path, {"schema_version": 1, "music_volume": 0.3})
    before = path.read_bytes()

    def fail_replace(source: object, destination: object) -> None:
        raise PermissionError("simulated write failure")

    monkeypatch.setattr(os, "replace", fail_replace)
    saved = SettingsStore(path).save(Settings())
    assert not saved.saved
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


def test_unavailable_storage_does_not_raise_during_load_or_save(tmp_path: Path) -> None:
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("keep")
    store = SettingsStore(blocked / "settings.json")
    assert not store.load().can_write
    assert not store.save(Settings()).saved
    assert blocked.read_text() == "keep"
