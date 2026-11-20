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

from echo_heist.autonomy.gateway import NexusGateway
from echo_heist.core.contracts.autonomy.policy import PRESETS, DeploymentRequest
from echo_heist.infrastructure.resources import load_game_rules, load_sensor_rules
from echo_heist.ui.audio.director import AudioDirector
from echo_heist.ui.render.surfaces.formats import opaque_surface
from echo_heist.ui.scenes.flow import GameFlow, Scene, load_level


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


def complete_mission(flow: GameFlow, audio: AudioDirector, screen: pygame.Surface) -> dict:
    """Measure actual infiltration and lockdown, beyond the short restart workload."""
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    flow.deployment.gateway.reset_protocols()
    seed = 44
    assert flow._start_run(
        DeploymentRequest("COMPANION", seed, flow.level.static_map.map_id, PRESETS["RUSH"])
    )
    flow.airlock.skip()
    assert flow.session
    session = flow.session
    canvas = opaque_surface(flow.view_size)
    costs: dict[str, dict[str, list[float]]] = {}
    alarm_seen = False
    for _ in range(6000):
        phase = str(session.simulation.presentation_snapshot().phase)
        began = perf_counter()
        pygame.event.pump()
        flow.frame([], 17)
        audio.update(flow.audio_frame(), 17)
        updated = perf_counter()
        flow.draw(canvas)
        drawn = perf_counter()
        screen.blit(canvas, (0, 0))
        pygame.display.flip()
        presented = perf_counter()
        for name, cost in (
            ("update", updated - began),
            ("draw", drawn - updated),
            ("present", presented - drawn),
            ("total", presented - began),
        ):
            costs.setdefault(phase, {name: [] for name in ("update", "draw", "present", "total")})[
                name
            ].append(cost * 1000)
        alarm_seen |= bool(audio.report()["lockdown_alarm_active"])
        if session.mission_end:
            break
    return {
        "seed": seed,
        "outcome": str(session.mission_end.outcome) if session.mission_end else "RUNNER_CAP",
        "tick": session.simulation.tick,
        "lockdown_alarm_seen": alarm_seen,
        "phase_frame_ms": {
            phase: {
                "frames": len(samples["total"]),
                **{name: distribution(values) for name, values in samples.items()},
            }
            for phase, samples in costs.items()
        },
        "python_tracing": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/cinematic-startup/performance"))
    parser.add_argument("--teaching", action="store_true", help="Include the live F3 diagnostics")
    parser.add_argument("--mode", choices=("both", "HUMAN", "COMPANION"), default="both")
    parser.add_argument("--cycles", type=int, default=12)
    parser.add_argument("--frames-per-cycle", type=int, default=300)
    parser.add_argument("--trace-memory", action="store_true", help="Adds Python tracing overhead")
    parser.add_argument("--complete-mission", action="store_true")
    args = parser.parse_args()
    if args.cycles < 8 or args.frames_per_cycle < 60:
        parser.error("Use at least eight cycles and 60 frames per cycle")
    args.output.mkdir(parents=True, exist_ok=True)
    pygame.display.init()
    pygame.font.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1280, 720))
    level, rules = load_level(), load_game_rules()
    gateway = NexusGateway(level, rules, load_sensor_rules(), None)
    flow = GameFlow((1280, 720), level=level, rules=rules, autonomy_gateway=gateway)
    audio = AudioDirector(enabled=True)
    samples: dict[str, list[float]] = {name: [] for name in ("update", "draw", "present", "total")}
    memory: list[dict[str, float | int]] = []
    modes: dict[str, dict[str, list[float]]] = {}
    runs: list[dict[str, object]] = []
    keys = (pygame.K_d, pygame.K_s, pygame.K_a, pygame.K_w)
    for cycle in range(args.cycles):
        view = (1280, 720) if cycle % 4 < 2 else (1440, 900)
        screen = pygame.display.set_mode(view)
        flow.resize(view)
        # Exercise the actual restart factory; no positions or AI state are injected.
        mode = args.mode if args.mode != "both" else ("HUMAN" if cycle % 2 == 0 else "COMPANION")
        # Start each sample from real baseline memory. No persistence IO is timed.
        gateway.reset_protocols()
        began = perf_counter()
        assert flow._start_run(DeploymentRequest(mode, 1042, level.static_map.map_id))
        deployment_ms = (perf_counter() - began) * 1000
        flow.airlock.skip()
        assert flow.session
        if args.teaching:
            flow.frame(
                [
                    pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F3),
                    pygame.event.Event(pygame.KEYUP, key=pygame.K_F3),
                ],
                0,
            )
        canvas = opaque_surface(view)
        previous_key = None
        for frame in range(args.frames_per_cycle):
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
            if cycle >= 4:
                for name, cost in (
                    ("update", updated - began),
                    ("draw", drawn - updated),
                    ("present", presented - drawn),
                    ("total", presented - began),
                ):
                    samples[name].append(cost * 1000)
                    modes.setdefault(mode, {name: [] for name in samples})[name].append(cost * 1000)
            assert flow.scene == Scene.HEIST
        telemetry = flow.session.telemetry
        runs.append(
            {
                "cycle": cycle + 1,
                "mode": mode,
                "tick": flow.session.simulation.tick,
                "deployment_ms": round(deployment_ms, 3),
                "companion_search": telemetry.companion.simulations
                if telemetry.companion
                else None,
                "props": len(flow.session.simulation.presentation_snapshot().environment.props),
            }
        )
        gc.collect()
        # Warm both modes at both resolutions before measuring retained growth.
        if cycle == 3 and args.trace_memory:
            tracemalloc.start()
        python_bytes = tracemalloc.get_traced_memory()[0] if tracemalloc.is_tracing() else 0
        memory.append(
            {"cycle": cycle + 1, "rss_mb": rss_mb(), "python_mb": round(python_bytes / 2**20, 3)}
        )
    tail = [float(sample["rss_mb"]) for sample in memory[-6:]]
    python_delta = float(memory[-1]["python_mb"]) - float(memory[3]["python_mb"])
    report = {
        "video_driver": pygame.display.get_driver(),
        "audio_ready": pygame.mixer.get_init() is not None,
        "cycles": args.cycles,
        "frames": args.cycles * args.frames_per_cycle,
        "measured_frames_after_warmup": len(samples["total"]),
        "sizes": [[1280, 720], [1440, 900]],
        "security_enabled": True,
        "production_gateway": True,
        "python_tracing": args.trace_memory,
        "runs": runs,
        "mode_frame_ms": {
            mode: {name: distribution(values) for name, values in costs.items()}
            for mode, costs in modes.items()
        },
        "teaching_view": args.teaching,
        "frame_ms": {name: distribution(values) for name, values in samples.items()},
        "memory": memory,
        "last_six_rss_span_mb": round(max(tail) - min(tail), 2),
        "python_growth_after_warmup_mb": round(python_delta, 3) if args.trace_memory else None,
        "rss_change_from_warmup_mb": round(
            float(memory[-1]["rss_mb"]) - float(memory[3]["rss_mb"]), 2
        ),
        "bounded_in_this_run": max(tail) < float(memory[3]["rss_mb"]) + 64 and python_delta < 4,
        "scope": (
            "Native macOS uncapped CPU/presentation workload, production AI/security/props; "
            "restarts and resizes, four warmup cycles (both modes at both sizes). "
            "Optional Python tracing adds overhead. "
            "Restart cycles use seed 1042 with reset protocol memory. No actor state injection. "
            "RSS includes OS compression and compositor buffers; bounded means final six samples "
            "stay within 64 MB of warmup and Python growth below 4 MB (including telemetry). "
            "A bounded short run is not proof against every long-session memory leak."
        ),
    }
    if args.complete_mission:
        report["complete_mission"] = complete_mission(flow, audio, screen)
    (args.output / "PERFORMANCE.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    tracemalloc.stop()
    pygame.quit()
    mission = report.get("complete_mission", {})
    return 0 if report["bounded_in_this_run"] and mission.get("outcome", "WIN") == "WIN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
