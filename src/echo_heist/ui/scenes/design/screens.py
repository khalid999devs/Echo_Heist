"""Player-facing guide, companion layout and contextual post-extraction epilogue."""

import pygame

from echo_heist.level.model import LevelData
from echo_heist.ui.render import theme
from echo_heist.ui.render.hud import panel
from echo_heist.ui.render.surfaces.cinematic import draw_scene
from echo_heist.ui.render.theme import Fonts
from echo_heist.ui.scenes.design.model import PRESETS, WorkshopDraft
from echo_heist.ui.scenes.design.workshop import WORKSHOP_CONTROLS, draw_workshop, portrait
from echo_heist.ui.scenes.navigation.controls import button, hit

GUIDE_TABS = ("STEALTH", "DEFENDERS", "COMPANION", "NEXUS")
GUIDE_COPY = (
    (
        (
            "READ THE ROOM",
            "Walls block sight. A guard needs time to identify you.",
            "Break line of sight before the warning fills.",
        ),
        (
            "LISTEN TO YOUR FOOTSTEPS",
            "Sprint is quick and loud. Walk near security.",
            "Echo draws attention; EMP opens a brief escape window.",
        ),
    ),
    (
        (
            "SENTINEL / ACTIVE",
            "Patrols, investigates noise and searches last known positions.",
            "BFS routes around obstacles; fuzzy urgency shapes its response.",
        ),
        (
            "TRACKER + INTERCEPTOR / PLANNED",
            "Tracker is designed for pursuit; Interceptor controls exits.",
            "Their specialized controllers are not connected in this build.",
        ),
    ),
    (
        (
            "PLAN YOUR APPROACH",
            "Ghost favors safety. Balanced mixes safety and progress.",
            "Rush accepts more risk. Edit the design in Workshop.",
        ),
        (
            "DECISION STACK / PLANNED",
            "A* plans routes; utility scores goals; MCTS tests choices.",
            "Emergency search compares nearby escape and tool actions.",
        ),
    ),
    (
        (
            "THE FACILITY RESPONDS",
            "Recovering the Core starts lockdown.",
            "Expect quicker guards, longer searches and warning lights.",
        ),
        (
            "COORDINATION / PLANNED",
            "NEXUS will coordinate guard roles using shared reports.",
            "Persistent learning and profile storage arrive in later phases.",
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
    def __init__(self) -> None:
        self.draft = WorkshopDraft()
        self.robot = portrait()
        self.guide_tab = 0
        self.lab_floor = 0
        self.selected = 0
        self.notice = ""
        self.lab_pan = [0, 0]
        self.drag_point: tuple[int, int] | None = None
        self.small_robot = pygame.transform.smoothscale(
            self.robot, self.robot.get_rect().fit(pygame.Rect(0, 0, 116, 146)).size
        )

    def controls(self, scene: str) -> tuple[pygame.Rect, ...]:
        return {
            "WORKSHOP": WORKSHOP_CONTROLS,
            "GUIDE": GUIDE_CONTROLS,
            "LAB": LAB_CONTROLS,
            "EPILOGUE": EPILOGUE_CONTROLS,
        }[scene]

    def handle(self, scene: str, events: list[pygame.event.Event]) -> str | None:
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
                    self.notice = (
                        "AI deployment will connect after the companion controller is ready."
                    )
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
    ) -> None:
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
        title = {"WORKSHOP": "AI WORKSHOP", "GUIDE": "FIELD GUIDE", "LAB": "COMPANION VIEW"}[scene]
        canvas.blit(
            fonts.micro.render("ECHO HEIST / RESEARCH SITE A1", True, theme.ACCENT), (44, 35)
        )
        canvas.blit(fonts.title.render(title, True, theme.TEXT), (40, 68))
        if scene != "GUIDE":
            badge = "DESIGN PREVIEW / AI DEPLOYMENT NOT CONNECTED"
            canvas.blit(fonts.micro.render(badge, True, theme.WARNING), (44, 137))
        if scene == "WORKSHOP":
            draw_workshop(canvas, fonts, self.robot, self.draft, self.selected)
            if self.notice:
                canvas.blit(fonts.micro.render(self.notice, True, theme.WARNING), (420, 664))
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
            self._lab(canvas, fonts, level, map_surface)

    def _lab(
        self, canvas: pygame.Surface, fonts: Fonts, level: LevelData, map_surface: pygame.Surface
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
        pygame.draw.rect(canvas, theme.BORDER, dest, 1, border_radius=4)
        panel(canvas, pygame.Rect(60, 188, 206, 30), fill=(4, 17, 27, 240))
        canvas.blit(fonts.micro.render("DRAG TO EXPLORE", True, theme.ACCENT), (74, 196))
        panel(canvas, pygame.Rect(844, 172, 366, 470), fill=(5, 19, 29, 240))
        canvas.blit(self.small_robot, self.small_robot.get_rect(midtop=(1027, 196)))
        preset = PRESETS[self.draft.preset] if self.draft.preset >= 0 else "CUSTOM"
        for i, line in enumerate(
            (
                "ECHO / " + preset,
                "Awaiting AI controller",
                "",
                "State / Not running",
                "Route / Not calculated",
                "Decisions / No live data",
            )
        ):
            canvas.blit(
                fonts.small.render(line, True, theme.ACCENT if i == 0 else theme.MUTED),
                (866, 366 + i * 34),
            )
        for i, label in enumerate(("01 / SERVICE", "02 / RESEARCH", "BACK TO WORKSHOP")):
            button(canvas, LAB_CONTROLS[i], label, fonts, self.selected == i)
