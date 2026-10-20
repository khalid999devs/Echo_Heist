"""Small deterministic facility and actor motifs; art never defines collision."""

from dataclasses import dataclass
from math import atan2, cos, degrees, pi, sin

import pygame

from echo_heist.core.contracts.world import ActorKind
from echo_heist.ui.render import theme


@dataclass(frozen=True, slots=True)
class ActorMotion:
    """Presentation-only gait derived from the last committed position change."""

    direction: tuple[int, int] = (0, -1)
    moving: bool = False
    sprinting: bool = False


def shade(color: theme.Color, amount: int) -> theme.Color:
    return tuple(max(0, min(255, part + amount)) for part in color)  # type: ignore[return-value]


def floor_tile(
    surface: pygame.Surface,
    rect: pygame.Rect,
    zone_id: str | None,
    variant: int,
    texture: pygame.Surface | None = None,
) -> None:
    base = theme.ZONE_FLOORS.get(zone_id or "", theme.CORRIDOR_FLOOR)
    if texture is None:
        surface.fill(shade(base, -3 if variant % 7 == 0 else 0), rect)
    else:
        source = pygame.Rect(
            rect.x % texture.get_width(), rect.y % texture.get_height(), rect.w, rect.h
        )
        surface.blit(texture, rect.topleft, source)
    pygame.draw.line(surface, shade(base, -12), rect.topleft, (rect.right - 1, rect.top), 1)
    pygame.draw.line(surface, shade(base, 7), (rect.left, rect.bottom - 1), rect.bottomright, 1)
    if variant % 5 == 0:
        pygame.draw.line(
            surface,
            shade(base, 10),
            (rect.left + 5, rect.top + 4),
            (rect.left + 12, rect.top + 4),
            1,
        )
        pygame.draw.circle(surface, shade(base, 16), (rect.right - 5, rect.bottom - 5), 1)
    if variant % 23 == 0:
        pygame.draw.rect(surface, shade(base, -14), rect.inflate(-12, -13), 1)
    if variant % 19 == 0:
        pygame.draw.line(
            surface, theme.ACCENT_DIM, (rect.x + 4, rect.y + 24), (rect.x + 17, rect.y + 24), 1
        )
        pygame.draw.circle(surface, theme.ACCENT_DIM, (rect.x + 19, rect.y + 24), 1)


def wall_tile(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    edge: bool,
    beacon: bool,
    variant: int = 0,
    texture: pygame.Surface | None = None,
) -> None:
    if texture is None:
        pygame.draw.rect(surface, (10, 20, 28), rect.move(0, 3))
    else:
        source = pygame.Rect(
            rect.x % texture.get_width(), rect.y % texture.get_height(), rect.w, rect.h
        )
        surface.blit(texture, rect.topleft, source)
    top = pygame.Rect(rect.x + 1, rect.y, rect.w - 2, rect.h - 5)
    if texture is None:
        pygame.draw.rect(surface, theme.WALL, top)
    pygame.draw.line(surface, (62, 83, 94), top.topleft, top.topright, 2)
    pygame.draw.line(surface, (13, 26, 35), top.bottomleft, top.bottomright, 3)
    pygame.draw.line(surface, (16, 29, 38), rect.bottomleft, rect.bottomright, 2)
    if texture is None:
        pygame.draw.rect(surface, (42, 57, 65), top.inflate(-11, -10), 1)
    if variant % 11 == 0:
        screen = pygame.Rect(rect.x + 5, rect.y + 6, 22, 13)
        pygame.draw.rect(surface, (4, 20, 30), screen)
        pygame.draw.rect(surface, theme.ACCENT_DIM, screen, 1)
        for index, height in enumerate((4, 7, 5, 8)):
            pygame.draw.line(
                surface,
                theme.ACCENT,
                (screen.x + 4 + index * 4, screen.bottom - 3),
                (screen.x + 4 + index * 4, screen.bottom - height),
                1,
            )
    elif variant % 17 == 0:
        for offset in (8, 12, 16, 20):
            pygame.draw.line(
                surface,
                (72, 97, 105),
                (rect.x + 7, rect.y + offset),
                (rect.right - 7, rect.y + offset),
                1,
            )
    if edge:
        pygame.draw.line(
            surface,
            theme.WARNING if beacon else theme.ACCENT_DIM,
            (rect.left + 5, rect.bottom - 4),
            (rect.right - 5, rect.bottom - 4),
            2,
        )
        if beacon:
            pygame.draw.rect(surface, theme.WARNING, (rect.centerx - 3, rect.bottom - 7, 6, 5))


def glass_tile(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, (20, 40, 50), rect)
    pygame.draw.rect(surface, (58, 76, 82), rect.inflate(-2, -2), 2)
    pygame.draw.rect(surface, (19, 82, 97), rect.inflate(-8, -4))
    pygame.draw.line(
        surface,
        (112, 226, 239),
        (rect.left + 9, rect.top + 4),
        (rect.left + 9, rect.bottom - 5),
        2,
    )
    pygame.draw.line(
        surface,
        (56, 148, 164),
        (rect.right - 6, rect.top + 4),
        (rect.right - 6, rect.bottom - 5),
        1,
    )
    pygame.draw.circle(surface, (7, 24, 34), rect.center, 2)


