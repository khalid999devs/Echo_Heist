"""Exercise the frozen artifact from an unrelated cwd with isolated user data."""

import argparse
import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from echo_heist.diagnostics.foundation import run_fixture


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path, help="A .app bundle or the native executable")
    parser.add_argument("--output-dir", type=Path, default=Path("output/native-smoke"))
    parser.add_argument("--mute", action="store_true")
    parser.add_argument("--dummy-video", action="store_true", help="CI only; not real display QA")
    args = parser.parse_args()
    binary = args.artifact.resolve()
    if binary.suffix == ".app":
        binary = binary / "Contents" / "MacOS" / "EchoHeist"
    if not binary.is_file():
        parser.error(f"Native executable not found: {binary}")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment["PATH"] = os.defpath
    if args.dummy_video:
        environment["SDL_VIDEODRIVER"] = "dummy"
        environment["SDL_AUDIODRIVER"] = "dummy"
    common = [str(binary)]
    headless = output / "headless.json"
    desktop = output / "desktop.json"
    screenshot = output / "desktop.png"
    with TemporaryDirectory(prefix="echo-heist-native-") as unrelated:
        subprocess.run(
            [*common, "--headless", "--seed", "1042", "--report", str(headless)],
            cwd=unrelated,
            env=environment,
            check=True,
            timeout=60,
        )
        command = [
            *common,
            "--smoke-frames",
            "12",
            "--data-dir",
            str(output / "profile"),
            "--report",
            str(desktop),
            "--screenshot",
            str(screenshot),
        ]
        if args.mute:
            command.append("--mute")
        subprocess.run(command, cwd=unrelated, env=environment, check=True, timeout=60)
    trace = json.loads(headless.read_text(encoding="utf-8"))
    window = json.loads(desktop.read_text(encoding="utf-8"))
    expected = run_fixture(1042)
    checks = {
        "frozen_headless": trace["runtime"]["frozen"] is True,
        "frozen_desktop": window["runtime"]["frozen"] is True,
        "same_state_hash": trace["state_hash"] == expected["state_hash"],
        "same_event_hash": trace["event_hash"] == expected["event_hash"],
        "resources_loaded": window["resources_loaded"] is True,
        "settings_saved": window["settings_saved"] is True,
        "frames_rendered": window["frames"] == 12,
        "surface_saved": screenshot.is_file(),
    }
    summary = {
        "artifact": str(binary),
        "checks": checks,
        "passed": all(checks.values()),
        "video_driver": window["video_driver"],
        "scope": "CI dummy video" if args.dummy_video else "native display smoke",
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
