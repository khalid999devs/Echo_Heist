from pathlib import Path

from platformdirs import user_data_path


def application_data_dir(override: Path | None = None) -> Path:
    """An override supports isolated checks without touching a real profile."""
    return override if override is not None else user_data_path("Echo Heist", appauthor=False)
