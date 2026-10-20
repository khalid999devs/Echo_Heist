"""Build the native primary artifact and record its actual environment/hash."""

import json
import os
import platform
import shutil
import subprocess
import sys
from hashlib import file_digest
from importlib.metadata import version
from pathlib import Path

from echo_heist import __version__

ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def main() -> int:
    mac = sys.platform == "darwin" and platform.machine().lower() == "arm64"
    windows = sys.platform == "win32" and platform.machine().lower() in {"amd64", "x86_64"}
    if not (mac or windows):
        raise SystemExit("Use native macOS arm64 or Windows x64 for a primary build")
    target = "macos-arm64" if mac else "windows-x64"
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--workpath",
        "build/pyinstaller",
        "packaging/echo_heist.spec",
    ]
    environment = dict(os.environ, PYINSTALLER_CONFIG_DIR=str(ROOT / ".cache" / "pyinstaller"))
    subprocess.run(command, cwd=ROOT, env=environment, check=True)
    stem = f"echo-heist-{__version__}-{target}"
    archive = ROOT / "dist" / f"{stem}.zip"
    signing = "unsigned"
    if mac:
        bundle = ROOT / "dist" / "Echo Heist.app"
        subprocess.run(["codesign", "--verify", "--deep", "--strict", str(bundle)], check=True)
        signature = subprocess.run(
            ["codesign", "-dv", str(bundle)], capture_output=True, text=True, check=True
        )
        signing = (
            "ad-hoc; not notarized"
            if "Signature=adhoc" in signature.stderr
            else "inspect signature"
        )
        subprocess.run(
            ["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(bundle), str(archive)],
            check=True,
        )
    else:
        shutil.make_archive(str(archive.with_suffix("")), "zip", ROOT / "dist", "EchoHeist")
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    changes = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    manifest = {
        "version": __version__,
        "stage": "P02 Human mission draft; full V1 remains in development",
        "target": target,
        "python": platform.python_version(),
        "host_os": platform.platform(),
        "architecture": platform.machine(),
        "pyinstaller": version("pyinstaller"),
        "source_commit": commit,
        "working_tree_dirty": bool(changes),
        "lock_sha256": sha256(ROOT / "uv.lock"),
        "archive": archive.name,
        "archive_sha256": sha256(archive),
        "archive_bytes": archive.stat().st_size,
        "signing": signing,
        "native_smoke": "NOT_RUN; run scripts/packaging/smoke.py against the artifact",
    }
    output = ROOT / "dist" / f"{stem}.manifest.json"
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
