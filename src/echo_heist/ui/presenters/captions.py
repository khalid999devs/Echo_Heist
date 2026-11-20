"""Audio-independent captions from committed, listener-permitted cues only."""

from collections import deque

from echo_heist.core.contracts.environment.presentation import EnvironmentCue
from echo_heist.core.contracts.events import EventKind, GameEvent
from echo_heist.core.contracts.observations import Observation


class CaptionStream:
    def __init__(self, hz: int) -> None:
        self.hz = hz
        self.message = ""
        self.until = 0
        self.seen: set[str] = set()
        self.order: deque[str] = deque()
        self.last: dict[str, int] = {}

    def observe(
        self,
        observation: Observation,
        events: tuple[GameEvent, ...],
        cues: tuple[EnvironmentCue, ...],
    ) -> None:
        heard = {cue.event_id for cue in observation.heard_events}
        own = observation.agent_id
        candidates = []
        for event in events:
            details = dict(event.details)
            message = ""
            if event.kind == EventKind.TOOL_USED and event.actor_id == own:
                message = {
                    "ECHO": "[Echo deployed]",
                    "EMP": "[EMP burst]",
                    "MELEE": "[Metal impact]",
                }.get(str(details.get("tool")), "")
            elif (
                event.kind == EventKind.NOISE_CREATED
                and event.actor_id != own
                and event.event_id in heard
            ):
                message = (
                    "[Nearby impact]"
                    if details.get("kind") not in ("FOOTSTEP", "SPRINT", "CROUCH")
                    else "[Footsteps nearby]"
                )
            if message:
                candidates.append((event.event_id, event.tick, message))
        for cue in cues:
            if cue.actor_id == own or cue.noise_event_id in heard:
                message = {
                    "DOOR": "[Door mechanism]",
                    "GLASS": "[Glass breaks]",
                    "CANISTER_IMPACT": "[Metal impact]",
                    "HIDE_ENTER": "[Locker closes]",
                    "HIDE_LEAVE": "[Locker opens]",
                }[cue.kind.value]
                candidates.append(("environment:" + cue.event_id, cue.tick, message))
        for identity, tick, message in candidates:
            if identity in self.seen or not 0 <= observation.tick - tick <= self.hz * 2:
                continue
            if len(self.order) == 256:
                self.seen.discard(self.order.popleft())
            self.order.append(identity)
            self.seen.add(identity)
            if observation.tick - self.last.get(message, -100000) < self.hz:
                continue
            self.message, self.until = message, observation.tick + self.hz * 2
            self.last[message] = observation.tick

    def at(self, observation: Observation) -> str:
        if observation.tick < self.until:
            return self.message
        return ""
