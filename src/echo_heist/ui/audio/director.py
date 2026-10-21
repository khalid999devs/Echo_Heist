"""Context music, bounded event cues, pause ducking and independent mix controls."""

from collections import deque
from io import BytesIO

import pygame

from echo_heist.core.contracts.events import EventKind, GameEvent
from echo_heist.core.contracts.results import RunOutcome
from echo_heist.core.contracts.world import MissionPhase
from echo_heist.infrastructure.resources import resource_bytes
from echo_heist.ui.audio.model import AudioFrame

MUSIC = ("title", "sector", "pulse", "urgent", "transmission")
MUSIC_GAINS = {"title": 0.44, "sector": 0.30, "pulse": 0.38, "urgent": 0.42, "transmission": 0.32}
CUES = {
    "hover": "ui/hover.ogg",
    "confirm": "ui/confirm.ogg",
    "victory": "ui/victory.ogg",
    "echo": "tools/echo.ogg",
    "emp": "tools/emp.ogg",
    "melee": "tools/melee.ogg",
    "alert": "signals/alert.ogg",
    "alarm": "signals/alarm.ogg",
    "step-0": "world/step-0.ogg",
    "step-1": "world/step-1.ogg",
    "step-2": "world/step-2.ogg",
}


def music_for(frame: AudioFrame) -> str:
    if frame.scene in ("TITLE", "MODE", "SETTINGS"):
        return "title"
    if frame.scene == "RESULTS":
        return "transmission"
    if frame.phase == MissionPhase.LOCKDOWN:
        return "urgent"
    return "pulse" if frame.alerted else "sector"


def event_cue(event: GameEvent) -> tuple[str, float, bool] | None:
    details = dict(event.details)
    if event.kind == EventKind.NOISE_CREATED and details.get("kind") in ("FOOTSTEP", "SPRINT"):
        return f"step-{event.tick % 3}", 0.46 if details["kind"] == "SPRINT" else 0.28, False
    if event.kind == EventKind.TOOL_USED:
        cue = str(details.get("tool", "")).lower()
        return (cue, 0.65, False) if cue in ("echo", "emp", "melee") else None
    if event.kind == EventKind.LOCKDOWN_STARTED:
        return "alarm", 0.64, True
    if event.kind in (EventKind.SIGHTING_CONFIRMED, EventKind.CAPTURE_STARTED):
        return "alert", 0.48, True
    if event.kind == EventKind.MISSION_ENDED and details.get("outcome") == RunOutcome.WIN:
        return "victory", 0.65, True
    return None


class AudioDirector:
    def __init__(
        self, *, enabled: bool, music_volume: float = 0.5, sfx_volume: float = 0.7
    ) -> None:
        self.enabled = enabled and pygame.mixer.get_init() is not None
        self.music_volume, self.sfx_volume = music_volume, sfx_volume
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.music_data: dict[str, bytes] = {}
        if self.enabled:
            pygame.mixer.set_num_channels(10)
            self.sounds = {
                name: pygame.mixer.Sound(file=BytesIO(resource_bytes(f"assets/audio/{path}")))
                for name, path in CUES.items()
            }
            self.music_data = {
                name: resource_bytes(f"assets/audio/music/{name}.ogg") for name in MUSIC
            }
        self.current_music: str | None = None
        self.target_music: str | None = None
        self.change_in_ms = 0
        self.stream: BytesIO | None = None
        self.last_frame: AudioFrame | None = None
        self.seen: set[str] = set()
        self.seen_order: deque[str] = deque()
        self.channel_gains: dict[int, float] = {}
        self.cues_played = 0
        self.footstep_index = 0

    def volumes(self, music: float, sfx: float) -> None:
        self.music_volume = max(0.0, min(1.0, music))
        self.sfx_volume = max(0.0, min(1.0, sfx))

    def play(self, cue: str, gain: float, *, critical: bool = False, ui: bool = False) -> None:
        if not self.enabled:
            return
        channel_id = (
            0
            if ui
            else 1
            if critical
            else next(
                (index for index in range(2, 10) if not pygame.mixer.Channel(index).get_busy()), -1
            )
        )
        if channel_id < 0:
            return
        channel = pygame.mixer.Channel(channel_id)
        self.channel_gains[channel_id] = gain
        channel.set_volume(gain * self.sfx_volume)
        channel.play(self.sounds[cue])
        self.cues_played += 1

    def update(self, frame: AudioFrame, elapsed_ms: int) -> None:
        if not self.enabled:
            self.last_frame = frame
            return
        previous = self.last_frame
        if previous is None or previous.run_id != frame.run_id:
            self.seen.clear()
            self.seen_order.clear()
            self.footstep_index = 0
        if previous is not None:
            if frame.scene != previous.scene:
                self.play("confirm", 0.36, ui=True)
            elif frame.selection != previous.selection:
                self.play("hover", 0.24, ui=True)
        for event in frame.events:
            if event.event_id in self.seen:
                continue
            if len(self.seen_order) >= 4096:
                self.seen.discard(self.seen_order.popleft())
            self.seen.add(event.event_id)
            self.seen_order.append(event.event_id)
            cue = event_cue(event)
            if cue is not None:
                name = cue[0]
                if name.startswith("step-"):
                    name = f"step-{self.footstep_index % 3}"
                    self.footstep_index += 1
                self.play(name, cue[1], critical=cue[2])
        desired = music_for(frame)
        if desired != self.target_music:
            self.target_music = desired
            self.change_in_ms = 250 if self.current_music is not None else 0
            if self.current_music is not None:
                pygame.mixer.music.fadeout(250)
        self.change_in_ms = max(0, self.change_in_ms - max(0, elapsed_ms))
        if self.current_music != self.target_music and self.change_in_ms == 0:
            self.stream = BytesIO(self.music_data[desired])
            pygame.mixer.music.load(self.stream, f"{desired}.ogg")
            pygame.mixer.music.play(loops=-1, fade_ms=700)
            self.current_music = desired
        duck = 0.3 if frame.paused else 1.0
        pygame.mixer.music.set_volume(self.music_volume * MUSIC_GAINS[desired] * duck)
        for index, gain in self.channel_gains.items():
            channel = pygame.mixer.Channel(index)
            channel.set_volume(gain * self.sfx_volume)
            if index and frame.paused:
                channel.pause()
            else:
                channel.unpause()
        self.last_frame = frame

    def report(self) -> dict[str, object]:
        return {
            "music_track": self.current_music,
            "audio_assets_loaded": len(self.sounds) + len(self.music_data),
            "audio_cues_played": self.cues_played,
        }
