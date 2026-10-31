"""Manual/native P04 presentation QA with prominently labeled synthetic data.

Run: uv run --locked python -m tests.fixtures.autonomy.capture --output <dir>
This is NOT MCTS/minimax/NEXUS proof or autonomous success evidence.
"""

import argparse
import json
from pathlib import Path
from statistics import median
from time import perf_counter

import pygame

from echo_heist.infrastructure.resources import load_game_rules
from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.bootstrap import _logical_events
from echo_heist.ui.render.autonomy.panel import AUTONOMY_TABS
from echo_heist.ui.render.autonomy.protocols import RESET_BUTTONS, RESET_MEMORY
from echo_heist.ui.render.layout.viewport import interface_origin, logical_size_for
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.design.screens import LAB_CONTROLS
from echo_heist.ui.scenes.design.workshop import WORKSHOP_CONTROLS
from echo_heist.ui.scenes.flow import GameFlow, Scene, load_level
from echo_heist.ui.scenes.menus import CHAPTER_CARD, MODE_BUTTONS
from echo_heist.ui.scenes.navigation.controls import PAUSE_BUTTONS
from echo_heist.ui.scenes.settings import OPTION_RECTS
from tests.fixtures.autonomy.scripted import ACTOR_ID, ScriptedGateway


def key(code: int) -> list[pygame.event.Event]:
    return [pygame.event.Event(kind, key=code) for kind in (pygame.KEYDOWN, pygame.KEYUP)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/phase04-presentation"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pygame.display.init()
    pygame.font.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1280, 720))
    canvas = opaque_surface((1280, 720))
    level, rules = load_level(), load_game_rules()
    audio = AudioDirector(enabled=True)
    current = GameFlow(canvas.get_size(), level=level, rules=rules)
    shots = []
    frame_times = []
    layouts = []

    def render() -> None:
        began = perf_counter()
        pygame.event.pump()
        audio.update(current.audio_frame(), 34)
        current.draw(canvas)
        # Synthetic traces never masquerade as real algorithm output in images.
        if current.deployment.gateway is not None:
            text = current.fonts.micro.render(
                "SCRIPTED QA FIXTURE / NOT ALGORITHM EVIDENCE", True, (251, 190, 82)
            )
            box = text.get_rect(midtop=(canvas.get_width() // 2, 4)).inflate(16, 6)
            pygame.draw.rect(canvas, (4, 13, 20), box, border_radius=4)
            canvas.blit(text, text.get_rect(center=box.center))
        screen.blit(pygame.transform.smoothscale(canvas, screen.get_size()), (0, 0))
        pygame.display.flip()
        frame_times.append((perf_counter() - began) * 1000)

    def shot(name: str) -> None:
        render()
        path = args.output / (name + ".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(screen, str(path))
        shots.append(name)

    def click(rect: pygame.Rect) -> None:
        origin = interface_origin(current.view_size)
        logical = (rect.centerx + origin[0], rect.centery + origin[1])
        window = pygame.display.get_window_size()
        position = (
            round(logical[0] * window[0] / current.view_size[0]),
            round(logical[1] * window[1] / current.view_size[1]),
        )
        events = [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position)]
        current.frame(_logical_events(events, window, current.view_size), 0)

    click(CHAPTER_CARD)
    click(MODE_BUTTONS[1])
    shot("shipped/unavailable-workshop")
    click(WORKSHOP_CONTROLS[8])
    assert current.runs_started == 0 and current.session is None
    shot("shipped/unavailable-reason")
    click(WORKSHOP_CONTROLS[7])
    for i, rect in enumerate(LAB_CONTROLS[:2]):
        click(rect)
        shot(f"shipped/facility-floor-{i + 1}")

    gateway = ScriptedGateway(level, rules, route=True)
    current = GameFlow(canvas.get_size(), level=level, rules=rules, autonomy_gateway=gateway)
    click(CHAPTER_CARD)
    click(MODE_BUTTONS[1])
    for i in range(3):
        click(WORKSHOP_CONTROLS[i])
        shot(f"fixture/policy-{i}")
    for i in range(3, 7):
        click(WORKSHOP_CONTROLS[i])
    shot("fixture/custom-policy")
    click(RESET_MEMORY)
    shot("fixture/reset-confirmation")
    click(RESET_BUTTONS[1])
    assert gateway.reset_calls == 0
    gateway.fail_reset = True
    click(RESET_MEMORY)
    click(RESET_BUTTONS[0])
    shot("fixture/reset-failure")
    click(RESET_BUTTONS[1])
    gateway.fail_reset = False
    click(RESET_MEMORY)
    click(RESET_BUTTONS[0])
    shot("fixture/reset-complete")
    assert gateway.reset_calls == 2 and gateway.state.active is None
    click(WORKSHOP_CONTROLS[8])
    assert current.session and current.session.observer_id == ACTOR_ID
    before = current.session.simulation.fingerprint()
    shot("fixture/entry")
    current.frame([], 700)
    assert current.session.simulation.fingerprint() == before
    current.frame([], 600)
    shot("fixture/initial-live-view")
    for i, tab in enumerate(AUTONOMY_TABS):
        click(tab)
        shot(f"fixture/live-tab-{i}")
    current.frame(key(pygame.K_ESCAPE), 0)
    shot("fixture/pause")
    before = current.session.simulation.fingerprint()
    click(PAUSE_BUTTONS[2])
    shot("fixture/settings")
    current.frame([], 5000)
    click(OPTION_RECTS[4])
    assert current.session.simulation.fingerprint() == before
    click(PAUSE_BUTTONS[0])
    current.frame(key(pygame.K_TAB), 0)
    shot("fixture/map")
    current.frame([], 5000)
    assert current.session.simulation.fingerprint() == before
    current.frame(key(pygame.K_TAB), 0)
    run = gateway.runs[-1]
    # Actual Simulation movement from scripted inputs verifies two-deck camera,
    # four-frame robot art on both stair directions, and terminal navigation.
    decks = set()
    stairs = set()
    phases = set()
    for frame in range(2400):
        current.frame([], 34)
        if current.session is None:
            raise AssertionError("The presentation lost its runtime")
        snapshot = current.session.simulation.presentation_snapshot()
        own = current.session.simulation.observe(ACTOR_ID).own_status
        deck = level.deck_at(own.tile)
        if deck and deck.deck_id not in decks:
            decks.add(deck.deck_id)
            shot("fixture/deck-" + deck.deck_id)
        for travel in snapshot.stairs:
            if travel.actor_id == ACTOR_ID:
                name = "up" if travel.destination[0] > travel.source[0] else "down"
                if name not in stairs:
                    stairs.add(name)
                    shot("fixture/stairs-" + name)
        if snapshot.phase.value not in phases:
            phases.add(snapshot.phase.value)
            shot("fixture/phase-" + snapshot.phase.value.lower())
        if current.scene == Scene.RESULTS:
            break
        if frame % 4 == 0:
            render()
    assert current.session.mission_end and current.session.mission_end.outcome.value == "WIN"
    current.frame([], 2200)
    shot("fixture/scripted-result-not-ai-proof")
    current.frame(key(pygame.K_r), 0)
    assert current.scene == Scene.WORKSHOP and len(gateway.requests) == 1
    shot("fixture/review-retry")

    for requested in ((1366, 768), (1440, 900), (0, 0)):
        screen = pygame.display.set_mode(
            requested, pygame.FULLSCREEN if requested == (0, 0) else pygame.RESIZABLE
        )
        actual = screen.get_size()
        logical = logical_size_for(actual)
        current.resize(logical)
        canvas = opaque_surface(logical)
        click(RESET_MEMORY)
        # Already-reset memory honestly leaves reset disabled; main controls still work.
        click(WORKSHOP_CONTROLS[1])
        shot(f"layouts/{actual[0]}x{actual[1]}-workshop")
        click(WORKSHOP_CONTROLS[8])
        assert current.session
        current.frame([], 1300)
        for tab in AUTONOMY_TABS:
            click(tab)
        shot(f"layouts/{actual[0]}x{actual[1]}-live")
        current.frame(key(pygame.K_ESCAPE), 0)
        current.frame(key(pygame.K_r), 0)
        assert current.scene == Scene.WORKSHOP
        layouts.append(
            {"actual": actual, "logical": logical, "fullscreen": pygame.display.is_fullscreen()}
        )
    report = {
        "scope": (
            "Presentation QA only. Synthetic search/protocol data; "
            "scripted inputs use real Simulation. NOT autonomous algorithm proof."
        ),
        "video_driver": pygame.display.get_driver(),
        "audio_ready": pygame.mixer.get_init() is not None,
        "screens": shots,
        "layouts": layouts,
        "frames": len(frame_times),
        "decks": sorted(decks),
        "stair_directions": sorted(stairs),
        "phases": sorted(phases),
        "scripted_simulation_outcome": run.presentation_snapshot().mission_end.outcome.value,
        "render_audio_present_ms": {
            "median": round(median(frame_times), 2),
            "p95": round(sorted(frame_times)[int(0.95 * len(frame_times))], 2),
            "max": round(max(frame_times), 2),
        },
    }
    (args.output / "QA.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
