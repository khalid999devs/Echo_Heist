"""Opening-only playback; existing CC0 cues, loaded before ownership transfer."""

from io import BytesIO

import pygame

from echo_heist.infrastructure.persistence.settings import Settings
from echo_heist.infrastructure.resources import resource_bytes


class OpeningAudio:
    def __init__(self, settings: Settings, *, mute: bool) -> None:
        self.state = "muted"
        self.settings = settings
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        if not mute:
            try:
                pygame.mixer.init()
                pygame.mixer.set_num_channels(12)
                for name, path in (
                    ("signal", "world/micro/discovery.ogg"),
                    ("ready", "world/micro/ready.ogg"),
                    ("bed", "ambience/ventilation.ogg"),
                ):
                    self.sounds[name] = pygame.mixer.Sound(
                        file=BytesIO(resource_bytes("assets/audio/" + path))
                    )
                self.state = "ready"
            except pygame.error:
                self.state = "unavailable; continuing silently"
        self.cues = 0

    def play(self, name: str, gain: float) -> None:
        if self.state != "ready" or self.settings.sfx_volume == 0:
            return
        channel = pygame.mixer.Channel(3 if name == "bed" else 0)
        channel.set_volume(gain * self.settings.sfx_volume)
        channel.play(self.sounds[name], loops=-1 if name == "bed" else 0, fade_ms=160)
        self.cues += 1

    def stop(self) -> None:
        if self.state == "ready":
            pygame.mixer.Channel(0).fadeout(180)
            pygame.mixer.Channel(3).fadeout(180)
