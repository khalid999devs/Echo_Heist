"""CLI dispatch; --headless never imports or initializes pygame."""

import argparse
import json
import os
import platform
import sys
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path

from echo_heist import __version__
from echo_heist.infrastructure.paths import application_data_dir
from echo_heist.infrastructure.persistence.atomic import atomic_write_json


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("Must be a positive integer")
    return number


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ECHO HEIST Phase 1 foundation")
    parser.add_argument("--version", action="version", version=__version__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--headless", action="store_true", help="Run the seeded foundation diagnostic"
    )
    mode.add_argument("--smoke-frames", type=_positive_int, help="Render N frames and exit")
    parser.add_argument("--seed", type=int, default=1042)
    parser.add_argument("--mute", action="store_true", help="Skip audio device initialization")
    parser.add_argument("--data-dir", type=Path, help="Override user data for isolated checks")
    parser.add_argument("--report", type=Path, help="Write a machine-readable run report")
    parser.add_argument("--screenshot", type=Path, help="Save the rendered desktop surface on exit")
    args = parser.parse_args(argv)
    if args.headless and args.screenshot is not None:
        parser.error("--screenshot requires desktop mode")
    try:
        if args.headless:
            from echo_heist.diagnostics.foundation import run_fixture

            report = run_fixture(args.seed)
            if report != run_fixture(args.seed):
                raise RuntimeError("Foundation trace did not repeat deterministically")
            report["repeatable"] = True
        else:
            os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
            from echo_heist.ui.bootstrap import run_desktop

            report = run_desktop(
                application_data_dir(args.data_dir),
                smoke_frames=args.smoke_frames,
                mute=args.mute,
                screenshot=args.screenshot,
            )
        report["runtime"] = {
            "python": platform.python_version(),
            "architecture": platform.machine(),
            "frozen": bool(getattr(sys, "frozen", False)),
        }
        if args.report is not None:
            atomic_write_json(args.report, report)
        if sys.stdout is not None:
            print(json.dumps(report, sort_keys=True))
    except (OSError, ValueError, RuntimeError) as error:
        failure = {"error": str(error), "version": __version__}
        if args.report is not None:
            with suppress(OSError):
                atomic_write_json(args.report, failure)
        if sys.stderr is not None:
            print(f"ECHO HEIST: {error}", file=sys.stderr)
        return 1
    return 0
