"""Real input-to-outcome trace, using a deterministic render clock for speed."""

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pygame
import pytest

from echo_heist.diagnostics.human_preview import run_preview
from echo_heist.infrastructure.persistence.atomic import atomic_write_json


def exercise(output: Path, *, scenario: str = "win") -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    frame = 0
    original_get = pygame.event.get

    def events() -> list[pygame.event.Event]:
        nonlocal frame
        frame += 1
        original_get()  # pump/discard native window events for a controlled trace
        win_sequence = {
            1: [(pygame.KEYDOWN, pygame.K_ESCAPE)],
            4: [(pygame.KEYDOWN, pygame.K_ESCAPE)],
            5: [(pygame.KEYDOWN, pygame.K_d)],
            42: [(pygame.KEYUP, pygame.K_d), (pygame.KEYDOWN, pygame.K_e)],
            50: [(pygame.KEYUP, pygame.K_e), (pygame.KEYDOWN, pygame.K_a)],
        }
        capture_sequence = {
            1: [(pygame.KEYDOWN, pygame.K_d)],
            24: [(pygame.KEYUP, pygame.K_d), (pygame.KEYDOWN, pygame.K_s)],
            32: [(pygame.KEYUP, pygame.K_s)],
        }
        sequence = capture_sequence if scenario == "capture" else win_sequence
        return [pygame.event.Event(kind, key=key) for kind, key in sequence.get(frame, [])]

    class FixedClock:
        def tick(self, fps: int) -> int:
            return 100

    with patch("pygame.event.get", events), patch("pygame.time.Clock", FixedClock):
        report = run_preview(smoke_frames=90, screenshot=output / f"{scenario}.png")
    if scenario == "capture":
        assert report["phase"] == "CAPTURED", report
        assert report["event_counts"]["CAPTURE_STARTED"] == 1
        assert report["event_counts"]["CAPTURE_COMPLETED"] == 1
    else:
        assert report["phase"] == "WON", report
        assert report["paused_frames"] == 3, report
        # Three paused render frames must contribute zero simulation ticks.
        assert report["tick"] == report["simulation_steps"] == 243, report
        assert report["event_counts"]["CORE_TAKEN"] == 1
        assert report["event_counts"]["LOCKDOWN_STARTED"] == 1
    assert report["event_counts"]["MISSION_ENDED"] == 1
    atomic_write_json(output / f"{scenario}.json", report)
    return report


@pytest.mark.smoke
@pytest.mark.parametrize("scenario", ["win", "capture"])
def test_input_pause_theft_and_win_in_real_preview(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scenario: str,
) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    report = exercise(tmp_path, scenario=scenario)
    assert report["video_driver"] == "dummy"
    assert (tmp_path / f"{scenario}.png").is_file()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scripted native or dummy P02 input trace")
    parser.add_argument("--output", type=Path, default=Path("output/phase02/native-preview"))
    parser.add_argument("--scenario", choices=("win", "capture", "both"), default="both")
    args = parser.parse_args()
    for scenario in ("win", "capture") if args.scenario == "both" else (args.scenario,):
        print(json.dumps(exercise(args.output, scenario=scenario), sort_keys=True))
