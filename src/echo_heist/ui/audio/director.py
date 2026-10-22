"""Context music, bounded event cues, pause ducking and independent mix controls."""

from collections import deque
from collections.abc import Callable
from io import BytesIO

import pygame

from echo_heist.core.contracts.events import EventKind, GameEvent
from echo_heist.core.contracts.results import RunOutcome
from echo_heist.core.contracts.world import MissionPhase
from echo_heist.infrastructure.resources import resource_bytes
from echo_heist.ui.audio.model import AudioFrame

MUSIC = ("title", "sector", "pulse", "urgent", "transmission")
MUSIC_GAINS = {"title": 0.40, "sector": 0.34, "pulse": 0.38, "urgent": 0.40, "transmission": 0.34}
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
    **{f"walk-{i}": f"world/walk-{i}.wav" for i in range(3)},
    **{
        name: f"world/micro/{name}.ogg"
        for name in ("stair-start", "stair-arrive", "core", "ready", "unavailable", "discovery")
    },
    **{name: f"ui/{name}.ogg" for name in ("adjust", "back", "toggle")},
    "ventilation": "ambience/ventilation.ogg",
}


def music_for(frame: AudioFrame) -> str:
    if frame.scene in ("TITLE", "MODE", "WORKSHOP", "LAB", "GUIDE") or (
        frame.scene == "SETTINGS" and not frame.paused
    ):
        return "title"
    if frame.scene in ("RESULTS", "EPILOGUE"):
        return "transmission"
    if frame.phase == MissionPhase.LOCKDOWN:
        return "urgent"
    return "pulse" if frame.alerted else "sector"


def event_cue(event: GameEvent) -> tuple[str, float, bool] | None:
    details = dict(event.details)
    if event.kind in (EventKind.STAIR_STARTED, EventKind.STAIR_USED) and details.get(
        "actor_kind"
    ) in (
        "OPERATIVE",
        "COMPANION",
    ):
        return (
            ("stair-start" if event.kind == EventKind.STAIR_STARTED else "stair-arrive"),
            0.18,
            False,
        )
    if event.kind == EventKind.NOISE_CREATED and details.get("kind") in (
        "FOOTSTEP",
        "SPRINT",
        "CROUCH",
    ):
        sprint = details["kind"] == "SPRINT"
        gain = 0.42 if sprint else 0.045 if details["kind"] == "CROUCH" else 0.09
        return f"{'step' if sprint else 'walk'}-{event.tick % 3}", gain, False
    if event.kind == EventKind.CORE_TAKEN:
        return "core", 0.3, False
    if event.kind == EventKind.STAIR_CANCELED:
        return "back", 0.12, False
    if event.kind == EventKind.ACTION_REJECTED and details.get("reason") in (
        "echo_empty",
        "emp_empty",
        "no_reachable_guard",
        "stair_landing_occupied",
        "low_headroom",
    ):
        return "unavailable", 0.15, False
    if event.kind == EventKind.TOOL_USED:
        cue = str(details.get("tool", "")).lower()
        return (cue, 0.65, False) if cue in ("echo", "emp", "melee") else None
    if event.kind == EventKind.LOCKDOWN_STARTED:
        return "alarm", 0.42, True
    if event.kind in (EventKind.SIGHTING_CONFIRMED, EventKind.CAPTURE_STARTED):
        return "alert", 0.48, True
    if event.kind == EventKind.MISSION_ENDED and details.get("outcome") == RunOutcome.WIN:
        return "victory", 0.65, True
    return None


