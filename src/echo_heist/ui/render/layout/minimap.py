"""Per-session static floor raster, invalidated by actual immutable map replacement."""

import pygame

from echo_heist.core.contracts.world import MissionPhase, StaticMap, Tile
from echo_heist.level.model import LevelData
from echo_heist.ui.render import theme
from echo_heist.ui.render.surfaces.glass import panel
from echo_heist.ui.render.theme import Fonts


class MinimapLayer:
    def __init__(self) -> None:
        self.world_map: StaticMap | None = None
        self.layers: dict[tuple[int, int, int, int], pygame.Surface] = {}

    def base(self, world_map: StaticMap, bounds: tuple[int, int, int, int]) -> pygame.Surface:
        if self.world_map is not world_map:
            self.layers.clear()
            self.world_map = world_map
        if bounds not in self.layers:
            if len(self.layers) == 8:
                self.layers.clear()
            left, top, width, height = bounds
            scale = min(148 / width, 120 / height)
            image = pygame.Surface((150, 122), pygame.SRCALPHA)
            for y in range(top, top + height):
                for x in range(left, left + width):
                    if world_map.can_walk((x, y)):
                        pygame.draw.rect(
                            image,
                            (55, 86, 96),
                            (
                                round((x - left) * scale),
                                round((y - top) * scale),
                                max(1, round(scale)),
                                max(1, round(scale)),
                            ),
                        )
            self.layers[bounds] = image
        return self.layers[bounds]


def _label(
    canvas: pygame.Surface,
    font: pygame.font.Font,
    value: str,
    color: tuple[int, int, int],
    pos: tuple[int, int],
) -> None:
    canvas.blit(font.render(value, True, color), pos)


def draw_minimap(
    canvas: pygame.Surface,
    level: LevelData,
    operative_tile: Tile,
    phase: MissionPhase,
    fonts: Fonts,
    *,
    layer: MinimapLayer | None = None,
    world_map: StaticMap | None = None,
) -> None:
    rect = pygame.Rect(20, canvas.get_height() - 202, 172, 182)
    panel(canvas, rect, fill=(5, 15, 25, 170))
    deck = level.deck_at(operative_tile)
    left, top = (deck.left, deck.top) if deck else (0, 0)
    width, height = (
        (deck.width, deck.height) if deck else (level.static_map.width, level.static_map.height)
    )
    _label(
        canvas,
        fonts.micro,
        "FLOOR 01" if deck and deck.deck_id == "ground" else "FLOOR 02" if deck else "FACILITY A1",
        theme.ACCENT,
        (32, rect.y + 9),
    )
    scale = min(148 / width, 120 / height)
    origin = rect.centerx - width * scale / 2, rect.y + 33
    source = world_map or level.static_map
    base = (layer or MinimapLayer()).base(source, (left, top, width, height))
    canvas.blit(base, (round(origin[0]), round(origin[1])))
    anchors = {obj.object_id: obj.tile for obj in level.static_map.objects}
    markers = [(anchors[level.exit_id], theme.ACCENT), (operative_tile, theme.TEXT)]
    if phase == MissionPhase.INFILTRATE:
        markers.append((anchors[level.core_id], theme.WARNING))
    for tile, color in markers:
        if deck and not deck.contains(tile):
            continue
        pygame.draw.circle(
            canvas,
            color,
            (
                round(origin[0] + (tile[0] - left + 0.5) * scale),
                round(origin[1] + (tile[1] - top + 0.5) * scale),
            ),
            3,
        )
    for link in level.static_map.stairs:
        if deck and deck.contains(link.tile):
            point = (
                round(origin[0] + (link.tile[0] - left + 0.5) * scale),
                round(origin[1] + (link.tile[1] - top + 0.5) * scale),
            )
            pygame.draw.rect(canvas, theme.ACCENT, (*point, 4, 4), 1)
    _label(canvas, fonts.micro, "TAB  Map", theme.MUTED, (32, rect.bottom - 24))
