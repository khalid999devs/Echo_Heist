"""Companion, NEXUS and Interceptor monitors for committed runtime data."""

import pygame

from echo_heist.core.contracts.actions import ActionKind
from echo_heist.core.contracts.autonomy.model import AutonomyTelemetry
from echo_heist.core.contracts.observations import OwnStatus
from echo_heist.ui.render import theme
from echo_heist.ui.render.layout.monitor import Monitor, age, identifier, tabs
from echo_heist.ui.render.security.signals import GUARD_NAMES
from echo_heist.ui.render.theme import Fonts

AUTONOMY_TABS = tabs(3)
TACTICS = {
    "ADVANCE": "Advance",
    "ALTERNATE": "Switch route",
    "HIDE": "Take cover",
    "WAIT": "Wait",
    "RETREAT": "Fall back",
    "ECHO": "Deploy decoy",
    "EMP": "Use EMP",
    "MELEE": "Stun a guard",
}
OBJECTIVES = {
    "INFILTRATE": "Infiltrate",
    "REACH_CORE": "Reach the Core",
    "TAKE_CORE": "Take the Core",
    "EXTRACT": "Reach an exit",
}
INTENTS = {
    ActionKind.MOVE: "Moving",
    ActionKind.WAIT: "Holding position",
    ActionKind.INTERACT: "Interacting",
    ActionKind.CROUCH: "Changing posture",
    ActionKind.HIDE: "Taking cover",
    ActionKind.ECHO: "Deploying Echo",
    ActionKind.EMP: "Discharging EMP",
    ActionKind.MELEE: "Striking a guard",
}
POST_NAMES = {
    "choke-security-core": "Security gate",
    "choke-research-core": "Research gate",
    "choke-service-security": "Stairs A",
    "choke-service-research": "Stairs B",
    "choke-entry-service": "Entry gate",
    "choke-cross-link": "Cross-link",
}


def _trigger(value: str) -> str:
    if value.startswith("seeing guard-"):
        actor_id = value.removeprefix("seeing ")
        return "Spotted " + GUARD_NAMES.get(actor_id, ("", identifier(actor_id)))[1]
    if value.startswith("reaching junction "):
        junction = value.removeprefix("reaching junction ")
        return "Reached " + POST_NAMES.get(junction, identifier(junction.removeprefix("choke-")))
    if value.startswith("objective "):
        state = value.removeprefix("objective ")
        return "New goal: " + OBJECTIVES.get(state, identifier(state)).lower()
    return identifier(value)


def _companion(
    ui: Monitor, data: AutonomyTelemetry, own: OwnStatus | None, tick: int, hz: int
) -> None:
    trace = data.companion
    execution = data.execution
    objective = OBJECTIVES.get(trace.state, identifier(trace.state)) if trace else ""
    ui.card(234, 92)
    ui.text("CURRENT ACTION", 244, theme.ACCENT, 48, width=178)
    if objective:
        ui.text(objective, 244, theme.MUTED, right=454, width=220)
    if execution is None:
        action, detail = "Awaiting first action", ""
    else:
        action = INTENTS[execution.action]
        detail = ""
        if execution.rejection:
            denied = TACTICS.get(execution.action.value, identifier(execution.action.value))
            action = (
                "Movement blocked" if execution.action == ActionKind.MOVE else f"{denied} denied"
            )
            detail = identifier(execution.rejection) if execution.rejection != "blocked" else ""
        elif own and own.stair_ticks_remaining:
            action = "Taking the stairs"
        elif own and own.concealed:
            action = "Staying in cover"
        elif own and execution.action == ActionKind.MOVE:
            action = (
                "Sprinting" if own.sprinting else "Crouch-walking" if own.crouched else "Walking"
            )
    ui.text(action, 264, theme.TEXT, 48, font=ui.fonts.body)
    if not detail and trace and trace.utility_action:
        detail = f"Utility override · {trace.utility_reason}"
    if detail:
        ui.text(detail, 300, theme.WARNING, 48, width=405)
    if trace is None:
        ui.text("The plan appears after the first tactical search.", 347, theme.MUTED)
        return

    ui.text("LAST TACTICAL PLAN", 340, theme.ACCENT)
    ui.text(age(tick, trace.evaluated_tick, hz), 340, theme.MUTED, right=466)
    tactic = TACTICS.get(trace.chosen_action, identifier(trace.chosen_action))
    trigger = _trigger(trace.search_trigger)
    ui.text(tactic, 361, theme.TEXT, font=ui.fonts.small, width=150)
    ui.text(trigger, 363, theme.MUTED, 195, width=271)
    depth = f"  /  depth cap {trace.search_depth}" if trace.search_depth else ""
    ui.text(f"MCTS  /  {trace.simulations} simulations{depth}", 389, theme.ACCENT)
    ui.text("CONSIDERED OPTIONS", 416, theme.MUTED, width=190)
    ui.text("VISITS", 416, theme.MUTED, 292)
    ui.text("MEAN REWARD", 416, theme.MUTED, right=466)
    options = sorted(
        (item for item in trace.alternatives if item.legal),
        key=lambda item: (item.action != trace.chosen_action, -item.visits, item.action),
    )
    for i, item in enumerate(options[:4]):
        y = 440 + i * 22
        color = theme.ACCENT if item.action == trace.chosen_action else theme.TEXT
        ui.text(TACTICS.get(item.action, identifier(item.action)), y, color, width=176)
        ui.bar((210, y + 6, 69, 5), item.visits / max(1, trace.simulations), color)
        ui.text(str(item.visits), y, color, 302)
        ui.text(
            "—" if item.mean_reward is None else f"{item.mean_reward:.2f}",
            y,
            color,
            right=466,
        )
    reward = "Reward is estimated from rollouts (0 to 1)."
    if len(options) > 4:
        reward += f"  /  Top 4 of {len(options)}"
    ui.text(reward, 529, theme.MUTED)

    ui.rule(552)
    ui.text("A* NAVIGATION", 565, theme.ACCENT)
    if trace.path_goal is not None and trace.path_cost is not None:
        ui.text(f"Waypoint {trace.path_goal}  /  {len(trace.path)} tiles left", 586)
        ui.text(
            f"Plan cost {trace.path_cost}  /  {trace.expanded_nodes} nodes expanded",
            607,
            theme.MUTED,
        )
    else:
        ui.text("No active route. The next move uses local observations.", 586, theme.MUTED)


