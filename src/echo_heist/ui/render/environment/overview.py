"""Paused facility map: known architecture and own position, without enemy telemetry."""

import pygame

from echo_heist.core.contracts.world import MissionPhase, Tile
from echo_heist.level.model import LevelData
from echo_heist.ui.render import theme
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.surfaces.glass import panel
from echo_heist.ui.render.theme import Fonts


def draw_overview(
    canvas: pygame.Surface,
    level: LevelData,
    tile: Tile,
    phase: MissionPhase,
    camera: Camera,
    fonts: Fonts,
) -> None:
    small = pygame.transform.smoothscale(canvas, (160, 90))
    canvas.blit(pygame.transform.smoothscale(small, canvas.get_size()), (0, 0))
    shade = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
    shade.fill((1, 6, 12, 170))
    canvas.blit(shade, (0, 0))
    rect = pygame.Rect(30, 20, canvas.get_width() - 60, canvas.get_height() - 40)
    panel(canvas, rect, fill=(5, 16, 25, 242), border=theme.ACCENT_DIM)
    canvas.blit(fonts.body.render("FACILITY MAP", True, theme.TEXT), (50, 35))
    canvas.blit(
        fonts.micro.render("PAUSED  /  TAB OR ESC TO RETURN", True, theme.ACCENT), (770, 43)
    )
    world = level.static_map
    scale = min(850 / world.width, 552 / world.height)
    origin = 50, 79

    def point(position: tuple[float, float]) -> tuple[int, int]:
        return round(origin[0] + position[0] * scale), round(origin[1] + position[1] * scale)

    for y in range(world.height):
        for x in range(world.width):
            if world.can_walk((x, y)):
                color = (48, 68, 77)
            elif (x, y) in level.glass_tiles:
                color = (47, 150, 167)
            else:
                continue
            pygame.draw.rect(
                canvas, color, (*point((x, y)), max(1, round(scale)), max(1, round(scale)))
            )
    current = level.room_at(tile)
    for number, room in enumerate(level.rooms, 1):
        center = point((room.left + room.width / 2, room.top + room.height / 2))
        if room.style == "reactor":
            center = point((room.left + 1, room.top + 1))
        active = current == room
        color = theme.ACCENT if active else theme.MUTED
        pygame.draw.circle(canvas, (6, 22, 32), center, 10)
        text = fonts.micro.render(str(number), True, color)
        canvas.blit(text, text.get_rect(center=center))
        legend = fonts.micro.render(f"{number:02d}  {room.label}", True, color)
        canvas.blit(legend, (875, 82 + (number - 1) * 23))
    size = world.tile_size_px
    view = pygame.Rect(
        *point((camera.x / size, camera.y / size)),
        round(camera.view_width / size * scale),
        round(camera.view_height / size * scale),
    )
    pygame.draw.rect(canvas, (82, 123, 139), view, 1)
    anchors = {obj.object_id: obj.tile for obj in world.objects}
    markers = [(anchors[level.exit_id], theme.ACCENT, "EXIT"), (tile, theme.TEXT, "YOU")]
    if phase == MissionPhase.INFILTRATE:
        markers.append((anchors[level.core_id], theme.WARNING, "CORE"))
    for location, color, label in markers:
        center = point((location[0] + 0.5, location[1] + 0.5))
        pygame.draw.circle(canvas, color, center, 5)
        text = fonts.micro.render(label, True, color)
        text_rect = text.get_rect(
            midtop=(center[0], center[1] - 24 if label == "EXIT" else center[1] + 11)
        )
        canvas.blit(text, text_rect)
    controls = "WASD Move   SHIFT Sprint   E Hold at Core   Q Echo   F EMP   SPACE Stun"
    canvas.blit(fonts.micro.render(controls, True, theme.MUTED), (50, 655))
