"""Real Human keyboard interactions with props on the production map and security."""

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pygame

from echo_heist.ai.navigation.grid import bfs
from echo_heist.autonomy.gateway import connect_gateway
from echo_heist.core.contracts.autonomy.policy import DeploymentRequest
from echo_heist.diagnostics.human_driver import HumanDriver
from echo_heist.infrastructure.resources import load_game_rules, load_sensor_rules
from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.flow import GameFlow, load_level


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
    with TemporaryDirectory(prefix="echo-prop-live-") as data:
        gateway = connect_gateway(level, rules, load_sensor_rules(), Path(data))
        flow = GameFlow((1280, 720), level=level, rules=rules, autonomy_gateway=gateway)
        flow._start_run(DeploymentRequest("HUMAN", 1042, level.static_map.map_id))
        flow.airlock.skip()
        session = flow.session
        assert session
        actor = session.observer_id
        driver = HumanDriver(rules, sprint=False)
        can = next(p for p in gateway.environment.props if p.object_id == "canister-service-1")
        locker = next(p for p in gateway.environment.props if p.object_id == "hide-2")

        def frame(events=()):
            pygame.event.pump()
            flow.frame(list(events), 34)
            audio.update(flow.audio_frame(), 34)
            assert session.mission_end is None, "Human was captured before the interaction review"

        def shot(name):
            flow.draw(canvas)
            screen.blit(canvas, (0, 0))
            pygame.display.flip()
            pygame.image.save(canvas, str(args.output / f"{name}.png"))
            shots.append(name)

        def walk_to(tile):
            observation = session.simulation.observe(actor)
            path = bfs(observation.map_static, observation.own_status.tile, tile).path
            assert path
            for waypoint in path[1:]:
                for _ in range(150):
                    observation = session.simulation.observe(actor)
                    if driver.arrived(observation, waypoint):
                        break
                    frame(driver.events(observation, waypoint))
                else:
                    raise AssertionError(f"Human route stalled at {waypoint}")
            frame(driver.release())

        while session.simulation.tick < 240:
            frame()
        walk_to((can.tile[0], can.tile[1] - 1))
        frame([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s)])
        for _ in range(13):
            frame()
        frame([pygame.event.Event(pygame.KEYUP, key=pygame.K_s)])
        shot("canister-roll")
        walk_to(locker.tile)
        shot("locker-prompt")
        frame([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)])
        for _ in range(30):
            frame()
        hidden = session.simulation.observe(actor).own_status.hidden_in
        assert hidden == locker.object_id, "Holding E must not repeatedly toggle the locker"
        shot("locker-hidden")
        frame([pygame.event.Event(pygame.KEYUP, key=pygame.K_e)])
        frame([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)])
        frame([pygame.event.Event(pygame.KEYUP, key=pygame.K_e)])
        assert session.simulation.observe(actor).own_status.hidden_in is None
        shot("locker-left")
        report = {
            "driver": pygame.display.get_driver(),
            "audio_ready": bool(pygame.mixer.get_init()),
            "tick": session.simulation.tick,
            "hidden_in": hidden,
            "environment_props": len(session.simulation.presentation_snapshot().environment.props),
            "shots": shots,
            "scope": "Ordinary keyboard Human movement, real security/map/props; "
            "no position, prop or outcome injection.",
        }
        (args.output / "REVIEW.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
