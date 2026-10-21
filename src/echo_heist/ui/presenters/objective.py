"""Objective and interaction text from permitted observations only."""

from dataclasses import dataclass

import pygame

from echo_heist.core.contracts.observations import Observation
from echo_heist.core.contracts.world import MissionPhase


@dataclass(frozen=True, slots=True)
class ObjectiveView:
    objective: str
    interaction: str
    inventory: str
    elapsed: str
    warning: str
    interaction_progress: tuple[int, int] | None
    echo_charges: int = 0
    emp_charges: int = 0
    core_held: bool = False


def build_objective_view(observation: Observation, *, ticks_per_second: int) -> ObjectiveView:
    if ticks_per_second <= 0:
        raise ValueError("Tick rate must be positive")
    objective = {
        MissionPhase.INFILTRATE: "Reach Core Chamber",
        MissionPhase.LOCKDOWN: "Return to Entry extraction",
        MissionPhase.WON: "Core extracted",
        MissionPhase.CAPTURED: "Captured",
        MissionPhase.ABORTED: "Run aborted",
    }[observation.phase]
    interaction = ""
    interaction_progress = None
    if observation.interactions:
        hint = observation.interactions[0]
        progress = 100 * hint.progress_ticks // max(1, hint.required_ticks)
        interaction = f"Hold E - Recover core ({progress}%)"
        interaction_progress = hint.progress_ticks, hint.required_ticks
    inventory = observation.own_status.inventory
    seconds = observation.tick // ticks_per_second
    remaining = observation.own_status.capture_ticks_remaining
    return ObjectiveView(
        objective,
        interaction,
        f"Echo {inventory.echo_charges} | EMP {inventory.emp_charges} | "
        f"Core {'YES' if inventory.core_held else 'NO'}",
        f"{seconds // 60:02d}:{seconds % 60:02d}",
        "CAPTURE WIND-UP - Escape, EMP or melee" if remaining is not None else "",
        interaction_progress,
        inventory.echo_charges,
        inventory.emp_charges,
        inventory.core_held,
    )


def draw_objective(
    surface: pygame.Surface,
    view: ObjectiveView,
    font: pygame.font.Font,
    *,
    position: tuple[int, int] = (16, 16),
    color: tuple[int, int, int] = (230, 238, 248),
) -> None:
    """Optional basic presenter; scenes can lay out the same values themselves."""
    lines = (
        f"OBJECTIVE: {view.objective} | {view.elapsed}",
        view.inventory,
        view.interaction,
        view.warning,
    )
    y = position[1]
    for line in lines:
        if line:
            surface.blit(font.render(line, True, color), (position[0], y))
            y += font.get_linesize()
