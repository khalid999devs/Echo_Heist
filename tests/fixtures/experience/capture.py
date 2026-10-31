"""Native UI review. Synthetic score/profile views are visibly marked as fixtures."""

import argparse
import json
from dataclasses import replace
from pathlib import Path
from time import perf_counter

import pygame

from echo_heist.core.contracts.results import RunOutcome
from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.render.layout.viewport import interface_origin, logical_size_for
from echo_heist.ui.render.surfaces.cinematic import draw_scene
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.experience.preferences import ACCESS_ROWS, EXTRA_SETTINGS, KEY_ROWS
from echo_heist.ui.scenes.experience.profiles import PROFILE_ACTIONS, PROFILE_BUTTON
from echo_heist.ui.scenes.experience.report import REPORT_CONTROLS, RESULT_DETAILS
from echo_heist.ui.scenes.flow import GameFlow, Scene
from echo_heist.ui.scenes.menus import CHAPTER_CARD, MODE_BUTTONS
from echo_heist.ui.scenes.navigation.controls import ABORT_BUTTONS, PAUSE_BUTTONS
from tests.fixtures.experience.gateway import MemoryGateway, report, request


def key(code: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=code)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/phase06-ui/native"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pygame.display.init()
    pygame.font.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1280, 720))
    flow = GameFlow((1280, 720))
    audio = AudioDirector(enabled=True)
    shots: list[str] = []
    assertions: list[str] = []
    frame_times: list[float] = []

    def click(rect: pygame.Rect) -> pygame.event.Event:
        x, y = interface_origin(flow.view_size)
        return pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=(rect.centerx + x, rect.centery + y)
        )

    def frame(*events: pygame.event.Event, elapsed: int = 0) -> None:
        pygame.event.pump()
        flow.frame(list(events), elapsed)
        audio.update(flow.audio_frame(), elapsed)

    def shot(name: str, fixture: bool = False) -> None:
        began = perf_counter()
        canvas = opaque_surface(flow.view_size)
        flow.draw(canvas)
        if fixture:
            strip = pygame.Rect(0, 0, canvas.get_width(), 24)
            pygame.draw.rect(canvas, (89, 42, 0), strip)
            canvas.blit(
                flow.fonts.micro.render(
                    "SCRIPTED QA / NOT SCORING, AI OR STORAGE EVIDENCE", True, (255, 238, 180)
                ),
                (12, 3),
            )
        screen.blit(pygame.transform.smoothscale(canvas, screen.get_size()), (0, 0))
        pygame.display.flip()
        pygame.image.save(canvas, str(args.output / (name + ".png")))
        frame_times.append((perf_counter() - began) * 1000)
        shots.append(name)

    shot("01-title")
    frame(click(CHAPTER_CARD))
    shot("02-briefing")
    frame(key(pygame.K_n))
    shot("03-seed")
    frame(key(pygame.K_ESCAPE), click(MODE_BUTTONS[2]))
    assert flow.scene == Scene.MODE and flow.runs_started == 0
    frame(click(MODE_BUTTONS[2]))
    assert flow.session
    flow.airlock.skip()
    frame(key(pygame.K_ESCAPE))
    frame(click(PAUSE_BUTTONS[2]))
    frozen = flow.session.simulation.fingerprint()
    shot("04-general-settings")
    frame(click(EXTRA_SETTINGS[0]))
    shot("05-controls")
    frame(click(KEY_ROWS[3]))
    shot("06-key-capture")
    frame(key(pygame.K_l))
    assert flow.preferences.preferences.controls
    shot("07-remapped")
    frame(key(pygame.K_ESCAPE), click(EXTRA_SETTINGS[1]))
    frame(click(ACCESS_ROWS[1]))
    shot("08-accessibility")
    frame(click(ACCESS_ROWS[2]))
    shot("09-session-save-notice")
    frame(key(pygame.K_ESCAPE), key(pygame.K_ESCAPE))
    assert flow.scene == Scene.HEIST and flow.session.paused
    assert flow.session.simulation.fingerprint() == frozen
    frame(click(PAUSE_BUTTONS[0]))
    frame(key(pygame.K_l), elapsed=70)
    shot("10-accessible-hud")
    frame(key(pygame.K_ESCAPE))
    frame(click(PAUSE_BUTTONS[3]))
    frame(click(ABORT_BUTTONS[0]))
    assert flow.scene == Scene.RESULTS and flow.reports.report is None
    shot("11-actual-aborted-unscored")
    frame(click(RESULT_DETAILS))
    shot("12-actual-report-unavailable")
    frame(click(REPORT_CONTROLS[0]))
    shot("13-history-unavailable")
    frame(key(pygame.K_ESCAPE), key(pygame.K_ESCAPE))
    flow._go(Scene.WORKSHOP)
    shot("14-workshop")
    frame(click(PROFILE_BUTTON))
    shot("15-profiles-unavailable")
    assertions.append(
        "Actual Human input, pause/settings freeze, remapping, captions/contrast controls, "
        "confirmed abort, default unscored report and unavailable storage."
    )

    # Supply a test-only backend; never use this to assert working SR scoring or persistence.
    gateway = MemoryGateway()
    flow.profiles.gateway = gateway
    flow.profiles.show()
    shot("16-fixture-profiles", True)
    frame(
        key(pygame.K_n),
        pygame.event.Event(pygame.TEXTINPUT, text="My Ghost"),
        key(pygame.K_RETURN),
        key(pygame.K_s),
    )
    assert len(gateway.saved) == 2
    flow.profiles.selected = 1
    frame(key(pygame.K_l))
    shot("17-fixture-profile-loaded", True)
    frame(key(pygame.K_DELETE))
    shot("18-fixture-delete-confirm", True)
    frame(key(pygame.K_ESCAPE))
    assert len(gateway.saved) == 2
    gateway.fail = True
    frame(key(pygame.K_s))
    shot("19-fixture-storage-failure", True)
    frame(click(PROFILE_ACTIONS[-1]))
    gateway.fail = False
    flow.reports.gateway = gateway
    flow.reports.capture(request())
    flow.scene = Scene.RESULTS
    # Only the pictured outcome is synthetic here; the script never mutates live Simulation.
    flow.inspector.open = True
    shot("20-fixture-score-details", True)
    frame(click(REPORT_CONTROLS[0]))
    shot("21-fixture-history", True)
    flow.inspector.open = False
    from echo_heist.ui.scenes.experience.report import draw_results

    for name, r in (
        ("22-fixture-rank-s", report()),
        (
            "23-fixture-rank-a",
            replace(
                report(),
                achievements=(),
                result=replace(
                    report().result, score=88, grade="A", detection_encounters=1, stealth_points=28
                ),
            ),
        ),
        (
            "24-fixture-failure",
            replace(
                report(),
                achievements=(),
                result=replace(
                    report().result,
                    outcome=RunOutcome.CAPTURED,
                    score=0,
                    grade="F",
                    completion_points=0,
                    stealth_points=0,
                    pace_points=0,
                ),
            ),
        ),
    ):
        canvas = opaque_surface((1280, 720))
        draw_scene(
            canvas,
            flow.extraction_backdrop,
            0,
            text_side="right",
            mirror_for_text=False,
            reactor_glow=False,
        )
        end = replace(request().end, outcome=r.result.outcome)
        draw_results(canvas, end, flow.fonts, ticks_per_second=30, request=request(), report=r)
        pygame.draw.rect(canvas, (89, 42, 0), (0, 0, 1280, 24))
        canvas.blit(
            flow.fonts.micro.render("SCRIPTED QA / NOT SCORING EVIDENCE", True, (255, 238, 180)),
            (12, 3),
        )
        pygame.image.save(canvas, str(args.output / (name + ".png")))
        shots.append(name)
    assertions.append(
        "Test-only profile save/load/delete confirmation and provider error; "
        "fixed S/A/F report examples and history inspection. No backend evidence."
    )
    for size in ((1366, 768), (1440, 900), (1920, 1080), (1024, 768)):
        screen = pygame.display.set_mode(size)
        flow.resize(logical_size_for(size))
        flow._go(Scene.SETTINGS)
        shot(f"25-settings-{size[0]}x{size[1]}")
        frame(click(EXTRA_SETTINGS[0]))
        assert flow.preferences.page == "CONTROLS"
        shot(f"26-controls-{size[0]}x{size[1]}")
    assertions.append("Visible pointer targets at 1366x768, 1440x900, 1920x1080, 1024x768.")
    data = {
        "video_driver": pygame.display.get_driver(),
        "audio_ready": bool(pygame.mixer.get_init()),
        "shots": shots,
        "checks": assertions,
        "scope": "Human/default and labeled UI fixtures; no finished P06/backend gate claim.",
    }
    (args.output / "REVIEW.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data))
    pygame.mixer.stop()
    pygame.mixer.music.stop()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
