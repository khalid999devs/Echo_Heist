"""NEXUS: event-driven coarse task utility over legitimately reported evidence.

NEXUS is not a physical guard. Its view is what its own guards sensed (heard
cues, unidentified motion, radio sightings), the public Core alarm and the
status of its own robots. It scores a few coarse tasks (protect exit 100,
intercept 90, support a fresh confirmed pursuit 80, strong unexplained noise
45), assigns them in stable priority order to eligible nearby guards, caps
dispatch counts and keeps routine sector coverage. Orders are radio reports a
guard walks to; nothing is teleported and no unseen position is invented.
"""

from dataclasses import dataclass, replace

from echo_heist.ai.navigation.grid import distances_from
from echo_heist.core.contracts.events import HeardCue, SecurityReport
from echo_heist.core.contracts.security.director import (
    NEXUS_ID,
    TASK_PRIORITY,
    DirectorRules,
    Dispatch,
    NexusEvidence,
    NexusMemory,
    RouteGraph,
    TaskKind,
)
from echo_heist.core.contracts.security.model import GuardRole, GuardState, VisualCue
from echo_heist.core.contracts.world import MissionPhase, StaticMap, Tile

STRONG_NOISE = frozenset({"SPRINT", "EMP", "MELEE", "GLASS", "METAL"})
ROUTINE = frozenset({GuardState.PATROL, GuardState.RETURN})
HANDLED_LIMIT = 64
LOCKDOWN_ANNOUNCEMENT = "GLOBAL LOCKDOWN / EXIT ROUTES UNDER INTERCEPT"


@dataclass(frozen=True, slots=True)
class GuardStatus:
    guard_id: str
    role: GuardRole
    tile: Tile
    available: bool
    state: GuardState


@dataclass(frozen=True, slots=True)
class DirectorView:
    """NEXUS's permitted observation: guard-sensed evidence and its own robots."""

    tick: int
    phase: MissionPhase
    world_map: StaticMap
    guards: tuple[GuardStatus, ...]
    reports: tuple[SecurityReport, ...]
    heard: tuple[HeardCue, ...]
    motion: tuple[VisualCue, ...]


@dataclass(frozen=True, slots=True)
class _Task:
    kind: TaskKind
    target: Tile
    evidence_id: str
    evidence_tick: int


def _count_contact(evidence: NexusEvidence, zone: str) -> NexusEvidence:
    counts = dict(evidence.contacts)
    counts[zone] = counts.get(zone, 0) + 1
    return replace(evidence, contacts=tuple(counts.items()))


def _exit_post(graph: RouteGraph) -> Tile:
    """Chokepoint protecting the extraction zone (nearest to the exit anchor)."""
    exit_zone = graph.zone_of(graph.exit_tile)
    nodes = [node for node in graph.nodes if exit_zone in node.zones] or list(graph.nodes)
    return min(
        nodes, key=lambda node: (graph.distance(node.node_id, "EXIT") or 10**6, node.node_id)
    ).tile


def _tasks(view: DirectorView, memory: NexusMemory, graph: RouteGraph) -> list[_Task]:
    tasks: list[_Task] = []
    handled = set(memory.handled)
    if view.phase == MissionPhase.LOCKDOWN and not memory.lockdown_handled:
        # The Core alarm is public and names the Core, never the intruder's later path.
        tasks.append(_Task(TaskKind.INTERCEPT, graph.core_tile, "alarm:core", view.tick))
        tasks.append(_Task(TaskKind.PROTECT_EXIT, _exit_post(graph), "alarm:exit", view.tick))
    sightings = [
        report
        for report in view.reports
        if report.report_kind == "SIGHTING"
        and view.tick <= report.expires_at_tick
        and report.event_id not in handled
    ]
    if sightings:
        newest = max(sightings, key=lambda report: (report.tick, report.event_id))
        tasks.append(_Task(TaskKind.SUPPORT_PURSUIT, newest.tile, newest.event_id, newest.tick))
    noises = [cue for cue in view.heard if cue.kind in STRONG_NOISE and cue.event_id not in handled]
    if noises:
        loudest = max(noises, key=lambda cue: (cue.tick, cue.event_id))
        tasks.append(
            _Task(TaskKind.INVESTIGATE_NOISE, loudest.tile, loudest.event_id, loudest.tick)
        )
    tasks.sort(key=lambda task: (-TASK_PRIORITY[task.kind], -task.evidence_tick, task.evidence_id))
    return tasks


