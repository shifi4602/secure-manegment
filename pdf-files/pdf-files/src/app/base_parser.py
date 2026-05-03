from __future__ import annotations

import re
from abc import abstractmethod
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pdfplumber

from src.domain.interfaces import IParser
from src.domain.models import AttendanceReport, ReportSummary, ReportType, WorkDay

# Shared regex and lookup table used by all parsers.
_DATE_RE = re.compile(r"(\d{1,2})[/.](\d{1,2})[/.](\d{2,4})")

_HEB_WEEKDAY: dict[str, int] = {
    "ראשון": 6, "שני": 0, "שלישי": 1, "רביעי": 2,
    "חמישי": 3, "שישי": 4, "שבת": 5,
}


class BaseParser(IParser):
    """
    Template Method base for all attendance-report parsers.

    Algorithm skeleton — concrete steps run in this order inside parse():
      1. _get_rows       — extract rows from the PDF        [concrete, overrideable]
      2. _rows_to_days   — convert rows → WorkDay list      [abstract]
      3. _build_summary  — summarise the WorkDay list       [abstract]
      4. Assemble and return AttendanceReport               [concrete, final]

    Adding a new report type only requires:
      • Subclassing BaseParser
      • Implementing the four @abstractmethod steps
      • Optionally overriding _get_rows / _is_data_row when extraction differs

    Shared infrastructure (_extract_table_rows, _is_data_row hook,
    _find_weekday, _parse_dec, _month_year) is inherited unchanged.
    """

    # ── Template method (the skeleton) ────────────────────────────────────────

    def parse(self, text: str, pdf_path: Path) -> AttendanceReport:
        rows    = self._get_rows(text, pdf_path)
        days    = self._rows_to_days(rows, text, pdf_path)
        summary = self._build_summary(days, text)
        month, year = self._month_year(days, text)
        return AttendanceReport(
            report_type=self._report_type(),
            employee_name=self._employee_name(text),
            month=month,
            year=year,
            days=days,
            summary=summary,
        )

    # ── Shared concrete steps ──────────────────────────────────────────────────

    def _get_rows(self, text: str, pdf_path: Path) -> list[list[str]]:
        """Prefer pdfplumber structured rows; fall back to text-derived rows."""
        rows = self._extract_table_rows(pdf_path)
        if not rows:
            rows = self._text_to_rows(text)
        return rows

    def _extract_table_rows(self, pdf_path: Path) -> list[list[str]]:
        """Extract data rows from the PDF using pdfplumber."""
        rows: list[list[str]] = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    for table in page.extract_tables():
                        for row in table:
                            cells = [c or "" for c in row]
                            if self._is_data_row(" ".join(cells)):
                                rows.append(cells)
        except Exception:
            pass
        return rows

    def _is_data_row(self, row_str: str) -> bool:
        """
        Hook: return True when row_str looks like an attendance data row.

        Default: any row that contains a full DD/MM/YYYY date.
        Subclasses may override to add type-specific heuristics.
        """
        return bool(_DATE_RE.search(row_str))

    @staticmethod
    def _month_year(days: list[WorkDay], text: str = "") -> tuple[int, int]:  # noqa: ARG004
        real = [d for d in days if d.date.year > 1900]
        if real:
            return real[0].date.month, real[0].date.year
        return 1, 2022

    def _employee_name(self, text: str) -> str:  # noqa: ARG002
        """Return the employee name extracted from the report header.
        Override per parser type."""
        return ""

    @staticmethod
    def _find_weekday(row_str: str) -> int | None:
        for heb, wd in _HEB_WEEKDAY.items():
            if heb in row_str:
                return wd
        return None

    @staticmethod
    def _parse_dec(s: str) -> Decimal:
        try:
            return Decimal(re.sub(r"[^\d.]", "", s))
        except InvalidOperation:
            return Decimal("0")

    # ── Abstract steps (each subclass fills these in) ─────────────────────────

    @abstractmethod
    def _report_type(self) -> ReportType:
        """Return the ReportType this parser handles."""

    @abstractmethod
    def _text_to_rows(self, text: str) -> list[list[str]]:
        """Convert raw OCR/extracted text into a list of cell-token rows."""

    @abstractmethod
    def _rows_to_days(
        self, rows: list[list[str]], text: str, pdf_path: Path
    ) -> list[WorkDay]:
        """Convert extracted rows into a final, ordered list of WorkDay objects."""

    @abstractmethod
    def _build_summary(self, days: list[WorkDay], text: str) -> ReportSummary:
        """Compute the ReportSummary for the finalised list of WorkDays."""