def _nexus(ui: Monitor, data: AutonomyTelemetry, tick: int, hz: int) -> None:
    nexus = data.nexus
    protocol = data.protocols
    ui.card(234, 91)
    ui.text("FACILITY DIRECTOR", 244, theme.ACCENT, 48)
    ui.paragraph("Rule-based dispatch uses reported evidence and the facility alarm.", 272, x=48)
    if nexus is not None:
        ui.text("GUARD ASSIGNMENTS", 342, theme.ACCENT)
        ui.text(age(tick, nexus.evaluated_tick, hz), 342, theme.MUTED, right=466)
        if not nexus.tasks:
            ui.text("No active assignments.", 368, theme.MUTED)
        for i, task in enumerate(nexus.tasks[:4]):
            y = 367 + i * 35
            name = GUARD_NAMES.get(task.guard_id, ("", identifier(task.guard_id)))[1]
            ui.text(f"{name}  /  {identifier(task.task)}", y)
            ui.text(
                f"Goal {task.target}  ·  evidence {age(tick, task.evidence_tick, hz)}",
                y + 16,
                theme.MUTED,
            )
        if nexus.announcement:
            ui.paragraph(nexus.announcement, 514, theme.WARNING, limit=1)
    else:
        ui.text("Awaiting the live director trace.", 342, theme.MUTED)
    if protocol is not None:
        ui.rule(548)
        ui.text("NEXUS MEMORY", 561, theme.ACCENT)
        state = "Memory off" if not protocol.enabled else "Memory on"
        ui.text(state, 561, theme.MUTED, right=466)
        active = protocol.active
        ui.text(active.label if active else "Standard security response", 584)
        if active:
            ui.paragraph(active.reason, 608)


def _interceptor(ui: Monitor, data: AutonomyTelemetry, tick: int, hz: int) -> None:
    traces = data.nexus.interceptors if data.nexus else ()
    if not traces:
        ui.card(234, 106)
        ui.text("INTERCEPT PLAN", 244, theme.ACCENT, 48)
        ui.text("Awaiting evidence", 267, theme.TEXT, 48, font=ui.fonts.body)
        ui.paragraph("Each guard needs a sighting, a radio report or a director order.", 300, x=48)
    # One card per Interceptor; each searches only the gates of its own zone.
    for index, trace in enumerate(traces[:2]):
        top = 234 + index * 112
        name = GUARD_NAMES.get(trace.guard_id, ("", identifier(trace.guard_id)))[1]
        label = POST_NAMES.get(trace.post_id, identifier(trace.post_id.removeprefix("choke-")))
        ui.card(top, 102)
        ui.text(name.upper(), top + 10, theme.ACCENT, 48)
        ui.text(age(tick, trace.evaluated_tick, hz), top + 10, theme.MUTED, right=454)
        ui.text(f"Holds {label}", top + 32, theme.TEXT, 48, font=ui.fonts.body)
        ui.text(
            f"{trace.evaluated_nodes} leaves scored  •  {trace.pruned_nodes} pruned"
            f"  •  value {trace.value:.2f}",
            top + 72,
            theme.MUTED,
            48,
        )
    ui.rule(461)
    ui.text("MINIMAX + ALPHA-BETA", 475, theme.ACCENT)
    ui.paragraph(
        "Minimax picks a gate against plausible routes. "
        "Alpha-beta skips branches that cannot improve the choice.",
        501,
        limit=3,
    )
    ui.paragraph(
        "A* then routes the guard to the post on foot. The plan is a prediction based on evidence.",
        570,
        limit=3,
    )


def draw_telemetry(
    canvas: pygame.Surface,
    fonts: Fonts,
    data: AutonomyTelemetry,
    tab: int,
    tick: int,
    hz: int,
    own: OwnStatus | None = None,
) -> None:
    ui = Monitor(canvas, fonts, "Decision monitor", "F2 Close")
    for i, label in enumerate(("1  Companion", "2  NEXUS", "3  Interceptor")):
        ui.select(AUTONOMY_TABS[i], label, tab == i)
    if tab == 0:
        _companion(ui, data, own, tick, hz)
    elif tab == 1:
        _nexus(ui, data, tick, hz)
    else:
        _interceptor(ui, data, tick, hz)
    ui.text("F3  Open guard monitor", 650, theme.MUTED)
