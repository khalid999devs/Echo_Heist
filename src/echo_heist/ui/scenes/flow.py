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
from echo_heist.ui.render.world import WorldArt, build_map_surface
from echo_heist.ui.scenes.heist import HeistRequest, HeistSession
from echo_heist.ui.scenes.menus import (
    BACKDROP_PAD,
    LAUNCH_BUTTON,
    MODE_ITEMS,
    RESULT_MENU,
    RESULT_RETRY,
    TITLE_ITEMS,
    draw_menu,
    draw_results,
    load_backdrop,
    load_operative_portrait,
    menu_hit,
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
        self.art = WorldArt.load()
        self.backdrop = load_backdrop(view_size)
        self.portrait = load_operative_portrait()
        self.map_surface = build_map_surface(self.level, self.fonts, self.art)
        self.scene = Scene.TITLE
        self.selected = 0
        self.notice = ""
        self.hovered_result: str | None = None
        self.running = True
        self.session: HeistSession | None = None
        self.outcomes: Counter[str] = Counter()
        self.runs_started = 0
        self.ambient_ms = 0

    def _start_run(self) -> None:
        self.hovered_result = None
        self.session = HeistSession(
            self.level,
            self.rules,
            seed=self.seed,
            fonts=self.fonts,
            view_size=self.view_size,
            map_surface=self.map_surface,
            art=self.art,
        )
        self.runs_started += 1
        self.scene = Scene.HEIST

    def _go(self, scene: Scene) -> None:
        self.scene, self.selected, self.notice = scene, 0, ""
        self.hovered_result = None

    def frame(self, events: Sequence[pygame.event.Event], elapsed_ms: int) -> None:
        self.ambient_ms += max(0, elapsed_ms)
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
                self.hovered_result = None
            return
        if any(event.type == pygame.QUIT for event in events):
            self.running = False
            return
        for event in events:
            if event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
                self._key(event.key)
                if not self.running or self.scene == Scene.HEIST:
                    return
            elif event.type == pygame.MOUSEMOTION and self.scene in (Scene.TITLE, Scene.MODE):
                hovered = menu_hit(self.scene.value, event.pos)
                if hovered is not None:
                    self.selected = hovered
            elif event.type == pygame.MOUSEMOTION and self.scene == Scene.RESULTS:
                self.hovered_result = (
                    "RETRY"
                    if RESULT_RETRY.collidepoint(event.pos)
                    else "MENU"
                    if RESULT_MENU.collidepoint(event.pos)
                    else None
                )
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.scene == Scene.RESULTS:
                    if RESULT_RETRY.collidepoint(event.pos):
                        self._start_run()
                    elif RESULT_MENU.collidepoint(event.pos):
                        self._go(Scene.TITLE)
                    return
                if self.scene not in (Scene.TITLE, Scene.MODE):
                    continue
                clicked = menu_hit(self.scene.value, event.pos)
                if clicked is not None:
                    self.selected = clicked
                    self._key(pygame.K_RETURN)
                elif self.scene == Scene.MODE and LAUNCH_BUTTON.collidepoint(event.pos):
                    self._key(pygame.K_RETURN)

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
                self.backdrop,
                self.portrait,
                scene="TITLE",
                selected=self.selected,
                notice=self.notice,
                clock_ms=self.ambient_ms,
            )
        elif self.scene == Scene.MODE:
            draw_menu(
                canvas,
                self.fonts,
                self.backdrop,
                self.portrait,
                scene="MODE",
                selected=self.selected,
                notice=self.notice,
                clock_ms=self.ambient_ms,
            )
        elif self.session is not None:
            self.session.draw(canvas)
            end = self.session.mission_end
            if self.scene == Scene.RESULTS and end is not None:
                canvas.fill((3, 12, 20))
                crop = pygame.Rect(650 + BACKDROP_PAD, BACKDROP_PAD, 620, self.view_size[1])
                canvas.blit(self.backdrop, (0, 0), crop)
                draw_results(
                    canvas,
                    end,
                    self.fonts,
                    ticks_per_second=self.rules.simulation_hz,
                    hovered=self.hovered_result,
                    clock_ms=self.ambient_ms,
                )

    def report(self) -> dict[str, object]:
        return {
            "scene": self.scene.value,
            "map_id": self.level.static_map.map_id,
            "seed": self.seed,
            "runs_started": self.runs_started,
            "outcomes": dict(self.outcomes),
            "simulation_steps": self.session.steps if self.session else 0,
        }
