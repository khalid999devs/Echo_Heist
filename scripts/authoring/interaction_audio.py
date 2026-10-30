"""Reproduce four original, quiet mono interaction cues without external samples."""

import json
import math
import random
import struct
import wave
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIO = ROOT / "src/echo_heist/resources/assets/audio"
RATE = 44100


def render(name: str, duration: float) -> bytes:
    rng = random.Random(name)
    samples = []
    low = 0.0
    for i in range(round(duration * RATE)):
        t = i / RATE
        low += 0.12 * (rng.uniform(-1, 1) - low)
        if name == "door":
            envelope = min(1, t / 0.06) * min(1, (duration - t) / 0.12)
            tone = 0.19 * math.sin(math.tau * (105 * t + 12 * t * t)) + low * 0.22
            tone += 0.2 * math.exp(-abs(t - 0.5) * 90) * math.sin(math.tau * 510 * t)
        elif name == "glass":
            envelope = min(1, t / 0.004) * math.exp(-t * 6)
            tone = sum(math.sin(math.tau * f * t) for f in (1753, 2309, 3413, 4691)) * 0.11
            tone += rng.uniform(-1, 1) * math.exp(-t * 25) * 0.22
        elif name == "canister":
            envelope = min(1, t / 0.003) * math.exp(-t * 7)
            tone = sum(math.sin(math.tau * f * t) for f in (147, 283, 619)) * 0.16
            tone += low * math.exp(-t * 35) * 0.3
        else:
            envelope = min(1, t / 0.015) * math.exp(-t * 6)
            tone = low * 0.3 + 0.13 * math.sin(math.tau * 270 * t)
            tone += 0.17 * math.exp(-abs(t - 0.2) * 90) * math.sin(math.tau * 780 * t)
        tail = min(1, (duration - t) / 0.03)
        samples.append(round(max(-0.85, min(0.85, tone * envelope * tail)) * 32767))
    return struct.pack(f"<{len(samples)}h", *samples)


def main() -> None:
    manifest = json.loads((AUDIO / "manifest.json").read_text())
    for name, duration in (("door", 0.7), ("glass", 0.8), ("canister", 0.65), ("locker", 0.45)):
        relative = f"world/interactions/{name}.wav"
        path = AUDIO / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as sound:
            sound.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
            sound.writeframes(render(name, duration))
        manifest["assets"] = [item for item in manifest["assets"] if item["path"] != relative]
        manifest["assets"].append(
            {
                "path": relative,
                "author": "ECHO HEIST project",
                "license": "MIT",
                "source": "scripts/authoring/interaction_audio.py",
                "created": "2026-10-25",
                "sha256": sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
                "modified": False,
                "notes": "Original procedural synthesis; no external samples.",
            }
        )
    (AUDIO / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
