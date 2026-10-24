"""Compact, selectable teaching panel; every value comes from a real decision."""

from functools import lru_cache

import pygame

from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.results import PresentationSnapshot
from echo_heist.core.contracts.security.model import GuardRole, GuardView
from echo_heist.core.contracts.world import ActorKind
from echo_heist.ui.render import theme
from echo_heist.ui.render.security.signals import STATE_COLORS, STATE_LABELS
from echo_heist.ui.render.surfaces.glass import panel
from echo_heist.ui.render.theme import Fonts

LAB_RECT = pygame.Rect(20, 156, 462, 500)
GUARD_TABS = tuple(pygame.Rect(36 + i * 108, 200, 104, 30) for i in range(4))
RULE_NAMES = ("Loud + near", "Partial + near", "Notable + far", "Unseen + quiet", "Notable + near")


@lru_cache(maxsize=512)
def _text(font: pygame.font.Font, value: str, color: theme.Color) -> pygame.Surface:
    return font.render(value, True, color)


def draw_lab(
    canvas: pygame.Surface,
    snapshot: PresentationSnapshot,
    guard: GuardView,
    observation: Observation,
    fonts: Fonts,
    *,
    ticks_per_second: int,
) -> None:
    panel(canvas, LAB_RECT, fill=(5, 16, 25, 242), border=theme.ACCENT_DIM)

    def text(value: str, y: int, color: theme.Color = theme.TEXT, x: int = 36) -> None:
        canvas.blit(_text(fonts.micro, value, color), (x, y))

    text("AI LAB", 170, theme.ACCENT)
    text("1-4 Guard   /   F3 Close", 170, theme.MUTED, 266)
    for index, item in enumerate(snapshot.guards):
        if index >= len(GUARD_TABS):
            break
        selected = item.actor_id == guard.actor_id
        rect = GUARD_TABS[index]
        panel(canvas, rect, border=theme.ACCENT if selected else theme.BORDER)
        name = item.actor_id.removeprefix("guard-").upper()
        label = _text(fonts.micro, f"{index + 1} {name}", theme.TEXT if selected else theme.MUTED)
        canvas.blit(label, label.get_rect(center=rect.center))
    role = (
        "POST / sensing only"
        if guard.role == GuardRole.POST
        else f"{guard.role} / {guard.algorithm}"
    )
    text(role, 246, theme.ACCENT)
    state = _text(fonts.micro, STATE_LABELS[guard.state], STATE_COLORS[guard.state])
    canvas.blit(state, state.get_rect(topright=(466, 246)))
    intruders = sum(
        entity.kind in (ActorKind.OPERATIVE, ActorKind.COMPANION)
        for entity in observation.visible_entities
    )
    text(
        f"LIVE SENSORS   sight {intruders}   sound {len(observation.heard_events)}"
        f"   cues {len(observation.visual_cues)}",
        272,
        theme.MUTED,
    )
    text(f"Identification  {guard.identification_ticks}/{guard.identification_required_ticks}", 296)
    bar = pygame.Rect(308, 303, 158, 5)
    pygame.draw.rect(canvas, theme.BORDER, bar, border_radius=2)
    pygame.draw.rect(
        canvas,
        STATE_COLORS[guard.state],
        (
            bar.x,
            bar.y,
            round(
                bar.w
                * min(1, guard.identification_ticks / max(1, guard.identification_required_ticks))
            ),
            bar.h,
        ),
        border_radius=2,
    )
    text(
        f"LAST PLAN   cost {guard.path_cost}   expanded {guard.expanded_nodes}"
        f"   rev {guard.path_revision}",
        324,
    )
    age = (
        "never"
        if guard.last_seen_tick < 0
        else f"{max(0, snapshot.tick - guard.last_seen_tick) / ticks_per_second:.1f}s ago"
    )
    text(f"Last sight: {age}   /   map rev {observation.geometry_revision}", 346, theme.MUTED)
    evidence_age = (
        ""
        if guard.evidence_tick < 0
        else f" / {max(0, snapshot.tick - guard.evidence_tick) / ticks_per_second:.1f}s old"
    )
    text(f"Goal from {guard.evidence_kind or 'patrol route'}{evidence_age}", 368, theme.WARNING)
    trace = guard.fuzzy_trace
    pygame.draw.line(canvas, theme.BORDER, (36, 395), (466, 395))
    if trace is None:
        text("FUZZY / No uncertain cue evaluated yet", 410, theme.MUTED)
        text("Sound or partial motion supplies the inputs.", 440, theme.MUTED)
        text("Identity requires actual visual contact.", 466, theme.MUTED)
    else:
        age_s = max(0, snapshot.tick - trace.evaluated_tick) / ticks_per_second
        text(f"LAST FUZZY   urgency {trace.urgency:.2f}   /   {age_s:.1f}s ago", 410, theme.ACCENT)
        text(
            f"Distance {trace.distance_tiles}   salience {trace.salience:.2f}"
            f"   visibility {trace.visibility:.2f}",
            434,
            theme.MUTED,
        )
        for index, (name, value) in enumerate(trace.memberships):
            x = 36 + index * 72
            text(name, 461, theme.MUTED, x)
            pygame.draw.rect(canvas, theme.BORDER, (x, 483, 58, 3))
            pygame.draw.rect(canvas, theme.ACCENT_DIM, (x, 483, round(58 * value), 3))
        for index, (weight, output) in enumerate(
            zip(trace.activations, trace.outputs, strict=True)
        ):
            y = 501 + index * 23
            text(RULE_NAMES[index], y)
            pygame.draw.rect(canvas, theme.BORDER, (200, y + 6, 112, 4))
            pygame.draw.rect(canvas, theme.ACCENT, (200, y + 6, round(112 * weight), 4))
            text(f"{weight:.2f} x {output:.2f}", y, theme.MUTED, 326)
    text("Teaching view / privileged display, never AI input", 632, theme.MUTED)
