"""Scene navigation (separate from mission phase); owns no gameplay rules."""

from collections import Counter
from collections.abc import Sequence
from enum import StrEnum

import pygame

from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.results import RunOutcome
from echo_heist.core.contracts.security.model import GuardState
from echo_heist.infrastructure.persistence.settings import Settings
from echo_heist.infrastructure.resources import load_game_rules, resource_bytes
from echo_heist.level.io import load_tiled_map
from echo_heist.level.model import LevelData
from echo_heist.ui.audio.feedback import UiFeedback
from echo_heist.ui.audio.model import AudioFrame
from echo_heist.ui.render.environment.furnishings.catalogue import prepare_furniture
from echo_heist.ui.render.layout.viewport import interface_canvas, interface_events
from echo_heist.ui.render.surfaces.cinematic import draw_scene
from echo_heist.ui.render.surfaces.glass import edge_veil
from echo_heist.ui.render.theme import Fonts
from echo_heist.ui.render.world import WorldArt, build_map_surface
from echo_heist.ui.scenes.design.screens import SceneDesigns
from echo_heist.ui.scenes.heist import HeistRequest, HeistSession
from echo_heist.ui.scenes.menus import (
    CHAPTER_CARD,
    MODE_BUTTONS,
    MODE_ITEMS,
    RESULT_MENU,
    RESULT_RETRY,
    RESULT_STORY,
    TITLE_BUTTONS,
    TITLE_ITEMS,
    draw_menu,
    draw_results,
    load_backdrop,
    menu_hit,
    move_selection,
)
from echo_heist.ui.scenes.navigation.controls import ABORT_BUTTONS, MAP_CLOSE, PAUSE_BUTTONS
from echo_heist.ui.scenes.settings import OPTION_RECTS, adjust, click, draw_settings

DEFAULT_MAP_ID = "vault-five-zone"
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


