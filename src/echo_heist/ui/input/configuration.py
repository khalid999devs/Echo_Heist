"""Validate desktop key assignments and convert them to the existing Human adapter."""

from dataclasses import fields, replace
from functools import lru_cache

import pygame

from echo_heist.core.contracts.experience.model import DesktopPreferences, KeyAssignment
from echo_heist.ui.input.human import KeyBindings

ACTIONS = ("up", "down", "left", "right", "sprint", "interact", "echo", "emp", "melee", "crouch")
RESERVED = frozenset(
    (
        pygame.K_ESCAPE,
        pygame.K_TAB,
        pygame.K_RETURN,
        pygame.K_KP_ENTER,
        pygame.K_F2,
        pygame.K_F3,
        pygame.K_F11,
    )
)


@lru_cache(maxsize=32)
def bindings_for(preferences: DesktopPreferences) -> KeyBindings:
    changes = {entry.action: entry.keys for entry in preferences.controls}
    if not changes.keys() <= set(ACTIONS):
        raise ValueError("Unknown or reserved control action")
    for keys in changes.values():
        if set(keys) & RESERVED:
            raise ValueError("That key is reserved for menus or diagnostics")
    return replace(KeyBindings(), **changes)


def assign(preferences: DesktopPreferences, action: str, key: int) -> DesktopPreferences:
    if action not in ACTIONS or key in RESERVED or key <= 0:
        raise ValueError("Choose a gameplay key; Escape and menu keys stay fixed")
    bindings = bindings_for(preferences)
    previous = getattr(bindings, action)
    keys = (key, *(code for code in previous[1:] if code != key))
    try:
        changed = replace(bindings, **{action: keys})
    except ValueError as error:
        raise ValueError("That key is already assigned to another action") from error
    entries = tuple(
        KeyAssignment(field.name, getattr(changed, field.name))
        for field in fields(changed)
        if field.name in ACTIONS
    )
    return replace(preferences, controls=entries)


def key_label(bindings: KeyBindings, action: str) -> str:
    return pygame.key.name(getattr(bindings, action)[0]).upper()


def movement_hint(bindings: KeyBindings) -> str:
    keys = "/".join(key_label(bindings, action) for action in ("up", "left", "down", "right"))
    return (
        f"{keys} Move  {key_label(bindings, 'crouch')} Crouch  "
        f"{key_label(bindings, 'sprint')} Sprint"
    )
