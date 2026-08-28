---
id: create-pdf
type: tool
status: stable
domain: ai_os
updated: 2026-06-18
summary: "How to create, read, merge, split, and manipulate PDF files using pypdf, pdfplumber, and reportlab."
triggers: "PDF: create, merge, split, extract, watermark, OCR"
expose: true
---

# Create / Process PDF

Use this whenever the task involves a PDF file: creating a new PDF, extracting text or tables from a PDF, merging or splitting PDFs, adding watermarks, rotating pages, or OCR on scanned documents.

**Triggers:** ".pdf", "PDF", "extract from PDF", "merge PDFs", "split PDF", "create a PDF report", "read this PDF", or any task where the input or output is a PDF file.

---

## Install

```bash
pip install pypdf pdfplumber reportlab --break-system-packages
pip install pytesseract pdf2image --break-system-packages  # for OCR on scanned PDFs
```

---

## Reading a PDF

```python
from pypdf import PdfReader

reader = PdfReader("document.pdf")
print(f"Pages: {len(reader.pages)}")

text = ""
for page in reader.pages:
    text += page.extract_text()
print(text)
```

---

## Extracting text with layout (better than pypdf for structured content)

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"\n--- Page {i+1} ---")
        print(page.extract_text())
```

---

## Extracting tables

```python
import pdfplumber
import pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table:
                df = pd.DataFrame(table[1:], columns=table[0])
                all_tables.append(df)

if all_tables:
    combined = pd.concat(all_tables, ignore_index=True)
    combined.to_excel("extracted_tables.xlsx", index=False)
```

---

## Creating a new PDF (reportlab)

```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

doc = SimpleDocTemplate("report.pdf", pagesize=letter,
                        leftMargin=72, rightMargin=72, topMargin=72, bottomMargin=72)
styles = getSampleStyleSheet()
story = []

# Title
story.append(Paragraph("Report Title", styles['Title']))
story.append(Spacer(1, 12))

# Body text
story.append(Paragraph("Body paragraph here.", styles['Normal']))
story.append(Spacer(1, 12))

# Section heading
story.append(Paragraph("Section Heading", styles['Heading1']))
story.append(Paragraph("Section content.", styles['Normal']))

# Table
data = [["Header 1", "Header 2", "Header 3"],
        ["Row 1 A", "Row 1 B", "Row 1 C"],
        ["Row 2 A", "Row 2 B", "Row 2 C"]]
table = Table(data, colWidths=[150, 150, 150])
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E2761")),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F5F5F5")),
]))
story.append(table)

# Page break
story.append(PageBreak())
story.append(Paragraph("Page 2 content.", styles['Normal']))

doc.build(story)
print("Created report.pdf")
```

**Critical:** Never use Unicode subscript/superscript characters in reportlab, use `<sub>` and `<super>` XML tags inside Paragraph objects instead.

---

## Merging PDFs

```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as f:
    writer.write(f)
```

---

## Splitting a PDF

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as f:
        writer.write(f)
```

---

## Rotating pages

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()
page = reader.pages[0]
page.rotate(90)
writer.add_page(page)

with open("rotated.pdf", "wb") as f:
    writer.write(f)
```

---

## OCR on scanned PDFs

```python
import pytesseract
from pdf2image import convert_from_path

images = convert_from_path("scanned.pdf")
text = ""
for i, image in enumerate(images):
    text += f"\n--- Page {i+1} ---\n"
    text += pytesseract.image_to_string(image)

print(text)
```

---

## Password protection

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()
for page in reader.pages:
    writer.add_page(page)

writer.encrypt("userpassword", "ownerpassword")
with open("encrypted.pdf", "wb") as f:
    writer.write(f)
```

---

## Quick reference

| Task | Library | Method |
|---|---|---|
| Read text | pypdf or pdfplumber | `page.extract_text()` |
| Extract tables | pdfplumber | `page.extract_tables()` |
| Create PDF | reportlab | `SimpleDocTemplate` + `doc.build(story)` |
| Merge PDFs | pypdf | `writer.add_page()` loop |
| Split PDF | pypdf | One `PdfWriter` per page |
| Rotate pages | pypdf | `page.rotate(90)` |
| OCR scanned | pytesseract + pdf2image | Convert to image first |
| Add watermark | pypdf | `page.merge_page(watermark)` |
| Password protect | pypdf | `writer.encrypt()` |

---

## Output location

Save final files to `Ideaverse/Outputs/` or the path the user specifies. Naming: `YYYY-MM-DD - [Title].pdf`.

---

## Related

[[Maps & Manuals/Me|Me]] (Proactive file creation) | [[Maps & Manuals/Skill Map|Skill Map]] | [[System/Skills/Tools/Create Word Document|Create Word Document]]
