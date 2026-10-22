# ruff: noqa: F821
"""Native Windows x64 one-folder / macOS arm64 app; run on the target OS."""

import platform
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

project = Path(SPECPATH).parent
machine = platform.machine().lower()
mac = sys.platform == "darwin"
if mac and machine != "arm64":
    raise SystemExit("The macOS primary build requires an Apple Silicon interpreter")
if sys.platform == "win32" and machine not in {"amd64", "x86_64"}:
    raise SystemExit("The Windows primary build requires an x64 interpreter")
if sys.platform not in {"darwin", "win32"}:
    raise SystemExit("Linux packaging is outside the Phase 1 primary build recipe")

analysis = Analysis(
    [str(project / "packaging" / "launcher.py")],
    pathex=[str(project / "src")],
    binaries=[],
    datas=collect_data_files("echo_heist"),
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "mypy", "ruff", "tkinter", "unittest"],
    noarchive=False,
    optimize=0,
)
archive = PYZ(analysis.pure)
executable = EXE(
    archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="EchoHeist",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=None if mac else str(project / "packaging/icons/echo-heist.ico"),
    target_arch="arm64" if mac else None,
    codesign_identity=None,
    entitlements_file=None,
)
collection = COLLECT(
    executable, analysis.binaries, analysis.datas, strip=False, upx=False, name="EchoHeist"
)
if mac:
    app = BUNDLE(
        collection,
        name="Echo Heist.app",
        icon=str(project / "packaging/icons/echo-heist.icns"),
        bundle_identifier="io.echoheist.game",
        info_plist={
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0.1",
            "NSHighResolutionCapable": True,
        },
    )
