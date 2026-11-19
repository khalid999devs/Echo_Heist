"""Evidence-backed protocol summary and explicit reset confirmation layout."""

import pygame

from echo_heist.core.contracts.autonomy.model import ProtocolState
from echo_heist.ui.render import theme
from echo_heist.ui.render.hud import panel
from echo_heist.ui.render.layout.text import lines
from echo_heist.ui.render.theme import Fonts
from echo_heist.ui.scenes.navigation.controls import button

RESET_MEMORY = pygame.Rect(64, 578, 142, 44)
TOGGLE_MEMORY = pygame.Rect(218, 578, 142, 44)
RESET_BUTTONS = (pygame.Rect(334, 424, 282, 48), pygame.Rect(638, 424, 282, 48))


def draw_protocol(
    canvas: pygame.Surface,
    fonts: Fonts,
    state: ProtocolState | None,
    *,
    selected: bool = False,
    toggle_selected: bool = False,
    can_toggle: bool = False,
) -> None:
    rect = pygame.Rect(62, 384, 300, 238)
    panel(canvas, rect, fill=(5, 18, 27, 238))

    def text(value: str, y: int, color: theme.Color = theme.MUTED) -> None:
        canvas.blit(fonts.micro.render(value, True, color), (78, y))

    text("NEXUS MEMORY", 399, theme.ACCENT)
    if state is None:
        text("NEXUS memory is not available.", 429)
    else:
        active = state.active
        text("MEMORY ON" if state.enabled else "MEMORY OFF", 424)
        label = active.label if active else "Baseline / no active protocol"
        for i, value in enumerate(lines(fonts.small, label, 268, 2)):
            canvas.blit(fonts.small.render(value, True, theme.TEXT), (78, 449 + i * 22))
        reason = active.reason if active else "The next attempt uses standard security responses."
        for i, value in enumerate(lines(fonts.micro, reason, 268, 2)):
            text(value, 501 + i * 19)
        if active and active.evidence:
            evidence = "Evidence: " + active.evidence[0]
            text(lines(fonts.micro, evidence, 268, 1)[0], 550, theme.WARNING)
    button(
        canvas,
        RESET_MEMORY,
        "RESET",
        fonts,
        selected,
        enabled=state is not None and state.can_reset,
    )
    button(
        canvas,
        TOGGLE_MEMORY,
        "TURN OFF" if state and state.enabled else "TURN ON",
        fonts,
        toggle_selected,
        enabled=can_toggle,
    )


def draw_reset(canvas: pygame.Surface, fonts: Fonts, selected: int, notice: str = "") -> None:
    shade = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
    shade.fill((1, 7, 13, 210))
    canvas.blit(shade, (0, 0))
    rect = pygame.Rect(310, 228, 660, 270)
    panel(canvas, rect, fill=(6, 20, 30, 250), border=theme.WARNING)
    canvas.blit(fonts.heading.render("RESET NEXUS MEMORY?", True, theme.TEXT), (334, 258))
    canvas.blit(
        fonts.small.render("Clear learned protocols for the next attempt.", True, theme.MUTED),
        (334, 320),
    )
    canvas.blit(
        fonts.micro.render("The current policy and seed stay selected.", True, theme.MUTED),
        (334, 356),
    )
    if notice:
        for i, value in enumerate(lines(fonts.micro, notice, 610, 1)):
            canvas.blit(fonts.micro.render(value, True, theme.WARNING), (334, 389 + i * 18))
    for i, label in enumerate(("RESET MEMORY", "KEEP MEMORY")):
        button(canvas, RESET_BUTTONS[i], label, fonts, selected == i)
