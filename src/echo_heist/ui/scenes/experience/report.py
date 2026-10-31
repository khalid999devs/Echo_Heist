"""Readable committed results and a read-only score/history inspection panel."""

import pygame

from echo_heist.core.contracts.experience.model import Achievement, ResultRequest, RunReport
from echo_heist.core.contracts.results import MissionEnd, RunOutcome
from echo_heist.ui.presenters.reporting import ReportState
from echo_heist.ui.render import theme
from echo_heist.ui.render.hud import panel
from echo_heist.ui.render.layout.text import fit, lines
from echo_heist.ui.render.theme import Fonts
from echo_heist.ui.scenes.navigation.controls import button, hit

RESULT_RETRY = pygame.Rect(660, 590, 552, 48)
RESULT_MENU = pygame.Rect(660, 648, 552, 48)
RESULT_STORY = pygame.Rect(660, 532, 552, 42)
RESULT_DETAILS = pygame.Rect(660, 480, 264, 40)
RESULT_NEW_SEED = pygame.Rect(940, 480, 272, 40)
REPORT_CONTROLS = (pygame.Rect(80, 610, 300, 46), pygame.Rect(900, 610, 300, 46))
ACHIEVEMENTS = {
    Achievement.GHOST: "GHOST",
    Achievement.AI_MASTER: "AI MASTER",
    Achievement.SPEEDRUNNER: "SPEEDRUNNER",
}


def label(
    canvas: pygame.Surface, fonts: Fonts, text: str, point: tuple[int, int], *, accent: bool = False
) -> None:
    canvas.blit(fonts.micro.render(text, True, theme.ACCENT if accent else theme.MUTED), point)


def draw_results(
    canvas: pygame.Surface,
    end: MissionEnd,
    fonts: Fonts,
    *,
    ticks_per_second: int,
    hovered: str | None = None,
    clock_ms: int = 0,
    autonomous: bool = False,
    request: ResultRequest | None = None,
    report: RunReport | None = None,
) -> None:
    color = (
        theme.ACCENT
        if end.outcome == RunOutcome.WIN
        else theme.DANGER
        if end.outcome == RunOutcome.CAPTURED
        else theme.WARNING
    )
    panel(canvas, pygame.Rect(640, 32, 592, 680), fill=(4, 16, 24, 224))
    label(canvas, fonts, "MISSION REPORT", (660, 52), accent=True)
    title = {
        RunOutcome.WIN: "CORE EXTRACTED",
        RunOutcome.CAPTURED: "CAPTURED",
        RunOutcome.ABORTED: "ABORTED",
    }[end.outcome]
    canvas.blit(fonts.heading.render(title, True, color), (658, 80))
    seconds = end.elapsed_ticks // max(1, ticks_per_second)
    label(canvas, fonts, "SCORE", (662, 140))
    total = str(report.result.score) if report else "—"
    canvas.blit(fonts.stat.render(total, True, theme.TEXT), (657, 157))
    if report:
        canvas.blit(fonts.stat.render(report.result.grade, True, color), (1090, 157))
        label(canvas, fonts, "RANK", (1090, 140))
    else:
        label(canvas, fonts, "Score unavailable in this build", (795, 184))
    for i, (name, value, maximum) in enumerate(
        (
            ("EXTRACTION", report.result.completion_points if report else None, 50),
            ("STEALTH", report.result.stealth_points if report else None, 40),
            ("PACE", report.result.pace_points if report else None, 10),
        )
    ):
        x = 660 + i * 186
        label(canvas, fonts, name, (x, 238))
        value_text = "—" if value is None else f"{value} / {maximum}"
        canvas.blit(fonts.body.render(value_text, True, theme.TEXT), (x, 261))
    pygame.draw.line(canvas, theme.BORDER, (660, 309), (1212, 309))
    label(canvas, fonts, f"TIME  {seconds // 60:02d}:{seconds % 60:02d}", (662, 327), accent=True)
    encounters = str(report.result.detection_encounters) if report else "—"
    label(canvas, fonts, "ENCOUNTERS  " + encounters, (940, 327))
    tools = report.tools if report else request.tools if request else None
    usage = f"Echo {tools.echo}   EMP {tools.emp}   Stun {tools.melee}" if tools else "—"
    label(canvas, fonts, "TOOLS  " + usage, (662, 362))
    label(canvas, fonts, "Tool use carries no direct score penalty.", (662, 385))
    badges = " / ".join(ACHIEVEMENTS[a] for a in report.achievements) if report else ""
    label(
        canvas,
        fonts,
        badges or ("SEED  " + str(request.seed) if request else ""),
        (662, 420),
        accent=bool(badges),
    )
    label(canvas, fonts, "D  Details     N  New seed", (662, 448))
    button(canvas, RESULT_DETAILS, "DETAILS", fonts, hovered == "DETAILS")
    button(canvas, RESULT_NEW_SEED, "NEW SEED", fonts, hovered == "NEW_SEED")
    if end.outcome == RunOutcome.WIN:
        button(canvas, RESULT_STORY, "C  ENCRYPTED TRANSMISSION", fonts, hovered == "STORY")
    button(
        canvas,
        RESULT_RETRY,
        "R  REVIEW & RETRY" if autonomous else "R  RETRY MISSION",
        fonts,
        hovered == "RETRY",
    )
    button(canvas, RESULT_MENU, "ENTER  MAIN MENU", fonts, hovered == "MENU")


