"""Bounded, pause-stable presentation of committed effects and own tool feedback."""

from collections import deque
from dataclasses import dataclass

from echo_heist.core.contracts.environment.presentation import EnvironmentCue
from echo_heist.core.contracts.events import EventKind, GameEvent
from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.results import PresentationSnapshot
from echo_heist.core.contracts.world import Position

REJECTIONS = {
    "echo_empty": ("ECHO", "OUT OF CHARGES"),
    "emp_empty": ("EMP", "OUT OF CHARGES"),
    "melee_empty": ("MELEE", "NO STUN CHARGES LEFT"),
    "melee_cooldown": ("MELEE", "STUN RECOVERING / KEEP MOVING"),
    "no_reachable_guard": ("MELEE", "NO GUARD IN REACH"),
    "stair_landing_occupied": ("", "STAIRS BLOCKED / WAIT FOR THE LANDING"),
    "low_headroom": ("", "LOW CLEARANCE / CROUCH OUT FIRST"),
}


@dataclass(frozen=True, slots=True)
class Feedback:
    tool: str
    message: str
    status: str
    tick: int


@dataclass(frozen=True, slots=True)
class Effect:
    event_id: str
    tick: int
    kind: str
    position: Position
    target: Position | None = None
    radius_units: int = 0


class InteractionPresentation:
    """No rendering clock or random data can change a gameplay outcome."""

    def __init__(self, actor_id: str, hz: int, *, emp_radius_units: int) -> None:
        self.actor_id, self.hz, self.emp_radius_units = actor_id, hz, emp_radius_units
        self.effects: deque[Effect] = deque(maxlen=32)
        self.feedback: Feedback | None = None
        self.audio: deque[EnvironmentCue] = deque(maxlen=128)
        self._seen: set[str] = set()
        self._order: deque[tuple[str, int]] = deque()
        self._retired_tick = -1
        self.tick = 0

    def _accept(self, identity: str, tick: int) -> bool:
        if tick > self.tick or tick <= self._retired_tick or tick < self.tick - self.hz * 4:
            return False
        if identity in self._seen:
            return False
        if len(self._order) >= 1024:
            old_id, old_tick = self._order.popleft()
            self._seen.discard(old_id)
            self._retired_tick = max(self._retired_tick, old_tick)
        self._order.append((identity, tick))
        self._seen.add(identity)
        return True

    def observe(
        self,
        snapshot: PresentationSnapshot,
        observation: Observation,
        events: tuple[GameEvent, ...],
    ) -> None:
        if snapshot.tick < self.tick:
            raise ValueError("Use a fresh presentation instance for a new attempt")
        self.tick = snapshot.tick
        self.effects = deque(
            (effect for effect in self.effects if self.tick - effect.tick <= self.hz * 2),
            maxlen=32,
        )
        if self.feedback and self.tick - self.feedback.tick > self.hz * 2:
            self.feedback = None
        for cue in snapshot.environment.cues:
            if not self._accept("environment:" + cue.event_id, cue.tick):
                continue
            self.audio.append(cue)
            if cue.visible:
                self.effects.append(Effect(cue.event_id, cue.tick, cue.kind.value, cue.position))
        actors = {actor.actor_id: actor for actor in snapshot.actors}
        visible = {actor.actor_id for actor in observation.visible_entities} | {self.actor_id}
        for event in events:
            if event.kind not in (EventKind.TOOL_USED, EventKind.ACTION_REJECTED):
                continue
            if not self._accept("tool:" + event.event_id, event.tick):
                continue
            data = dict(event.details)
            if event.kind == EventKind.ACTION_REJECTED:
                if event.actor_id == self.actor_id and str(data.get("reason")) in REJECTIONS:
                    tool, rejection = REJECTIONS[str(data["reason"])]
                    self.feedback = Feedback(tool, rejection, "REJECTED", event.tick)
                continue
            tool = str(data.get("tool", ""))
            affected = data.get("affected", True) is not False
            if event.actor_id == self.actor_id:
                status = "USED" if affected else "RESISTED"
                message = {
                    "ECHO": "ECHO DECOY DEPLOYED",
                    "EMP": "EMP DISCHARGED",
                    "MELEE": "GUARD STUNNED" if affected else "GUARD RESISTED / CREATE DISTANCE",
                }.get(tool)
                if message:
                    self.feedback = Feedback(tool, message, status, event.tick)
            actor = actors.get(event.actor_id)
            if actor is None or actor.position is None or event.actor_id not in visible:
                continue
            target = actors.get(str(data.get("target_id", "")))
            target_position = target.position if target and target.actor_id in visible else None
            if tool in ("ECHO", "EMP", "MELEE"):
                self.effects.append(
                    Effect(
                        event.event_id,
                        event.tick,
                        "RESISTED" if tool == "MELEE" and not affected else tool,
                        actor.position,
                        target_position,
                        self.emp_radius_units if tool == "EMP" else 0,
                    )
                )

    def feedback_at(self, tick: float) -> Feedback | None:
        return (
            self.feedback if self.feedback and tick - self.feedback.tick < self.hz * 1.6 else None
        )

    def take_audio(self) -> tuple[EnvironmentCue, ...]:
        result = tuple(self.audio)
        self.audio.clear()
        return result
