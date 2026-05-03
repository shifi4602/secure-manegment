from __future__ import annotations

from decimal import Decimal

from src.domain.interfaces import IVariationEngine
from src.domain.models import AttendanceReport, ReportType


class ValidatingStrategyDecorator(IVariationEngine):
    """
    Decorator that adds pre- and post-condition validation around any
    IVariationEngine, without the wrapped strategy knowing.

    Design (interview note):
    ─────────────────────────────────────────────────────────────────────
    Implements the same IVariationEngine interface as the wrapped strategy,
    so callers never need to change.  Stackable:

        ValidatingStrategyDecorator(ValidatingStrategyDecorator(engine))

    Pre-conditions checked before calling apply():
      • The report has at least one day.
      • The wrapped engine declares it can handle the report type.

    Post-conditions checked after calling apply():
      • The result contains the same number of days as the input.
      • No original dates were removed or added.
      • total_hours in the summary (if present) is non-negative.
    ─────────────────────────────────────────────────────────────────────
    """

    def __init__(self, strategy: IVariationEngine) -> None:
        self._strategy = strategy

    # ── IVariationEngine interface ─────────────────────────────────────────────

    def can_handle(self, report_type: ReportType) -> bool:
        return self._strategy.can_handle(report_type)

    def apply(self, report: AttendanceReport) -> AttendanceReport:
        self._validate_input(report)
        result = self._strategy.apply(report)
        self._validate_output(report, result)
        return result

    # ── validation helpers ─────────────────────────────────────────────────────

    def _validate_input(self, report: AttendanceReport) -> None:
        if not report.days:
            raise ValueError(
                f"[{type(self._strategy).__name__}] Variation input has no days."
            )
        if not self._strategy.can_handle(report.report_type):
            raise ValueError(
                f"[{type(self._strategy).__name__}] Cannot handle "
                f"report type {report.report_type.value!r}."
            )

    @staticmethod
    def _validate_output(original: AttendanceReport, result: AttendanceReport) -> None:
        if len(result.days) != len(original.days):
            raise ValueError(
                f"Variation changed day count: "
                f"{len(original.days)} → {len(result.days)}."
            )

        original_dates = {d.date for d in original.days}
        result_dates   = {d.date for d in result.days}
        if original_dates != result_dates:
            missing = original_dates - result_dates
            extra   = result_dates - original_dates
            raise ValueError(
                f"Variation altered dates — missing: {missing}, extra: {extra}."
            )

        if result.summary and result.summary.total_hours < Decimal("0"):
            raise ValueError(
                f"Variation produced negative total_hours: {result.summary.total_hours}."
            )
