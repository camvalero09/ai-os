---
id: create-word-document
type: tool
status: stable
domain: ai_os
updated: 2026-06-18
summary: "How to create, edit, and read .docx Word documents using docx-js (new files) or python-docx (editing existing files)."
triggers: "Word doc, report, letter, memo, CV, contract, template, .docx"
expose: false
---

# Create Word Document (.docx)

Use this whenever the task produces a Word document: reports, letters, memos, templates, CVs, contracts, or any formatted document intended for a human reader.

**Triggers:** "Word doc", "word document", ".docx", "report", "memo", "letter", "template", "CV", "contract", or any request for a professional formatted document.

---

## Install

```bash
npm install -g docx          # for creating new documents
pip install python-docx --break-system-packages   # for editing existing
pip install mammoth --break-system-packages        # for reading/extracting
```

---

## Creating a new document (docx-js)

```javascript
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
        ShadingType, PageNumber, PageBreak, LevelFormat, ExternalHyperlink,
        TableOfContents } = require('docx');
const fs = require('fs');

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 180, after: 180 }, outlineLevel: 1 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },       // US Letter (default is A4)
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }  // 1 inch
      }
    },
    headers: {
      default: new Header({ children: [new Paragraph({ children: [new TextRun("Header text")] })] })
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        children: [new TextRun("Page "), new TextRun({ children: [PageNumber.CURRENT] })]
      })] })
    },
    children: [
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Title")] }),
      new Paragraph({ children: [new TextRun("Body text here.")] }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("output.docx", buffer);
  console.log("Created output.docx");
});
```

Save as `create_doc.js` and run with `node create_doc.js`.

---

## Key rules for docx-js

- **Page size:** always set explicitly, default is A4. Use `{ width: 12240, height: 15840 }` for US Letter.
- **Never use `\n`**, use separate `Paragraph` elements.
- **Never use unicode bullets**, use `LevelFormat.BULLET` with numbering config.
- **PageBreak must be inside a Paragraph**, `new Paragraph({ children: [new PageBreak()] })`.
- **Tables need dual widths**, set `columnWidths` on the table AND `width` on each cell.
- **Always use `WidthType.DXA`**, never `WidthType.PERCENTAGE` (breaks in Google Docs).
- **Use `ShadingType.CLEAR`**, never `ShadingType.SOLID` for table cell shading.
- **Override built-in heading styles** with exact IDs: `"Heading1"`, `"Heading2"` etc.
- **Include `outlineLevel`** on heading styles, required for Table of Contents.

### Bullet lists

```javascript
const doc = new Document({
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  sections: [{ children: [
    new Paragraph({ numbering: { reference: "bullets", level: 0 },
      children: [new TextRun("Bullet item")] }),
  ]}]
});
```

### Tables

```javascript
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [4680, 4680],
  rows: [new TableRow({ children: [
    new TableCell({
      borders,
      width: { size: 4680, type: WidthType.DXA },
      shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: [new Paragraph({ children: [new TextRun("Cell text")] })]
    })
  ]})]
})
```

---

## Editing an existing document (python-docx)

```python
from docx import Document

doc = Document("existing.docx")

# Read content
for para in doc.paragraphs:
    print(para.style.name, para.text)

# Edit a paragraph
for para in doc.paragraphs:
    if "old text" in para.text:
        for run in para.runs:
            run.text = run.text.replace("old text", "new text")

# Add content
doc.add_heading("New Section", level=1)
doc.add_paragraph("New paragraph text.")

doc.save("modified.docx")
```

---

## Reading / extracting text

```python
import mammoth

with open("document.docx", "rb") as f:
    result = mammoth.extract_raw_text(f)
    print(result.value)
```

---

## Output location

Save final files to the vault's `Ideaverse/Outputs/` folder or deliver to the path the user specifies. Naming convention: `YYYY-MM-DD - [Title].docx`.

---

## Related

[[Maps & Manuals/Me|Me]] (Proactive file creation) | [[Maps & Manuals/Skill Map|Skill Map]] | [[System/Skills/Tools/Create PDF|Create PDF]]
