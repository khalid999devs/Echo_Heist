import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.smoke
def test_desktop_resources_audio_fallback_and_saved_settings_outside_repo(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    environment = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="unavailable-driver")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "echo_heist",
            "--smoke-frames",
            "2",
            "--data-dir",
            str(tmp_path / "profile"),
            "--report",
            str(report),
        ],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        # The verified Windows laptop has cold source starts up to 72 seconds.
        # Startup latency is measured separately by the native profile.
        timeout=90,
    )
    result = json.loads(report.read_text())
    assert result["frames"] == 2
    assert result["resources_loaded"]
    assert result["startup"]["completed"] and result["startup"]["frames"] > 0
    assert result["startup"]["sound_cues"] == 0
    assert result["settings_saved"]
    assert result["audio"].startswith("unavailable")
    assert result["video_driver"] == "dummy"
    assert Path(result["settings_path"]).parent == tmp_path / "profile"