def cover_tile(surface: pygame.Surface, rect: pygame.Rect, variant: int) -> None:
    pygame.draw.rect(surface, (9, 17, 23), rect.move(2, 4), border_radius=2)
    cabinet = rect.inflate(-3, -5).move(0, -2)
    pygame.draw.rect(surface, theme.COVER, cabinet, border_radius=2)
    pygame.draw.rect(surface, (151, 124, 76), cabinet, 1, border_radius=2)
    pygame.draw.rect(surface, (22, 35, 40), cabinet.inflate(-9, -8))
    pygame.draw.line(surface, (195, 147, 66), cabinet.topleft, cabinet.topright, 2)
    if variant % 2 == 0:
        pygame.draw.rect(surface, theme.ACCENT_DIM, (rect.x + 9, rect.y + 12, 6, 4))
    else:
        pygame.draw.line(
            surface,
            theme.WARNING,
            (rect.x + 8, rect.y + 23),
            (rect.x + 23, rect.y + 23),
            2,
        )


def core_floor(surface: pygame.Surface, point: tuple[int, int]) -> None:
    """A walkable reactor floor inset; only the map's Core object is interactive."""
    x, y = point
    pygame.draw.circle(surface, (8, 34, 45), point, 57)
    pygame.draw.circle(surface, (20, 71, 83), point, 54, 3)
    for radius, color, width in (
        (46, (18, 49, 59), 8),
        (40, theme.ACCENT_DIM, 2),
        (32, (8, 28, 38), 8),
        (24, (46, 152, 169), 2),
    ):
        pygame.draw.circle(surface, color, point, radius, width)
    for index in range(8):
        theta = index * pi / 4
        outer = (round(x + 56 * cos(theta)), round(y + 56 * sin(theta)))
        inner = (round(x + 47 * cos(theta)), round(y + 47 * sin(theta)))
        pygame.draw.line(
            surface, theme.WARNING if index % 2 == 0 else theme.ACCENT, inner, outer, 4
        )
    pygame.draw.circle(surface, (3, 20, 28), point, 16)
    pygame.draw.circle(surface, theme.ACCENT, point, 12, 2)


def extraction_floor(surface: pygame.Surface, point: tuple[int, int]) -> None:
    """Paint a distinct walkable lift pad beneath the extraction beacon."""
    x, y = point
    pygame.draw.rect(surface, (4, 34, 43), (x - 35, y - 35, 70, 70), border_radius=7)
    pygame.draw.rect(surface, theme.ACCENT_DIM, (x - 34, y - 34, 68, 68), 2, border_radius=7)
    for offset in (-23, -13, 13, 23):
        pygame.draw.line(surface, theme.ACCENT_DIM, (x + offset, y - 29), (x + offset, y - 22), 2)
        pygame.draw.line(surface, theme.ACCENT_DIM, (x + offset, y + 22), (x + offset, y + 29), 2)
    pygame.draw.line(surface, theme.ACCENT, (x - 20, y), (x + 20, y), 2)


def beacon_glow(
    canvas: pygame.Surface, point: tuple[int, int], color: theme.Color, radius: int, pulse: float
) -> None:
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    glow.fill((0, 0, 0, 0))
    center = radius, radius
    for fraction, alpha in ((1.0, 10), (0.7, 19), (0.42, 32), (0.19, 65)):
        pygame.draw.circle(glow, (*color, alpha), center, max(1, int(radius * fraction)))
    canvas.blit(glow, (point[0] - radius, point[1] - radius))
    pygame.draw.circle(canvas, color, point, 10 + int(2 * pulse), 2)


def light_pool(
    surface: pygame.Surface, point: tuple[int, int], color: theme.Color, radius: int
) -> None:
    """Soft presentation light with no effect on sight, hearing or collision."""
    layer = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    layer.fill((0, 0, 0, 0))
    center = radius, radius
    for fraction, alpha in ((1.0, 8), (0.78, 16), (0.52, 28), (0.28, 60)):
        pygame.draw.circle(layer, (*color, alpha), center, int(radius * fraction))
    surface.blit(layer, (point[0] - radius, point[1] - radius))


