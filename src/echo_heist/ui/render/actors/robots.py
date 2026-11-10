"""Rigged robot locomotion: stable torso, articulated joints and planted support feet.

Pose tables are prepared once. Phase is supplied only by committed displacement,
never an independent animation clock that could make a stopped robot skate.
"""

from dataclasses import dataclass
from io import BytesIO
from math import pi, sin, sqrt

import pygame
from pygame import Vector2

from echo_heist.infrastructure.resources import resource_bytes
from echo_heist.ui.render.actors.model import COMPANION_SIZE, DEFENDER_SIZE

POSES = 16
PADDING = 12


@dataclass(frozen=True, slots=True)
class Part:
    image: pygame.Surface
    pivot: Vector2


def _part(source: pygame.Surface, polygon: list[tuple[float, float]], pivot: Vector2) -> Part:
    mask = pygame.Surface(source.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), polygon)
    result = source.copy()
    result.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    rect = result.get_bounding_rect(min_alpha=8)
    return Part(result.subsurface(rect).copy(), pivot - Vector2(rect.topleft))


def _place(canvas: pygame.Surface, part: Part, pivot: Vector2, angle: float = 0) -> None:
    image = pygame.transform.rotozoom(part.image, angle, 1)
    center = Vector2(part.image.get_rect().center) - part.pivot
    center = pivot + center.rotate(-angle)
    canvas.blit(image, image.get_rect(center=(round(center.x), round(center.y))))


def _skin_leg(
    canvas: pygame.Surface,
    source: pygame.Surface,
    left: int,
    right: int,
    original: tuple[Vector2, Vector2, Vector2],
    posed: tuple[Vector2, Vector2, Vector2],
    *,
    far: bool,
) -> None:
    # Continuous row skinning retains the original knee/ankle artwork. Separate
    # rotated rectangles leave seams as joints bend, especially at game scale.
    hip, knee, ankle = original
    root, joint, target = posed
    strip_source = source.copy()
    if far:
        strip_source.fill((192, 202, 207, 255), special_flags=pygame.BLEND_RGBA_MULT)

    def mapped(row: float) -> Vector2:
        if row <= knee.y:
            t = (row - hip.y) / max(1, knee.y - hip.y)
            point, base = root + (joint - root) * t, hip + (knee - hip) * t
        elif row <= ankle.y:
            t = (row - knee.y) / max(1, ankle.y - knee.y)
            point, base = joint + (target - joint) * t, knee + (ankle - knee) * t
        else:
            point, base = target + Vector2(0, row - ankle.y), Vector2(ankle.x, row)
        return Vector2(left + point.x - base.x, point.y)

    for row in range(round(hip.y), source.get_height()):
        start, end = mapped(row), mapped(row + 1)
        band = strip_source.subsurface((left, row, right - left, 1))
        height = max(1, round(end.y) - round(start.y))
        canvas.blit(
            pygame.transform.scale(band, (band.get_width(), height)),
            (round(start.x), round(start.y)),
        )


def _knee(hip: Vector2, ankle: Vector2, upper: float, lower: float, bend: int) -> Vector2:
    delta = ankle - hip
    distance = min(upper + lower - 0.3, max(0.2, delta.length()))
    direction = delta.normalize() if delta.length_squared() else Vector2(0, 1)
    along = (upper * upper - lower * lower + distance * distance) / (2 * distance)
    out = sqrt(max(0, upper * upper - along * along))
    return hip + direction * along + Vector2(-direction.y, direction.x) * out * bend


def _cycle(phase: float) -> tuple[float, float]:
    # Support foot travels backwards relative to the moving chassis. Swing foot
    # follows a low arc forward; it never drags over the floor or hops the torso.
    if phase < 0.6:
        return 0.5 - phase / 0.6, 0.0
    t = (phase - 0.6) / 0.4
    smooth = t * t * (3 - 2 * t)
    return -0.5 + smooth, sin(t * pi)


