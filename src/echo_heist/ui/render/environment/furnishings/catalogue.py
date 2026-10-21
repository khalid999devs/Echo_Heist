"""Cache coherent overhead props at physical footprints; never rotate a 3D picture sideways."""

from dataclasses import dataclass
from math import sin

import pygame

from echo_heist.level.model import LevelData
from echo_heist.ui.render.actors.shadows import GroundShadow, cast_shadow
from echo_heist.ui.render.camera import Camera


@dataclass(frozen=True, slots=True)
class FurnitureVisual:
    object_id: str
    tile: tuple[int, int]
    footprint: pygame.Rect
    render_rect: pygame.Rect
    sprite: pygame.Surface
    shadow: GroundShadow
    style: str
    indicators: tuple[tuple[int, int], ...]

    @property
    def depth(self) -> int:
        return self.footprint.bottom


def prepare_furniture(
    level: LevelData, props: tuple[pygame.Surface, ...]
) -> tuple[FurnitureVisual, ...]:
    result = []
    size = level.static_map.tile_size_px
    for obj in level.static_map.objects:
        if obj.kind != "Furniture":
            continue
        data = dict(obj.properties)
        width, height = data["width_tiles"], data["height_tiles"]
        assert isinstance(width, int) and isinstance(height, int)
        style = str(data["style"])
        rect = pygame.Rect(obj.tile[0] * size, obj.tile[1] * size, width * size, height * size)
        source_id = {
            "rack": 21,
            "console": 20,
            "desk": 20,
            "tank": 24,
            "crates": 3,
            "plant": 4,
            "planter": 23,
            "pump": 22,
            "shelf": 25,
            "workbench": 26 if width == height else 25,
            "labbench": 19 if height > width else 18,
        }.get(style, 25)
        source = props[source_id]
        render_rect = rect.copy()
        if style == "tank":
            render_rect.height = round(rect.width * 1.6)
            render_rect.bottom = rect.bottom
        sprite = pygame.Surface(render_rect.size, pygame.SRCALPHA)
        indicators = []
        # Long service rows are repeated cabinet/pump modules, not one tall,
        # stretched picture. Other tables use a genuinely vertical source view.
        count = max(1, height // width) if style in ("rack", "pump") else 1
        for i in range(count):
            cell = pygame.Rect(
                3, i * render_rect.h // count + 3, render_rect.w - 6, render_rect.h // count - 6
            )
            fitted = source.get_rect().fit(cell)
            fitted.midbottom = cell.midbottom
            scaled = pygame.transform.smoothscale(source, fitted.size)
            sprite.blit(scaled, fitted)
            if style in ("console", "desk", "labbench", "rack"):
                u, v = (0.5, 0.3) if style in ("console", "desk") else (0.72, 0.4)
                indicators.append((fitted.x + round(fitted.w * u), fitted.y + round(fitted.h * v)))
            elif style == "tank":
                indicators.append((fitted.centerx, fitted.y + round(fitted.h * 0.65)))
        shadow = cast_shadow(sprite)
        result.append(
            FurnitureVisual(
                obj.object_id, obj.tile, rect, render_rect, sprite, shadow, style, tuple(indicators)
            )
        )
    return tuple(sorted(result, key=lambda item: (item.depth, item.footprint.x, item.object_id)))


def draw_instrument(
    canvas: pygame.Surface, item: FurnitureVisual, camera: Camera, clock_ms: int
) -> None:
    x, y = camera.to_screen(item.render_rect.topleft)
    canvas.blit(item.sprite, (x, y))
    brightness = 140 + round(24 * sin(clock_ms / 750 + item.footprint.x))
    for px, py in item.indicators:
        if item.style == "tank":
            for bubble in range(3):
                progress = (clock_ms / 1500 + bubble / 3) % 1
                pygame.draw.circle(
                    canvas,
                    (139, 231, 226),
                    (
                        x + px + round(4 * sin(bubble * 2 + progress * 4)),
                        y + py - round(progress * 20),
                    ),
                    1,
                )
            continue
        pygame.draw.line(
            canvas,
            (60, brightness, min(255, brightness + 35)),
            (x + px - 3, y + py),
            (x + px + 3, y + py),
        )


def draw_preview(
    canvas: pygame.Surface,
    furnishings: tuple[FurnitureVisual, ...],
    source: pygame.Rect,
    destination: tuple[int, int],
) -> None:
    clip = canvas.get_clip()
    canvas.set_clip(pygame.Rect(destination, source.size).clip(clip))
    for item in furnishings:
        if item.render_rect.colliderect(source):
            canvas.blit(
                item.sprite,
                (
                    item.render_rect.x - source.x + destination[0],
                    item.render_rect.y - source.y + destination[1],
                ),
            )
    canvas.set_clip(clip)
