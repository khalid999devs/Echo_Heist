"""Grounded cutaway props drawn from committed state, with no collision callbacks."""

from functools import lru_cache
from hashlib import blake2b
from math import cos, pi, sin
from random import Random

import pygame

from echo_heist.core.contracts.environment.presentation import PropKind, PropView
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE
from echo_heist.ui.render import theme
from echo_heist.ui.render.camera import Camera


def footprint(view: PropView, tile_px: int, fraction: float = 1.0) -> pygame.Rect:
    scale = tile_px / POSITION_UNITS_PER_TILE
    position = view.position
    if view.previous_position is not None and view.kind == PropKind.CANISTER:
        blend = max(0, min(1, fraction))
        x, y = view.previous_position
        position = (round(x + (position[0] - x) * blend), round(y + (position[1] - y) * blend))
    rect = pygame.Rect(0, 0, *(max(2, round(axis * scale)) for axis in view.size))
    rect.center = round(position[0] * scale), round(position[1] * scale)
    return rect


def depth(view: PropView, tile_px: int, fraction: float) -> float:
    return footprint(view, tile_px, fraction).bottom


@lru_cache(maxsize=96)
def metal(size: tuple[int, int], shade: int = 0) -> pygame.Surface:
    """A restrained machined panel, cached at the actual render resolution."""
    w, h = size
    surface = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(h):
        value = 49 + round(14 * (1 - y / max(1, h))) + ((y * 7) % 3) + shade
        pygame.draw.line(surface, (value, value + 7, value + 9), (0, y), (w, y))
    pygame.draw.rect(surface, (18, 27, 30), surface.get_rect(), 2, border_radius=2)
    pygame.draw.line(surface, (107, 119, 120), (2, 2), (w - 3, 2))
    pygame.draw.line(surface, (24, 34, 37), (2, h - 3), (w - 3, h - 3))
    for x in (4, w - 5):
        for y in (5, h - 6):
            pygame.draw.circle(surface, (27, 35, 38), (x, y), 2)
            pygame.draw.line(surface, (102, 112, 113), (x - 1, y), (x + 1, y))
    return surface


@lru_cache(maxsize=64)
def contact(size: tuple[int, int]) -> pygame.Surface:
    w, h = size
    shadow = pygame.Surface((w + 12, h + 10), pygame.SRCALPHA)
    for i in range(5, 0, -1):
        pygame.draw.ellipse(
            shadow, (0, 4, 7, 12 + (5 - i) * 7), (6 - i, 5 - i, w + i * 2, h + i * 2)
        )
    return shadow


