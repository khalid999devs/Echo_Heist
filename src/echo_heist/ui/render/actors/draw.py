"""Foot-anchored directional poses with distance-driven walk/run cycles."""

import pygame

from echo_heist.ui.render import theme
from echo_heist.ui.render.actors.model import ActorMotion
from echo_heist.ui.render.actors.shadows import draw_shadow


def draw_actor(
    canvas: pygame.Surface,
    point: tuple[int, int],
    sprites: tuple[pygame.Surface, ...],
    motion: ActorMotion,
    clock_ms: int,
    *,
    disabled: bool,
    stunned: bool,
    carries_core: bool,
    pulse: float,
    walk: tuple[pygame.Surface, ...] = (),
    run: tuple[pygame.Surface, ...] = (),
    fraction: float = 1.0,
) -> None:
    active = motion.moving and not (disabled or stunned)
    dx, dy = motion.direction
    row = (1 if dx > 0 else 3) if abs(dx) > abs(dy) else (0 if dy < 0 else 2)
    phase = (motion.phase - motion.phase_step * (1 - fraction)) % 1
    if active and walk:
        poses = run if motion.sprinting and run else walk
        index = int(phase * 8) % 8
        frame = poses[row * 8 + index]
        if not motion.sprinting and index in (2, 6):
            # Close the stride at passing points instead of holding every frame
            # in an extended contact pose. Use the matching authored viewpoint.
            frame = sprites[row * 4]
        pivot = (frame.get_width() // 2, frame.get_height())
    else:
        pose = 1 + int(phase * 2) if active else 0
        frame = sprites[(row * 4 if len(sprites) == 16 else 0) + pose]
        pivot = (frame.get_width() // 2, frame.get_height())
    feet = (point[0], point[1] + 3)
    draw_shadow(canvas, frame, feet)
    canvas.blit(frame, (feet[0] - pivot[0], feet[1] - pivot[1]))
    if carries_core:
        pygame.draw.circle(canvas, theme.WARNING, (point[0] + 19, point[1] - 45), 5, 2)
    if disabled or stunned:
        color = theme.DISABLED if disabled else theme.WARNING
        pygame.draw.arc(canvas, color, (point[0] - 24, point[1] - 13, 48, 23), 0, 5.4, 3)
