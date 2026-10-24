"""Actual decision alternatives and director traces in an optional teaching panel."""

import pygame

from echo_heist.core.contracts.autonomy.model import AutonomyTelemetry
from echo_heist.ui.render import theme
from echo_heist.ui.render.hud import panel
from echo_heist.ui.render.layout.text import fit, lines, render
from echo_heist.ui.render.theme import Fonts

PANEL_RECT = pygame.Rect(20, 156, 462, 500)
AUTONOMY_TABS = tuple(pygame.Rect(36 + i * 145, 200, 139, 30) for i in range(3))


def draw_telemetry(
    canvas: pygame.Surface, fonts: Fonts, data: AutonomyTelemetry, tab: int, tick: int, hz: int
) -> None:
    panel(canvas, PANEL_RECT, fill=(5, 16, 25, 242), border=theme.ACCENT_DIM)

    def text(value: str, y: int, color: theme.Color = theme.TEXT, x: int = 36) -> None:
        canvas.blit(render(fonts.micro, fit(fonts.micro, value, 466 - x), color), (x, y))

    def wrapped(value: str, y: int, color: theme.Color = theme.MUTED, limit: int = 2) -> None:
        for i, line in enumerate(lines(fonts.micro, value, 430, limit)):
            text(line, y + i * 20, color)

    text("LIVE AI / F2 CLOSE", 170, theme.ACCENT)
    text("1-3 Select", 170, theme.MUTED, 363)
    for i, label in enumerate(("COMPANION", "NEXUS", "INTERCEPTOR")):
        rect = AUTONOMY_TABS[i]
        panel(canvas, rect, border=theme.ACCENT if tab == i else theme.BORDER)
        title = render(fonts.micro, label, theme.TEXT if tab == i else theme.MUTED)
        canvas.blit(title, title.get_rect(center=rect.center))

    def age(at: int) -> str:
        return f"{max(0, tick - at) / hz:.1f}s ago"

    if tab == 0:
        trace = data.companion
        if trace is None:
            text("Awaiting an actual Companion decision.", 252, theme.MUTED)
        else:
            text(trace.state.replace("_", " "), 247, theme.ACCENT)
            text("LAST DECISION / " + age(trace.evaluated_tick), 272, theme.MUTED)
            text(trace.chosen_action.replace("_", " "), 300, theme.TEXT)
            wrapped(trace.reason, 326)
            text(f"MCTS / {trace.simulations} simulations", 378, theme.ACCENT)
            text("ACTION", 405, theme.MUTED)
            text("VISITS", 405, theme.MUTED, 299)
            text("MEAN", 405, theme.MUTED, 410)
            maximum = max((item.visits for item in trace.alternatives), default=1)
            for i, item in enumerate(trace.alternatives[:4]):
                y = 432 + i * 29
                color = (
                    theme.ACCENT
                    if item.action == trace.chosen_action
                    else theme.TEXT
                    if item.legal
                    else theme.DISABLED
                )
                label = item.action.replace("_", " ")
                canvas.blit(render(fonts.micro, fit(fonts.micro, label, 185), color), (36, y))
                pygame.draw.rect(canvas, theme.BORDER, (224, y + 7, 64, 4))
                pygame.draw.rect(
                    canvas, color, (224, y + 7, round(64 * item.visits / max(1, maximum)), 4)
                )
                text(str(item.visits), y, color, 305)
                text("--" if item.mean_reward is None else f"{item.mean_reward:.2f}", y, color, 418)
            cost = "--" if trace.path_cost is None else str(trace.path_cost)
            text(f"A* / cost {cost} / expanded {trace.expanded_nodes}", 559, theme.MUTED)
            if trace.utility_action:
                text("UTILITY / " + trace.utility_action.replace("_", " "), 586, theme.WARNING)
                wrapped(trace.utility_reason, 608, limit=1)
            else:
                text("Measured alternatives / unknown rewards shown as --", 608, theme.MUTED)
    elif tab == 1:
        nexus = data.nexus
        protocols = data.protocols
        text("FACILITY DIRECTOR", 251, theme.ACCENT)
        if nexus is None:
            text("No live NEXUS trace available.", 282, theme.MUTED)
        else:
            text("LAST EVALUATION / " + age(nexus.evaluated_tick), 278, theme.MUTED)
            wrapped(nexus.announcement or "No director announcement.", 307, theme.WARNING)
            for i, task in enumerate(nexus.tasks[:4]):
                y = 367 + i * 42
                text(task.guard_id.removeprefix("guard-").upper() + " / " + task.task, y)
                text(
                    f"Goal {task.target} / evidence {age(task.evidence_tick)}", y + 20, theme.MUTED
                )
        if protocols is not None:
            text(
                "PROTOCOL / " + (protocols.active.label if protocols.active else "BASELINE"),
                558,
                theme.ACCENT,
            )
            wrapped(
                protocols.active.reason
                if protocols.active
                else "Standard security response. No active adaptation.",
                586,
            )
    else:
        interceptor = data.nexus.interceptor if data.nexus else None
        text("MINIMAX / ALPHA-BETA", 251, theme.ACCENT)
        if interceptor is None:
            text("No Interceptor decision has been reported.", 282, theme.MUTED)
        else:
            text(interceptor.guard_id.upper(), 284)
            text("LAST SEARCH / " + age(interceptor.evaluated_tick), 311, theme.MUTED)
            text("SELECTED POST / " + interceptor.post_id, 351, theme.ACCENT)
            text(f"Target {interceptor.target}", 379)
            text(f"Depth {interceptor.depth} / evaluated {interceptor.evaluated_nodes}", 422)
            text(f"Pruned {interceptor.pruned_nodes} / value {interceptor.value:.2f}", 453)
            wrapped("The guard must travel to this post. Search telemetry does not move it.", 508)
    text("Privileged display / never a controller input", 633, theme.MUTED)
