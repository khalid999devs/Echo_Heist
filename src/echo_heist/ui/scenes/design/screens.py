"""Player-facing guide, companion layout and contextual post-extraction epilogue."""

import pygame

from echo_heist.level.model import LevelData
from echo_heist.ui.render import theme
from echo_heist.ui.render.autonomy.protocols import RESET_BUTTONS, draw_reset
from echo_heist.ui.render.environment.furnishings.catalogue import FurnitureVisual, draw_preview
from echo_heist.ui.render.hud import panel
from echo_heist.ui.render.layout.text import fit
from echo_heist.ui.render.surfaces.cinematic import draw_scene
from echo_heist.ui.render.theme import Fonts
from echo_heist.ui.scenes.companion.deployment import DeploymentPanel
from echo_heist.ui.scenes.design.model import PRESETS, WorkshopDraft
from echo_heist.ui.scenes.design.workshop import WORKSHOP_CONTROLS, draw_workshop, portrait
from echo_heist.ui.scenes.navigation.controls import button, hit

GUIDE_TABS = ("STEALTH", "DEFENDERS", "COMPANION", "NEXUS")
GUIDE_COPY = (
    (
        (
            "READ THE ROOM",
            "Walls block sight. A guard needs time to identify you.",
            "Break sight early. Space: two loud stuns, with 4s recovery.",
        ),
        (
            "LISTEN TO YOUR FOOTSTEPS",
            "Sprint is loud. C toggles a slower, quieter crouch.",
            "Crouch beneath open desks. Leave the low space before standing.",
        ),
    ),
    (
        (
            "SENTINEL / ACTIVE",
            "Patrols, investigates noise and searches last known positions.",
            "BFS routes around obstacles; fuzzy urgency shapes its response.",
        ),
        (
            "TRACKER / ACTIVE",
            "A* pursues actual sightings, then searches the last known area.",
            "Reports retain their original time; hidden routes stay unknown.",
        ),
    ),
    (
        (
            "PLAN YOUR APPROACH",
            "Ghost favors safety. Balanced mixes safety and progress.",
            "Rush accepts more risk. Edit the design in Workshop.",
        ),
        (
            "DECISION STACK / ACTIVE",
            "A* follows known routes; utility handles immediate danger.",
            "MCTS selects, expands, rolls out and backs up belief-based choices.",
        ),
    ),
    (
        (
            "INTERCEPTOR / ACTIVE",
            "Minimax chooses a reachable post; alpha-beta prunes branches.",
            "The robot travels there physically using legitimate sightings.",
        ),
        (
            "COORDINATION / ACTIVE",
            "NEXUS dispatches from guard reports and preserves coverage.",
            "One evidence-backed protocol can adapt; reset clears its memory.",
        ),
    ),
)
GUIDE_CONTROLS = (
    *(pygame.Rect(60 + i * 295, 170, 275, 50) for i in range(4)),
    pygame.Rect(44, 650, 130, 42),
)
LAB_CONTROLS = (
    pygame.Rect(64, 590, 240, 48),
    pygame.Rect(320, 590, 240, 48),
    pygame.Rect(44, 650, 250, 42),
)
EPILOGUE_CONTROLS = (pygame.Rect(720, 570, 470, 52),)