def _gait(
    source: pygame.Surface, facing: int, role: int, *, fast: bool = False
) -> tuple[pygame.Surface, ...]:
    width, height = source.get_size()
    bounds = source.get_bounding_rect(min_alpha=32)
    x, y, w, h = bounds
    side_view = facing in (1, 3)
    east = 1 if facing == 1 else -1
    hip_y = y + h * (0.66 if role == 3 else 0.61)
    knee_y, ankle_y = y + h * 0.82, y + h * 0.93
    center = x + w / 2
    pad = Vector2(PADDING, PADDING)
    body_mask = pygame.Surface(source.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(body_mask, (255, 255, 255), (0, 0, width, round(hip_y + 2)))
    body = source.copy()
    body.blit(body_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    arms = []
    if not side_view:
        for sign in (-1, 1):
            edge = x if sign == -1 else x + w
            inner = center + sign * w * 0.25
            shoulder = Vector2(center + sign * w * 0.28, y + h * (0.48 if role == 3 else 0.4))
            points = [
                (edge, shoulder.y - h * 0.07),
                (inner, shoulder.y - h * 0.07),
                (inner, hip_y + h * 0.12),
                (edge, hip_y + h * 0.12),
            ]
            arms.append((_part(source, points, shoulder), shoulder))
            pygame.draw.polygon(body, (0, 0, 0, 0), points)
    # A side profile's visible arm remains attached to the torso. The hip/leg
    # articulation below provides the silhouette; no duplicated arm is cut across it.
    legs = []
    for sign in (-1, 1):
        if side_view:
            left, right = x + w * 0.12, x + w * 0.90
            hip = Vector2(center - east * w * 0.08, hip_y)
            knee = Vector2(center + east * w * 0.04, knee_y)
            ankle = Vector2(center - east * w * 0.01, ankle_y)
        else:
            left, right = (x + w * 0.14, center) if sign == -1 else (center, x + w * 0.86)
            hip = Vector2(center + sign * w * 0.13, hip_y)
            knee = Vector2(center + sign * w * 0.18, knee_y)
            ankle = Vector2(center + sign * w * 0.18, ankle_y)
        legs.append((round(left), round(right), hip, knee, ankle, sign))
    frames = []
    for frame in range(POSES):
        phase = frame / POSES
        canvas = pygame.Surface((width + PADDING * 2, height + PADDING * 2), pygame.SRCALPHA)
        settle = abs(sin(phase * 2 * pi)) * (0.9 if role == 3 else 1.3)
        body_offset = pad + Vector2(0.6 * sin(phase * 2 * pi), settle)
        # Opposite support/swing phases; the chassis remains a stable rigid body.
        for index, (left, right, hip, knee, ankle, sign) in enumerate(legs):
            travel, lift = _cycle((phase + (0.5 if index else 0)) % 1)
            stride = h * ((0.24, 0.30, 0.26, 0.25)[role] if side_view else 0.12)
            stride *= 1.3 if fast else 1.0
            shift = (
                Vector2(east * travel * stride, -lift * h * (0.065 if fast else 0.055))
                if side_view
                else Vector2(
                    sign * lift * 0.8,
                    (1 if facing == 2 else -1) * travel * stride - lift * h * 0.04,
                )
            )
            target = ankle + pad + shift
            root = hip + body_offset
            joint = _knee(
                root,
                target,
                hip.distance_to(knee),
                knee.distance_to(ankle),
                -east if side_view else -sign,
            )
            if side_view and index == 0:
                target.y -= 2
            _skin_leg(
                canvas,
                source,
                left,
                right,
                (hip, knee, ankle),
                (root, joint, target),
                far=side_view and index == 0,
            )
        if side_view:
            # Chassis leans into travel; its head/arm silhouette stays rigid.
            _place(
                canvas,
                Part(body, Vector2(center, hip_y)),
                Vector2(center, hip_y) + body_offset,
                -east * ((2.4 if fast else 1.4) + 0.5 * sin(phase * 4 * pi)),
            )
        else:
            canvas.blit(body, (round(body_offset.x), round(body_offset.y)))
        for arm_index, (arm, shoulder) in enumerate(arms):
            _place(
                canvas,
                arm,
                shoulder + body_offset,
                sin(phase * 2 * pi) * (1 if arm_index else -1) * (10 if fast else 7),
            )
        frames.append(canvas)
    return tuple(frames)


def load_robots() -> tuple[
    tuple[tuple[pygame.Surface, ...], ...],
    tuple[tuple[pygame.Surface, ...], ...],
    tuple[tuple[pygame.Surface, ...], ...],
]:
    """Four roles, each with north/east/south/west idle and sixteen gait poses."""
    sheet = pygame.image.load(BytesIO(resource_bytes("assets/characters/robots/turnarounds.png")))
    idle, walking, running = [], [], []
    for role in range(4):
        size = COMPANION_SIZE if role == 3 else DEFENDER_SIZE
        cells = []
        for facing in range(4):
            cell = sheet.subsurface(
                (
                    facing * sheet.get_width() // 4,
                    role * sheet.get_height() // 4,
                    sheet.get_width() // 4,
                    sheet.get_height() // 4,
                )
            ).copy()
            component = pygame.mask.from_surface(cell, 48).connected_component()
            cell.blit(
                component.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)),
                (0, 0),
                special_flags=pygame.BLEND_RGBA_MULT,
            )
            cells.append(cell)
        bounds = [cell.get_bounding_rect(min_alpha=48) for cell in cells]
        scale = min((size[0] - 8) / max(b.w for b in bounds), size[1] / max(b.h for b in bounds))
        facings = []
        for cell, rect in zip(cells, bounds, strict=True):
            image = pygame.transform.smoothscale(
                cell.subsurface(rect),
                (max(1, round(rect.w * scale)), max(1, round(rect.h * scale))),
            )
            pose = pygame.Surface(size, pygame.SRCALPHA)
            pose.blit(image, image.get_rect(midbottom=(size[0] // 2, size[1])))
            facings.append(pose)
        idle.append(tuple(facings))
        walking.append(
            tuple(
                frame
                for facing, source in enumerate(facings)
                for frame in _gait(source, facing, role)
            )
        )
        running.append(
            tuple(
                frame
                for facing, source in enumerate(facings)
                for frame in _gait(source, facing, role, fast=True)
            )
        )
    return tuple(idle), tuple(walking), tuple(running)
