"""Only the active Companion's reported planned route; no inferred hidden state."""

import pygame

from echo_heist.core.contracts.autonomy.model import CompanionTrace
from echo_heist.core.contracts.results import PresentationSnapshot
from echo_heist.level.model import LevelData
from echo_heist.ui.render import theme
from echo_heist.ui.render.camera import Camera


def draw_route(
    canvas: pygame.Surface,
    level: LevelData,
    snapshot: PresentationSnapshot,
    camera: Camera,
    trace: CompanionTrace | None,
    actor_id: str,
) -> None:
    if trace is None or trace.actor_id != actor_id or trace.path_goal is None:
        return
    actor = next((actor for actor in snapshot.actors if actor.actor_id == actor_id), None)
    if actor is None:
        return
    deck = level.deck_at(actor.tile)
    size = snapshot.world_map.tile_size_px
    previous = actor.tile
    for tile in trace.path:
        on_deck = deck is None or (deck.contains(previous) and deck.contains(tile))
        if on_deck and sum(abs(a - b) for a, b in zip(previous, tile, strict=True)) <= 1:
            start = camera.to_screen(((previous[0] + 0.5) * size, (previous[1] + 0.5) * size))
            end = camera.to_screen(((tile[0] + 0.5) * size, (tile[1] + 0.5) * size))
            pygame.draw.line(canvas, theme.ACCENT_DIM, start, end, 2)
            pygame.draw.circle(canvas, theme.ACCENT, end, 3)
        previous = tile
