"""One heist run: feeds HumanInput into Simulation at fixed ticks and draws the result."""

from collections import deque
from collections.abc import Sequence
from enum import StrEnum

import pygame

from echo_heist.core.contracts.config.gameplay import GameRules
from echo_heist.core.contracts.events import EventKind, GameEvent
from echo_heist.core.contracts.results import MissionEnd
from echo_heist.core.contracts.security.model import GuardPatrol, SecuritySpec
from echo_heist.core.contracts.world import ActorKind
from echo_heist.core.simulation.engine import Simulation
from echo_heist.infrastructure.resources import load_sensor_rules
from echo_heist.level.model import LevelData
from echo_heist.ui.input.human import HumanInput, UiCommand
from echo_heist.ui.presenters.objective import build_objective_view
from echo_heist.ui.render import theme
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.hud import draw_dialog, draw_hud, panel
from echo_heist.ui.render.motifs import ActorMotion
from echo_heist.ui.render.theme import Fonts
from echo_heist.ui.render.world import (
    VisualPulse,
    WorldArt,
    build_map_surface,
    draw_world,
    to_pixels,
)

MAX_CATCH_UP = 8_000  # At most eight 30 Hz ticks after a long frame.
ROUTE_SUMMARY = (
    ("1  Follow the amber CORE marker on the minimap.", theme.WARNING),
    ("2  Take the upper Security or lower Research route.", theme.TEXT),
    ("3  Hold E beside the Core until the link fills.", theme.TEXT),
    ("4  Escape through the green Entry lift.", theme.ACCENT),
    ("WASD move  /  Shift sprint  /  Q Echo decoy", theme.MUTED),
    ("F EMP  /  Space melee  /  Esc pause", theme.MUTED),
    ("Tab closes this guide", theme.ACCENT),
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
        art: WorldArt | None = None,
        reduced_flashing: bool = False,
        security_enabled: bool = True,
    ) -> None:
        self.level, self.seed, self.fonts, self.rules = level, seed, fonts, rules
        candidates = tuple(post for post in level.guards if post.kind == ActorKind.SENTINEL)
        patrols: tuple[GuardPatrol, ...] = ()
        if candidates and security_enabled:
            # First milestone: activate the Sentinel nearest Entry using the
            # already-validated P02 patrol data. The shared P03 registry remains separate.
            post = min(
                candidates,
                key=lambda value: (
                    abs(value.tile[0] - level.spawn_tile[0])
                    + abs(value.tile[1] - level.spawn_tile[1]),
                    value.guard_id,
                ),
            )
            route = next(route for route in level.routes if route.route_id == post.route_id)
            points = route.points[:-1] if route.points[0] == route.points[-1] else route.points
            patrols = (GuardPatrol(post.guard_id, points),)
        security = (
            SecuritySpec(patrols, load_sensor_rules(), level.sound_blocking_tiles)
            if patrols
            else None
        )
        self.simulation = Simulation(
            level.static_map,
            level.spawns(),
            rules=rules,
            mission=level.mission(),
            seed=seed,
            security=security,
        )
        self.input = HumanInput(level.operative_id)
        self.art = art or WorldArt.load()
        self.map_surface = map_surface or build_map_surface(level, fonts, self.art)
        self.camera = Camera(*view_size, *self.map_surface.get_size())
        self.paused = self.summary = self.lab_note = self.confirm_abort = False
        self.accumulator = 0
        self.clock_ms = 0
        self.steps = 0
        self._last_positions = {
            actor.actor_id: actor.position
            for actor in self.simulation.presentation_snapshot().actors
        }
        self.actor_motion: dict[str, ActorMotion] = {}
        self.pulses: list[VisualPulse] = []
        self.audio_events: deque[GameEvent] = deque(maxlen=512)
        self.reduced_flashing = reduced_flashing
        self.notice = ""
        self.notice_until_ms = 0
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
        if not self.paused and self.mission_end is None:
            self.clock_ms += elapsed_ms
            self.pulses = [pulse for pulse in self.pulses if self.clock_ms - pulse.started_ms < 650]
        if self.paused or self.mission_end is not None:
            self.accumulator = 0
        else:
            hz = self.simulation.ticks_per_second
            self.accumulator = min(self.accumulator + elapsed_ms * hz, MAX_CATCH_UP)
            while self.accumulator >= 1000:
                observation = self.simulation.observe(self.level.operative_id)
                result = self.simulation.step((self.input.action_for(observation),))
                self._record_motion()
                self._record_events(result.events)
                self.accumulator -= 1000
                self.steps += 1
                if result.mission_end is not None:
                    self.accumulator = 0
                    break
        self._follow(elapsed_ms / 1000)

    def _record_motion(self) -> None:
        sprint_delta = (
            self.rules.walk_speed_units_per_second + self.rules.sprint_speed_units_per_second
        ) / (2 * self.simulation.ticks_per_second)
        for actor in self.simulation.presentation_snapshot().actors:
            previous, current = self._last_positions.get(actor.actor_id), actor.position
            if current is None:
                continue
            old_motion = self.actor_motion.get(actor.actor_id, ActorMotion())
            if previous is None:
                self.actor_motion[actor.actor_id] = ActorMotion(old_motion.direction)
            else:
                dx, dy = current[0] - previous[0], current[1] - previous[1]
                moving = dx != 0 or dy != 0
                direction = (
                    (1 if dx > 0 else -1 if dx < 0 else 0, 1 if dy > 0 else -1 if dy < 0 else 0)
                    if moving
                    else actor.facing
                )
                sprinting = actor.actor_id == self.level.operative_id and (
                    dx * dx + dy * dy > sprint_delta * sprint_delta
                )
                self.actor_motion[actor.actor_id] = ActorMotion(direction, moving, sprinting)
            self._last_positions[actor.actor_id] = current

    def _record_events(self, events: tuple[GameEvent, ...]) -> None:
        self.audio_events.extend(events)
        actors = {actor.actor_id: actor for actor in self.simulation.presentation_snapshot().actors}
        for event in events:
            if event.kind == EventKind.CORE_TAKEN:
                self.notice = "CORE SECURED  /  RETURN TO THE GREEN EXIT"
                self.notice_until_ms = self.clock_ms + 4200
            elif event.kind == EventKind.CAPTURE_STARTED:
                self.notice = "GUARD GRAB INCOMING  /  BREAK RANGE"
                self.notice_until_ms = self.clock_ms + 1800
            elif event.kind == EventKind.CAPTURE_CANCELED:
                self.notice = "GRAB ESCAPED"
                self.notice_until_ms = self.clock_ms + 1200
            elif event.kind == EventKind.ACTION_REJECTED:
                reason = dict(event.details).get("reason")
                self.notice = {
                    "echo_empty": "NO ECHO CHARGES LEFT",
                    "emp_empty": "NO EMP CHARGES LEFT",
                    "no_reachable_guard": "MELEE NEEDS A NEARBY GUARD",
                }.get(str(reason), self.notice)
                self.notice_until_ms = self.clock_ms + 1400
            elif event.kind == EventKind.TOOL_USED:
                tool = dict(event.details).get("tool")
                self.notice = {
                    "ECHO": "ECHO DECOY DEPLOYED",
                    "EMP": "EMP DISCHARGED",
                    "MELEE": "MELEE CONTACT",
                }.get(str(tool), "TOOL USED")
                self.notice_until_ms = self.clock_ms + 1600
                actor = actors.get(event.actor_id)
                if actor is not None and actor.position is not None and tool in ("ECHO", "EMP"):
                    self.pulses.append(VisualPulse(actor.position, str(tool), self.clock_ms))

    def zone_label(self) -> str:
        observation = self.simulation.observe(self.level.operative_id)
        zone = self.level.zone_at(observation.own_status.tile)
        return zone.label if zone is not None else "Corridor"

    def draw(self, canvas: pygame.Surface) -> None:
        snapshot = self.simulation.presentation_snapshot()
        pulse = 0.5 if self.reduced_flashing else abs((self.clock_ms % 1000) - 500) / 500
        draw_world(
            canvas,
            self.level,
            self.map_surface,
            snapshot,
            self.camera,
            self.fonts,
            pulse,
            actor_motion=self.actor_motion,
            clock_ms=self.clock_ms,
            pulses=tuple(self.pulses),
            art=self.art,
        )
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
                clock_ms=self.clock_ms,
                notice=self.notice if self.clock_ms < self.notice_until_ms else "",
                guards=snapshot.guards,
            )
        if self.lab_note:
            self._draw_lab(canvas)
        if self.paused:
            self._draw_pause(canvas)
        elif self.summary:
            draw_dialog(canvas, "Mission route", ROUTE_SUMMARY, self.fonts)

    def _draw_lab(self, canvas: pygame.Surface) -> None:
        snapshot = self.simulation.presentation_snapshot()
        panel(canvas, pygame.Rect(20, 158, 410, 200), border=theme.ACCENT_DIM)
        lines = ["AI LAB  /  F3 to close"]
        for guard in snapshot.guards:
            age = (
                "none"
                if guard.last_seen_tick < 0
                else f"{snapshot.tick - guard.last_seen_tick} ticks ago"
            )
            lines.extend(
                (
                    f"Sentinel  /  {guard.state.value}",
                    f"BFS  {guard.expanded_nodes} expanded / {len(guard.path)} path tiles",
                    f"Identification  {guard.identification_ticks}/"
                    f"{guard.identification_required_ticks}",
                    f"Last visual contact: {age}",
                    f"Fuzzy urgency  {guard.fuzzy_urgency:.2f}",
                )
            )
        if not snapshot.guards:
            lines.append("No active controller in this diagnostic fixture.")
        for index, line in enumerate(lines):
            canvas.blit(
                self.fonts.micro.render(line, True, theme.ACCENT if index == 0 else theme.TEXT),
                (34, 173 + index * 29),
            )

    def _draw_pause(self, canvas: pygame.Surface) -> None:
        if self.confirm_abort:
            lines = (
                ("Ending now marks this attempt unsuccessful.", theme.TEXT),
                ("X: confirm abort    Esc: keep playing", theme.WARNING),
            )
            draw_dialog(canvas, "Abort this run?", lines, self.fonts, title_color=theme.DANGER)
            return
        menu = (
            ("Take a breath. Mission time is paused.", theme.MUTED),
            ("Esc / Enter: resume", theme.TEXT),
            ("R: restart mission", theme.TEXT),
            ("X: abort run", theme.TEXT),
            ("Restarting keeps this facility layout.", theme.MUTED),
        )
        draw_dialog(canvas, "PAUSED", menu, self.fonts, title_color=theme.WARNING)
