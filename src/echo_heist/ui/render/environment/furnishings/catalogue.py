"""Cache coherent overhead props at physical footprints; never rotate a 3D picture sideways."""

from dataclasses import dataclass
from math import sin

import pygame

from echo_heist.level.model import LevelData
from echo_heist.ui.render.actors.shadows import GroundShadow, cast_shadow
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.environment.architecture.materials import room_grade

APPEARANCE_SOURCES = {
    "centrifuge": 27,
    "spectrometer": 28,
    "fume-hood": 29,
    "freezer": 30,
    "vacuum": 31,
    "robot-arm": 32,
    "cable-cabinet": 33,
    "screen": 34,
    "sample-drawers": 35,
    "coolant": 36,
    "security-console": 37,
    "reagents": 38,
    "displaced-chair": 40,
    "abandoned-station": 41,
    "sample-cart": 42,
    "broken-console": 43,
    "wilted-plant": 44,
    "unfinished-bench": 45,
    "hiding-desk": 47,
}


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
        if self.style == "recess":
            # Empty cabinet art is behind the operative. Only a future committed
            # concealed state may remove the actor; entering this floor tile
            # must never visually fake invisibility.
            return self.footprint.top
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
        appearance = str(data.get("appearance", "standard"))
        condition = str(data.get("condition", "used"))
        rect = pygame.Rect(obj.tile[0] * size, obj.tile[1] * size, width * size, height * size)
        source_id = {
            "rack": 0,
            "console": 39,
            "desk": 39,
            "tank": 24,
            "crates": 3,
            "plant": 4,
            "planter": 23,
            "pump": 22,
            "shelf": 25,
            "workbench": 26 if width == height else 25,
            "labbench": 19 if height > width else 18,
        }.get(style, 25)
        source_id = APPEARANCE_SOURCES.get(appearance, source_id)
        source = props[source_id]
        render_rect = rect.copy()
        if style == "tank":
            render_rect.height = round(rect.width * 1.6)
            render_rect.bottom = rect.bottom
        elif appearance in ("freezer", "fume-hood", "screen"):
            render_rect.height += round(size * 0.55)
            render_rect.bottom = rect.bottom
        elif style in ("console", "desk") or appearance in (
            "abandoned-station",
            "unfinished-bench",
        ):
            render_rect.height = max(
                rect.h, round((rect.w - 6) * source.get_height() / source.get_width()) + 6
            )
            render_rect.bottom = rect.bottom
        sprite = pygame.Surface(render_rect.size, pygame.SRCALPHA)
        indicators = []
        # Long service rows are repeated cabinet/pump modules, not one tall,
        # stretched picture. Other tables use a genuinely vertical source view.
        horizontal_modules = (
            width
            if appearance == "freezer"
            else max(1, (width + 1) // 2)
            if appearance == "fume-hood"
            else 1
        )
        count = (
            max(1, height // width)
            if style in ("rack", "pump") and appearance == "standard"
            else horizontal_modules
        )
        for i in range(count):
            cell = (
                pygame.Rect(
                    i * render_rect.w // count + 3, 3, render_rect.w // count - 6, render_rect.h - 6
                )
                if horizontal_modules > 1
                else pygame.Rect(
                    3, i * render_rect.h // count + 3, render_rect.w - 6, render_rect.h // count - 6
                )
            )
            fitted = source.get_rect().fit(cell)
            fitted.midbottom = cell.midbottom
            scaled = pygame.transform.smoothscale(source, fitted.size)
            sprite.blit(scaled, fitted)
            if appearance in ("broken-console", "abandoned-station", "displaced-chair"):
                continue
            if style in ("console", "desk", "labbench", "rack"):
                u, v = (0.5, 0.3) if style in ("console", "desk") else (0.72, 0.4)
                indicators.append((fitted.x + round(fitted.w * u), fitted.y + round(fitted.h * v)))
            elif style == "tank":
                indicators.append((fitted.centerx, fitted.y + round(fitted.h * 0.65)))
        room = level.room_at(obj.tile)
        grade = room_grade(room.style if room else "corridor", condition)
        sprite.fill((*grade, 255), special_flags=pygame.BLEND_RGBA_MULT)
        shadow = cast_shadow(sprite)
        result.append(
            FurnitureVisual(
                obj.object_id, obj.tile, rect, render_rect, sprite, shadow, style, tuple(indicators)
            )
        )
    for index, tile in enumerate(sorted(level.cover_tiles)):
        rect = pygame.Rect(tile[0] * size, tile[1] * size, size, size)
        render_rect = rect.copy()
        render_rect.height += size // 3
        render_rect.bottom = rect.bottom
        sprite = pygame.Surface(render_rect.size, pygame.SRCALPHA)
        source = props[35 if index % 2 else 33]
        fitted = source.get_rect().fit(
            render_rect.move(-render_rect.x, -render_rect.y).inflate(-5, -5)
        )
        fitted.midbottom = (render_rect.w // 2, render_rect.h - 2)
        sprite.blit(pygame.transform.smoothscale(source, fitted.size), fitted)
        sprite.fill((198, 213, 213, 255), special_flags=pygame.BLEND_RGBA_MULT)
        result.append(
            FurnitureVisual(
                f"cover-art-{index}",
                tile,
                rect,
                render_rect,
                sprite,
                cast_shadow(sprite),
                "cover",
                (),
            )
        )
    for marker in level.markers:
        if marker.kind != "HideSpot":
            continue
        rect = pygame.Rect(marker.tile[0] * size, marker.tile[1] * size, size, size)
        render_rect = rect.copy()
        render_rect.h = round(size * 1.55)
        render_rect.bottom = rect.bottom
        sprite = pygame.Surface(render_rect.size, pygame.SRCALPHA)
        fitted = props[46].get_rect().fit(sprite.get_rect().inflate(-4, -4))
        fitted.midbottom = (render_rect.w // 2, render_rect.h - 2)
        sprite.blit(pygame.transform.smoothscale(props[46], fitted.size), fitted)
        sprite.fill((183, 206, 204, 255), special_flags=pygame.BLEND_RGBA_MULT)
        result.append(
            FurnitureVisual(
                marker.marker_id,
                marker.tile,
                rect,
                render_rect,
                sprite,
                cast_shadow(sprite),
                "recess",
                (),
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
