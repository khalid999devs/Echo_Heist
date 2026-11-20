"""World-aligned feedback derived from committed guard views and events."""

from dataclasses import dataclass

import pygame

from echo_heist.core.contracts.results import PresentationSnapshot
from echo_heist.core.contracts.security.model import GuardState, GuardView
from echo_heist.core.contracts.world import POSITION_UNITS_PER_TILE as UNIT
from echo_heist.core.contracts.world import Tile
from echo_heist.level.model import LevelData
from echo_heist.ui.render import theme
from echo_heist.ui.render.actors.model import DEFENDER_SIZE
from echo_heist.ui.render.camera import Camera
from echo_heist.ui.render.theme import Fonts

GUARD_NAMES = {
    "guard-cargo": ("Cargo", "Cargo Sentinel"),
    "guard-core": ("Core", "Core Interceptor"),
    "guard-core-sentinel": ("Vault", "Vault Sentinel"),
    "guard-research": ("Lab", "Research Tracker"),
    "guard-security": ("Sec", "Security Sentinel"),
    "guard-service": ("Svc", "Service Sentinel"),
}
STATE_COLORS = {
    GuardState.PATROL: theme.MUTED,
    GuardState.INVESTIGATE: theme.WARNING,
    GuardState.SPOTTED: theme.WARNING,
    GuardState.CHASE: theme.DANGER,
    GuardState.SEARCH: (193, 170, 247),
    GuardState.RETURN: (128, 193, 233),
}
STATE_LABELS = {
    GuardState.PATROL: "PATROL",
    GuardState.INVESTIGATE: "CHECKING",
    GuardState.SPOTTED: "IDENTIFYING",
    GuardState.CHASE: "PURSUIT",
    GuardState.SEARCH: "SEARCHING",
    GuardState.RETURN: "RETURNING",
}


@dataclass(frozen=True, slots=True)
class CuePulse:
    tile: Tile
    kind: str
    started_ms: int


def draw_badges(
    canvas: pygame.Surface,
    level: LevelData,
    snapshot: PresentationSnapshot,
    camera: Camera,
    fonts: Fonts,
    *,
    observer_id: str | None = None,
) -> None:
    actors = {actor.actor_id: actor for actor in snapshot.actors}
    own = actors[observer_id or level.operative_id]
    deck = level.deck_at(own.tile)
    size = snapshot.world_map.tile_size_px
    for guard in snapshot.guards:
        actor = actors[guard.actor_id]
        if actor.position is None or (deck and not deck.contains(actor.tile)):
            continue
        x, y = camera.to_screen((actor.position[0] * size / UNIT, actor.position[1] * size / UNIT))
        if not canvas.get_rect().inflate(120, 260).collidepoint(x, y):
            continue
        if actor.disabled or actor.stunned:
            value, color = "DISABLED" if actor.disabled else "STUNNED", theme.DISABLED
        elif guard.state == GuardState.PATROL:
            continue  # Routine guards retain an uncluttered silhouette.
        else:
            value, color = STATE_LABELS[guard.state], STATE_COLORS[guard.state]
        label = fonts.micro.render(value, True, color)
        rect = label.get_rect(midbottom=(x, y - DEFENDER_SIZE[1] - 15)).inflate(14, 6)
        pygame.draw.rect(canvas, (6, 17, 25), rect, border_radius=4)
        pygame.draw.line(canvas, color, rect.bottomleft, rect.bottomright, 2)
        canvas.blit(label, label.get_rect(center=rect.center))


def draw_cues(
    canvas: pygame.Surface,
    level: LevelData,
    snapshot: PresentationSnapshot,
    camera: Camera,
    pulses: tuple[CuePulse, ...],
    clock_ms: int,
    *,
    observer_id: str | None = None,
) -> None:
    own = next(
        actor for actor in snapshot.actors if actor.actor_id == (observer_id or level.operative_id)
    )
    deck = level.deck_at(own.tile)
    size = snapshot.world_map.tile_size_px
    for cue in pulses:
        if deck and not deck.contains(cue.tile):
            continue
        age = clock_ms - cue.started_ms
        if not 0 <= age < 900:
            continue
        point = camera.to_screen(((cue.tile[0] + 0.5) * size, (cue.tile[1] + 0.5) * size))
        if not canvas.get_rect().inflate(80, 80).collidepoint(point):
            continue
        layer = pygame.Surface((84, 84), pygame.SRCALPHA)
        radius = 10 + round(26 * age / 900)
        color = theme.WARNING if cue.kind == "NOISE" else theme.DANGER
        pygame.draw.circle(layer, (*color, round(160 * (1 - age / 900))), (42, 42), radius, 2)
        pygame.draw.circle(layer, (*color, 150), (42, 42), 3)
        canvas.blit(layer, (point[0] - 42, point[1] - 42))


def draw_debug_path(
    canvas: pygame.Surface,
    level: LevelData,
    snapshot: PresentationSnapshot,
    camera: Camera,
    guard: GuardView,
    fonts: Fonts,
    *,
    observer_id: str | None = None,
) -> None:
    """Privileged teaching view only; never a source for controller decisions."""
    own = next(
        actor for actor in snapshot.actors if actor.actor_id == (observer_id or level.operative_id)
    )
    deck = level.deck_at(own.tile)
    size = snapshot.world_map.tile_size_px
    actor = next(actor for actor in snapshot.actors if actor.actor_id == guard.actor_id)

    def point(tile: Tile) -> tuple[int, int]:
        return camera.to_screen(((tile[0] + 0.5) * size, (tile[1] + 0.5) * size))

    def on_deck(tile: Tile) -> bool:
        return deck is None or deck.contains(tile)

    previous = actor.tile
    for tile in guard.path:
        if (
            on_deck(previous)
            and on_deck(tile)
            and sum(abs(a - b) for a, b in zip(previous, tile, strict=True)) <= 1
        ):
            pygame.draw.line(canvas, theme.ACCENT_DIM, point(previous), point(tile), 2)
            pygame.draw.circle(canvas, theme.ACCENT, point(tile), 3)
        previous = tile
    for tile in guard.search_tiles if guard.state == GuardState.SEARCH else ():
        if on_deck(tile):
            pygame.draw.circle(canvas, STATE_COLORS[GuardState.SEARCH], point(tile), 9, 1)
    markers: dict[Tile, tuple[list[str], theme.Color]] = {}
    for marker_tile, label, color in (
        (guard.last_seen_tile, "LAST SEEN", theme.MUTED),
        (guard.evidence_tile, "CUE", theme.WARNING),
        (guard.target, "GOAL", theme.ACCENT),
    ):
        if marker_tile is None or not on_deck(marker_tile):
            continue
        if marker_tile in markers:
            markers[marker_tile][0].append(label)
        else:
            markers[marker_tile] = ([label], color)
    for marker_tile, (labels, color) in markers.items():
        x, y = point(marker_tile)
        pygame.draw.polygon(canvas, color, ((x, y - 8), (x + 8, y), (x, y + 8), (x - 8, y)), 1)
        text = fonts.micro.render(" / ".join(labels), True, color)
        text_rect = text.get_rect(topleft=(x + 11, y - 7))
        if text_rect.right > canvas.get_width() - 12:
            text_rect.right = x - 11
        text_rect.clamp_ip(canvas.get_rect().inflate(-24, -24))
        if canvas.get_rect().collidepoint(x, y):
            canvas.blit(text, text_rect)
