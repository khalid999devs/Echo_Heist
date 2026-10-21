"""Scene navigation (separate from mission phase); owns no gameplay rules."""

from collections import Counter
from collections.abc import Sequence
from enum import StrEnum

import pygame

from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.security.model import GuardState
from echo_heist.infrastructure.persistence.settings import Settings
from echo_heist.infrastructure.resources import load_game_rules, resource_bytes
from echo_heist.level.io import load_tiled_map
from echo_heist.level.model import LevelData
from echo_heist.ui.audio.model import AudioFrame
from echo_heist.ui.render.surfaces.cinematic import draw_scene
from echo_heist.ui.render.theme import Fonts
from echo_heist.ui.render.world import WorldArt, build_map_surface
from echo_heist.ui.scenes.heist import HeistRequest, HeistSession
from echo_heist.ui.scenes.menus import (
    MODE_ITEMS,
    RESULT_MENU,
    RESULT_RETRY,
    TITLE_ITEMS,
    draw_menu,
    draw_results,
    load_backdrop,
    menu_hit,
    move_selection,
)
from echo_heist.ui.scenes.settings import OPTION_RECTS, adjust, click, draw_settings

DEFAULT_MAP_ID = "vault-five-zone"
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


class Scene(StrEnum):
    TITLE = "TITLE"
    MODE = "MODE"
    HEIST = "HEIST"
    RESULTS = "RESULTS"
    SETTINGS = "SETTINGS"


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
        settings: Settings | None = None,
        security_enabled: bool = True,
    ) -> None:
        self.view_size, self.seed = view_size, seed
        self.level = level or load_level()
        self.rules = rules or load_game_rules()
        self.settings = settings or Settings()
        self.security_enabled = security_enabled
        self.fonts = Fonts()
        self.art = WorldArt.load()
        self.backdrop = load_backdrop(view_size)
        self.map_surface = build_map_surface(self.level, self.fonts, self.art)
        self.scene = Scene.TITLE
        self.selected = 0
        self.mode_choice = 0
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
            reduced_flashing=self.settings.reduced_flashing,
            security_enabled=self.security_enabled,
        )
        self.runs_started += 1
        self.scene = Scene.HEIST

    def _go(self, scene: Scene) -> None:
        self.scene, self.selected, self.notice = scene, 2 if scene == Scene.MODE else 0, ""
        self.hovered_result = None

    def frame(self, events: Sequence[pygame.event.Event], elapsed_ms: int) -> None:
        self.ambient_ms += max(0, elapsed_ms)
        if self.scene == Scene.SETTINGS:
            self._settings_events(events)
            return
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

    def _key(self, key: int) -> None:
        if self.scene == Scene.TITLE:
            self.selected = move_selection(self.selected, TITLE_ITEMS, key)
            if key == pygame.K_ESCAPE or (key in CONFIRM_KEYS and self.selected == 3):
                self.running = False
            elif key in CONFIRM_KEYS:
                if self.selected == 0:
                    self._go(Scene.MODE)
                elif self.selected == 1:
                    if self.session is not None and self.session.mission_end is not None:
                        self._go(Scene.RESULTS)
                    else:
                        self.notice = "Complete a mission to view its report."
                elif self.selected == 2:
                    self._go(Scene.SETTINGS)
        elif self.scene == Scene.MODE:
            self.selected = move_selection(self.selected, MODE_ITEMS, key)
            if key == pygame.K_ESCAPE or (key in CONFIRM_KEYS and self.selected == 3):
                self._go(Scene.TITLE)
            elif key in CONFIRM_KEYS:
                if self.selected == 2:
                    self._start_run()
                elif MODE_ITEMS[self.selected].enabled:
                    self.mode_choice = self.selected
                    self.selected, self.notice = 2, ""
                else:
                    self.notice = "Companion mode is coming later. Human mode remains selected."
        elif self.scene == Scene.RESULTS:
            if key == pygame.K_r:
                self._start_run()
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._go(Scene.TITLE)
            elif key == pygame.K_ESCAPE:
                self.running = False

    def _settings_events(self, events: Sequence[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or (
                    event.key in CONFIRM_KEYS and self.selected == 4
                ):
                    self._go(Scene.TITLE)
                    return
                if event.key in (pygame.K_UP, pygame.K_DOWN):
                    self.selected = (
                        self.selected + (1 if event.key == pygame.K_DOWN else -1)
                    ) % len(OPTION_RECTS)
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    self.settings = adjust(
                        self.settings, self.selected, 1 if event.key == pygame.K_RIGHT else -1
                    )
                elif event.key in CONFIRM_KEYS and self.selected in (2, 3):
                    self.settings = adjust(self.settings, self.selected, 1)
            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                hit = next(
                    (
                        index
                        for index, rect in enumerate(OPTION_RECTS)
                        if rect.collidepoint(event.pos)
                    ),
                    None,
                )
                if hit is not None:
                    self.selected = hit
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if hit == 4:
                            self._go(Scene.TITLE)
                            return
                        self.settings = click(self.settings, hit, event.pos)

    def draw(self, canvas: pygame.Surface) -> None:
        if self.scene == Scene.TITLE:
            draw_menu(
                canvas,
                self.fonts,
                self.backdrop,
                scene="TITLE",
                selected=self.selected,
                notice=self.notice,
                clock_ms=self.ambient_ms,
                reduced_motion=self.settings.reduced_flashing,
                report_available=self.session is not None and self.session.mission_end is not None,
            )
        elif self.scene == Scene.MODE:
            draw_menu(
                canvas,
                self.fonts,
                self.backdrop,
                scene="MODE",
                selected=self.selected,
                notice=self.notice,
                clock_ms=self.ambient_ms,
                reduced_motion=self.settings.reduced_flashing,
                mode_choice=self.mode_choice,
            )
        elif self.scene == Scene.SETTINGS:
            draw_settings(
                canvas, self.fonts, self.backdrop, self.settings, self.selected, self.ambient_ms
            )
        elif self.session is not None:
            self.session.draw(canvas)
            end = self.session.mission_end
            if self.scene == Scene.RESULTS and end is not None:
                draw_scene(
                    canvas,
                    self.backdrop,
                    self.ambient_ms,
                    text_side="right",
                    reduced_motion=self.settings.reduced_flashing,
                )
                draw_results(
                    canvas,
                    end,
                    self.fonts,
                    ticks_per_second=self.rules.simulation_hz,
                    hovered=self.hovered_result,
                    clock_ms=self.ambient_ms,
                )

    def audio_frame(self) -> AudioFrame:
        events = tuple(self.session.audio_events) if self.session is not None else ()
        if self.session is not None:
            self.session.audio_events.clear()
        snapshot = self.session.simulation.presentation_snapshot() if self.session else None
        return AudioFrame(
            self.scene.value,
            f"{self.selected}:{self.hovered_result}",
            self.runs_started,
            phase=snapshot.phase if snapshot else None,
            paused=(self.session.paused or self.session.summary) if self.session else False,
            outcome=snapshot.mission_end.outcome if snapshot and snapshot.mission_end else None,
            alerted=any(
                guard.state in (GuardState.CHASE, GuardState.SEARCH) for guard in snapshot.guards
            )
            if snapshot
            else False,
            events=events,
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