class ReportInspector:
    def __init__(self, state: ReportState) -> None:
        self.state = state
        self.open = False
        self.history: tuple[RunReport, ...] = ()
        self.index = -1
        self.selected = 0

    def controls(self) -> tuple[pygame.Rect, ...]:
        return REPORT_CONTROLS

    def handle(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            activate = None
            if event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
                if event.key == pygame.K_ESCAPE:
                    self.open = False
                elif event.key in (pygame.K_LEFT, pygame.K_UP):
                    self.index = max(-1, self.index - 1)
                elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                    self.index = min(len(self.history) - 1, self.index + 1)
                elif event.key == pygame.K_h:
                    activate = 0
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    activate = 1
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                activate = hit(REPORT_CONTROLS, event.pos)
            if activate == 0:
                self.history = self.state.history()
                self.index = 0 if self.history else -1
            elif activate == 1:
                self.open = False

    def draw(self, canvas: pygame.Surface, fonts: Fonts) -> None:
        panel(canvas, pygame.Rect(44, 60, 1192, 628), fill=(3, 13, 21, 252))
        report = self.history[self.index] if self.index >= 0 else self.state.report
        label(
            canvas,
            fonts,
            "SAVED RUN" if self.index >= 0 else "CURRENT ATTEMPT",
            (80, 90),
            accent=True,
        )
        canvas.blit(fonts.heading.render("MISSION DETAILS", True, theme.TEXT), (78, 119))
        rows: tuple[str, ...]
        if report:
            r = report.result
            rows = (
                f"{r.mode} / Seed {r.seed} / {report.policy_label}",
                f"Score {r.score}   Rank {r.grade}   Encounters {r.detection_encounters}",
                f"Extraction {r.completion_points}/50   Stealth {r.stealth_points}/40   "
                f"Pace {r.pace_points}/10",
                f"Echo {report.tools.echo}   EMP {report.tools.emp}   Stun {report.tools.melee}",
                f"Scoring version {r.scoring_version} / Pace reference "
                f"{r.pace_reference_ticks // report.ticks_per_second}s",
            )
        else:
            request = self.state.request
            rows = (
                f"Seed {request.seed} / {request.mode}" if request else "No completed attempt.",
                "A score breakdown is unavailable for this attempt.",
            )
        for i, row in enumerate(rows):
            canvas.blit(
                fonts.small.render(fit(fonts.small, row, 1080), True, theme.TEXT),
                (80, 202 + i * 39),
            )
        explanatory = (
            "Confirmed encounters reduce stealth. Hearing and suspicion alone do not count. "
            "Tool use is unpenalized."
        )
        for i, row in enumerate(lines(fonts.small, explanatory, 1070, 2)):
            canvas.blit(fonts.small.render(row, True, theme.MUTED), (80, 432 + i * 28))
        label(canvas, fonts, fit(fonts.micro, self.state.notice, 1070), (80, 526))
        label(canvas, fonts, "ARROWS  Browse saved reports     ESC  Close", (80, 565))
        button(canvas, REPORT_CONTROLS[0], "H  SAVED REPORTS", fonts)
        button(canvas, REPORT_CONTROLS[1], "BACK", fonts, True)
