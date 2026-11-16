"""Native current-service navigation/accessibility acceptance, without synthetic experience data."""

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pygame

from echo_heist.autonomy.gateway import connect_gateway
from echo_heist.infrastructure.resources import load_game_rules, load_sensor_rules
from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.bootstrap import _logical_events
from echo_heist.ui.render.layout.viewport import interface_origin, logical_size_for
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.design.screens import GUIDE_CONTROLS
from echo_heist.ui.scenes.design.workshop import WORKSHOP_CONTROLS
from echo_heist.ui.scenes.experience.preferences import ACCESS_ROWS, EXTRA_SETTINGS, KEY_ROWS
from echo_heist.ui.scenes.experience.profiles import PROFILE_BUTTON
from echo_heist.ui.scenes.experience.report import REPORT_CONTROLS, RESULT_DETAILS, RESULT_NEW_SEED
from echo_heist.ui.scenes.flow import GameFlow, Scene, load_level
from echo_heist.ui.scenes.menus import CHAPTER_CARD, MODE_BUTTONS, TITLE_BUTTONS
from echo_heist.ui.scenes.navigation.controls import ABORT_BUTTONS, PAUSE_BUTTONS


def key(code):
    return [pygame.event.Event(kind, key=code) for kind in (pygame.KEYDOWN, pygame.KEYUP)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pygame.display.init()
    pygame.font.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1280, 720))
    level, rules = load_level(), load_game_rules()
    audio = AudioDirector(enabled=True)
    shots, checks, windows = [], [], []
    with TemporaryDirectory(prefix="echo-live-experience-") as data:
        gateway = connect_gateway(level, rules, load_sensor_rules(), Path(data))
        flow = GameFlow((1280, 720), level=level, rules=rules, autonomy_gateway=gateway)

        def frame(events=(), elapsed=0):
            pygame.event.pump()
            flow.frame(list(events), elapsed)
            audio.update(flow.audio_frame(), elapsed)

        def click(rect):
            x, y = interface_origin(flow.view_size)
            # Use the desktop's physical-window mapping before GameFlow's safe area.
            point = (
                round((rect.centerx + x) * screen.get_width() / flow.view_size[0]),
                round((rect.centery + y) * screen.get_height() / flow.view_size[1]),
            )
            frame(
                _logical_events(
                    [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point)],
                    screen.get_size(),
                    flow.view_size,
                )
            )

        def shot(name):
            canvas = opaque_surface(flow.view_size)
            flow.draw(canvas)
            screen.blit(pygame.transform.smoothscale(canvas, screen.get_size()), (0, 0))
            pygame.display.flip()
            pygame.image.save(canvas, str(args.output / f"{name}.png"))
            shots.append(name)

        click(CHAPTER_CARD)
        click(MODE_BUTTONS[1])
        assert flow.scene == Scene.WORKSHOP and flow.deployment.can_deploy
        shot("workshop-real")
        choices = tuple(flow.designs.draft.choices)
        for rect in WORKSHOP_CONTROLS[3:7]:
            click(rect)
        assert all(a != b for a, b in zip(choices, flow.designs.draft.choices, strict=True))
        click(WORKSHOP_CONTROLS[1])
        click(PROFILE_BUTTON)
        assert flow.profiles.open and flow.profiles.gateway is None
        shot("profiles-honestly-unavailable")
        frame(key(pygame.K_ESCAPE))
        for size in ((1280, 720), (1440, 900), (1366, 768), (1024, 768)):
            screen = pygame.display.set_mode(size)
            flow.resize(logical_size_for(screen.get_size()))
            windows.append(
                {"requested": size, "actual": screen.get_size(), "logical": flow.view_size}
            )
            shot(f"workshop-{size[0]}x{size[1]}")
            click(PROFILE_BUTTON)
            assert flow.profiles.open
            frame(key(pygame.K_ESCAPE))
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        fullscreen_size = screen.get_size()
        flow.resize(logical_size_for(fullscreen_size))
        shot("workshop-fullscreen")
        click(PROFILE_BUTTON)
        assert flow.profiles.open
        frame(key(pygame.K_ESCAPE))
        screen = pygame.display.set_mode((1280, 720))
        flow.resize(logical_size_for(screen.get_size()))
        click(WORKSHOP_CONTROLS[8])
        assert flow.session and flow.session.autonomous
        flow.airlock.skip()
        request = flow.last_deployment
        assert request and request.seed == 1042
        session = flow.session
        for _ in range(1000):
            if session.mission_end:
                break
            frame(elapsed=100)
            if session.simulation.tick % 120 == 0:
                shot_name = "companion-live"
                if shot_name not in shots:
                    shot(shot_name)
        assert session.mission_end and session.mission_end.outcome == "WIN"
        flow.airlock.skip()
        assert flow.scene == Scene.RESULTS
        assert flow.reports.report is None
        shot("actual-companion-win-unscored")
        click(RESULT_DETAILS)
        shot("actual-report-details")
        click(REPORT_CONTROLS[0])
        shot("history-honestly-unavailable")
        frame(key(pygame.K_ESCAPE))
        click(RESULT_NEW_SEED)
        frame(key(pygame.K_ESCAPE))
        assert flow.scene == Scene.RESULTS and flow.seed == 1042
        click(RESULT_NEW_SEED)
        frame([pygame.event.Event(pygame.TEXTINPUT, text="4")])
        frame(key(pygame.K_RETURN))
        assert flow.scene == Scene.WORKSHOP and flow.seed == 4
        assert flow.last_deployment and flow.last_deployment.policy == request.policy
        shot("new-seed-protocol-review")
        click(WORKSHOP_CONTROLS[8])
        flow.airlock.skip()
        assert flow.last_deployment and flow.last_deployment.seed == 4
        assert flow.session and flow.session.autonomous
        frame(key(pygame.K_ESCAPE))
        frozen = flow.session.simulation.fingerprint()
        click(PAUSE_BUTTONS[2])
        click(EXTRA_SETTINGS[0])
        click(KEY_ROWS[3])
        frame(key(pygame.K_l))
        shot("controls-remapped")
        frame(key(pygame.K_ESCAPE))
        click(EXTRA_SETTINGS[1])
        before_captions = flow.preferences.preferences.subtitles
        click(ACCESS_ROWS[0])
        assert flow.preferences.preferences.subtitles != before_captions
        if not flow.preferences.preferences.subtitles:
            click(ACCESS_ROWS[0])
        click(ACCESS_ROWS[1])
        click(ACCESS_ROWS[2])
        assert flow.preferences.preferences.subtitles and flow.preferences.preferences.high_contrast
        shot("accessibility-session-only")
        frame(elapsed=1000)
        assert flow.session.simulation.fingerprint() == frozen
        frame(key(pygame.K_ESCAPE))
        frame(key(pygame.K_ESCAPE))
        assert flow.scene == Scene.HEIST and flow.session.paused
        click(PAUSE_BUTTONS[0])
        frame(elapsed=70)
        shot("actual-accessible-companion-hud")
        frame(key(pygame.K_ESCAPE))
        click(PAUSE_BUTTONS[3])
        click(ABORT_BUTTONS[0])
        assert flow.scene == Scene.RESULTS and flow.session.mission_end.outcome == "ABORTED"
        shot("actual-companion-abort")
        frame(key(pygame.K_ESCAPE))
        click(TITLE_BUTTONS[4])
        assert flow.scene == Scene.GUIDE
        for i, rect in enumerate(GUIDE_CONTROLS[:4]):
            click(rect)
            shot(f"guide-{i}")
        click(GUIDE_CONTROLS[4])
        click(CHAPTER_CARD)
        click(MODE_BUTTONS[0])
        click(MODE_BUTTONS[2])
        flow.airlock.skip()
        assert flow.session and not flow.session.autonomous
        human = flow.session
        before = human.simulation.observe(human.observer_id).own_status.position
        frame([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_l)], elapsed=100)
        frame([pygame.event.Event(pygame.KEYUP, key=pygame.K_l)])
        after = human.simulation.observe(human.observer_id).own_status.position
        assert after[0] > before[0]
        shot("actual-remapped-human-hud")
        checks.extend(
            (
                "Real Companion deployment/win/result through production gateway",
                "Four editable blocks, real Balanced selection and responsive pointer navigation",
                "Explicit seed cancel/change retains Companion mode and policy",
                "Actual paused Companion settings freeze and confirmed abort",
                "Controls/captions/contrast apply in session; persistence honestly unavailable",
            )
        )
        report = {
            "driver": pygame.display.get_driver(),
            "audio_ready": bool(pygame.mixer.get_init()),
            "shots": shots,
            "checks": checks,
            "experience_service": "NOT_IMPLEMENTED: no production ExperienceGateway in main",
            "fullscreen_size": fullscreen_size,
            "windows": windows,
            "scope": "Actual AI/gameplay/UI; no synthetic scores/profiles/preferences/history.",
        }
        (args.output / "REVIEW.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))
    pygame.mixer.stop()
    pygame.mixer.music.stop()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
