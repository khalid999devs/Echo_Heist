"""Native review of the production gateway, real outcomes and actual telemetry.

Uses ordinary deployment/input only; no actor, result or algorithm state injection.
"""

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

import pygame

from echo_heist.autonomy.gateway import connect_gateway
from echo_heist.core.contracts.autonomy.model import ControlMode
from echo_heist.core.contracts.autonomy.policy import DeploymentRequest
from echo_heist.infrastructure.resources import load_game_rules, load_sensor_rules
from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.render.autonomy.panel import AUTONOMY_TABS
from echo_heist.ui.render.autonomy.protocols import RESET_BUTTONS
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.design.workshop import WORKSHOP_CONTROLS
from echo_heist.ui.scenes.flow import GameFlow, Scene, load_level
from echo_heist.ui.scenes.menus import CHAPTER_CARD, MODE_BUTTONS

WIN_SEED = 42


def key(code: int) -> list[pygame.event.Event]:
    return [pygame.event.Event(kind, key=code) for kind in (pygame.KEYDOWN, pygame.KEYUP)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pygame.display.init()
    pygame.font.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1280, 720))
    canvas = opaque_surface((1280, 720))
    level, rules = load_level(), load_game_rules()
    audio = AudioDirector(enabled=True)
    shots = []
    outcomes = {}
    with TemporaryDirectory(prefix="echo-real-ai-") as data:
        gateway = connect_gateway(level, rules, load_sensor_rules(), Path(data))
        flow = GameFlow(
            (1280, 720), seed=WIN_SEED, level=level, rules=rules, autonomy_gateway=gateway
        )

        def frame(events=(), elapsed=0):
            pygame.event.pump()
            flow.frame(list(events), elapsed)
            audio.update(flow.audio_frame(), elapsed)

        def shot(name):
            flow.draw(canvas)
            screen.blit(canvas, (0, 0))
            pygame.display.flip()
            pygame.image.save(canvas, str(args.output / f"{name}.png"))
            shots.append(name)

        def click(rect):
            frame([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)])

        shot("title")
        click(CHAPTER_CARD)
        click(MODE_BUTTONS[1])
        assert flow.scene == Scene.WORKSHOP and flow.deployment.can_deploy
        shot("workshop-baseline")
        click(WORKSHOP_CONTROLS[2])  # Rush, the verified extraction policy for this seed.
        click(WORKSHOP_CONTROLS[8])
        assert flow.session and flow.session.autonomous
        flow.airlock.skip()
        for seed in (WIN_SEED, 4):
            if seed != WIN_SEED:
                flow._start_run(
                    DeploymentRequest(ControlMode.COMPANION, seed, level.static_map.map_id)
                )
                flow.airlock.skip()
            assert flow.session
            session = flow.session
            captured_telemetry = False
            while flow.scene == Scene.HEIST and session.simulation.tick < 9000:
                frame(elapsed=100)
                tick = session.simulation.tick
                if seed == WIN_SEED and tick >= 90 and not captured_telemetry:
                    for i, rect in enumerate(AUTONOMY_TABS):
                        click(rect)
                        shot(f"live-tab-{i}")
                    frame(key(pygame.K_ESCAPE))
                    frozen = session.simulation.fingerprint()
                    frame(elapsed=1000)
                    shot("pause")
                    assert frozen == session.simulation.fingerprint()
                    frame(key(pygame.K_ESCAPE))
                    captured_telemetry = True
                if (
                    seed == WIN_SEED
                    and session.simulation.presentation_snapshot().core_owner
                    and "lockdown" not in shots
                ):
                    shot("lockdown")
                if (
                    seed == WIN_SEED
                    and session.telemetry.nexus is not None
                    and session.telemetry.nexus.interceptors
                    and "interceptor-search" not in shots
                ):
                    click(AUTONOMY_TABS[2])
                    shot("interceptor-search")
                    click(AUTONOMY_TABS[1])
                    shot("nexus-dispatch")
                if tick % 30 == 0:
                    flow.draw(canvas)
                    screen.blit(canvas, (0, 0))
                    pygame.display.flip()
            assert session.mission_end is not None, "Real Companion did not finish"
            flow.airlock.skip()
            outcomes[str(seed)] = asdict(session.mission_end)
            shot(f"result-{seed}")
        assert outcomes[str(WIN_SEED)]["outcome"] == "WIN"
        assert outcomes["4"]["outcome"] == "CAPTURED"
        flow._go(Scene.WORKSHOP)
        shot("workshop-after-attempts")
        before = gateway.protocols()
        click(WORKSHOP_CONTROLS[10])
        assert flow.designs.reset_confirmation
        shot("reset-confirmation")
        click(RESET_BUTTONS[0])
        cleared = gateway.protocols()
        assert not flow.designs.reset_confirmation
        shot("workshop-reset")
        assert cleared.active is None
        report = {
            "driver": pygame.display.get_driver(),
            "audio_ready": bool(pygame.mixer.get_init()),
            "outcomes": outcomes,
            "shots": shots,
            "protocol_before": asdict(before),
            "protocol_after": asdict(cleared),
            "scope": "Production gateway, actual autonomous runs, live tabs, frozen pause/reset; "
            "no synthetic algorithm/outcome/actor injection.",
        }
        (args.output / "REVIEW.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))
    pygame.mixer.stop()
    pygame.mixer.music.stop()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
