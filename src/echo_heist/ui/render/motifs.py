"""Small deterministic facility and actor motifs; art never defines collision."""

import pygame

from echo_heist.core.contracts.world import ActorKind
from echo_heist.ui.render import theme


def shade(color: theme.Color, amount: int) -> theme.Color:
    return tuple(max(0, min(255, part + amount)) for part in color)  # type: ignore[return-value]


def floor_tile(
    surface: pygame.Surface, rect: pygame.Rect, zone_id: str | None, variant: int
) -> None:
    base = theme.ZONE_FLOORS.get(zone_id or "", theme.CORRIDOR_FLOOR)
    surface.fill(shade(base, -3 if variant % 7 == 0 else 0), rect)
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


def wall_tile(surface: pygame.Surface, rect: pygame.Rect, *, edge: bool, beacon: bool) -> None:
    pygame.draw.rect(surface, (10, 20, 28), rect.move(0, 3))
    top = pygame.Rect(rect.x + 1, rect.y, rect.w - 2, rect.h - 5)
    pygame.draw.rect(surface, theme.WALL, top)
    pygame.draw.line(surface, (62, 83, 94), top.topleft, top.topright, 2)
    pygame.draw.line(surface, (13, 26, 35), top.bottomleft, top.bottomright, 3)
    pygame.draw.line(surface, (16, 29, 38), rect.bottomleft, rect.bottomright, 2)
    pygame.draw.rect(surface, (42, 57, 65), top.inflate(-11, -10), 1)
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
    for fraction, alpha in ((1.0, 5), (0.78, 8), (0.52, 13), (0.28, 22)):
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
) -> None:
    """A readable armored top-down silhouette at the fixed gameplay tile scale."""
    x, y = point
    guard = kind != ActorKind.OPERATIVE
    accent = (
        theme.DISABLED
        if disabled
        else theme.WARNING
        if stunned
        else theme.DANGER
        if guard
        else theme.OPERATIVE
    )
    pygame.draw.ellipse(canvas, (1, 6, 9), (x - 13, y + 6, 27, 11))
    pygame.draw.circle(canvas, (7, 15, 21), (x, y), 12)
    pygame.draw.circle(canvas, (71, 91, 98) if guard else (81, 117, 128), (x, y - 2), 10)
    pygame.draw.circle(canvas, (16, 29, 37), (x, y - 3), 8)
    pygame.draw.polygon(
        canvas,
        (22, 38, 46),
        ((x - 12, y - 1), (x - 8, y - 8), (x - 5, y - 4), (x - 7, y + 4)),
    )
    pygame.draw.polygon(
        canvas,
        (22, 38, 46),
        ((x + 12, y - 1), (x + 8, y - 8), (x + 5, y - 4), (x + 7, y + 4)),
    )
    pygame.draw.line(canvas, accent, (x - 5, y - 5), (x + 5, y - 5), 3)
    pygame.draw.circle(canvas, accent, (x, y + 4), 2)
    if guard:
        pygame.draw.line(canvas, (147, 88, 62), (x - 11, y + 7), (x - 5, y + 10), 2)
        pygame.draw.line(canvas, (147, 88, 62), (x + 11, y + 7), (x + 5, y + 10), 2)
    else:
        pygame.draw.rect(canvas, (9, 56, 66), (x - 5, y + 7, 10, 4))
    if carries_core:
        pygame.draw.circle(canvas, theme.WARNING, (x + 9, y - 8), 3 + int(pulse))
    if disabled or stunned:
        pygame.draw.arc(canvas, accent, (x - 15, y - 16, 30, 30), 0, 5.4, 2)
