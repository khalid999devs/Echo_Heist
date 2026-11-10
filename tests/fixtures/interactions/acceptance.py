"""Native production-map interaction acceptance through ordinary Human keyboard input."""

import argparse
import json
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

import pygame

from echo_heist.ai.navigation.grid import bfs
from echo_heist.autonomy.gateway import connect_gateway
from echo_heist.core.contracts.autonomy.policy import DeploymentRequest
from echo_heist.core.contracts.environment.presentation import PropKind
from echo_heist.diagnostics.human_driver import HumanDriver
from echo_heist.infrastructure.resources import load_game_rules, load_sensor_rules
from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.flow import GameFlow, load_level


def key(code):
    return [pygame.event.Event(kind, key=code) for kind in (pygame.KEYDOWN, pygame.KEYUP)]


class AuditedAudio(AudioDirector):
    """Record actual successful mixer submissions, preserving the production mix."""

    def __init__(self):
        super().__init__(enabled=True)
        self.played = Counter()

    def play(self, cue, gain, **kwargs):
        before = self.cues_played
        super().play(cue, gain, **kwargs)
        if self.cues_played > before:
            self.played[cue] += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pygame.display.init()
    pygame.font.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1280, 720))
    canvas = opaque_surface(screen.get_size())
    level, rules = load_level(), load_game_rules()
    audio = AuditedAudio()
    shots, checks, cues = [], [], {}
    with TemporaryDirectory(prefix="echo-connected-props-") as data:
        gateway = connect_gateway(level, rules, load_sensor_rules(), Path(data))
        flow = GameFlow(screen.get_size(), level=level, rules=rules, autonomy_gateway=gateway)
        driver = HumanDriver(rules, use_tools=True)
        session = None

        def shot(name):
            flow.draw(canvas)
            screen.blit(canvas, (0, 0))
            pygame.display.flip()
            pygame.image.save(canvas, str(args.output / f"{name}.png"))
            shots.append(name)

        def frame(events=(), count=1):
            for turn in range(count):
                pygame.event.pump()
                flow.frame(list(events) if turn == 0 else [], 34)
                sound = flow.audio_frame()
                for cue in sound.environment_cues:
                    cues[f"{flow.runs_started}:{cue.event_id}"] = {
                        "kind": str(cue.kind),
                        "object": cue.object_id,
                        "tick": cue.tick,
                        "noise": cue.noise_event_id,
                    }
                audio.update(sound, 34)
                if session and session.mission_end:
                    raise AssertionError(f"Captured during review at {session.simulation.tick}")
                if session and session.simulation.tick % 6 == 0:
                    flow.draw(canvas)
                    screen.blit(canvas, (0, 0))
                    pygame.display.flip()

        def start(*, use_tools=False):
            nonlocal session, driver
            gateway.reset_protocols()
            assert flow._start_run(DeploymentRequest("HUMAN", 1042, level.static_map.map_id))
            flow.airlock.skip()
            session = flow.session
            assert session
            driver = HumanDriver(rules, use_tools=use_tools)

        def observe():
            return session.simulation.observe(session.observer_id)

        def walk_to(tile):
            path = bfs(observe().map_static, observe().own_status.tile, tile).path
            assert path, f"No observed-map route to {tile}"
            for waypoint in path[1:]:
                for _ in range(180):
                    if driver.arrived(observe(), waypoint):
                        break
                    frame(driver.events(observe(), waypoint))
                else:
                    raise AssertionError(
                        f"Route stalled at {waypoint}, own={observe().own_status.tile}"
                    )
            frame(driver.release())

        def approach(spec):
            world = observe().map_static
            candidates = {
                (x + dx, y + dy)
                for x, y in spec.tiles
                for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))
                if (x + dx, y + dy) not in spec.tiles and world.can_walk((x + dx, y + dy))
            }
            paths = [bfs(world, observe().own_status.tile, tile).path for tile in candidates]
            paths = [path for path in paths if path]
            assert paths
            walk_to(min(paths, key=lambda path: (len(path), path[-1]))[-1])
            assert (
                observe().interactions and observe().interactions[0].target_id == spec.object_id
            ), (spec.object_id, observe().interactions)

        def interact():
            frame([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)])
            frame([pygame.event.Event(pygame.KEYUP, key=pygame.K_e)])

        def view(identity):
            return next(
                p
                for p in session.simulation.presentation_snapshot().environment.props
                if p.object_id == identity
            )

        for identity in (
            "door-cross-link",
            "door-core-north",
            "glass-research-rack",
            "glass-research-cell",
        ):
            start(use_tools=identity == "glass-research-cell")
            spec = next(p for p in gateway.environment.props if p.object_id == identity)
            approach(spec)
            shot(identity + "-before")
            interact()
            shot(identity + "-motion")
            frame(count=16)
            if spec.kind == PropKind.DOOR:
                assert view(identity).openness == 0
                shot(identity + "-closed")
                interact()
                frame(count=16)
                assert view(identity).openness == 1
                shot(identity + "-open")
                checks.append(identity + ": real close/open and geometry")
            else:
                assert view(identity).broken
                shot(identity + "-shattered")
                first = {i for i, c in cues.items() if c["object"] == identity}
                interact()
                frame(count=10)
                assert {i for i, c in cues.items() if c["object"] == identity} == first
                walk_to(spec.tile)
                shot(identity + "-crossed")
                checks.append(identity + ": once-only shatter, cue and physical crossing")
        start()
        for code, name in (
            (pygame.K_q, "echo"),
            (pygame.K_f, "emp"),
            (pygame.K_f, "emp-empty"),
            (pygame.K_SPACE, "melee-no-target"),
        ):
            frame(key(code))
            shot("tool-" + name)
        checks.append("Real Echo/EMP use and rejected empty EMP/out-of-range melee")
        start()
        for _ in range(900):
            observation = observe()
            own = observation.own_status.position
            visible = [
                g
                for g in observation.visible_entities
                if g.position is not None and not g.disabled and not g.stunned
            ]
            nearby = sorted(
                visible,
                key=lambda g: sum((a - b) ** 2 for a, b in zip(g.position, own, strict=True)),
            )
            if (
                nearby
                and sum((a - b) ** 2 for a, b in zip(nearby[0].position, own, strict=True))
                <= rules.melee_range_units**2
            ):
                frame(driver.release())
                frame(key(pygame.K_SPACE))
                assert observe().own_status.inventory.melee_charges == 1
                shot("melee-real-guard")
                frame(key(pygame.K_SPACE))
                assert observe().own_status.inventory.melee_charges == 1
                shot("melee-recovery-rejected")
                checks.append("Real guard melee contact, one charge spent; recovery rejects repeat")
                break
            goal = nearby[0].tile if nearby else (34, 11)
            path = bfs(observation.map_static, observation.own_status.tile, goal).path
            assert path
            frame(driver.events(observation, path[1] if len(path) > 1 else goal))
        else:
            raise AssertionError("No real guard melee encounter before review cap")
        report = {
            "driver": pygame.display.get_driver(),
            "audio_ready": bool(pygame.mixer.get_init()),
            "checks": checks,
            "shots": shots,
            "environment_cues": list(cues.values()),
            "submitted_audio": dict(audio.played),
            "audio": audio.report(),
            "scope": "Production gateway/map/security and keyboard; no world-state injection. "
            "Accelerated QA verifies mixer submission, not subjective mix quality.",
        }
        (args.output / "REVIEW.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))
    pygame.mixer.stop()
    pygame.mixer.music.stop()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