def decide(
    view: DirectorView, rules: DirectorRules, graph: RouteGraph, memory: NexusMemory
) -> NexusMemory:
    rules = rules.effective()
    tick = view.tick
    live = [order for order in memory.dispatches if tick <= order.expires_at_tick]
    evidence = memory.evidence
    fresh = [
        report
        for report in view.reports
        if report.report_kind == "SIGHTING" and tick <= report.expires_at_tick
    ]
    if fresh and not memory.contact_active:
        newest = max(fresh, key=lambda report: (report.tick, report.event_id))
        evidence = _count_contact(evidence, graph.zone_of(newest.tile) or "unknown")
    echo_ids = list(memory.echo_ids)
    for cue in view.motion:
        if cue.cue_id.startswith("echo:") and cue.cue_id not in echo_ids:
            echo_ids.append(cue.cue_id)
            evidence = replace(evidence, echo_witnessed=evidence.echo_witnessed + 1)
    announcement, announced_at = memory.announcement, memory.announcement_tick
    lockdown = memory.lockdown_handled
    if view.phase == MissionPhase.LOCKDOWN and not lockdown:
        announcement, announced_at, lockdown = LOCKDOWN_ANNOUNCEMENT, tick, True
        away = {order.guard_id for order in live if order.task != TaskKind.INTERCEPT}
        if len(away) >= 2:
            # Core taken while a group was drawn off: evidence the formation was bypassed.
            evidence = replace(evidence, bypassed_groups=evidence.bypassed_groups + 1)
    tasks = _tasks(view, memory, graph)
    handled = list(memory.handled)
    busy = {order.guard_id for order in live}
    routine = sum(
        1
        for status in view.guards
        if status.available
        and status.state in ROUTINE
        and status.guard_id not in busy
        and status.role != GuardRole.INTERCEPTOR
    )
    caps = {
        TaskKind.PROTECT_EXIT: 1,
        TaskKind.SUPPORT_PURSUIT: rules.support_cap,
        TaskKind.INVESTIGATE_NOISE: rules.noise_cap,
    }
    for task in tasks:
        handled.append(task.evidence_id)
        persistent = task.kind in (TaskKind.INTERCEPT, TaskKind.PROTECT_EXIT)
        expires = task.evidence_tick + rules.dispatch_ttl_ticks * (4 if persistent else 1)
        if task.kind == TaskKind.INTERCEPT:
            for status in view.guards:
                if status.role == GuardRole.INTERCEPTOR and status.available:
                    live.append(
                        Dispatch(
                            status.guard_id,
                            task.kind,
                            task.target,
                            task.evidence_id,
                            task.evidence_tick,
                            expires,
                        )
                    )
                    busy.add(status.guard_id)
            continue
        steps = distances_from(view.world_map, task.target)
        radius = None if task.kind == TaskKind.PROTECT_EXIT else rules.support_radius_tiles
        candidates = sorted(
            (steps[status.tile], status.guard_id)
            for status in view.guards
            if status.available
            and status.role != GuardRole.INTERCEPTOR
            and status.state in ROUTINE
            and status.guard_id not in busy
            and status.tile in steps
            and (radius is None or steps[status.tile] <= radius)
        )
        for _, guard_id in candidates[: caps[task.kind]]:
            if routine - 1 < rules.routine_coverage:
                break  # never strip the last routine patrol from sector coverage
            routine -= 1
            busy.add(guard_id)
            live.append(
                Dispatch(
                    guard_id, task.kind, task.target, task.evidence_id, task.evidence_tick, expires
                )
            )
    return NexusMemory(
        tick,
        tuple(handled[-HANDLED_LIMIT:]),
        tuple(sorted(live, key=lambda order: (order.guard_id, order.evidence_tick))),
        announcement,
        announced_at,
        lockdown,
        bool(fresh),
        tuple(echo_ids[-HANDLED_LIMIT:]),
        evidence,
    )


def dispatch_reports(memory: NexusMemory) -> tuple[SecurityReport, ...]:
    """Addressed radio orders carrying the original evidence tick and a TTL."""
    return tuple(
        SecurityReport(
            NEXUS_ID,
            "DISPATCH",
            order.target,
            order.evidence_tick,
            TASK_PRIORITY[order.task] / 100,
            f"nexus:{order.task.value}:{order.evidence_id}:{order.guard_id}",
            order.expires_at_tick,
            order.guard_id,
        )
        for order in memory.dispatches
    )