def _door(canvas: pygame.Surface, view: PropView, rect: pygame.Rect) -> None:
    horizontal = rect.w >= rect.h
    lift = 13
    body = rect.move(0, -lift)
    # Only frame/rails cover the floor. The open centre stays transparent.
    canvas.blit(contact(rect.size), (rect.x - 6, rect.y - 5))
    rail = (
        pygame.Rect(body.x, body.y, body.w, 5)
        if horizontal
        else pygame.Rect(body.x, body.y, 5, body.h)
    )
    canvas.blit(metal(rail.size), rail)
    second = rail.move(0, body.h - 5) if horizontal else rail.move(body.w - 5, 0)
    canvas.blit(metal(second.size), second)
    original_clip = canvas.get_clip()
    canvas.set_clip(body.clip(original_clip))
    if horizontal:
        width = max(6, body.w // 2 - 3)
        leaf = metal((width, max(8, body.h - 4)), 8)
        offset = round((width + 1) * view.openness)
        for x in (body.left + 3 - offset, body.centerx + offset):
            canvas.blit(leaf, (x, body.y + 2))
        seam = body.centerx
        pygame.draw.line(
            canvas,
            theme.ACCENT_DIM,
            (seam - offset - 1, body.top + 6),
            (seam - offset - 1, body.bottom - 5),
            2,
        )
        pygame.draw.line(
            canvas,
            theme.ACCENT_DIM,
            (seam + offset + 1, body.top + 6),
            (seam + offset + 1, body.bottom - 5),
            2,
        )
    else:
        height = max(6, body.h // 2 - 3)
        leaf = metal((max(8, body.w - 4), height), 8)
        offset = round((height + 1) * view.openness)
        for y in (body.top + 3 - offset, body.centery + offset):
            canvas.blit(leaf, (body.x + 2, y))
    canvas.set_clip(original_clip)
    for edge in ((rect.left, rect.top), (rect.right - 6, rect.bottom - 7)):
        column = pygame.Rect(edge[0], edge[1] - lift, 7, lift + 7)
        canvas.blit(metal(column.size, -7), column)
        pygame.draw.line(
            canvas,
            theme.DANGER if view.locked else theme.ACCENT,
            (column.x + 3, column.y + 3),
            (column.x + 3, column.y + 10),
            2,
        )
    # Ground threshold and a small directional seam preserve a readable opening.
    if horizontal:
        pygame.draw.line(canvas, (132, 131, 102), rect.bottomleft, rect.bottomright)
    else:
        pygame.draw.line(canvas, (132, 131, 102), rect.topright, rect.bottomright)


@lru_cache(maxsize=128)
def shard_points(identity: str, count: int = 14) -> tuple[tuple[float, float, float], ...]:
    rng = Random(int.from_bytes(blake2b(identity.encode(), digest_size=8).digest(), "big"))
    return tuple(
        (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0.5, 1.4)) for _ in range(count)
    )


def _glass(canvas: pygame.Surface, view: PropView, rect: pygame.Rect) -> None:
    horizontal = rect.w >= rect.h
    a, b = (rect.midleft, rect.midright) if horizontal else (rect.midtop, rect.midbottom)
    height = 25
    top_a, top_b = (a[0], a[1] - height), (b[0], b[1] - height)
    pygame.draw.line(canvas, (16, 34, 40), a, b, 5)
    if not view.broken:
        bounds = pygame.Rect(
            min(a[0], b[0]) - 3,
            min(a[1], b[1]) - height - 3,
            max(6, abs(a[0] - b[0]) + 6),
            abs(a[1] - b[1]) + height + 6,
        )
        pane = pygame.Surface(bounds.size, pygame.SRCALPHA)
        points = [(p[0] - bounds.x, p[1] - bounds.y) for p in (a, b, top_b, top_a)]
        pygame.draw.polygon(pane, (111, 168, 177, 63), points)
        pygame.draw.lines(pane, (164, 204, 207, 150), False, points[2:] + points[:1], 1)
        canvas.blit(pane, bounds)
        pygame.draw.line(canvas, (87, 118, 122), top_a, top_b, 2)
        middle = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
        pygame.draw.line(
            canvas, (155, 181, 184), (middle[0] - 5, middle[1] - 5), (middle[0] + 5, middle[1] - 20)
        )
    else:
        for dx, dy, length in shard_points(view.object_id):
            x, y = (
                rect.centerx + round(dx * max(12, rect.w * 0.48)),
                rect.centery + round(dy * max(12, rect.h * 0.48)),
            )
            pygame.draw.polygon(
                canvas,
                (101, 137, 145),
                ((x, y), (x + round(5 * length), y + 2), (x + 1, y + round(4 * length))),
            )
        # Broken stubs read as a removed pane rather than an invisible barrier.
        for p, sign in ((a, 1), (b, -1)):
            pygame.draw.line(canvas, (116, 154, 159), p, (p[0] + 4 * sign, p[1] - 9), 2)
    for p, top in ((a, top_a), (b, top_b)):
        pygame.draw.line(canvas, (36, 52, 58), p, top, 5)
        pygame.draw.line(canvas, (95, 116, 121), (p[0] - 1, p[1]), (top[0] - 1, top[1]), 1)
        pygame.draw.circle(canvas, (19, 34, 38), p, 4)


@lru_cache(maxsize=32)
def _canister(size: tuple[int, int]) -> pygame.Surface:
    w, h = size
    sprite = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(sprite, (73, 89, 92), (3, 2, w - 6, h - 4), border_radius=4)
    for x in range(4, w - 4):
        tone = round(100 + 75 * sin(pi * (x - 4) / max(1, w - 8)))
        pygame.draw.line(sprite, (tone, tone + 7, tone + 9), (x, 4), (x, h - 5))
    for y in (4, h - 7):
        pygame.draw.ellipse(sprite, (43, 58, 64), (2, y - 3, w - 4, 7), 2)
    pygame.draw.rect(sprite, (185, 141, 54), (3, h // 2 - 3, w - 6, 6))
    pygame.draw.line(sprite, (49, 58, 59), (w // 2, h // 2 - 3), (w // 2 + 4, h // 2 + 2), 2)
    return sprite


@lru_cache(maxsize=64)
def _locker_body(source: pygame.Surface, size: tuple[int, int]) -> pygame.Surface:
    # The existing authored recess includes an open leaf at its left. Separate
    # the cabinet body for animation; do not rotate a complete perspective image.
    region = pygame.Rect(
        round(source.get_width() * 0.24), 0, round(source.get_width() * 0.76), source.get_height()
    )
    region.clamp_ip(source.get_rect())
    return pygame.transform.smoothscale(source.subsurface(region), size)


def _locker(
    canvas: pygame.Surface, view: PropView, rect: pygame.Rect, source: pygame.Surface | None
) -> None:
    body = pygame.Rect(
        rect.x,
        rect.bottom - max(rect.h, round(rect.w * 1.75)),
        rect.w,
        max(rect.h, round(rect.w * 1.75)),
    )
    canvas.blit(contact(rect.size), (rect.x - 6, rect.y - 5))
    if source is not None:
        canvas.blit(_locker_body(source, body.size), body)
    else:
        canvas.blit(metal(body.size), body)
    face = body.inflate(-round(body.w * 0.18), -round(body.h * 0.26))
    face.bottom = body.bottom - 3
    openness = view.openness
    width = max(5, round(face.w * cos(openness * pi * 0.47)))
    lid = metal((width, face.h), -8)
    offset = round(sin(openness * pi / 2) * face.w * 0.56)
    canvas.blit(lid, (face.left - offset, face.top + round(openness * 7)))
    handle = (face.left - offset + max(3, width - 7), face.centery + round(openness * 7))
    pygame.draw.line(
        canvas, (150, 162, 160), (handle[0], handle[1] - 7), (handle[0], handle[1] + 7), 2
    )
    lamp = (body.right - 4, face.top + 8)
    pygame.draw.line(
        canvas,
        theme.WARNING if view.occupant_id else theme.ACCENT_DIM,
        lamp,
        (lamp[0], lamp[1] + 7),
        2,
    )


@lru_cache(maxsize=144)
def _rotated_canister(size: tuple[int, int], angle: int) -> pygame.Surface:
    return pygame.transform.rotate(_canister(size), angle)


def draw_prop(
    canvas: pygame.Surface,
    view: PropView,
    camera: Camera,
    tile_px: int,
    fraction: float,
    locker_source: pygame.Surface | None = None,
) -> None:
    world = footprint(view, tile_px, fraction)
    rect = pygame.Rect(camera.to_screen(world.topleft), world.size)
    if not rect.inflate(80, 240).colliderect(canvas.get_clip()):
        return
    if view.kind == PropKind.DOOR:
        _door(canvas, view, rect)
    elif view.kind == PropKind.GLASS:
        _glass(canvas, view, rect)
    elif view.kind == PropKind.LOCKER:
        _locker(canvas, view, rect, locker_source)
    else:
        size = max(12, rect.w), max(18, rect.h)
        canvas.blit(
            contact((size[0], max(5, size[1] // 3))),
            (rect.centerx - size[0] // 2 - 6, rect.centery - 6),
        )
        # Quantized image angle bounds work per frame; translation still uses
        # the actual consecutive world samples, not a scripted rolling path.
        image = _rotated_canister(size, (round(view.roll_degrees / 5) * 5) % 360)
        canvas.blit(image, image.get_rect(center=(rect.centerx, rect.centery - 4)))
