"""Live guard states, evidence and reasoning from the selected defender's observation."""

import pygame

from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.results import PresentationSnapshot
from echo_heist.core.contracts.security.model import GuardRole, GuardState, GuardView
from echo_heist.core.contracts.world import ActorKind
from echo_heist.ui.render import theme
from echo_heist.ui.render.layout.monitor import Monitor, age, identifier, tabs
from echo_heist.ui.render.security.signals import GUARD_NAMES, STATE_COLORS, STATE_LABELS
from echo_heist.ui.render.theme import Fonts

GUARD_TABS = tabs(6)
STATE_SUMMARY = {
    GuardState.PATROL: "Following its assigned patrol.",
    GuardState.INVESTIGATE: "Checking a cue or a reported location.",
    GuardState.SPOTTED: "Trying to identify movement.",
    GuardState.CHASE: "Pursuing a confirmed target.",
    GuardState.SEARCH: "Checking the area where contact was lost.",
    GuardState.RETURN: "Heading back to its patrol.",
}
EVIDENCE_NAME = {
    "SIGHT": "Confirmed sighting",
    "NOISE": "Heard sound",
    "MOTION": "Unidentified motion",
    "REPORT": "Radio report",
    "DISPATCH": "NEXUS order",
    "HIDE_ENTRY": "Witnessed a hide",
}
RULE_NAMES = ("Loud + near", "Partial + near", "Notable + far", "Unseen + quiet", "Notable + near")
NAVIGATION = {
    GuardRole.SENTINEL: ("BFS", "Finds a route in the fewest grid steps."),
    GuardRole.TRACKER: ("A*", "Uses a goal heuristic to guide pursuit and search."),
    GuardRole.INTERCEPTOR: (
        "Alpha-beta + A*",
        "Predicts a gate, then finds a route to it. F2 / 3 for search.",
    ),
    GuardRole.POST: ("Fixed post", "This unit observes from its assigned position."),
}


def _reasoning(ui: Monitor, guard: GuardView, tick: int, hz: int) -> None:
    trace = guard.fuzzy_trace
    if trace is None and guard.role != GuardRole.SENTINEL:
        if guard.role == GuardRole.TRACKER:
            title = "LAST-SEEN MEMORY"
            note = "Search starts at the last known position. A* routes across the search area."
        elif guard.role == GuardRole.INTERCEPTOR:
            title = "INTERCEPT LOGIC"
            note = "Radio or lockdown can trigger a route search. F2 / 3 shows the selected post."
        else:
            return
        ui.text(title, 524, theme.ACCENT)
        ui.paragraph(note, 552, limit=3)
        return
    ui.text("FUZZY SUSPICION", 516, theme.ACCENT)
    if trace is None:
        ui.text("No ambiguous cue evaluated yet.", 543, theme.MUTED)
        ui.paragraph(
            "Sound and partial motion contribute to urgency. Sight confirms identity.", 567
        )
        return

    ui.text(
        f"Urgency {trace.urgency:.2f}  ·  {age(tick, trace.evaluated_tick, hz)}",
        516,
        theme.WARNING,
        right=466,
        width=224,
    )
    ui.text(
        f"Range {trace.distance_tiles}  /  salience {trace.salience:.2f}"
        f"  /  visibility {trace.visibility:.2f}",
        540,
        theme.MUTED,
        width=306,
    )
    ui.text("Weight x output", 540, theme.MUTED, right=466, width=128)
    for index, (weight, output) in enumerate(zip(trace.activations, trace.outputs, strict=True)):
        y = 563 + index * 16
        ui.text(RULE_NAMES[index], y, width=160)
        ui.bar((218, y + 5, 71, 4), weight, theme.ACCENT)
        ui.text(f"{weight:.2f} x {output:.2f}", y, right=466, width=124)


def draw_lab(
    canvas: pygame.Surface,
    snapshot: PresentationSnapshot,
    guard: GuardView,
    observation: Observation,
    fonts: Fonts,
    *,
    ticks_per_second: int,
) -> None:
    ui = Monitor(canvas, fonts, "Guard monitor", "F3 Close")
    for index, (rect, item) in enumerate(zip(GUARD_TABS, snapshot.guards, strict=False)):
        short, _ = GUARD_NAMES.get(item.actor_id, (identifier(item.actor_id), ""))
        ui.select(rect, f"{index + 1}  {short}", item.actor_id == guard.actor_id)

    actor = next((item for item in snapshot.actors if item.actor_id == guard.actor_id), None)
    _, name = GUARD_NAMES.get(guard.actor_id, ("", identifier(guard.actor_id)))
    state, color = STATE_LABELS[guard.state].capitalize(), STATE_COLORS[guard.state]
    explanation = STATE_SUMMARY[guard.state]
    if actor and (actor.disabled or actor.stunned):
        state, color = ("Disabled" if actor.disabled else "Stunned"), theme.WARNING
        explanation = "Temporarily unable to pursue or capture."
    elif guard.role == GuardRole.INTERCEPTOR and guard.evidence_kind in ("REPORT", "DISPATCH"):
        explanation = "Acting on a reported route or a director order."
    ui.card(234, 80)
    ui.text(name, 245, theme.TEXT, 48, font=fonts.body, width=286)
    ui.text(state.upper(), 249, color, right=454, width=115)
    ui.text(explanation, 282, theme.MUTED, 48, width=406)

    visible = sum(
        entity.kind in (ActorKind.OPERATIVE, ActorKind.COMPANION)
        for entity in observation.visible_entities
    )
    ui.text("LIVE GUARD SENSORS", 327, theme.ACCENT)
    ui.text(
        f"Intruders seen {visible}   ·   sounds {len(observation.heard_events)}"
        f"   ·   motion cues {len(observation.visual_cues)}",
        351,
    )
    id_ticks, threshold = guard.identification_ticks, guard.identification_required_ticks
    ui.text(f"Identification   {id_ticks}/{threshold}", 375, theme.MUTED)
    ui.bar((294, 382, 172, 5), id_ticks / max(1, threshold), color)
    if guard.evidence_tick >= 0:
        source = EVIDENCE_NAME.get(guard.evidence_kind, identifier(guard.evidence_kind))
        origin = f" at {guard.evidence_tile}" if guard.evidence_tile is not None else ""
        cue_age = age(snapshot.tick, guard.evidence_tick, ticks_per_second)
        evidence = f"{source}{origin}  /  {cue_age}"
    else:
        evidence = "No evidence assigned to this goal."
    ui.text(evidence, 401)

    ui.rule(428)
    algorithm, note = NAVIGATION[guard.role]
    nav = f"{algorithm}  /  goal {guard.target}" if guard.target is not None else algorithm
    ui.text(nav, 440, theme.ACCENT)
    if guard.path or guard.expanded_nodes:
        ui.text(f"Plan cost {guard.path_cost}  /  {guard.expanded_nodes} nodes expanded", 463)
    else:
        ui.text("No active path to display.", 463, theme.MUTED)
    ui.text(note, 484, theme.MUTED)

    _reasoning(ui, guard, snapshot.tick, ticks_per_second)
    ui.text("F2  Open decision monitor", 650, theme.MUTED)
