"""Named-profile browser/editor; persistence and policy translation stay behind a port."""

from dataclasses import dataclass

import pygame

from echo_heist.core.contracts.autonomy.policy import PolicySelection
from echo_heist.core.contracts.experience.model import SavedProfile
from echo_heist.core.contracts.experience.ports import ExperienceGateway, ExperienceUnavailable
from echo_heist.ui.render import theme
from echo_heist.ui.render.hud import panel
from echo_heist.ui.render.layout.text import fit
from echo_heist.ui.render.theme import Fonts
from echo_heist.ui.scenes.navigation.controls import button, hit

PROFILE_BUTTON = pygame.Rect(920, 103, 270, 42)
PROFILE_ROWS = tuple(pygame.Rect(80, 205 + i * 71, 570, 60) for i in range(4))
PROFILE_NAME = pygame.Rect(690, 255, 490, 62)
PROFILE_ACTIONS = (
    *(pygame.Rect(690, 347 + i * 68, 490, 52) for i in range(3)),
    pygame.Rect(80, 606, 1100, 46),
)


@dataclass(slots=True)
class ProfilePanel:
    gateway: ExperienceGateway | None
    open: bool = False
    profiles: tuple[SavedProfile, ...] = ()
    selected: int = 0
    name: str = ""
    editing: bool = False
    confirm_delete: bool = False
    notice: str = ""

    def refresh(self) -> None:
        try:
            self.profiles = tuple(self.gateway.profiles()) if self.gateway else ()
            if len(self.profiles) > 32 or len({p.profile_id for p in self.profiles}) != len(
                self.profiles
            ):
                raise ExperienceUnavailable("Saved profiles need recovery.")
            self.selected = min(self.selected, max(0, len(self.profiles) - 1))
            self.notice = "" if self.gateway else "Saved profiles are unavailable in this build."
        except (ExperienceUnavailable, ValueError) as error:
            self.profiles, self.notice = (), str(error)

    def show(self) -> None:
        self.open, self.editing, self.confirm_delete = True, False, False
        self.refresh()
        pygame.key.start_text_input()

    def controls(self) -> tuple[pygame.Rect, ...]:
        return (*PROFILE_ROWS, PROFILE_NAME, *PROFILE_ACTIONS)

    def handle(
        self, events: list[pygame.event.Event], policy: PolicySelection
    ) -> PolicySelection | None:
        loaded = None
        for event in events:
            action = None
            if event.type == pygame.WINDOWFOCUSLOST:
                self.editing = self.confirm_delete = False
            elif event.type == pygame.TEXTINPUT and self.editing:
                clean = "".join(c for c in event.text if c.isprintable())
                self.name = (self.name + clean)[:24]
            elif event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
                if event.key == pygame.K_ESCAPE:
                    if self.editing or self.confirm_delete:
                        self.editing = self.confirm_delete = False
                    else:
                        self.open = False
                elif self.editing:
                    if event.key == pygame.K_a and getattr(event, "mod", 0) & (
                        pygame.KMOD_CTRL | pygame.KMOD_META
                    ):
                        self.name = ""
                    elif event.key == pygame.K_BACKSPACE:
                        self.name = self.name[:-1]
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.editing = False
                elif event.key in (pygame.K_UP, pygame.K_DOWN):
                    self.selected = (self.selected + (-1 if event.key == pygame.K_UP else 1)) % max(
                        1, len(self.profiles)
                    )
                    self.confirm_delete = False
                elif event.key == pygame.K_n:
                    self.name, self.editing = "", True
                elif event.key == pygame.K_s:
                    action = 0
                elif event.key == pygame.K_l:
                    action = 1
                elif event.key == pygame.K_DELETE or (
                    self.confirm_delete and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
                ):
                    action = 2
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                row = hit(PROFILE_ROWS, event.pos)
                if row is not None and self.selected // 4 * 4 + row < len(self.profiles):
                    self.selected = self.selected // 4 * 4 + row
                    self.confirm_delete = False
                elif PROFILE_NAME.collidepoint(event.pos):
                    self.editing = True
                else:
                    action = hit(PROFILE_ACTIONS, event.pos)
            if action == 3:
                self.open = False
            elif action is not None:
                if action != 2:
                    self.confirm_delete = False
                try:
                    chosen = self.profiles[self.selected] if self.profiles else None
                    if self.gateway is None:
                        raise ExperienceUnavailable("Saved profiles are unavailable in this build.")
                    if action == 0:
                        if not self.name.strip():
                            self.notice, self.editing = "Enter a profile name first.", True
                            continue
                        saved = self.gateway.save_profile(self.name.strip(), policy)
                        self.refresh()
                        self.selected = next(
                            (
                                index
                                for index, profile in enumerate(self.profiles)
                                if profile.profile_id == saved.profile_id
                            ),
                            self.selected,
                        )
                        self.name, self.notice = saved.name, "Profile saved."
                        self.editing = False
                    elif action == 1 and chosen:
                        loaded, self.notice, self.name = (
                            chosen.policy,
                            "Profile loaded.",
                            chosen.name,
                        )
                    elif action == 2 and chosen:
                        if not self.confirm_delete:
                            self.confirm_delete, self.notice = (
                                True,
                                "Delete this profile? Press Delete or Enter again.",
                            )
                        else:
                            self.gateway.delete_profile(chosen.profile_id)
                            self.confirm_delete = False
                            self.refresh()
                            self.notice = "Profile deleted."
                except (ExperienceUnavailable, ValueError) as error:
                    self.notice = str(error)
        if not self.open:
            pygame.key.stop_text_input()
        return loaded

    def draw(self, canvas: pygame.Surface, fonts: Fonts) -> None:
        panel(canvas, pygame.Rect(44, 60, 1192, 628), fill=(3, 13, 21, 252))
        canvas.blit(fonts.heading.render("SAVED POLICIES", True, theme.TEXT), (78, 100))
        canvas.blit(
            fonts.micro.render(
                "Load a policy or save your current configuration.", True, theme.MUTED
            ),
            (80, 154),
        )
        start = self.selected // 4 * 4
        for i, rect in enumerate(PROFILE_ROWS):
            index = start + i
            profile = self.profiles[index] if index < len(self.profiles) else None
            button(
                canvas,
                rect,
                profile.name if profile else "—",
                fonts,
                index == self.selected and profile is not None,
                enabled=profile is not None,
            )
        canvas.blit(fonts.micro.render("PROFILE NAME", True, theme.ACCENT), (690, 217))
        panel(canvas, PROFILE_NAME, border=theme.ACCENT if self.editing else theme.BORDER)
        canvas.blit(
            fonts.body.render(
                fit(fonts.body, self.name or "Click to name…", 450), True, theme.TEXT
            ),
            (710, 273),
        )
        for rect, label in zip(
            PROFILE_ACTIONS,
            (
                "S  SAVE CURRENT",
                "L  LOAD SELECTED",
                "CONFIRM DELETE" if self.confirm_delete else "DELETE SELECTED",
                "BACK",
            ),
            strict=True,
        ):
            button(
                canvas,
                rect,
                label,
                fonts,
                enabled=rect == PROFILE_ACTIONS[-1] or self.gateway is not None,
            )
        for i, row in enumerate(("ARROWS Browse   N Name   ESC Cancel", self.notice)):
            canvas.blit(
                fonts.micro.render(
                    fit(fonts.micro, row, 1080), True, theme.WARNING if i else theme.MUTED
                ),
                (80, 530 + i * 31),
            )
