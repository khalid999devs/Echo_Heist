"""Short, bounded effects driven by committed ticks; reduced motion stays readable."""

from functools import lru_cache
from math import cos, pi, sin

import pygame

from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE
from echo_heist.ui.presenters.interactions import Effect
from echo_heist.ui.render import theme
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.interactions.props import shard_points


@lru_cache(maxsize=96)
def _ring(radius: int, alpha: int, amber: bool) -> pygame.Surface:
    radius = max(3, radius)
    surface = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
    center = radius + 4, radius + 4
    color = theme.WARNING if amber else theme.ACCENT
    pygame.draw.circle(surface, (*color, alpha // 3), center, radius, 5)
    pygame.draw.circle(surface, (*color, alpha), center, radius, 1)
    return surface


def draw_effects(
    canvas: pygame.Surface,
    effects: tuple[Effect, ...],
    camera: Camera,
    tile_px: int,
    tick: float,
    hz: int,
    *,
    reduced_motion: bool,
) -> None:
    scale = tile_px / POSITION_UNITS_PER_TILE
    for effect in effects:
        age = (tick - effect.tick) / hz
        if not 0 <= age < 1.1:
            continue
        point = camera.to_screen((effect.position[0] * scale, effect.position[1] * scale))
        if not pygame.Rect(point[0] - 180, point[1] - 180, 360, 360).colliderect(canvas.get_clip()):
            continue
        kind = effect.kind
        if kind in ("EMP", "ECHO"):
            duration = 0.65
            if age >= duration:
                continue
            progress = age / duration
            limit = max(12, round(effect.radius_units * scale)) if kind == "EMP" else 30
            radius = limit if reduced_motion else max(8, round(limit * progress))
            alpha = 50 if reduced_motion else max(8, round((1 - progress) * 130 / 8) * 8)
            ring = _ring(radius, alpha, False)
            canvas.blit(ring, ring.get_rect(center=point))
            if kind == "EMP" and not reduced_motion:
                for i in range(6):
                    theta = i * pi / 3
                    start = (
                        round(point[0] + radius * 0.8 * cos(theta)),
                        round(point[1] + radius * 0.8 * sin(theta)),
                    )
                    end = (
                        round(point[0] + radius * cos(theta + 0.05)),
                        round(point[1] + radius * sin(theta + 0.05)),
                    )
                    pygame.draw.line(canvas, (98, 174, 183), start, end)
        elif kind == "GLASS":
            for dx, dy, amplitude in shard_points(effect.event_id, 16):
                travel = 0.28 if reduced_motion else min(1, age / 0.55)
                lift = 0 if reduced_motion else sin(min(1, age / 0.7) * pi) * 18 * amplitude
                x = point[0] + round(dx * travel * 32)
                y = point[1] + round(dy * travel * 17 - lift)
                tone = (86, 128, 138) if reduced_motion else (139, 177, 184)
                pygame.draw.polygon(canvas, tone, ((x, y), (x + 3, y - 4), (x + 5, y + 1)))
        elif kind in ("MELEE", "RESISTED") and effect.target is not None:
            if age > 0.38:
                continue
            target = camera.to_screen((effect.target[0] * scale, effect.target[1] * scale))
            contact = target[0], target[1] - 30
            color = theme.MUTED if kind == "RESISTED" else theme.WARNING
            if not reduced_motion:
                start = (point[0], point[1] - 32)
                progress = min(1, age / 0.15)
                end = (
                    round(start[0] + (contact[0] - start[0]) * progress),
                    round(start[1] + (contact[1] - start[1]) * progress),
                )
                pygame.draw.line(canvas, (62, 80, 85), start, end, 4)
                pygame.draw.line(canvas, color, start, end, 1)
            if kind == "RESISTED":
                pygame.draw.arc(
                    canvas, color, (contact[0] - 12, contact[1] - 14, 24, 27), 0.3, 2.9, 3
                )
            else:
                for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    pygame.draw.line(
                        canvas,
                        color,
                        (contact[0] + dx * 5, contact[1] + dy * 5),
                        (contact[0] + dx * 10, contact[1] + dy * 10),
                        2,
                    )
        elif kind in ("CANISTER_IMPACT", "DOOR", "HIDE_ENTER", "HIDE_LEAVE"):
            if age >= 0.5:
                continue
            radius = 10 if reduced_motion else 5 + round(age * 22)
            ring = _ring(radius, 48, kind == "CANISTER_IMPACT")
            canvas.blit(ring, ring.get_rect(center=point))
