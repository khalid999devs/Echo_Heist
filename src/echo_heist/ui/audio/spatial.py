"""Panning uses legitimate heard locations; cosmetic sound never changes perception."""

from math import hypot

from echo_heist.core.contracts.environment.presentation import EnvironmentCue
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE
from echo_heist.ui.audio.model import AudioFrame

CUE_NAMES = {
    "DOOR": "door",
    "GLASS": "glass",
    "CANISTER_IMPACT": "canister",
    "HIDE_ENTER": "locker",
    "HIDE_LEAVE": "locker",
}


def environment_sound(cue: EnvironmentCue, frame: AudioFrame) -> tuple[str, float, float] | None:
    if frame.scene != "HEIST" or not 0 <= frame.tick - cue.tick <= frame.hz * 4:
        return None
    if cue.actor_id == frame.listener_id:
        source = tuple(axis / POSITION_UNITS_PER_TILE for axis in cue.position)
    else:
        heard = next(
            (item for item in frame.heard_events if item.event_id == cue.noise_event_id), None
        )
        if heard is None:
            return None
        # Never pan from a hidden source's exact snapshot coordinates.
        source = (heard.tile[0] + 0.5, heard.tile[1] + 0.5)
    if frame.listener_position is None:
        return CUE_NAMES[cue.kind.value], 0.25, 0.0
    x, y = (axis / POSITION_UNITS_PER_TILE for axis in frame.listener_position)
    distance = hypot(source[0] - x, source[1] - y)
    return (
        CUE_NAMES[cue.kind.value],
        0.32 / (1 + distance * 0.18),
        max(-0.85, min(0.85, (source[0] - x) / 6)),
    )


def stereo(gain: float, pan: float) -> tuple[float, float]:
    """Center preserves the existing mono gain; no side ever receives extra gain."""
    return gain * (1 - max(0, pan)), gain * (1 + min(0, pan))
