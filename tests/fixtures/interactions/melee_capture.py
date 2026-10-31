"""Native melee HUD audit using real Simulation/input; one stationary practice guard.

This practice layout disables AI only. Charges, cooldown, movement and capture
rules are real. Default Human missions are verified separately with security on.
"""

import argparse
import json
from dataclasses import replace
from pathlib import Path

import pygame

from echo_heist.core.contracts.world import ActorKind
from echo_heist.level.model import GuardPost
from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.flow import GameFlow, load_level


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/melee-balance/hud"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pygame.display.init()
    pygame.font.init()
    pygame.mixer.init()
    display = pygame.display.set_mode((1280, 720))
    canvas = opaque_surface((1280, 720))
    level = load_level()
    x, y = level.spawn_tile
    level = replace(level, guards=(GuardPost("practice", ActorKind.SENTINEL, (x + 1, y), "qa"),))
    flow = GameFlow(canvas.get_size(), level=level, security_enabled=False)
    flow._start_run()
    audio = AudioDirector(enabled=True)
    session = flow.session
    assert session is not None
    shots, states = [], []

    def shot(name):
        pygame.event.pump()
        audio.update(flow.audio_frame(), 34)
        session.draw(canvas)
        label = flow.fonts.micro.render(
            "MELEE QA / REAL RULES / PRACTICE GUARD AI OFF", True, (251, 190, 82)
        )
        canvas.blit(label, (370, 102))
        display.blit(canvas, (0, 0))
        pygame.display.flip()
        pygame.image.save(canvas, str(args.output / (name + ".png")))
        shots.append(name)
        own = session.simulation.observe(session.observer_id).own_status
        states.append(
            {
                "name": name,
                "tick": session.simulation.presentation_snapshot().tick,
                "charges": own.inventory.melee_charges,
                "cooldown": own.melee_cooldown_remaining,
                "notice": session.notice,
            }
        )

    def press(code):
        session.input.feed(
            [pygame.event.Event(kind, key=code) for kind in (pygame.KEYDOWN, pygame.KEYUP)]
        )
        session.update(34)

    def walk(code, frames):
        session.input.feed([pygame.event.Event(pygame.KEYDOWN, key=code)])
        for _ in range(frames):
            session.update(34)
            audio.update(flow.audio_frame(), 34)
        session.input.feed([pygame.event.Event(pygame.KEYUP, key=code)])

    shot("ready-two")
    press(pygame.K_SPACE)
    shot("one-charge-recovery")
    press(pygame.K_SPACE)
    shot("cooldown-rejected")
    before = session.simulation.fingerprint()
    session.paused = True
    session.update(2000)
    assert session.simulation.fingerprint() == before
    shot("paused-recovery")
    session.paused = False
    walk(pygame.K_a, 15)  # Escape before the real stun expires.
    while session.simulation.observe(session.observer_id).own_status.melee_cooldown_remaining:
        session.update(34)
    shot("recovered-one")
    walk(pygame.K_d, 15)
    press(pygame.K_SPACE)
    assert session.simulation.observe(session.observer_id).own_status.inventory.melee_charges == 0
    shot("second-strike-empty")
    press(pygame.K_SPACE)
    shot("empty-rejected")
    flow._start_run()
    session = flow.session
    assert session is not None
    shot("retry-restored-two")
    assert session.simulation.observe(session.observer_id).own_status.inventory.melee_charges == 2
    report = {
        "kind": "Native practice layout, real melee/movement/capture; guard AI disabled",
        "video_driver": pygame.display.get_driver(),
        "audio_ready": pygame.mixer.get_init() is not None,
        "shots": shots,
        "states": states,
        "audio": audio.report(),
        "paused_clock": "PASS",
        "retry": "PASS",
    }
    (args.output / "REVIEW.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
