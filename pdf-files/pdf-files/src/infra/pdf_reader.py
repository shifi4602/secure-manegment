from __future__ import annotations
import re
from pathlib import Path

import pdfplumber
from PIL import Image, ImageFilter, ImageEnhance

from src.domain.interfaces import IPdfReader

_DATE_PAT = re.compile(r'\d{1,2}[/.]\d{1,2}[/.]\d{2,4}')
# A monthly attendance report should contain at least this many date rows.
# If pdfplumber yields fewer, we also try OCR and use the richer result.
_MIN_EXPECTED_DATES = 15



class PdfReader(IPdfReader):
    """
    Implements IPdfReader with a two-strategy approach:

    1. pdfplumber  — fast, accurate for digital (text-based) PDFs.
    2. pdf2image + pytesseract — OCR fallback for scanned / image-based PDFs.

    Strategy selection is automatic: if pdfplumber returns non-empty text,
    it is used.  Otherwise the OCR pipeline is activated.
    """

    def __init__(self, dpi: int = 300) -> None:
        self._dpi = dpi

    # ── IPdfReader ─────────────────────────────────────────────────────────────

    def read_text(self, pdf_path: Path) -> str:
        text = self._read_with_pdfplumber(pdf_path)
        date_count = len(_DATE_PAT.findall(text))
        # Use pdfplumber result only when it contains enough date rows.
        # A partially-embedded scanned PDF may yield some text but miss most
        # rows; in that case we still run OCR and take whichever is richer.
        if text.strip() and date_count >= _MIN_EXPECTED_DATES:
            return text
        # Fallback: convert pages to images and OCR them.
        # If OCR dependencies are missing, keep the direct extraction result.
        try:
            pages = self.read_pages(pdf_path)
            ocr_text = self._ocr_pages(pages)
        except Exception:
            return text
        ocr_date_count = len(_DATE_PAT.findall(ocr_text))
        # Prefer whichever source produced more date rows
        return ocr_text if ocr_date_count > date_count else (text if text.strip() else ocr_text)

    def read_pages(self, pdf_path: Path) -> list[Image.Image]:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(str(pdf_path))
        scale = self._dpi / 72
        images = []
        for page in pdf:
            bitmap = page.render(scale=scale)
            images.append(bitmap.to_pil())
        return images

    # ── private helpers ────────────────────────────────────────────────────────

    def _read_with_pdfplumber(self, pdf_path: Path) -> str:
        lines: list[str] = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            for row in table:
                                lines.append("\t".join(cell or "" for cell in row))
                    else:
                        raw = page.extract_text(x_tolerance=3, y_tolerance=3)
                        if raw:
                            lines.append(raw)
        except Exception:
            pass
        return "\n".join(lines)

    def _ocr_pages(self, pages: list[Image.Image]) -> str:
        import ssl
        import easyocr
        import numpy as np
        # Python 3.14 on Windows may fail to verify easyocr's model download
        # certificate due to a missing Authority Key Identifier.  Patching the
        # default context for this local-only tool is acceptable.
        _orig_ctx = ssl._create_default_https_context
        ssl._create_default_https_context = ssl._create_unverified_context
        try:
            reader = easyocr.Reader(["he", "en"], gpu=False, verbose=False)
        finally:
            ssl._create_default_https_context = _orig_ctx
        results: list[str] = []
        for img in pages:
            img = img.convert("L")                          # greyscale
            img = ImageEnhance.Contrast(img).enhance(1.5)  # boost contrast
            img = img.filter(ImageFilter.SHARPEN)           # sharpen edges
            lines = reader.readtext(np.array(img), detail=0, paragraph=True)
            results.append("\n".join(lines))
        return "\n".join(results)
