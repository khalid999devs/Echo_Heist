"""Workshop and companion visual designs, with explicit deployment boundary."""

from math import sin

import pygame

from echo_heist.ui.render import theme
from echo_heist.ui.render.autonomy.protocols import RESET_MEMORY, TOGGLE_MEMORY, draw_protocol
from echo_heist.ui.render.environment.art import image
from echo_heist.ui.render.hud import panel
from echo_heist.ui.render.theme import Fonts
from echo_heist.ui.scenes.companion.deployment import DeploymentPanel
from echo_heist.ui.scenes.design.model import POLICIES, PRESETS, WorkshopDraft
from echo_heist.ui.scenes.navigation.controls import button

WORKSHOP_CONTROLS = (
    *(pygame.Rect(420 + i * 262, 162, 246, 52) for i in range(3)),
    *(pygame.Rect(420, 242 + i * 80, 770, 64) for i in range(4)),
    pygame.Rect(420, 588, 372, 54),
    pygame.Rect(810, 588, 380, 54),
    pygame.Rect(44, 650, 130, 42),
    RESET_MEMORY,
    TOGGLE_MEMORY,
)


def portrait() -> pygame.Surface:
    sheet = image("assets/characters/companion.png")
    cell = sheet.subsurface((0, 0, sheet.get_width() // 2, sheet.get_height() // 2))
    crop = cell.subsurface(cell.get_bounding_rect(min_alpha=24))
    size = crop.get_rect().fit(pygame.Rect(0, 0, 264, 340)).size
    return pygame.transform.smoothscale(crop, size)


def draw_workshop(
    canvas: pygame.Surface,
    fonts: Fonts,
    robot: pygame.Surface,
    draft: WorkshopDraft,
    selected: int,
    deployment: DeploymentPanel,
    *,
    clock_ms: int = 0,
    reduced_motion: bool = False,
) -> None:
    panel(canvas, pygame.Rect(44, 162, 336, 480), fill=(6, 23, 33, 230))
    canvas.blit(fonts.micro.render("ECHO / RECON COMPANION", True, theme.ACCENT), (66, 182))
    bob = 0 if reduced_motion else round(2 * sin(clock_ms / 600))
    canvas.blit(robot, robot.get_rect(midbottom=(212, 371 + bob)))
    draw_protocol(
        canvas,
        fonts,
        deployment.protocol_state,
        selected=selected == 10,
        toggle_selected=selected == 11,
        can_toggle=deployment.can_toggle_memory,
    )
    for i, label in enumerate(PRESETS):
        button(canvas, WORKSHOP_CONTROLS[i], label, fonts, selected == i or draft.preset == i)
    for i, (label, options) in enumerate(POLICIES):
        rect = WORKSHOP_CONTROLS[3 + i]
        panel(
            canvas,
            rect,
            fill=(5, 24, 34, 230),
            border=theme.ACCENT if selected == i + 3 else theme.BORDER,
        )
        canvas.blit(fonts.micro.render(label.upper(), True, theme.MUTED), (rect.x + 18, rect.y + 9))
        canvas.blit(
            fonts.body.render(options[draft.choices[i]], True, theme.TEXT),
            (rect.x + 18, rect.y + 29),
        )
        canvas.blit(fonts.body.render("+", True, theme.ACCENT), (rect.right - 38, rect.y + 20))
    button(canvas, WORKSHOP_CONTROLS[7], "EXPLORE FACILITY", fonts, selected == 7)
    button(
        canvas,
        WORKSHOP_CONTROLS[8],
        "DEPLOY COMPANION",
        fonts,
        selected == 8,
        enabled=deployment.can_deploy,
    )
    button(canvas, WORKSHOP_CONTROLS[9], "BACK", fonts, selected == 9)