class SceneDesigns:
    def __init__(self, deployment: DeploymentPanel | None = None) -> None:
        self.deployment = deployment or DeploymentPanel()
        self.reset_confirmation = False
        self.reset_selected = 1
        self.draft = WorkshopDraft()
        self.robot = portrait()
        self.guide_tab = 0
        self.lab_floor = 0
        self.selected = 0
        self.notice = ""
        self.lab_pan = [0, 0]
        self.drag_point: tuple[int, int] | None = None
        self.workshop_robot = pygame.transform.smoothscale(
            self.robot, self.robot.get_rect().fit(pygame.Rect(0, 0, 158, 174)).size
        )
        self.small_robot = pygame.transform.smoothscale(
            self.robot, self.robot.get_rect().fit(pygame.Rect(0, 0, 116, 146)).size
        )

    def controls(self, scene: str) -> tuple[pygame.Rect, ...]:
        if scene == "WORKSHOP" and self.reset_confirmation:
            return RESET_BUTTONS
        return {
            "WORKSHOP": WORKSHOP_CONTROLS,
            "GUIDE": GUIDE_CONTROLS,
            "LAB": LAB_CONTROLS,
            "EPILOGUE": EPILOGUE_CONTROLS,
        }[scene]

    def handle(self, scene: str, events: list[pygame.event.Event]) -> str | None:
        if scene == "WORKSHOP" and self.reset_confirmation:
            self._reset_events(events)
            return None
        rects = self.controls(scene)
        for event in events:
            activate = False
            if scene == "LAB":
                viewport = pygame.Rect(44, 172, 774, 404)
                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and viewport.collidepoint(event.pos)
                ):
                    self.drag_point = event.pos
                    continue
                if event.type in (pygame.WINDOWFOCUSLOST, pygame.MOUSEBUTTONUP):
                    self.drag_point = None
                if event.type == pygame.MOUSEMOTION and self.drag_point is not None:
                    self.lab_pan[0] -= event.pos[0] - self.drag_point[0]
                    self.lab_pan[1] -= event.pos[1] - self.drag_point[1]
                    self.drag_point = event.pos
                    continue
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                target = hit(rects, event.pos)
                if target is not None:
                    self.selected = target
                    activate = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            elif event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
                if event.key == pygame.K_ESCAPE:
                    return (
                        "WORKSHOP" if scene == "LAB" else "MODE" if scene == "WORKSHOP" else "TITLE"
                    )
                if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_TAB):
                    self.selected = (self.selected + (-1 if event.key == pygame.K_UP else 1)) % len(
                        rects
                    )
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    activate = True
                elif (
                    scene == "WORKSHOP"
                    and 3 <= self.selected <= 6
                    and event.key in (pygame.K_LEFT, pygame.K_RIGHT)
                ):
                    self.draft.cycle(self.selected - 3, -1 if event.key == pygame.K_LEFT else 1)
            if not activate:
                continue
            i = self.selected
            if scene == "WORKSHOP":
                if i < 3:
                    self.draft.select_preset(i)
                elif i < 7:
                    self.draft.cycle(i - 3)
                elif i == 7:
                    return "LAB"
                elif i == 8:
                    if self.deployment.can_deploy:
                        return "DEPLOY"
                    self.notice = self.deployment.available.reason
                elif i == 10:
                    if self.deployment.can_reset:
                        self.reset_confirmation = True
                        self.reset_selected = 1
                        self.notice = ""
                    else:
                        self.notice = "NEXUS memory is not available to reset."
                elif i == 11:
                    self.deployment.toggle_memory()
                    self.notice = self.deployment.notice
                else:
                    return "MODE"
            elif scene == "GUIDE":
                if i == 4:
                    return "TITLE"
                self.guide_tab = i
            elif scene == "LAB":
                if i < 2:
                    self.lab_floor = i
                    self.lab_pan = [0, 0]
                else:
                    return "WORKSHOP"
            else:
                return "TITLE"
        return None

    def _reset_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            activate = False
            if event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
                if event.key == pygame.K_ESCAPE:
                    self.reset_confirmation = False
                    return
                if event.key in (
                    pygame.K_LEFT,
                    pygame.K_RIGHT,
                    pygame.K_UP,
                    pygame.K_DOWN,
                    pygame.K_TAB,
                ):
                    self.reset_selected = 1 - self.reset_selected
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    activate = True
            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                selected = hit(RESET_BUTTONS, event.pos)
                if selected is not None:
                    self.reset_selected = selected
                    activate = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            if activate:
                if self.reset_selected == 1 or self.deployment.reset():
                    self.reset_confirmation = False
                self.notice = self.deployment.notice
                return

    def draw(
        self,
        canvas: pygame.Surface,
        scene: str,
        fonts: Fonts,
        backdrop: pygame.Surface,
        extraction: pygame.Surface,
        clock_ms: int,
        reduced_motion: bool,
        level: LevelData,
        map_surface: pygame.Surface,
        furnishings: tuple[FurnitureVisual, ...],
        *,
        paint_background: bool = True,
    ) -> None:
        if paint_background:
            draw_scene(
                canvas,
                extraction if scene == "EPILOGUE" else backdrop,
                clock_ms,
                reduced_motion=reduced_motion,
                text_side="right" if scene == "EPILOGUE" else "left",
                mirror_for_text=False,
                reactor_glow=scene != "EPILOGUE",
            )
        if scene == "EPILOGUE":
            canvas.blit(
                fonts.micro.render("ENCRYPTED TRANSMISSION", True, theme.ACCENT), (720, 230)
            )
            canvas.blit(fonts.heading.render("A LARGER PATTERN", True, theme.TEXT), (716, 280))
            for i, line in enumerate(
                (
                    "Core secured. Facility control lost.",
                    "",
                    "Auxiliary archive:",
                    "Replication seed intact.",
                )
            ):
                canvas.blit(fonts.small.render(line, True, theme.MUTED), (720, 356 + i * 32))
            button(canvas, EPILOGUE_CONTROLS[0], "RETURN TO MENU", fonts, True)
            return
        title = {"WORKSHOP": "AI WORKSHOP", "GUIDE": "FIELD GUIDE", "LAB": "FACILITY VIEW"}[scene]
        canvas.blit(
            fonts.micro.render("ECHO HEIST / RESEARCH SITE A1", True, theme.ACCENT), (44, 35)
        )
        canvas.blit(fonts.title.render(title, True, theme.TEXT), (40, 68))
        if scene != "GUIDE":
            badge = (
                "CHOOSE A POLICY" if scene == "WORKSHOP" else "FACILITY PREVIEW / NO ACTIVE MISSION"
            )
            canvas.blit(fonts.micro.render(badge, True, theme.WARNING), (44, 137))
        if scene == "WORKSHOP":
            draw_workshop(
                canvas,
                fonts,
                self.workshop_robot,
                self.draft,
                self.selected,
                self.deployment,
                clock_ms=clock_ms,
                reduced_motion=reduced_motion,
            )
            if self.notice and not self.reset_confirmation:
                canvas.blit(
                    fonts.micro.render(fit(fonts.micro, self.notice, 770), True, theme.WARNING),
                    (420, 664),
                )
            if self.reset_confirmation:
                draw_reset(canvas, fonts, self.reset_selected, self.notice)
        elif scene == "GUIDE":
            for i, label in enumerate(GUIDE_TABS):
                button(
                    canvas,
                    GUIDE_CONTROLS[i],
                    label,
                    fonts,
                    self.selected == i or self.guide_tab == i,
                )
            for i, copy in enumerate(GUIDE_COPY[self.guide_tab]):
                rect = pygame.Rect(60, 250 + i * 174, 1160, 148)
                panel(canvas, rect, fill=(5, 21, 31, 230))
                canvas.blit(fonts.body.render(copy[0], True, theme.ACCENT), (82, rect.y + 22))
                for j, line in enumerate(copy[1:]):
                    canvas.blit(
                        fonts.small.render(line, True, theme.TEXT), (82, rect.y + 66 + j * 30)
                    )
            button(canvas, GUIDE_CONTROLS[4], "BACK", fonts, self.selected == 4)
        else:
            self._lab(canvas, fonts, level, map_surface, furnishings)

    def _lab(
        self,
        canvas: pygame.Surface,
        fonts: Fonts,
        level: LevelData,
        map_surface: pygame.Surface,
        furnishings: tuple[FurnitureVisual, ...],
    ) -> None:
        deck = level.decks[self.lab_floor]
        tile_px = level.static_map.tile_size_px
        bounds = pygame.Rect(
            deck.left * tile_px, deck.top * tile_px, deck.width * tile_px, deck.height * tile_px
        )
        dest = pygame.Rect(44, 172, 774, 404)
        source = pygame.Rect(0, 0, dest.w, dest.h)
        source.center = (bounds.centerx + self.lab_pan[0], bounds.centery + self.lab_pan[1])
        source.clamp_ip(bounds)
        self.lab_pan = [source.centerx - bounds.centerx, source.centery - bounds.centery]
        canvas.blit(map_surface, dest, source)
        draw_preview(canvas, furnishings, source, dest.topleft)
        pygame.draw.rect(canvas, theme.BORDER, dest, 1, border_radius=4)
        panel(canvas, pygame.Rect(60, 188, 206, 30), fill=(4, 17, 27, 240))
        canvas.blit(fonts.micro.render("DRAG TO EXPLORE", True, theme.ACCENT), (74, 196))
        panel(canvas, pygame.Rect(844, 172, 366, 470), fill=(5, 19, 29, 240))
        canvas.blit(self.small_robot, self.small_robot.get_rect(midtop=(1027, 196)))
        preset = PRESETS[self.draft.preset] if self.draft.preset >= 0 else "CUSTOM"
        for i, line in enumerate(
            (
                "ECHO / " + preset,
                "No mission deployed.",
                "",
                "Inspect the facility before deployment.",
                "Live decisions appear in F2 during play.",
                "Pause or inspect without taking control.",
            )
        ):
            canvas.blit(
                fonts.micro.render(line, True, theme.ACCENT if i == 0 else theme.MUTED),
                (866, 366 + i * 34),
            )
        for i, label in enumerate(("01 / SERVICE", "02 / RESEARCH", "BACK TO WORKSHOP")):
            button(canvas, LAB_CONTROLS[i], label, fonts, self.selected == i)
