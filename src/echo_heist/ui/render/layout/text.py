"""Bounded word wrapping and fitted labels for variable runtime explanations."""

from functools import lru_cache

import pygame


@lru_cache(maxsize=512)
def fit(font: pygame.font.Font, text: str, width: int) -> str:
    if font.size(text)[0] <= width:
        return text
    left, right = 0, len(text)
    while left < right:
        middle = (left + right + 1) // 2
        if font.size(text[:middle] + "...")[0] <= width:
            left = middle
        else:
            right = middle - 1
    return text[:left].rstrip() + "..." if left else ""


@lru_cache(maxsize=256)
def lines(font: pygame.font.Font, text: str, width: int, limit: int = 2) -> tuple[str, ...]:
    words = text.split()
    result: list[str] = []
    current = ""
    for index, word in enumerate(words):
        candidate = (current + " " + word).strip()
        if font.size(candidate)[0] > width and current:
            result.append(current)
            current = word
        else:
            current = candidate
        if len(result) == limit - 1:
            result.append(fit(font, " ".join([current, *words[index + 1 :]]), width))
            return tuple(result)
    if current:
        result.append(fit(font, current, width))
    return tuple(result[:limit])


@lru_cache(maxsize=512)
def render(font: pygame.font.Font, text: str, color: tuple[int, int, int]) -> pygame.Surface:
    """Small bounded cache; callers only blit the returned surface."""
    return font.render(text, True, color)
