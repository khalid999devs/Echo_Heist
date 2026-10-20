"""One heist run: feeds HumanInput into Simulation at fixed ticks and draws the result."""

from collections.abc import Sequence
from enum import StrEnum

import pygame

from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.results import MissionEnd
from echo_heist.core.simulation.engine import Simulation
from echo_heist.level.model import LevelData
from echo_heist.ui.input.human import HumanInput, UiCommand
from echo_heist.ui.presenters.objective import build_objective_view
from echo_heist.ui.render import theme
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.hud import draw_dialog, draw_hud
from echo_heist.ui.render.theme import Fonts
from echo_heist.ui.render.world import build_map_surface, draw_world, to_pixels

MAX_CATCH_UP = 8_000  # At most eight 30 Hz ticks after a long frame.
ROUTE_SUMMARY = (
    ("Entry -> Service Wing -> Security Control (upper)", theme.TEXT),
    ("or Research Floor (lower); a cross-link joins both", theme.TEXT),
    ("Hold E at the gold Core, then return to the green Exit", theme.ACCENT),
    ("Press Tab to close", theme.MUTED),
)


class HeistRequest(StrEnum):
    QUIT = "QUIT"
    RETRY = "RETRY"


class HeistSession:
    def __init__(
        self,
        level: LevelData,
        rules: GameRules,
        *,
        seed: int,
        fonts: Fonts,
        view_size: tuple[int, int],
        map_surface: pygame.Surface | None = None,
    ) -> None:
        self.level, self.seed, self.fonts = level, seed, fonts
        self.simulation = Simulation(
            level.static_map, level.spawns(), rules=rules, mission=level.mission(), seed=seed
        )
        self.input = HumanInput(level.operative_id)
        self.map_surface = map_surface or build_map_surface(level, fonts)
        self.camera = Camera(*view_size, *self.map_surface.get_size())
        self.paused = self.summary = self.lab_note = self.confirm_abort = False
        self.accumulator = 0
        self.clock_ms = 0
        self.steps = 0
        self._follow(0.0, snap=True)

    @property
    def mission_end(self) -> MissionEnd | None:
        return self.simulation.presentation_snapshot().mission_end

    def _follow(self, seconds: float, *, snap: bool = False) -> None:
        snapshot = self.simulation.presentation_snapshot()
        actor = next(a for a in snapshot.actors if a.actor_id == self.level.operative_id)
        if actor.position is not None:
            size = self.level.static_map.tile_size_px
            self.camera.follow(to_pixels(actor.position, size), seconds, snap=snap)

    def pause(self) -> None:
        self.paused, self.confirm_abort, self.accumulator = True, False, 0
        self.input.clear()

    def handle(self, events: Sequence[pygame.event.Event]) -> HeistRequest | None:
        if self.mission_end is not None:
            return None
        if self.paused:
            return self._handle_paused(events)
        commands = self.input.feed(events)
        if UiCommand.QUIT in commands:
            return HeistRequest.QUIT
        if UiCommand.PAUSE in commands or UiCommand.FOCUS_LOST in commands:
            self.pause()
        if UiCommand.OBJECTIVE in commands:
            self.summary = not self.summary
        if UiCommand.LAB in commands:
            self.lab_note = not self.lab_note
        return None

    def _handle_paused(self, events: Sequence[pygame.event.Event]) -> HeistRequest | None:
        for event in events:
            if event.type == pygame.QUIT:
                return HeistRequest.QUIT
            if event.type != pygame.KEYDOWN or getattr(event, "repeat", False):
                continue
            if self.confirm_abort:
                if event.key == pygame.K_x:
                    # Voluntary abort is recorded by Simulation, not decided by the UI.
                    self.simulation.step(abort=True)
                    self.paused = self.confirm_abort = False
                elif event.key == pygame.K_ESCAPE:
                    self.confirm_abort = False
            elif event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.paused = False
                self.input.clear()  # Players repress held movement after resuming.
            elif event.key == pygame.K_x:
                self.confirm_abort = True
            elif event.key == pygame.K_r:
                return HeistRequest.RETRY
        return None

    def update(self, elapsed_ms: int) -> None:
        self.clock_ms += elapsed_ms
        if self.paused or self.mission_end is not None:
            self.accumulator = 0
        else:
            hz = self.simulation.ticks_per_second
            self.accumulator = min(self.accumulator + elapsed_ms * hz, MAX_CATCH_UP)
            while self.accumulator >= 1000:
                observation = self.simulation.observe(self.level.operative_id)
                result = self.simulation.step((self.input.action_for(observation),))
                self.accumulator -= 1000
                self.steps += 1
                if result.mission_end is not None:
                    self.accumulator = 0
                    break
        self._follow(elapsed_ms / 1000)

    def zone_label(self) -> str:
        observation = self.simulation.observe(self.level.operative_id)
        zone = self.level.zone_at(observation.own_status.tile)
        return zone.label if zone is not None else "Corridor"

    def draw(self, canvas: pygame.Surface) -> None:
        snapshot = self.simulation.presentation_snapshot()
        pulse = abs((self.clock_ms % 1000) - 500) / 500
        draw_world(canvas, self.level, self.map_surface, snapshot, self.camera, self.fonts, pulse)
        view = build_objective_view(
            self.simulation.observe(self.level.operative_id),
            ticks_per_second=self.simulation.ticks_per_second,
        )
        operative_tile = self.simulation.observe(self.level.operative_id).own_status.tile
        if snapshot.mission_end is None:
            draw_hud(
                canvas,
                view,
                self.zone_label(),
                self.fonts,
                level=self.level,
                operative_tile=operative_tile,
                phase=snapshot.phase,
            )
        if self.lab_note:
            note = "Algorithm Lab View arrives with P03 telemetry (F3 to close)"
            canvas.blit(self.fonts.small.render(note, True, theme.WARNING), (24, 160))
        if self.paused:
            self._draw_pause(canvas)
        elif self.summary:
            draw_dialog(canvas, "Mission route", ROUTE_SUMMARY, self.fonts)

    def _draw_pause(self, canvas: pygame.Surface) -> None:
        if self.confirm_abort:
            lines = (
                ("Abort records an unsuccessful run.", theme.TEXT),
                ("X: confirm abort    Esc: keep playing", theme.WARNING),
            )
            draw_dialog(canvas, "Abort this run?", lines, self.fonts, title_color=theme.DANGER)
            return
        menu = (
            ("Simulation time is frozen", theme.MUTED),
            ("Esc / Enter: resume", theme.TEXT),
            ("R: restart with the same seed", theme.TEXT),
            ("X: abort run", theme.TEXT),
            ("Map " + self.level.static_map.map_id + f"  |  seed {self.seed}", theme.MUTED),
        )
        draw_dialog(canvas, "PAUSED", menu, self.fonts, title_color=theme.WARNING)
