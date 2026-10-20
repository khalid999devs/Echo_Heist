"""Scene navigation (separate from mission phase); owns no gameplay rules."""

from collections import Counter
from collections.abc import Sequence
from enum import StrEnum

import pygame

from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.infrastructure.resources import load_game_rules, resource_bytes
from echo_heist.level.io import load_tiled_map
from echo_heist.level.model import LevelData
from echo_heist.ui.render.theme import Fonts
from echo_heist.ui.render.world import build_map_surface
from echo_heist.ui.scenes.heist import HeistRequest, HeistSession
from echo_heist.ui.scenes.menus import (
    MODE_ITEMS,
    TITLE_ITEMS,
    draw_menu,
    draw_results,
    move_selection,
)

DEFAULT_MAP_ID = "vault-five-zone"
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


class Scene(StrEnum):
    TITLE = "TITLE"
    MODE = "MODE"
    HEIST = "HEIST"
    RESULTS = "RESULTS"


def load_level(map_id: str = DEFAULT_MAP_ID) -> LevelData:
    """Packaged map through the resource service; invalid maps raise MapFormatError."""
    return load_tiled_map(resource_bytes(f"data/maps/{map_id}.json"), expected_map_id=map_id)


class GameFlow:
    def __init__(
        self,
        view_size: tuple[int, int],
        *,
        seed: int = 1042,
        level: LevelData | None = None,
        rules: GameRules | None = None,
    ) -> None:
        self.view_size, self.seed = view_size, seed
        self.level = level or load_level()
        self.rules = rules or load_game_rules()
        self.fonts = Fonts()
        self.map_surface = build_map_surface(self.level, self.fonts)
        self.scene = Scene.TITLE
        self.selected = 0
        self.notice = ""
        self.running = True
        self.session: HeistSession | None = None
        self.outcomes: Counter[str] = Counter()
        self.runs_started = 0

    def _start_run(self) -> None:
        self.session = HeistSession(
            self.level,
            self.rules,
            seed=self.seed,
            fonts=self.fonts,
            view_size=self.view_size,
            map_surface=self.map_surface,
        )
        self.runs_started += 1
        self.scene = Scene.HEIST

    def _go(self, scene: Scene) -> None:
        self.scene, self.selected, self.notice = scene, 0, ""

    def frame(self, events: Sequence[pygame.event.Event], elapsed_ms: int) -> None:
        if self.scene == Scene.HEIST and self.session is not None:
            request = self.session.handle(events)
            if request == HeistRequest.QUIT:
                self.running = False
                return
            if request == HeistRequest.RETRY:
                self._start_run()
                return
            self.session.update(elapsed_ms)
            end = self.session.mission_end
            if end is not None:
                self.outcomes[end.outcome.value] += 1
                self.scene = Scene.RESULTS
            return
        if any(event.type == pygame.QUIT for event in events):
            self.running = False
            return
        for event in events:
            if event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
                self._key(event.key)
                if not self.running or self.scene == Scene.HEIST:
                    return

    def _key(self, key: int) -> None:
        if self.scene == Scene.TITLE:
            self.selected = move_selection(self.selected, TITLE_ITEMS, key)
            if key == pygame.K_ESCAPE or (key in CONFIRM_KEYS and self.selected == 1):
                self.running = False
            elif key in CONFIRM_KEYS:
                self._go(Scene.MODE)
        elif self.scene == Scene.MODE:
            self.selected = move_selection(self.selected, MODE_ITEMS, key)
            if key == pygame.K_ESCAPE:
                self._go(Scene.TITLE)
            elif key in CONFIRM_KEYS and MODE_ITEMS[self.selected].enabled:
                self._start_run()
            elif key in CONFIRM_KEYS:
                self.notice = "Companion mode is not playable until Phase 04."
        elif self.scene == Scene.RESULTS:
            if key == pygame.K_r:
                self._start_run()
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._go(Scene.TITLE)
            elif key == pygame.K_ESCAPE:
                self.running = False

    def draw(self, canvas: pygame.Surface) -> None:
        if self.scene == Scene.TITLE:
            draw_menu(
                canvas,
                self.fonts,
                heading="Main menu",
                items=TITLE_ITEMS,
                selected=self.selected,
                notice=self.notice,
                footer="Up/Down select   Enter confirm   Esc quit",
            )
        elif self.scene == Scene.MODE:
            draw_menu(
                canvas,
                self.fonts,
                heading=f"Choose mode  |  map {self.level.static_map.map_id}",
                items=MODE_ITEMS,
                selected=self.selected,
                notice=self.notice,
                footer="Up/Down select   Enter start   Esc back",
            )
        elif self.session is not None:
            self.session.draw(canvas)
            end = self.session.mission_end
            if self.scene == Scene.RESULTS and end is not None:
                draw_results(canvas, end, self.fonts, ticks_per_second=self.rules.simulation_hz)

    def report(self) -> dict[str, object]:
        return {
            "scene": self.scene.value,
            "map_id": self.level.static_map.map_id,
            "seed": self.seed,
            "runs_started": self.runs_started,
            "outcomes": dict(self.outcomes),
            "simulation_steps": self.session.steps if self.session else 0,
        }
