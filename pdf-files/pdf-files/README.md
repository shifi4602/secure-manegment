# Attendance Report Variation Generator 📄

This project creates a realistic "alternative version" of a Hebrew employee attendance report PDF.

In simple words, it does this:
1. 📥 Reads an existing attendance PDF.
2. 🧠 Understands what type of report it is.
3. 🧾 Extracts the daily work rows into structured data.
4. ⏱️ Changes times and totals using fixed, repeatable rules.
5. 🖨️ Generates a new PDF that looks like the original report format.

The goal is to produce believable sample reports while keeping the process deterministic and consistent.

## 🎯 What Problem This Solves

If you need attendance reports for testing, demos, QA, or training, creating them manually is slow and error-prone.
This tool automates the process by reusing a real report layout and applying controlled changes to the data.

## 📌 Supported Report Types

- 🅰️ Type A: נשר כח אדם
- 🅱️ Type B: כרטיס עובד

Each type has its own parser, variation rules, and PDF generator.

## ⚙️ How It Works

Pipeline:

1. 🔎 PDF text extraction: Uses direct text extraction, and OCR as fallback for scanned documents.
2. 🏷️ Type detection: Identifies report type by Hebrew keyword matching.
3. 🧱 Parsing: Converts raw report text into structured attendance data.
4. 🎛️ Variation: Applies deterministic rules to shift entry/exit times and recalculate summaries.
5. 🧾 Generation: Writes a new PDF in the same report style.

## 🧰 Prerequisites

### 1) 🔤 Tesseract OCR (with Hebrew language data)

Download: https://github.com/UB-Mannheim/tesseract/wiki

During install, include Hebrew language support.

Default path used by the project:
`C:\Program Files\Tesseract-OCR\tesseract.exe`

### 2) 🪟 Poppler for Windows

Download: https://github.com/oschwartz10612/poppler-windows/releases

Extract so the binary folder is available at:
`C:\poppler\Library\bin`

### 3) 🔠 Hebrew font

Download Noto Sans Hebrew:
https://fonts.google.com/noto/specimen/Noto+Sans+Hebrew

Place `NotoSansHebrew-Regular.ttf` inside the `fonts/` folder.

### 4) 🛠️ Update paths if needed

If your local paths are different, edit the OCR/Poppler constants in `pdf_reader.py`.

## 📦 Installation

```bash
pip install -r requirements.txt
```

## ▶️ Usage

```bash
# Save output to the default output path
python main.py --input "C:\reports\october_2022.pdf"

# Save output to a custom file path
python main.py --input "C:\reports\report.pdf" --output "C:\output\varied.pdf"
```

## ✅ Run Tests

```bash
pytest tests/ -v
```

## 🗂️ Project Structure

| File | Responsibility |
|---|---|
| `models.py` | Domain entities: `WorkDay`, `ShiftTime`, `AttendanceReport`, enums |
| `interfaces.py` | ABCs: `IPdfReader`, `IDetector`, `IParser`, `IVariationEngine`, `IGenerator` |
| `pdf_reader.py` | PDF to text via pdfplumber; OCR fallback via pdf2image + pytesseract |
| `detector.py` | Identify Type A vs Type B by Hebrew keyword scoring |
| `parser_type_a.py` | Parse Type A report rows into structured data |
| `parser_type_b.py` | Parse Type B report rows into structured data |
| `variation_type_a.py` | Deterministic variation rules for Type A |
| `variation_type_b.py` | Deterministic variation rules for Type B |
| `generator_type_a.py` | Generate Type A PDF (ReportLab + Hebrew BiDi) |
| `generator_type_b.py` | Generate Type B PDF (ReportLab + Hebrew BiDi) |
| `container.py` | Dependency injection wiring (dependency-injector) |
| `main.py` | CLI entry point (Click) |

## 📊 Variation Rules Summary

### 🅰️ Type A

| Property | Rule |
|---|---|
| Entry time | +/- (day % 3) * 5 min; deterministic from date |
| Total hours | Preserved exactly |
| Exit time | Recalculated from new entry + total |
| Overtime | Re-classified: <=8h to 100%, 8-9h to 125%, >9h to 150% |
| Shabbat rows | Entry +/- (day % 2) * 15 min, total preserved |
| Monthly totals | Re-summed from rows |

### 🅱️ Type B

| Property | Rule |
|---|---|
| Entry time | (day % 5) - 2 minutes |
| Total hours | +/- 0.05 * (day % 3), clamped to 0.5-12h |
| Exit time | Recalculated from new entry + new total |
| Shabbat / holiday rows | Unchanged |
| Monthly total | Re-summed from rows |
| סה"כ לתשלום | new_hours * original_rate |
