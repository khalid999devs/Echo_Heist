"""Scene navigation (separate from mission phase); owns no gameplay rules."""

from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import replace
from enum import StrEnum
from uuid import uuid4

import pygame

from echo_heist.core.contracts.autonomy.model import ControlMode
from echo_heist.core.contracts.autonomy.policy import DeploymentRequest
from echo_heist.core.contracts.autonomy.runtime import AutonomyGateway, DeploymentUnavailable
from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.experience.model import ResultRequest, ToolUsage
from echo_heist.core.contracts.experience.ports import ExperienceGateway
from echo_heist.core.contracts.results import RunOutcome
from echo_heist.core.contracts.security.model import GuardState
from echo_heist.infrastructure.persistence.settings import Settings
from echo_heist.infrastructure.resources import load_game_rules, resource_bytes
from echo_heist.level.io import load_tiled_map
from echo_heist.level.model import LevelData
from echo_heist.ui.audio.feedback import UiFeedback
from echo_heist.ui.audio.model import AudioFrame
from echo_heist.ui.input.configuration import bindings_for, key_label, movement_hint
from echo_heist.ui.presenters.reporting import ReportState
from echo_heist.ui.render.autonomy.panel import AUTONOMY_TABS
from echo_heist.ui.render.environment.furnishings.catalogue import prepare_furniture
from echo_heist.ui.render.layout.viewport import interface_canvas, interface_events
from echo_heist.ui.render.security.lab import GUARD_TABS
from echo_heist.ui.render.surfaces.cinematic import draw_scene
from echo_heist.ui.render.surfaces.glass import edge_veil
from echo_heist.ui.render.theme import Fonts
from echo_heist.ui.render.world import WorldArt, build_map_surface
from echo_heist.ui.scenes.companion.deployment import DeploymentPanel, restore_selection, selection
from echo_heist.ui.scenes.design.screens import SceneDesigns
from echo_heist.ui.scenes.experience.preferences import PreferencesPanel
from echo_heist.ui.scenes.experience.profiles import PROFILE_BUTTON, ProfilePanel
from echo_heist.ui.scenes.experience.report import RESULT_DETAILS, RESULT_NEW_SEED, ReportInspector
from echo_heist.ui.scenes.experience.seed import SEED_ACTIONS, SEED_BUTTON, SeedDialog
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
from echo_heist.ui.scenes.transitions.airlock import AirlockTransition

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
        loading: Callable[[float, str], None] | None = None,
        autonomy_gateway: AutonomyGateway | None = None,
        experience_gateway: ExperienceGateway | None = None,
    ) -> None:
        def prepared(fraction: float, label: str) -> None:
            if loading is not None:
                loading(fraction, label)

        self.view_size, self.seed = view_size, seed
        self.level = level or load_level()
        self.rules = rules or load_game_rules()
        self.settings = settings or Settings()
        self.security_enabled = security_enabled
        prepared(0.06, "Preparing the facility")
        self.fonts = Fonts()
        self.backdrop = load_backdrop(view_size)
        self.extraction_backdrop = load_backdrop(view_size, "assets/scenes/extraction-dawn.png")
        prepared(0.18, "Preparing the facility")
        self.art = WorldArt.load()
        prepared(0.52, "Preparing the facility")
        self.furnishings = prepare_furniture(self.level, self.art.props)
        prepared(0.68, "Preparing the facility")
        self.map_surface = build_map_surface(
            self.level, self.fonts, self.art, furnishings=self.furnishings
        )
        prepared(0.96, "Preparing the facility")
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
        self.deployment = DeploymentPanel(autonomy_gateway)
        self.last_deployment: DeploymentRequest | None = None
        self.designs = SceneDesigns(self.deployment)
        self.ui_feedback = UiFeedback()
        self.airlock = AirlockTransition()
        self.app_nonce = uuid4().hex[:12]
        self.reports = ReportState(experience_gateway)
        self.inspector = ReportInspector(self.reports)
        self.profiles = ProfilePanel(experience_gateway)
        self.preferences = PreferencesPanel(experience_gateway)
        self.seed_dialog = SeedDialog()
        prepared(1.0, "Facility ready")

    def _feedback_rects(self) -> tuple[pygame.Rect, ...]:
        if self.seed_dialog.open:
            return SEED_ACTIONS
        if self.profiles.open:
            return self.profiles.controls()
        if self.inspector.open:
            return self.inspector.controls()
        if self.scene == Scene.TITLE:
            return (CHAPTER_CARD, *TITLE_BUTTONS[1:])
        if self.scene == Scene.MODE:
            return (*MODE_BUTTONS, SEED_BUTTON)
        if self.scene == Scene.SETTINGS:
            return self.preferences.controls()
        if self.scene == Scene.RESULTS:
            return (RESULT_RETRY, RESULT_MENU, RESULT_STORY, RESULT_DETAILS, RESULT_NEW_SEED)
        if self.scene in (Scene.WORKSHOP, Scene.LAB, Scene.GUIDE, Scene.EPILOGUE):
            return (
                (*self.designs.controls(self.scene.value), PROFILE_BUTTON, SEED_BUTTON)
                if self.scene == Scene.WORKSHOP
                else self.designs.controls(self.scene.value)
            )
        if self.session is not None:
            if self.session.summary:
                return (MAP_CLOSE,)
            if self.session.paused:
                return ABORT_BUTTONS if self.session.confirm_abort else PAUSE_BUTTONS
            if not self.session.panels_interactive:
                return ()
            if self.session.lab_note:
                return GUARD_TABS
            if self.session.autonomy_panel:
                return AUTONOMY_TABS
        return ()

    def _start_run(self, request: DeploymentRequest | None = None) -> bool:
        request = request or DeploymentRequest(
            ControlMode.HUMAN,
            self.seed,
            self.level.static_map.map_id,
            selection(self.designs.draft),
        )
        self.deployment.refresh()
        try:
            run = self.deployment.deploy(request, self.level, self.rules)
        except DeploymentUnavailable as error:
            self.notice = self.designs.notice = str(error)
            return False
        session = HeistSession(
            self.level,
            self.rules,
            seed=request.seed,
            fonts=self.fonts,
            view_size=self.view_size,
            map_surface=self.map_surface,
            art=self.art,
            furnishings=self.furnishings,
            reduced_flashing=self.settings.reduced_flashing,
            security_enabled=self.security_enabled,
            run=run,
        )
        session.input.bindings = bindings_for(self.preferences.preferences)
        session.subtitles = self.preferences.preferences.subtitles
        session.high_contrast = self.preferences.preferences.high_contrast
        self.inspector.open = self.profiles.open = self.seed_dialog.open = False
        self.hovered_result = None
        self.session = session
        self.last_deployment = request
        self.runs_started += 1
        self.scene = Scene.HEIST
        self.airlock.start("ENTRY")
        return True

    def _retry_run(self) -> None:
        request = self.last_deployment
        if request and request.mode == ControlMode.COMPANION:
            restore_selection(self.designs.draft, request.policy)
            self.mode_choice = 1
            self._go(Scene.WORKSHOP)
        elif self.deployment.protocols_for(ControlMode.HUMAN) is not None:
            self.mode_choice = 0
            self._go(Scene.MODE)
        else:
            self._start_run(request)

    def resize(self, view_size: tuple[int, int]) -> None:
        self.view_size = view_size
        self.backdrop = load_backdrop(view_size)
        self.extraction_backdrop = load_backdrop(view_size, "assets/scenes/extraction-dawn.png")
        self.dragging_slider = None
        self.preferences.dragging = None
        self.preferences.capturing = None
        if self.session is not None:
            self.session.resize(view_size)

    def _go(self, scene: Scene) -> None:
        self.airlock.skip()
        self.scene, self.selected, self.notice = scene, 2 if scene == Scene.MODE else 0, ""
        self.hovered_result = None
        self.dragging_slider = None
        self.designs.selected = 0
        self.designs.notice = ""
        self.designs.reset_confirmation = False
        self.inspector.open = self.profiles.open = self.seed_dialog.open = False
        if scene == Scene.SETTINGS:
            self.preferences.reset_page()
        if scene in (Scene.WORKSHOP, Scene.MODE):
            self.deployment.refresh()

    def frame(self, events: Sequence[pygame.event.Event], elapsed_ms: int) -> None:
        events = interface_events(events, self.view_size)
        self.ui_feedback.feed(events, self.scene.value, self._feedback_rects())
        self.ambient_ms += max(0, elapsed_ms)
        if self.airlock.active:
            intent = any(
                event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.WINDOWFOCUSLOST)
                for event in events
            )
            if any(event.type == pygame.QUIT for event in events):
                self.running = False
                return
            if intent:
                self.airlock.skip()
            elif self.airlock.kind == "ENTRY":
                # No hidden guard/capture/timer advances while the entrance is
                # obscured. A deliberate input skips straight into normal play.
                self.airlock.advance(elapsed_ms)
                return
            else:
                self.airlock.advance(elapsed_ms)
        if any(event.type == pygame.QUIT for event in events):
            self.running = False
            return
        if self.seed_dialog.open:
            chosen = self.seed_dialog.handle(list(events))
            if chosen is not None:
                self.seed = chosen
                if self.scene == Scene.RESULTS and self.last_deployment:
                    self.last_deployment = replace(self.last_deployment, seed=chosen)
                    self._retry_run()
            return
        if self.inspector.open:
            self.inspector.handle(list(events))
            return
        if self.profiles.open:
            policy = self.profiles.handle(list(events), selection(self.designs.draft))
            if policy is not None:
                restore_selection(self.designs.draft, policy)
            return
        if self.scene in (Scene.MODE, Scene.WORKSHOP):
            for event in events:
                if (event.type == pygame.KEYDOWN and event.key == pygame.K_n) or (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and SEED_BUTTON.collidepoint(event.pos)
                ):
                    self.seed_dialog.show(self.seed)
                    return
                if self.scene == Scene.WORKSHOP and (
                    (event.type == pygame.KEYDOWN and event.key == pygame.K_p)
                    or (
                        event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                        and PROFILE_BUTTON.collidepoint(event.pos)
                    )
                ):
                    self.profiles.show()
                    return
        if self.scene in (Scene.WORKSHOP, Scene.LAB, Scene.GUIDE, Scene.EPILOGUE):
            if any(event.type == pygame.QUIT for event in events):
                self.running = False
                return
            target = self.designs.handle(self.scene.value, list(events))
            if target == "DEPLOY":
                self._start_run(
                    DeploymentRequest(
                        ControlMode.COMPANION,
                        self.seed,
                        self.level.static_map.map_id,
                        selection(self.designs.draft),
                    )
                )
            elif target is not None:
                self._go(Scene(target))
            return
        if self.scene == Scene.SETTINGS:
            self._settings_events(events)
            return
        if self.scene == Scene.HEIST and self.session is not None:
            self.session.reduced_flashing = self.settings.reduced_flashing
            bindings = bindings_for(self.preferences.preferences)
            if self.session.input.bindings != bindings:
                self.session.input.clear()
                self.session.input.bindings = bindings
            self.session.subtitles = self.preferences.preferences.subtitles
            self.session.high_contrast = self.preferences.preferences.high_contrast
            request = self.session.handle(events)
            if request == HeistRequest.QUIT:
                self.running = False
                return
            if request == HeistRequest.RETRY:
                self._retry_run()
                return
            if request == HeistRequest.SETTINGS:
                self.settings_return = Scene.HEIST
                self._go(Scene.SETTINGS)
                return
            self.session.update(elapsed_ms)
            end = self.session.mission_end
            if end is not None:
                result_request = ResultRequest(
                    f"{self.app_nonce}:{self.runs_started}",
                    self.level.static_map.map_id,
                    self.last_deployment.seed if self.last_deployment else self.seed,
                    self.session.control_mode,
                    end,
                    self.rules.simulation_hz,
                    ToolUsage(
                        self.session.tool_counts["ECHO"],
                        self.session.tool_counts["EMP"],
                        self.session.tool_counts["MELEE"],
                    ),
                )
                self.reports.capture(result_request, self.session.terminal_result)
                self.outcomes[end.outcome.value] += 1
                self.scene = Scene.RESULTS
                self.hovered_result = None
                if end.outcome == RunOutcome.WIN:
                    self.airlock.start("EXIT")
            return
        if any(event.type == pygame.QUIT for event in events):
            self.running = False
            return
        for event in events:
            initial_scene = self.scene
            if event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
                self._key(event.key)
                if (
                    not self.running
                    or self.scene == Scene.HEIST
                    or self.seed_dialog.open
                    or self.inspector.open
                ):
                    return
            elif event.type == pygame.MOUSEMOTION and self.scene in (Scene.TITLE, Scene.MODE):
                hovered = menu_hit(self.scene.value, event.pos)
                if hovered is not None:
                    self.selected = hovered
            elif event.type == pygame.MOUSEMOTION and self.scene == Scene.RESULTS:
                self.hovered_result = (
                    "DETAILS"
                    if RESULT_DETAILS.collidepoint(event.pos)
                    else "NEW_SEED"
                    if RESULT_NEW_SEED.collidepoint(event.pos)
                    else "STORY"
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
                    if RESULT_DETAILS.collidepoint(event.pos):
                        self.inspector.show()
                        return
                    if RESULT_NEW_SEED.collidepoint(event.pos):
                        self.seed_dialog.show((self.seed + 1) % 2**31)
                        return
                    if (
                        RESULT_STORY.collidepoint(event.pos)
                        and self.session
                        and self.session.mission_end
                        and self.session.mission_end.outcome == RunOutcome.WIN
                    ):
                        self._go(Scene.EPILOGUE)
                    elif RESULT_RETRY.collidepoint(event.pos):
                        self._retry_run()
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
                    elif self.reports.gateway is not None:
                        self.inspector.show(saved=True)
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
                    if self.mode_choice == 1:
                        self._go(Scene.WORKSHOP)
                    else:
                        self._start_run()
                elif self.selected == 1:
                    if self.deployment.can_deploy:
                        self.mode_choice = 1
                    self._go(Scene.WORKSHOP)
                elif MODE_ITEMS[self.selected].enabled:
                    self.mode_choice = self.selected
                    self.selected, self.notice = 2, ""
                else:
                    self.notice = "Companion deployment unavailable. Check the Workshop notice."
        elif self.scene == Scene.RESULTS:
            if key == pygame.K_d:
                self.inspector.show()
            elif key == pygame.K_n:
                self.seed_dialog.show((self.seed + 1) % 2**31)
            elif key == pygame.K_r:
                self._retry_run()
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
        if any(event.type == pygame.QUIT for event in events):
            self.running = False
            return
        self.preferences.selected = self.selected
        self.settings, close = self.preferences.handle(list(events), self.settings)
        self.selected = self.preferences.selected
        self.dragging_slider = self.preferences.dragging
        if close:
            self._go(self.settings_return)

    def draw(self, canvas: pygame.Surface) -> None:
        if self.scene == Scene.HEIST and self.session is not None:
            self.session.draw(canvas)
            self.airlock.draw(canvas, reduced_motion=self.settings.reduced_flashing)
            return
        if self.airlock.showing_mission and self.session is not None:
            self.session.draw(canvas)
            self.airlock.draw(canvas, reduced_motion=self.settings.reduced_flashing)
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
                control_hints=(
                    key_label(bindings_for(self.preferences.preferences), "interact"),
                    movement_hint(bindings_for(self.preferences.preferences)),
                    "  ".join(
                        f"{key_label(bindings_for(self.preferences.preferences), a)} {name}"
                        for a, name in (("echo", "Echo"), ("emp", "EMP"), ("melee", "Stun"))
                    ),
                ),
                report_available=end is not None or self.reports.gateway is not None,
                companion_available=self.deployment.can_deploy,
                protocols=self.deployment.protocols_for(
                    ControlMode.COMPANION if self.mode_choice else ControlMode.HUMAN
                ),
                paint_background=False,
            )
        elif self.scene == Scene.SETTINGS:
            self.preferences.draw(
                content, self.fonts, self.backdrop, self.settings, self.ambient_ms
            )
        elif self.scene == Scene.RESULTS and end is not None:
            draw_results(
                content,
                end,
                self.fonts,
                ticks_per_second=self.rules.simulation_hz,
                hovered=self.hovered_result,
                clock_ms=self.ambient_ms,
                autonomous=self.session.autonomous if self.session else False,
                request=self.reports.request,
                report=self.reports.report,
            )
        if self.scene in (Scene.MODE, Scene.WORKSHOP):
            from echo_heist.ui.scenes.navigation.controls import button

            button(content, SEED_BUTTON, f"N  SEED {self.seed}", self.fonts)
            if self.scene == Scene.WORKSHOP:
                button(content, PROFILE_BUTTON, "P  SAVED POLICIES", self.fonts)
        if self.inspector.open:
            self.inspector.draw(content, self.fonts)
        if self.profiles.open:
            self.profiles.draw(content, self.fonts)
        if self.seed_dialog.open:
            self.seed_dialog.draw(content, self.fonts)
        self.airlock.draw(canvas, reduced_motion=self.settings.reduced_flashing)

    def audio_frame(self) -> AudioFrame:
        events = tuple(self.session.audio_events) if self.session is not None else ()
        if self.session is not None:
            self.session.audio_events.clear()
        snapshot = self.session.simulation.presentation_snapshot() if self.session else None
        observation = (
            self.session.simulation.observe(self.session.observer_id) if self.session else None
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
            environment_cues=self.session.interactions.take_audio() if self.session else (),
            heard_events=observation.heard_events if observation else (),
            listener_position=observation.own_status.position if observation else None,
            tick=snapshot.tick if snapshot else 0,
            hz=self.session.rules.simulation_hz if self.session else 30,
            listener_id=self.session.observer_id if self.session else self.level.operative_id,
            nexus_serial=self.session.announcement_serial if self.session else 0,
            ui_feedback_serial=self.ui_feedback.serial,
            ui_feedback_cue=self.ui_feedback.cue,
            explicit_ui_feedback=True,
            transition_serial=self.airlock.serial,
            transition_cue=self.airlock.cue,
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