class AudioDirector:
    def __init__(
        self,
        *,
        enabled: bool,
        music_volume: float = 0.5,
        sfx_volume: float = 0.7,
        loading: Callable[[float], None] | None = None,
    ) -> None:
        self.enabled = enabled and pygame.mixer.get_init() is not None
        self.music_volume, self.sfx_volume = music_volume, sfx_volume
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.music_data: dict[str, bytes] = {}
        if self.enabled:
            if pygame.mixer.get_num_channels() < 12:
                pygame.mixer.set_num_channels(12)
            count = len(CUES) + len(MUSIC)
            for name, path in CUES.items():
                self.sounds[name] = pygame.mixer.Sound(
                    file=BytesIO(resource_bytes(f"assets/audio/{path}"))
                )
                if loading is not None:
                    loading(len(self.sounds) / count)
            for name in MUSIC:
                self.music_data[name] = resource_bytes(f"assets/audio/music/{name}.ogg")
                if loading is not None:
                    loading((len(self.sounds) + len(self.music_data)) / count)
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
        self.clock_ms = 0
        self.last_adjust_ms = -1000
        self.last_rejected_ms = -1000

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
                (index for index in range(4, 12) if not pygame.mixer.Channel(index).get_busy()), -1
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
        self.clock_ms += max(0, elapsed_ms)
        alarm = pygame.mixer.Channel(2)
        lockdown = frame.scene == "HEIST" and frame.phase == MissionPhase.LOCKDOWN
        if lockdown and not alarm.get_busy():
            alarm.play(self.sounds["alarm"], loops=-1, fade_ms=350)
        elif not lockdown:
            alarm.stop()
        alarm.set_volume(0.22 * self.sfx_volume)
        if frame.paused:
            alarm.pause()
        else:
            alarm.unpause()
        ambience = pygame.mixer.Channel(3)
        if frame.scene == "HEIST":
            if not ambience.get_busy():
                ambience.play(self.sounds["ventilation"], loops=-1, fade_ms=700)
            ambience.set_volume(
                (0.065 if frame.room_style in ("server", "maintenance") else 0.035)
                * self.sfx_volume
            )
            if frame.paused:
                ambience.pause()
            else:
                ambience.unpause()
        else:
            ambience.stop()
        if previous is None or previous.run_id != frame.run_id:
            self.seen.clear()
            self.seen_order.clear()
            self.footstep_index = 0
        if frame.transition_serial and (
            previous is None or frame.transition_serial != previous.transition_serial
        ):
            self.play(frame.transition_cue, 0.32)
        if previous is None and frame.ui_feedback_serial:
            self.play(
                frame.ui_feedback_cue, 0.26 if frame.ui_feedback_cue == "hover" else 0.48, ui=True
            )
        if previous is not None:
            if frame.ui_feedback_serial != previous.ui_feedback_serial:
                self.play(
                    frame.ui_feedback_cue,
                    0.26 if frame.ui_feedback_cue == "hover" else 0.48,
                    ui=True,
                )
            elif frame.scene != previous.scene or frame.paused != previous.paused:
                self.play("back" if frame.paused else "confirm", 0.22, ui=True)
            elif frame.scene == "SETTINGS" and frame.settings_values != previous.settings_values:
                if frame.settings_values[2:] != previous.settings_values[2:]:
                    self.play("toggle", 0.17, ui=True)
                elif self.clock_ms - self.last_adjust_ms >= 85:
                    self.play("adjust", 0.09, ui=True)
                    self.last_adjust_ms = self.clock_ms
            elif not frame.explicit_ui_feedback and frame.selection != previous.selection:
                self.play("hover", 0.26, ui=True)
            if frame.scene == "HEIST" and frame.suspicious and not previous.suspicious:
                self.play("discovery", 0.12)
            if (
                frame.run_id == previous.run_id
                and frame.scene == "HEIST"
                and previous.sprint_recharge_remaining > 0
                and frame.sprint_recharge_remaining == 0
            ):
                self.play("ready", 0.16)
        for event in frame.events:
            if event.event_id in self.seen:
                continue
            if len(self.seen_order) >= 4096:
                self.seen.discard(self.seen_order.popleft())
            self.seen.add(event.event_id)
            self.seen_order.append(event.event_id)
            if event.kind in (
                EventKind.NOISE_CREATED,
                EventKind.TOOL_USED,
                EventKind.STAIR_STARTED,
                EventKind.STAIR_USED,
                EventKind.STAIR_CANCELED,
                EventKind.ACTION_REJECTED,
            ) and (
                event.actor_id != frame.listener_id
                and event.event_id not in frame.audible_event_ids
            ):
                continue
            cue = event_cue(event)
            if cue is not None:
                name = cue[0]
                if name == "unavailable":
                    if self.clock_ms - self.last_rejected_ms < 400:
                        continue
                    self.last_rejected_ms = self.clock_ms
                if name.startswith(("step-", "walk-")):
                    name = f"{name.split('-')[0]}-{self.footstep_index % 3}"
                    self.footstep_index += 1
                self.play(name, cue[1], critical=cue[2])
        desired = music_for(frame)
        if desired != self.target_music:
            self.target_music = desired
            # music.fadeout blocks the calling thread until the fade completes.
            # Ramp its gain across frames instead; never sleep the gameplay loop.
            self.change_in_ms = (
                250 if self.current_music is not None and self.current_music != desired else 0
            )
        self.change_in_ms = max(0, self.change_in_ms - max(0, elapsed_ms))
        duck = 0.3 if frame.paused else 1.0
        if self.current_music != self.target_music and self.change_in_ms == 0:
            self.stream = BytesIO(self.music_data[desired])
            pygame.mixer.music.load(self.stream, f"{desired}.ogg")
            # load resets volume; set it before play to avoid a full-volume burst.
            pygame.mixer.music.set_volume(self.music_volume * MUSIC_GAINS[desired] * duck)
            pygame.mixer.music.play(loops=-1, fade_ms=700)
            self.current_music = desired
        gain = MUSIC_GAINS[self.current_music or desired]
        fade = self.change_in_ms / 250 if self.current_music != desired else 1.0
        pygame.mixer.music.set_volume(self.music_volume * gain * duck * fade)
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
            "lockdown_alarm_active": self.enabled and pygame.mixer.Channel(2).get_busy(),
            "room_ambience_active": self.enabled and pygame.mixer.Channel(3).get_busy(),
        }
