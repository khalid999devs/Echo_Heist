"""Paused two-floor architecture, own position and public stair connections only."""

import pygame

from echo_heist.core.contracts.world import MissionPhase, Tile
from echo_heist.level.model import Deck, LevelData
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
    panel(
        canvas,
        pygame.Rect(30, 20, canvas.get_width() - 60, canvas.get_height() - 40),
        fill=(5, 16, 25, 242),
        border=theme.ACCENT_DIM,
    )
    canvas.blit(fonts.body.render("FACILITY MAP", True, theme.TEXT), (50, 35))
    canvas.blit(fonts.micro.render("PAUSED / TAB OR ESC TO RETURN", True, theme.ACCENT), (768, 43))
    world = level.static_map
    decks = level.decks or (Deck("facility", "FACILITY A1", 0, 0, world.width, world.height),)
    current = level.deck_at(tile)
    for index, deck in enumerate(decks):
        frame = pygame.Rect(50 + index * 595, 86, 570, 542)
        panel(
            canvas,
            frame,
            fill=(4, 15, 23, 215),
            border=theme.ACCENT_DIM if current == deck else theme.BORDER,
        )
        canvas.blit(
            fonts.small.render(deck.label, True, theme.ACCENT if current == deck else theme.MUTED),
            (frame.x + 16, frame.y + 10),
        )
        scale = min((frame.width - 50) / deck.width, (frame.height - 64) / deck.height)
        origin = frame.centerx - deck.width * scale / 2, frame.top + 48

        def point(
            position: tuple[float, float],
            origin: tuple[float, float] = origin,
            deck: Deck = deck,
            scale: float = scale,
        ) -> tuple[int, int]:
            return (
                round(origin[0] + (position[0] - deck.left) * scale),
                round(origin[1] + (position[1] - deck.top) * scale),
            )

        for y in range(deck.top, deck.top + deck.height):
            for x in range(deck.left, deck.left + deck.width):
                color = (
                    (48, 68, 77)
                    if world.can_walk((x, y))
                    else (47, 150, 167)
                    if (x, y) in level.glass_tiles
                    else None
                )
                if color:
                    pygame.draw.rect(
                        canvas, color, (*point((x, y)), max(1, round(scale)), max(1, round(scale)))
                    )
        for zone in level.zones:
            if not deck.contains((zone.left + zone.width // 2, zone.top + zone.height // 2)):
                continue
            center = point((zone.left + zone.width / 2, zone.top + zone.height / 2))
            zone_text = fonts.micro.render(zone.label.upper(), True, theme.MUTED)
            canvas.blit(zone_text, zone_text.get_rect(center=center))
        anchors = {obj.object_id: obj.tile for obj in world.objects}
        markers = [(anchors[level.exit_id], theme.ACCENT, "EXIT"), (tile, theme.TEXT, "YOU")]
        if phase == MissionPhase.INFILTRATE:
            markers.append((anchors[level.core_id], theme.WARNING, "CORE"))
        for location, color, label in markers:
            if not deck.contains(location):
                continue
            center = point((location[0] + 0.5, location[1] + 0.5))
            pygame.draw.circle(canvas, color, center, 5)
            text = fonts.micro.render(label, True, color)
            canvas.blit(
                text,
                text.get_rect(
                    midtop=(center[0], center[1] - 24 if label == "EXIT" else center[1] + 9)
                ),
            )
        for link in world.stairs:
            if deck.contains(link.tile):
                center = point((link.tile[0] + 0.5, link.tile[1] + 0.5))
                pygame.draw.rect(canvas, theme.ACCENT, (center[0] - 5, center[1] - 5, 10, 10), 1)
                name = "A" if "security" in link.object_id else "B"
                stair_text = fonts.micro.render(name, True, theme.ACCENT)
                canvas.blit(stair_text, (center[0] + 9, center[1] - 7))
    canvas.blit(
        fonts.micro.render(
            "A / B  Stairs     E  Change floor     SHIFT  Sprint burst", True, theme.MUTED
        ),
        (50, 653),
    )