class Scene(StrEnum):
    TITLE = "TITLE"
    MODE = "MODE"
    HEIST = "HEIST"
    RESULTS = "RESULTS"
    SETTINGS = "SETTINGS"
    WORKSHOP = "WORKSHOP"
    LAB = "LAB"
    GUIDE = "GUIDE"
    EPILOGUE = "EPILOGUE"


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
        self.extraction_backdrop = load_backdrop(view_size, "assets/scenes/extraction-dawn.png")
        self.map_surface = build_map_surface(self.level, self.fonts, self.art)
        self.furnishings = prepare_furniture(self.level, self.art.props)
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
        self.settings_return = Scene.TITLE
        self.dragging_slider: int | None = None
        self.designs = SceneDesigns()
        self.ui_feedback = UiFeedback()

    def _feedback_rects(self) -> tuple[pygame.Rect, ...]:
        if self.scene == Scene.TITLE:
            return (*TITLE_BUTTONS, CHAPTER_CARD)
        if self.scene == Scene.MODE:
            return MODE_BUTTONS
        if self.scene == Scene.SETTINGS:
            return OPTION_RECTS
        if self.scene == Scene.RESULTS:
            return (RESULT_RETRY, RESULT_MENU, RESULT_STORY)
        if self.scene in (Scene.WORKSHOP, Scene.LAB, Scene.GUIDE, Scene.EPILOGUE):
            return self.designs.controls(self.scene.value)
        if self.session is not None:
            if self.session.summary:
                return (MAP_CLOSE,)
            if self.session.paused:
                return ABORT_BUTTONS if self.session.confirm_abort else PAUSE_BUTTONS
        return ()

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
            furnishings=self.furnishings,
            reduced_flashing=self.settings.reduced_flashing,
            security_enabled=self.security_enabled,
        )
        self.runs_started += 1
        self.scene = Scene.HEIST

    def resize(self, view_size: tuple[int, int]) -> None:
        self.view_size = view_size
        self.backdrop = load_backdrop(view_size)
        self.extraction_backdrop = load_backdrop(view_size, "assets/scenes/extraction-dawn.png")
        self.dragging_slider = None
        if self.session is not None:
            self.session.resize(view_size)

    def _go(self, scene: Scene) -> None:
        self.scene, self.selected, self.notice = scene, 2 if scene == Scene.MODE else 0, ""
        self.hovered_result = None
        self.dragging_slider = None
        self.designs.selected = 0
        self.designs.notice = ""

    def frame(self, events: Sequence[pygame.event.Event], elapsed_ms: int) -> None:
        events = interface_events(events, self.view_size)
        self.ui_feedback.feed(events, self.scene.value, self._feedback_rects())
        self.ambient_ms += max(0, elapsed_ms)
        if self.scene in (Scene.WORKSHOP, Scene.LAB, Scene.GUIDE, Scene.EPILOGUE):
            if any(event.type == pygame.QUIT for event in events):
                self.running = False
                return
            target = self.designs.handle(self.scene.value, list(events))
            if target is not None:
                self._go(Scene(target))
            return
        if self.scene == Scene.SETTINGS:
            self._settings_events(events)
            return
        if self.scene == Scene.HEIST and self.session is not None:
            self.session.reduced_flashing = self.settings.reduced_flashing
            request = self.session.handle(events)
            if request == HeistRequest.QUIT:
                self.running = False
                return
            if request == HeistRequest.RETRY:
                self._start_run()
                return
            if request == HeistRequest.SETTINGS:
                self.settings_return = Scene.HEIST
                self._go(Scene.SETTINGS)
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
            initial_scene = self.scene
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
                    "STORY"
                    if RESULT_STORY.collidepoint(event.pos)
                    and self.session
                    and self.session.mission_end
                    and self.session.mission_end.outcome == RunOutcome.WIN
                    else "RETRY"
                    if RESULT_RETRY.collidepoint(event.pos)
                    else "MENU"
                    if RESULT_MENU.collidepoint(event.pos)
                    else None
                )
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.scene == Scene.RESULTS:
                    if (
                        RESULT_STORY.collidepoint(event.pos)
                        and self.session
                        and self.session.mission_end
                        and self.session.mission_end.outcome == RunOutcome.WIN
                    ):
                        self._go(Scene.EPILOGUE)
                    elif RESULT_RETRY.collidepoint(event.pos):
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
                    return
            if self.scene != initial_scene:
                return

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
                    self.settings_return = Scene.TITLE
                    self._go(Scene.SETTINGS)
                elif self.selected == 4:
                    self._go(Scene.GUIDE)
        elif self.scene == Scene.MODE:
            self.selected = move_selection(self.selected, MODE_ITEMS, key)
            if key == pygame.K_ESCAPE or (key in CONFIRM_KEYS and self.selected == 3):
                self._go(Scene.TITLE)
            elif key in CONFIRM_KEYS:
                if self.selected == 2:
                    self._start_run()
                elif self.selected == 1:
                    self._go(Scene.WORKSHOP)
                elif MODE_ITEMS[self.selected].enabled:
                    self.mode_choice = self.selected
                    self.selected, self.notice = 2, ""
                else:
                    self.notice = "Companion mode is coming later. Human mode remains selected."
        elif self.scene == Scene.RESULTS:
            if key == pygame.K_r:
                self._start_run()
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER) or key == pygame.K_ESCAPE:
                self._go(Scene.TITLE)
            elif (
                key == pygame.K_c
                and self.session
                and self.session.mission_end
                and self.session.mission_end.outcome == RunOutcome.WIN
            ):
                self._go(Scene.EPILOGUE)

    def _settings_events(self, events: Sequence[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or (
                    event.key in CONFIRM_KEYS and self.selected == 4
                ):
                    self._go(self.settings_return)
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
            elif (
                event.type == pygame.MOUSEBUTTONUP and event.button == 1
            ) or event.type == pygame.WINDOWFOCUSLOST:
                self.dragging_slider = None
            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                if event.type == pygame.MOUSEMOTION and self.dragging_slider is not None:
                    self.settings = click(self.settings, self.dragging_slider, event.pos)
                    continue
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
                            self._go(self.settings_return)
                            return
                        if hit in (0, 1):
                            self.dragging_slider = hit
                        self.settings = click(self.settings, hit, event.pos)

    def draw(self, canvas: pygame.Surface) -> None:
        if self.scene == Scene.HEIST and self.session is not None:
            self.session.draw(canvas)
            return
        end = self.session.mission_end if self.session is not None else None
        ending = self.scene == Scene.EPILOGUE or (
            self.scene == Scene.RESULTS and end is not None and end.outcome == RunOutcome.WIN
        )
        if self.scene == Scene.RESULTS and self.session is not None and not ending:
            self.session.draw(canvas)
            small = pygame.transform.smoothscale(canvas, (320, 180))
            canvas.blit(pygame.transform.smoothscale(small, canvas.get_size()), (0, 0))
            canvas.blit(edge_veil(canvas.get_size(), "right"), (0, 0))
            if end is not None and end.outcome == RunOutcome.CAPTURED:
                warning = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
                warning.fill((75, 8, 10, 28))
                canvas.blit(warning, (0, 0))
        else:
            draw_scene(
                canvas,
                self.extraction_backdrop if ending else self.backdrop,
                self.ambient_ms,
                text_side="right" if ending else "left",
                reduced_motion=self.settings.reduced_flashing,
                mirror_for_text=False,
                reactor_glow=not ending,
            )
        content = interface_canvas(canvas)
        if self.scene in (Scene.WORKSHOP, Scene.LAB, Scene.GUIDE, Scene.EPILOGUE):
            self.designs.draw(
                content,
                self.scene.value,
                self.fonts,
                self.backdrop,
                self.extraction_backdrop,
                self.ambient_ms,
                self.settings.reduced_flashing,
                self.level,
                self.map_surface,
                self.furnishings,
                paint_background=False,
            )
        elif self.scene in (Scene.TITLE, Scene.MODE):
            draw_menu(
                content,
                self.fonts,
                self.backdrop,
                scene=self.scene.value,
                selected=self.selected,
                notice=self.notice,
                clock_ms=self.ambient_ms,
                reduced_motion=self.settings.reduced_flashing,
                mode_choice=self.mode_choice,
                report_available=end is not None,
                paint_background=False,
            )
        elif self.scene == Scene.SETTINGS:
            draw_settings(
                content,
                self.fonts,
                self.backdrop,
                self.settings,
                self.selected,
                self.ambient_ms,
                paint_background=False,
            )
        elif self.scene == Scene.RESULTS and end is not None:
            draw_results(
                content,
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
        observation = (
            self.session.simulation.observe(self.level.operative_id) if self.session else None
        )
        room = self.level.room_at(observation.own_status.tile) if observation else None
        return AudioFrame(
            self.scene.value,
            f"{self.selected}:{self.hovered_result}:{self.designs.selected}:"
            f"{self.designs.draft.choices}:{self.designs.guide_tab}:{self.designs.lab_floor}",
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
            listener_id=self.level.operative_id,
            ui_feedback_serial=self.ui_feedback.serial,
            ui_feedback_cue=self.ui_feedback.cue,
            audible_event_ids=frozenset(cue.event_id for cue in observation.heard_events)
            if observation
            else frozenset(),
            room_style=room.style if room else "",
            sprint_recharge_remaining=observation.own_status.sprint_recharge_remaining
            if observation
            else 0,
            settings_values=(
                self.settings.music_volume,
                self.settings.sfx_volume,
                self.settings.reduced_flashing,
                self.settings.fullscreen,
            ),
            suspicious=any(
                guard.state in (GuardState.SPOTTED, GuardState.INVESTIGATE)
                and observation is not None
                and guard.actor_id in {entity.actor_id for entity in observation.visible_entities}
                for guard in snapshot.guards
            )
            if snapshot
            else False,
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
