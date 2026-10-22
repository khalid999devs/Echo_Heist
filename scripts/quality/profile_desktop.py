"""Native frame costs and resident-memory plateau across repeated mission/resize cycles."""

import argparse
import gc
import json
import os
import subprocess
import tracemalloc
from pathlib import Path
from statistics import median
from time import perf_counter

import pygame

from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.flow import GameFlow, Scene


def rss_mb() -> float:
    # tracemalloc alone misses SDL's native pixel and decoded-audio allocations.
    result = subprocess.run(
        ["ps", "-o", "rss=", "-p", str(os.getpid())],
        check=True,
        capture_output=True,
        text=True,
    )
    return round(int(result.stdout.strip()) / 1024, 2)


def distribution(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "median": round(median(values), 3),
        "p95": round(ordered[int(len(ordered) * 0.95)], 3),
        "max": round(max(values), 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/cinematic-startup/performance"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pygame.display.init()
    pygame.font.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1280, 720))
    flow = GameFlow((1280, 720))
    audio = AudioDirector(enabled=True)
    samples: dict[str, list[float]] = {name: [] for name in ("update", "draw", "present", "total")}
    memory: list[dict[str, float | int]] = []
    keys = (pygame.K_d, pygame.K_s, pygame.K_a, pygame.K_w)
    for cycle in range(12):
        view = (1280, 720) if cycle % 2 == 0 else (1440, 900)
        screen = pygame.display.set_mode(view)
        flow.resize(view)
        # Exercise the actual restart factory; no positions or AI state are injected.
        flow._start_run()
        canvas = opaque_surface(view)
        previous_key = None
        for frame in range(300):
            events = []
            key = keys[(frame // 60) % 4]
            if key != previous_key:
                if previous_key is not None:
                    events.append(pygame.event.Event(pygame.KEYUP, key=previous_key))
                events.append(pygame.event.Event(pygame.KEYDOWN, key=key))
                previous_key = key
            if frame == 10:
                events.append(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LSHIFT))
            if frame == 100:
                events.append(pygame.event.Event(pygame.KEYUP, key=pygame.K_LSHIFT))
            began = perf_counter()
            pygame.event.pump()
            flow.frame(events, 17)
            audio.update(flow.audio_frame(), 17)
            updated = perf_counter()
            flow.draw(canvas)
            drawn = perf_counter()
            screen.blit(canvas, (0, 0))
            pygame.display.flip()
            presented = perf_counter()
            if cycle >= 2:
                for name, cost in (
                    ("update", updated - began),
                    ("draw", drawn - updated),
                    ("present", presented - drawn),
                    ("total", presented - began),
                ):
                    samples[name].append(cost * 1000)
            assert flow.scene == Scene.HEIST
        gc.collect()
        if cycle == 1:
            tracemalloc.start()
        python_bytes = tracemalloc.get_traced_memory()[0] if cycle >= 1 else 0
        memory.append(
            {"cycle": cycle + 1, "rss_mb": rss_mb(), "python_mb": round(python_bytes / 2**20, 3)}
        )
    tail = [float(sample["rss_mb"]) for sample in memory[-6:]]
    python_delta = float(memory[-1]["python_mb"]) - float(memory[1]["python_mb"])
    report = {
        "video_driver": pygame.display.get_driver(),
        "audio_ready": pygame.mixer.get_init() is not None,
        "cycles": 12,
        "frames": 3600,
        "measured_frames_after_warmup": len(samples["total"]),
        "sizes": [[1280, 720], [1440, 900]],
        "security_enabled": True,
        "frame_ms": {name: distribution(values) for name, values in samples.items()},
        "memory": memory,
        "last_six_rss_span_mb": round(max(tail) - min(tail), 2),
        "python_growth_after_warmup_mb": round(python_delta, 3),
        "rss_change_from_warmup_mb": round(
            float(memory[-1]["rss_mb"]) - float(memory[1]["rss_mb"]), 2
        ),
        "bounded_in_this_run": max(tail) < float(memory[1]["rss_mb"]) + 64 and python_delta < 4,
        "scope": (
            "Native macOS uncapped CPU/presentation workload, 61.2 seconds of simulated play; "
            "12 restarts and alternating resizes, 2 warmup cycles. Python tracing adds overhead. "
            "RSS includes OS compression and compositor buffers; bounded means final six samples "
            "stay within 64 MB of warmup and Python growth below 4 MB (including telemetry). "
            "A bounded short run is not proof against every long-session memory leak."
        ),
    }
    (args.output / "PERFORMANCE.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    tracemalloc.stop()
    pygame.quit()
    return 0 if report["bounded_in_this_run"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
