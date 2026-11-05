"""Read-only report retrieval with strict attempt matching; never calculates a score."""

from echo_heist.core.contracts.experience.model import ResultRequest, RunReport
from echo_heist.core.contracts.experience.ports import ExperienceGateway, ExperienceUnavailable
from echo_heist.core.contracts.results import RunResult


class ReportState:
    def __init__(self, gateway: ExperienceGateway | None) -> None:
        self.gateway = gateway
        self.request: ResultRequest | None = None
        self.report: RunReport | None = None
        self.notice = ""

    def capture(self, request: ResultRequest, terminal: RunResult | None = None) -> None:
        self.request, self.report, self.notice = request, None, ""
        try:
            if self.gateway is not None:
                report = self.gateway.report(request)
            elif terminal is not None:
                report = RunReport(
                    request.run_key,
                    request.map_id,
                    terminal,
                    request.ticks_per_second,
                    request.tools,
                )
            else:
                report = None
            if report is not None and not report.matches(request):
                raise ExperienceUnavailable("The score report belongs to a different attempt.")
            self.report = report
        except (ExperienceUnavailable, ValueError) as error:
            self.notice = str(error)

    def history(self) -> tuple[RunReport, ...]:
        if self.gateway is None:
            self.notice = "Saved reports are unavailable in this build."
            return ()
        try:
            reports = tuple(self.gateway.history())
            if len(reports) > 100 or len({r.run_key for r in reports}) != len(reports):
                raise ExperienceUnavailable("Saved report data needs recovery.")
            self.notice = ""
            return reports
        except (ExperienceUnavailable, ValueError) as error:
            self.notice = str(error)
            return ()
