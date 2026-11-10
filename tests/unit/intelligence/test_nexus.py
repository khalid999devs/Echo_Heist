"""NEXUS task utility: evidence-only dispatch, caps, coverage and one lockdown order."""

from echo_heist.ai.director.nexus import DirectorView, GuardStatus, decide, dispatch_reports
from echo_heist.core.contracts.events import HeardCue, SecurityReport
from echo_heist.core.contracts.security.director import (
    ActiveProtocol,
    DirectorRules,
    NexusMemory,
    ProtocolId,
    RouteGraph,
    RouteNode,
    TaskKind,
    ZoneArea,
)
from echo_heist.core.contracts.security.model import GuardRole, GuardState, VisualCue
from echo_heist.core.contracts.world import MissionPhase, StaticMap

WORLD = StaticMap("nexus-fixture", 30, 8)
GRAPH = RouteGraph(
    (ZoneArea("west", 0, 0, 15, 8), ZoneArea("east", 15, 0, 15, 8)),
    (RouteNode("gate", (15, 4), ("west", "east")),),
    core_tile=(28, 4),
    exit_tile=(1, 4),
    distances=(("gate", "CORE", 13), ("gate", "EXIT", 14)),
)


def guards(*states: GuardState) -> tuple[GuardStatus, ...]:
    tiles = ((3, 2), (8, 2), (20, 2), (26, 6))
    roles = (GuardRole.SENTINEL, GuardRole.SENTINEL, GuardRole.TRACKER, GuardRole.INTERCEPTOR)
    return tuple(
        GuardStatus(f"g{index}", roles[index], tiles[index], True, state)
        for index, state in enumerate(states)
    )


def view(
    tick: int, *, phase: MissionPhase = MissionPhase.INFILTRATE, **values: object
) -> DirectorView:
    return DirectorView(
        tick,
        phase,
        WORLD,
        values.get("guards", guards(*(GuardState.PATROL,) * 4)),  # type: ignore[arg-type]
        values.get("reports", ()),  # type: ignore[arg-type]
        values.get("heard", ()),  # type: ignore[arg-type]
        values.get("motion", ()),  # type: ignore[arg-type]
    )


def test_no_evidence_means_no_orders_and_quiet_footsteps_are_ignored() -> None:
    memory = decide(view(10), DirectorRules(), GRAPH, NexusMemory())
    assert memory.dispatches == () and memory.announcement == ""
    quiet = (HeardCue("5:1", "FOOTSTEP", (5, 5), 5),)
    assert decide(view(11, heard=quiet), DirectorRules(), GRAPH, memory).dispatches == ()


def test_strong_noise_sends_one_nearest_routine_guard_and_keeps_coverage() -> None:
    heard = (HeardCue("7:3", "SPRINT", (6, 4), 7),)
    states = guards(GuardState.INVESTIGATE, GuardState.PATROL, GuardState.PATROL, GuardState.PATROL)
    memory = decide(view(9, guards=states, heard=heard), DirectorRules(), GRAPH, NexusMemory())
    (order,) = memory.dispatches
    # g0 already investigates what it heard; g1 is the nearest routine guard.
    assert (order.guard_id, order.task, order.target) == ("g1", TaskKind.INVESTIGATE_NOISE, (6, 4))
    assert order.evidence_tick == 7  # original evidence time, not the decision time
    (report,) = dispatch_reports(memory)
    assert report.recipient == "g1" and report.tick == 7 and report.source_guard == "nexus"
    # The same evidence is never dispatched twice.
    again = decide(view(10, guards=states, heard=heard), DirectorRules(), GRAPH, memory)
    assert again.dispatches == memory.dispatches
    # With only one routine non-Interceptor guard left, coverage forbids sending it.
    lonely = guards(GuardState.INVESTIGATE, GuardState.CHASE, GuardState.PATROL, GuardState.PATROL)
    assert (
        decide(
            view(9, guards=lonely, heard=heard), DirectorRules(), GRAPH, NexusMemory()
        ).dispatches
        == ()
    )


def test_fresh_sighting_support_is_capped_and_counts_one_contact() -> None:
    sighting = SecurityReport("g0", "SIGHTING", (5, 3), 20, 1.0, "sight:g0:20", 110)
    states = guards(GuardState.CHASE, GuardState.PATROL, GuardState.PATROL, GuardState.PATROL)
    memory = decide(
        view(21, guards=states, reports=(sighting,)), DirectorRules(), GRAPH, NexusMemory()
    )
    assert [(d.guard_id, d.task) for d in memory.dispatches] == [("g1", TaskKind.SUPPORT_PURSUIT)]
    assert memory.evidence.contacts == (("west", 1),)
    relay = SecurityReport("g0", "SIGHTING", (6, 3), 35, 1.0, "sight:g0:35", 125)
    later = decide(view(36, guards=states, reports=(relay,)), DirectorRules(), GRAPH, memory)
    assert later.evidence.contacts == (("west", 1),)  # the same pursuit is one contact
    spread = DirectorRules(protocol=ActiveProtocol(ProtocolId.SPREAD_FORMATION))
    assert (
        decide(
            view(21, guards=states, reports=(sighting,)), spread, GRAPH, NexusMemory()
        ).dispatches
        == ()
    )


def test_lockdown_announces_once_and_orders_intercept_and_exit_defense() -> None:
    states = guards(*(GuardState.PATROL,) * 4)
    first = decide(
        view(50, phase=MissionPhase.LOCKDOWN, guards=states), DirectorRules(), GRAPH, NexusMemory()
    )
    tasks = {(d.guard_id, d.task) for d in first.dispatches}
    assert ("g3", TaskKind.INTERCEPT) in tasks and (
        "g2",
        TaskKind.PROTECT_EXIT,
    ) in tasks  # nearest to the exit gate
    assert first.announcement and first.announcement_tick == 50
    second = decide(
        view(51, phase=MissionPhase.LOCKDOWN, guards=states), DirectorRules(), GRAPH, first
    )
    assert second.announcement_tick == 50 and second.dispatches == first.dispatches


def test_witnessed_echo_motion_is_logged_once_as_evidence() -> None:
    cue = VisualCue("echo:0", (9, 3), 40)
    memory = decide(view(40, motion=(cue,)), DirectorRules(), GRAPH, NexusMemory())
    memory = decide(view(41, motion=(cue,)), DirectorRules(), GRAPH, memory)
    assert memory.evidence.echo_witnessed == 1 and memory.dispatches == ()