def actor(
    canvas: pygame.Surface,
    point: tuple[int, int],
    kind: ActorKind,
    *,
    disabled: bool,
    stunned: bool,
    carries_core: bool,
    pulse: float,
    motion: ActorMotion,
    clock_ms: int,
    sprites: tuple[pygame.Surface, ...] | None = None,
) -> None:
    """Animate a facing armored silhouette without changing actor location or hitbox."""
    x, y = point
    guard = kind != ActorKind.OPERATIVE
    accent = (
        theme.DISABLED
        if disabled
        else theme.WARNING
        if stunned
        else {
            ActorKind.SENTINEL: theme.DANGER,
            ActorKind.TRACKER: (255, 135, 77),
            ActorKind.INTERCEPTOR: (232, 93, 159),
        }.get(kind, theme.DANGER)
        if guard
        else theme.OPERATIVE
    )
    active = motion.moving and not (disabled or stunned)
    cycle = clock_ms / 1000 * (17 if motion.sprinting else 11)
    stride = round(4 * sin(cycle)) if active else 0
    bob = round(abs(sin(cycle)) * 2) if active else round(sin(clock_ms / 530) * 0.5)
    pygame.draw.ellipse(canvas, (1, 6, 9), (x - 15, y + 6, 30, 12))
    if active and motion.sprinting:
        dx, dy = motion.direction
        trail = pygame.Surface((64, 64), pygame.SRCALPHA)
        for offset, alpha in ((11, 65), (19, 30)):
            start = (32 - dx * offset, 32 - dy * offset)
            pygame.draw.circle(trail, (*accent, alpha), start, 5 if offset == 11 else 3)
        canvas.blit(trail, (x - 32, y - 32))

    dx, dy = motion.direction
    angle = degrees(atan2(-dx, -dy))
    if sprites is not None:
        if active and motion.sprinting:
            frame_index = (1, 3, 2, 3)[(clock_ms // 95) % 4]
        elif active:
            frame_index = 1 + (clock_ms // 180) % 2
        else:
            frame_index = 0
        frame = pygame.transform.rotate(sprites[frame_index], angle)
        frame_rect = frame.get_rect(center=(x, y - bob))
        contour = pygame.mask.from_surface(frame, 96).outline(every=2)
        if len(contour) > 2:
            halo = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
            pygame.draw.lines(halo, (*accent, 195), True, contour, 3)
            canvas.blit(halo, frame_rect)
        canvas.blit(frame, frame_rect)
        pygame.draw.circle(canvas, accent, (x, y + 10), 17, 1)
        if carries_core:
            pygame.draw.circle(canvas, theme.WARNING, (x + 12, y - 12), 4 + int(pulse), 2)
        if disabled or stunned:
            pygame.draw.arc(canvas, accent, (x - 20, y - 21, 40, 40), 0, 5.4, 3)
        return

    sprite = pygame.Surface((44, 44), pygame.SRCALPHA)
    cx, cy = 22, 22
    metal = (74, 92, 103) if guard else (89, 122, 133)
    for side in (-1, 1):
        leg_x = cx + side * 6
        leg_y = cy + 7 + side * stride
        pygame.draw.line(sprite, (10, 20, 27), (cx + side * 5, cy + 4), (leg_x, leg_y), 6)
        pygame.draw.ellipse(sprite, metal, (leg_x - 4, leg_y - 1, 8, 10))
        pygame.draw.line(sprite, accent, (leg_x - 2, leg_y + 5), (leg_x + 2, leg_y + 5), 1)
    pygame.draw.circle(sprite, (7, 15, 21), (cx, cy - bob), 12)
    pygame.draw.circle(sprite, metal, (cx, cy - 2 - bob), 10)
    pygame.draw.circle(sprite, (16, 29, 37), (cx, cy - 3 - bob), 8)
    for side in (-1, 1):
        arm_x = cx + side * 10
        arm_y = cy + (side * -stride // 2 if active else 1) - bob
        pygame.draw.line(sprite, (14, 27, 35), (cx + side * 7, cy - 4 - bob), (arm_x, arm_y + 4), 6)
        pygame.draw.circle(sprite, metal, (arm_x, arm_y), 3)
        pygame.draw.line(sprite, accent, (arm_x - 2, arm_y), (arm_x + 2, arm_y), 1)
    pygame.draw.polygon(
        sprite,
        (8, 18, 25),
        (
            (cx - 7, cy - 9 - bob),
            (cx + 7, cy - 9 - bob),
            (cx + 8, cy - 3 - bob),
            (cx - 8, cy - 3 - bob),
        ),
    )
    pygame.draw.line(sprite, accent, (cx - 6, cy - 6 - bob), (cx + 6, cy - 6 - bob), 3)
    pygame.draw.circle(sprite, accent, (cx, cy + 3 - bob), 2)
    if guard:
        pygame.draw.line(sprite, accent, (cx - 8, cy + 7), (cx - 4, cy + 10), 2)
        pygame.draw.line(sprite, accent, (cx + 8, cy + 7), (cx + 4, cy + 10), 2)
    else:
        pygame.draw.rect(sprite, (9, 56, 66), (cx - 5, cy + 7, 10, 4))
    if carries_core:
        pygame.draw.circle(sprite, theme.WARNING, (cx + 9, cy - 8), 3 + int(pulse))
    if disabled or stunned:
        pygame.draw.arc(sprite, accent, (cx - 15, cy - 16, 30, 30), 0, 5.4, 2)
    rotated = pygame.transform.rotate(sprite, angle)
    canvas.blit(rotated, rotated.get_rect(center=point))
