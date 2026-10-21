"""Explicit RGB render targets, independent of the native display's alpha masks."""

import pygame


def opaque_surface(size: tuple[int, int]) -> pygame.Surface:
    # Cocoa can supply an alpha mask even for a flags=0 Surface. Layered alpha
    # blits then leave zero destination alpha and later sprites copy dark corners.
    # A truly opaque RGB target has no alpha channel to be accidentally cleared.
    return pygame.Surface(size, depth=32, masks=(0x00FF0000, 0x0000FF00, 0x000000FF, 0))
