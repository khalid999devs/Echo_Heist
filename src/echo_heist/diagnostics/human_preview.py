"""Explicit P02 contact-test room; this is not Suhita's five-zone game scene."""

import argparse
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import pygame

from echo_heist.core.contracts.results import MissionSpec, PresentationSnapshot
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import ActorKind, ActorSpawn, MapObject, StaticMap
from echo_heist.core.simulation.engine import Simulation
from echo_heist.infrastructure.persistence.atomic import atomic_write_json
from echo_heist.infrastructure.resources import load_game_rules
from echo_heist.ui.input.human import HumanInput, UiCommand
from echo_heist.ui.presenters.objective import build_objective_view, draw_objective

TILE_PX = 50
ORIGIN = (24, 190)


def create_preview(seed: int = 1042) -> Simulation:
    """Deliberate diagnostic geometry; no Tiled loading or game-scene ownership."""
    world_map = StaticMap(
        "p02-contact-diagnostic",
        12,
        8,
        frozenset({(5, 1), (5, 2)}),
        frozenset({(5, 1), (5, 2)}),
        (MapObject("preview-core", "Core", (10, 3)), MapObject("preview-exit", "Exit", (1, 3))),
    )
    return Simulation(
        world_map,
        (ActorSpawn("operative", (1, 3)), ActorSpawn("contact-guard", (6, 5), ActorKind.SENTINEL)),
        rules=load_game_rules(),
        mission=MissionSpec("operative", "preview-core", "preview-exit"),
        seed=seed,
    )


def _draw_room(
    screen: pygame.Surface, snapshot: PresentationSnapshot, font: pygame.font.Font
) -> None:
    def point(position: tuple[int, int]) -> tuple[int, int]:
        return ORIGIN[0] + position[0] * TILE_PX // UNIT, ORIGIN[1] + position[1] * TILE_PX // UNIT

    for x in range(snapshot.world_map.width):
        for y in range(snapshot.world_map.height):
            rect = pygame.Rect(ORIGIN[0] + x * TILE_PX, ORIGIN[1] + y * TILE_PX, TILE_PX, TILE_PX)
            pygame.draw.rect(
                screen,
                (53, 67, 87) if (x, y) in snapshot.world_map.blocked_tiles else (22, 34, 49),
                rect,
            )
            pygame.draw.rect(screen, (37, 49, 65), rect, 1)
    for obj in snapshot.world_map.objects:
        rect = pygame.Rect(
            ORIGIN[0] + obj.tile[0] * TILE_PX + 8,
            ORIGIN[1] + obj.tile[1] * TILE_PX + 8,
            TILE_PX - 16,
            TILE_PX - 16,
        )
        if obj.kind == "Exit":
            pygame.draw.rect(screen, (91, 222, 166), rect, 3)
        elif snapshot.core_owner is None:
            pygame.draw.rect(screen, (255, 207, 100), rect)
    for actor in snapshot.actors:
        assert actor.position is not None
        color = (75, 214, 246) if actor.kind == ActorKind.OPERATIVE else (242, 109, 131)
        if actor.disabled:
            color = (115, 134, 156)
        elif actor.stunned:
            color = (255, 207, 100)
        pygame.draw.circle(screen, color, point(actor.position), 15)
        if actor.kind != ActorKind.OPERATIVE:
            screen.blit(
                font.render("stationary", True, color),
                (point(actor.position)[0] - 40, point(actor.position)[1] + 20),
            )
        if any(capture.target_id == actor.actor_id for capture in snapshot.captures):
            pygame.draw.circle(screen, (255, 207, 100), point(actor.position), 21, 2)
    for echo in snapshot.echoes:
        pygame.draw.circle(screen, (75, 214, 246), point(echo.position), 13, 2)


