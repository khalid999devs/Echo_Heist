"""Translucent character projections for the recorded Echo path."""

from functools import lru_cache
from typing import TYPE_CHECKING

import pygame

from echo_heist.core.contracts.results import EchoView
from echo_heist.core.contracts.world import ActorKind
from echo_heist.ui.render import theme

if TYPE_CHECKING:
    from echo_heist.ui.render.world import WorldArt


@lru_cache(maxsize=128)
def _tint(frame: pygame.Surface) -> pygame.Surface:
    projection = frame.copy()
    projection.fill((79, 219, 255), special_flags=pygame.BLEND_RGB_MULT)
    projection.fill((19, 80, 96), special_flags=pygame.BLEND_RGB_ADD)
    for y in range(2, projection.get_height(), 4):
        projection.fill(
            (255, 255, 255, 166),
            (0, y, projection.get_width(), 1),
            special_flags=pygame.BLEND_RGBA_MULT,
        )
    return projection


def draw_echo(
    canvas: pygame.Surface,
    point: tuple[int, int],
    echo: EchoView,
    art: "WorldArt | None",
    tick: float,
    *,
    reduced_motion: bool,
) -> None:
    fade = min(1, echo.remaining_ticks / 12)
    if art is None:
        pygame.draw.ellipse(canvas, theme.ACCENT_DIM, (point[0] - 10, point[1] - 32, 20, 31), 2)
        pygame.draw.circle(canvas, theme.ACCENT_DIM, (point[0], point[1] - 36), 6, 2)
        return
    dx, dy = echo.facing
    row = (1 if dx > 0 else 3) if abs(dx) > abs(dy) else (0 if dy < 0 else 2)
    robot = echo.owner_kind == ActorKind.COMPANION and bool(art.robot_idle)
    moving = echo.previous_position != echo.position and not reduced_motion
    walk = art.robot_walk[3] if robot else art.operative_walk
    if moving and walk:
        stride = len(walk) // 4
        frame = walk[row * stride + int(tick / 3) % stride]
    elif robot:
        frame = art.robot_idle[3][row]
    elif echo.owner_kind == ActorKind.COMPANION:
        frame = art.companion[0]
    else:
        frame = art.operative[row * 4]
    projection = _tint(frame)
    projection.set_alpha(round(152 * fade))
    feet = point[0], point[1] + (15 if robot and moving and walk else 3)
    canvas.blit(projection, projection.get_rect(midbottom=feet))
