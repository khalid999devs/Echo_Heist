"""Decode production atlases once; preserve proportions and transparent margins."""

from io import BytesIO

import pygame

from echo_heist.infrastructure.resources import resource_bytes


def image(path: str) -> pygame.Surface:
    return pygame.image.load(BytesIO(resource_bytes(path)), path)


def sprite_grid(
    path: str,
    columns: int,
    rows: int,
    size: tuple[int, int],
    *,
    row_edges: tuple[int, ...] | None = None,
    column_edges: tuple[int, ...] | None = None,
) -> tuple[pygame.Surface, ...]:
    sheet = image(path)
    frames = []
    cells = []
    for row in range(rows):
        for col in range(columns):
            left, right = (
                column_edges[col : col + 2]
                if column_edges
                else (col * sheet.get_width() // columns, (col + 1) * sheet.get_width() // columns)
            )
            top, bottom = (
                row_edges[row : row + 2]
                if row_edges
                else (row * sheet.get_height() // rows, (row + 1) * sheet.get_height() // rows)
            )
            cell = sheet.subsurface((left, top, right - left, bottom - top))
            # Atlas poses can cross a nominal cell edge by a few pixels. Keep
            # the connected figure, excluding a neighbouring boot/head fragment.
            silhouette = pygame.mask.from_surface(cell, 32).connected_component()
            clean = cell.copy()
            clean.blit(
                silhouette.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)),
                (0, 0),
                special_flags=pygame.BLEND_RGBA_MULT,
            )
            cells.append(clean)
    # One scale for the complete cycle prevents body/head size changing with
    # every lifted knee or swinging arm. Keep the authored cell pivot stable.
    bounds = [cell.get_bounding_rect(min_alpha=48) for cell in cells]
    scale = min(size[0] / max(rect.w for rect in bounds), size[1] / max(rect.h for rect in bounds))
    for cell, safe in zip(cells, bounds, strict=True):
        fitted = pygame.transform.smoothscale(
            cell.subsurface(safe), (max(1, round(safe.w * scale)), max(1, round(safe.h * scale)))
        )
        frame = pygame.Surface(size, pygame.SRCALPHA)
        frame.blit(fitted, fitted.get_rect(midbottom=(size[0] // 2, size[1])))
        frames.append(frame)
    return tuple(frames)


def clinical_props() -> tuple[pygame.Surface, ...]:
    sheet = image("assets/tiles/clinical-topdown-props.png")
    # The generated sheet uses irregular padding; explicit regions avoid
    # borrowing the edge of a neighbouring instrument.
    regions = (
        (0, 0, 535, 480),
        (540, 0, 220, 480),
        (775, 0, 479, 480),
        (35, 480, 380, 330),
        (440, 480, 330, 330),
        (780, 480, 474, 330),
        (40, 810, 280, 444),
        (350, 810, 490, 444),
        (860, 810, 394, 444),
    )
    cells = (sheet.subsurface(rect) for rect in regions)
    result = []
    for cell in cells:
        # Tighten the exported matte at decode time; source PNGs are preserved.
        mask = pygame.mask.from_surface(cell, 100).connected_component()
        for offset in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            mask = mask.overlap_mask(mask, offset)
        clean = cell.copy()
        clean.blit(
            mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)),
            (0, 0),
            special_flags=pygame.BLEND_RGBA_MULT,
        )
        result.append(clean.subsurface(clean.get_bounding_rect(min_alpha=32)))
    return tuple(result)


def laboratory_props() -> tuple[pygame.Surface, ...]:
    sheet = image("assets/tiles/laboratory-props.png")
    regions = (
        (0, 0, 615, 515),
        (630, 0, 285, 515),
        (940, 0, 596, 515),
        (50, 515, 430, 509),
        (540, 515, 450, 509),
        (1000, 515, 536, 509),
    )
    cells = (sheet.subsurface(rect) for rect in regions)
    return tuple(cell.subsurface(cell.get_bounding_rect(min_alpha=24)) for cell in cells)


def research_props() -> tuple[pygame.Surface, ...]:
    """Measured transparent source regions; keep large equipment fully inside its crop."""
    kits = (
        (
            "instruments",
            (
                (0, 0, 455, 480),
                (455, 0, 600, 480),
                (1055, 0, 481, 480),
                (40, 480, 400, 544),
                (465, 480, 565, 544),
                (1030, 480, 506, 544),
            ),
        ),
        (
            "utility",
            (
                (0, 0, 520, 490),
                (520, 0, 535, 490),
                (1055, 0, 481, 490),
                (0, 490, 450, 534),
                (450, 490, 560, 534),
                (1010, 490, 526, 534),
            ),
        ),
        ("dual-console", None),
        (
            "aftermath",
            (
                (0, 0, 455, 510),
                (455, 0, 630, 510),
                (1085, 0, 451, 510),
                (0, 510, 550, 514),
                (550, 510, 410, 514),
                (960, 510, 576, 514),
            ),
        ),
        ("hiding-recess", None),
    )
    result = []
    for name, regions in kits:
        sheet = image(f"assets/tiles/laboratory/{name}.png")
        cells = [sheet] if regions is None else [sheet.subsurface(rect) for rect in regions]
        for cell in cells:
            mask = pygame.mask.from_surface(cell, 64).connected_component()
            clean = cell.copy()
            clean.blit(
                mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)),
                (0, 0),
                special_flags=pygame.BLEND_RGBA_MULT,
            )
            result.append(clean.subsurface(clean.get_bounding_rect(min_alpha=32)))
    desk = image("assets/tiles/laboratory/hiding-desk.png")
    result.append(desk.subsurface(desk.get_bounding_rect(min_alpha=32)))
    return tuple(result)