def run_preview(
    *, seed: int = 1042, smoke_frames: int | None = None, screenshot: Path | None = None
) -> dict[str, object]:
    if smoke_frames is not None and smoke_frames <= 0:
        raise ValueError("Smoke frames must be positive")
    simulation = create_preview(seed)
    adapter = HumanInput("operative")
    frames = paused_frames = restarts = steps = 0
    counts: Counter[str] = Counter()
    paused, summary, running, accumulator = False, False, True, 0
    try:
        pygame.display.init()
        pygame.font.init()
        screen = pygame.display.set_mode((960, 700))
        pygame.display.set_caption("ECHO HEIST - P02 diagnostic contact room")
        font = pygame.font.Font(None, 27)
        small = pygame.font.Font(None, 22)
        clock = pygame.time.Clock()
        while running:
            elapsed_ms = clock.tick(60)
            events = pygame.event.get()
            commands = adapter.feed(events)
            if UiCommand.QUIT in commands:
                running = False
            if UiCommand.PAUSE in commands:
                paused = not paused
                adapter.clear()
            if UiCommand.FOCUS_LOST in commands:
                paused = True
            if UiCommand.OBJECTIVE in commands:
                summary = not summary
            if any(
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_r
                and not getattr(event, "repeat", False)
                for event in events
            ):
                simulation = create_preview(seed)
                adapter.clear()
                paused, accumulator = False, 0
                restarts += 1
            if not running:
                break
            if paused or simulation.presentation_snapshot().mission_end is not None:
                accumulator = 0
                paused_frames += int(paused)
            else:
                accumulator = min(accumulator + elapsed_ms * simulation.ticks_per_second, 8000)
                while accumulator >= 1000:
                    action = adapter.action_for(simulation.observe("operative"))
                    result = simulation.step((action,))
                    counts.update(event.kind.value for event in result.events)
                    accumulator -= 1000
                    steps += 1
                    if result.mission_end is not None:
                        accumulator = 0
                        break
            screen.fill((11, 19, 31))
            view = build_objective_view(
                simulation.observe("operative"), ticks_per_second=simulation.ticks_per_second
            )
            draw_objective(screen, view, font)
            screen.blit(
                small.render(
                    "P02 DIAGNOSTIC ROOM / stationary guard / not the five-zone mission",
                    True,
                    (150, 167, 190),
                ),
                (24, 150),
            )
            _draw_room(screen, simulation.presentation_snapshot(), small)
            labels = [
                "WASD / arrows: move",
                "Shift: sprint",
                "Hold E: recover core",
                "Q: Echo | F: EMP",
                "Space: single-target melee",
                "Esc: pause / resume",
                "R: restart same seed",
                "Tab: objective summary",
                "No score until P06",
            ]
            for index, text in enumerate(labels):
                screen.blit(small.render(text, True, (190, 207, 226)), (660, 200 + index * 30))
            if paused:
                screen.blit(
                    font.render("PAUSED - simulation time frozen", True, (255, 207, 100)), (24, 612)
                )
            elif simulation.presentation_snapshot().mission_end is not None:
                text = f"{simulation.presentation_snapshot().phase.value} - R to retry"
                screen.blit(font.render(text, True, (91, 222, 166)), (24, 612))
            elif summary:
                screen.blit(
                    font.render(
                        "Recover the core, then return to the green Entry marker.",
                        True,
                        (91, 222, 166),
                    ),
                    (24, 612),
                )
            if UiCommand.LAB in commands:
                summary = True  # P03 adds actual algorithm telemetry; none invented here.
            pygame.display.flip()
            frames += 1
            if smoke_frames is not None and frames >= smoke_frames:
                running = False
        if screenshot is not None:
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(screen, str(screenshot))
        end = simulation.presentation_snapshot().mission_end
        return {
            "diagnostic": "p02-contact-room",
            "seed": seed,
            "frames": frames,
            "tick": simulation.tick,
            "simulation_steps": steps,
            "paused_frames": paused_frames,
            "restarts": restarts,
            "phase": simulation.presentation_snapshot().phase.value,
            "mission_end": asdict(end) if end is not None else None,
            "event_counts": dict(counts),
            "state_hash": simulation.fingerprint(),
            "video_driver": pygame.display.get_driver(),
        }
    finally:
        pygame.quit()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1042)
    parser.add_argument("--smoke-frames", type=int)
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = run_preview(seed=args.seed, smoke_frames=args.smoke_frames, screenshot=args.screenshot)
    if args.report:
        atomic_write_json(args.report, report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
