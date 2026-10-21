"""Feed pygame events per frame; request one action per fixed simulation tick."""

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, fields
from enum import StrEnum

import pygame

from echo_heist.core.contracts.actions import Action, ActionKind
from echo_heist.core.contracts.observations import Observation


class UiCommand(StrEnum):
    PAUSE = "PAUSE"
    FOCUS_LOST = "FOCUS_LOST"
    OBJECTIVE = "OBJECTIVE"
    LAB = "LAB"
    QUIT = "QUIT"


@dataclass(frozen=True, slots=True)
class KeyBindings:
    up: tuple[int, ...] = (pygame.K_w, pygame.K_UP)
    down: tuple[int, ...] = (pygame.K_s, pygame.K_DOWN)
    left: tuple[int, ...] = (pygame.K_a, pygame.K_LEFT)
    right: tuple[int, ...] = (pygame.K_d, pygame.K_RIGHT)
    sprint: tuple[int, ...] = (pygame.K_LSHIFT, pygame.K_RSHIFT)
    interact: tuple[int, ...] = (pygame.K_e,)
    echo: tuple[int, ...] = (pygame.K_q,)
    emp: tuple[int, ...] = (pygame.K_f,)
    melee: tuple[int, ...] = (pygame.K_SPACE,)
    crouch: tuple[int, ...] = (pygame.K_c,)
    pause: tuple[int, ...] = (pygame.K_ESCAPE,)
    objective: tuple[int, ...] = (pygame.K_TAB,)
    lab: tuple[int, ...] = (pygame.K_F3,)

    def __post_init__(self) -> None:
        seen: set[int] = set()
        for field in fields(self):
            keys = tuple(getattr(self, field.name))
            if not keys or any(type(key) is not int for key in keys):
                raise ValueError("Bindings need nonempty integer key tuples")
            if seen.intersection(keys) or len(set(keys)) != len(keys):
                raise ValueError("A key may bind to only one command")
            seen.update(keys)
            object.__setattr__(self, field.name, keys)


class HumanInput:
    def __init__(self, actor_id: str, bindings: KeyBindings | None = None) -> None:
        self.actor_id = actor_id
        self.bindings = bindings or KeyBindings()
        self._held: set[int] = set()
        self._tools: deque[ActionKind] = deque()
        self._last_action: Action | None = None
        self._interact_armed = False

    def clear(self) -> None:
        """Call on pause, scene switch, restart or focus loss."""
        self._held.clear()
        self._tools.clear()
        self._last_action = None
        self._interact_armed = False

    def feed(self, events: Iterable[pygame.event.Event]) -> tuple[UiCommand, ...]:
        commands: list[UiCommand] = []
        for event in events:
            if event.type == pygame.WINDOWFOCUSLOST:
                self.clear()
                commands.append(UiCommand.FOCUS_LOST)
            elif event.type == pygame.QUIT:
                self.clear()
                commands.append(UiCommand.QUIT)
            elif event.type == pygame.KEYUP:
                self._held.discard(event.key)
            elif event.type == pygame.KEYDOWN:
                fresh = event.key not in self._held and not getattr(event, "repeat", False)
                self._held.add(event.key)
                if not fresh:
                    continue
                if event.key in self.bindings.interact:
                    self._interact_armed = True
                for name, kind in (
                    ("echo", ActionKind.ECHO),
                    ("emp", ActionKind.EMP),
                    ("melee", ActionKind.MELEE),
                    ("crouch", ActionKind.CROUCH),
                ):
                    if event.key in getattr(self.bindings, name) and len(self._tools) < 8:
                        self._tools.append(kind)
                for name, command in (
                    ("pause", UiCommand.PAUSE),
                    ("objective", UiCommand.OBJECTIVE),
                    ("lab", UiCommand.LAB),
                ):
                    if event.key in getattr(self.bindings, name):
                        commands.append(command)
                        if command == UiCommand.PAUSE:
                            self.clear()
        return tuple(commands)

    def action_for(self, observation: Observation) -> Action:
        if observation.agent_id != self.actor_id:
            raise ValueError("Human adapter requires its actor's own observation")
        if self._last_action is not None and self._last_action.tick_issued == observation.tick:
            return self._last_action

        def held(keys: tuple[int, ...]) -> bool:
            return bool(self._held.intersection(keys))

        direction = (
            int(held(self.bindings.right)) - int(held(self.bindings.left)),
            int(held(self.bindings.down)) - int(held(self.bindings.up)),
        )
        kind, target, sprint = ActionKind.WAIT, None, False
        if self._tools:
            kind = self._tools.popleft()
        elif direction != (0, 0):
            kind, sprint = ActionKind.MOVE, held(self.bindings.sprint)
        elif held(self.bindings.interact) and not observation.own_status.stair_ticks_remaining:
            hint = observation.interactions[0] if observation.interactions else None
            if hint is None or hint.kind != "Stair" or self._interact_armed:
                kind = ActionKind.INTERACT
                target = hint.target_id if hint else None
            self._interact_armed = False
        self._last_action = Action(
            self.actor_id,
            kind,
            observation.tick,
            direction if kind == ActionKind.MOVE else (0, 0),
            target_id=target,
            sprint=sprint,
        )
        return self._last_action
