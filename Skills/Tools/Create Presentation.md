---
id: create-presentation
type: tool
status: stable
domain: ai_os
updated: 2026-06-18
summary: "How to create and edit .pptx presentations using pptxgenjs (new files) or python-pptx (editing existing), with visual QA via image conversion."
triggers: "slides, deck, presentation, pitch deck, .pptx"
expose: true
---

# Create Presentation (.pptx)

Use this whenever the task produces a slide deck or presentation.

**Triggers:** "slides", "deck", "presentation", ".pptx", "pitch deck", "slide deck", or any request to create or edit a PowerPoint file.

---

## Install

```bash
npm install -g pptxgenjs                               # for creating new presentations
pip install python-pptx --break-system-packages        # for editing existing
pip install "markitdown[pptx]" --break-system-packages # for reading/extracting text
```

---

## Creating a new presentation (pptxgenjs)

```javascript
const pptxgen = require('pptxgenjs');
const prs = new pptxgen();

// Global settings
prs.layout = 'LAYOUT_WIDE';  // 16:9 widescreen

// Title slide
const slide1 = prs.addSlide();
slide1.background = { color: "1E2761" };
slide1.addText("Presentation Title", {
  x: 0.5, y: 1.5, w: '90%', h: 1.5,
  fontSize: 44, bold: true, color: "FFFFFF", align: "center"
});
slide1.addText("Subtitle or date", {
  x: 0.5, y: 3.2, w: '90%', h: 0.8,
  fontSize: 20, color: "CADCFC", align: "center"
});

// Content slide
const slide2 = prs.addSlide();
slide2.addText("Section Title", {
  x: 0.5, y: 0.3, w: '90%', h: 0.8,
  fontSize: 32, bold: true, color: "1E2761"
});
slide2.addText([
  { text: "Key point one", options: { bullet: true, breakLine: true } },
  { text: "Key point two", options: { bullet: true, breakLine: true } },
  { text: "Key point three", options: { bullet: true } },
], {
  x: 0.5, y: 1.3, w: 5.5, h: 4,
  fontSize: 16, color: "333333", valign: "top"
});

prs.writeFile({ fileName: "output.pptx" }).then(() => console.log("Created output.pptx"));
```

Save as `create_pptx.js` and run with `node create_pptx.js`.

---

## Design rules (apply to every presentation)

**Color:** pick a bold palette specific to the topic, don't default to blue. One color dominates (60-70%), two supporting tones, one accent. Recommended palettes:

| Theme | Primary | Secondary | Accent |
|---|---|---|---|
| Midnight Executive | `1E2761` navy | `CADCFC` ice blue | `FFFFFF` white |
| Warm Terracotta | `B85042` terracotta | `E7E8D1` sand | `A7BEAE` sage |
| Charcoal Minimal | `36454F` charcoal | `F2F2F2` off-white | `212121` black |
| Teal Trust | `028090` teal | `00A896` seafoam | `02C39A` mint |

**Structure:** dark background for title and conclusion slides, light for content slides (sandwich structure).

**Every slide needs a visual element**, image, chart, icon, or shape. Text-only slides are forgettable.

**Typography:** slide title 36-44pt bold; section headers 20-24pt bold; body 14-16pt. Left-align paragraphs and lists; center only titles.

**Avoid:**
- Repeating the same layout across slides
- Plain bullet lists on white background
- Accent lines under titles (hallmark of AI-generated slides)
- Low-contrast text or icons
- Centering body text

---

## Editing an existing presentation (python-pptx)

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

prs = Presentation("existing.pptx")

# Read slide content
for i, slide in enumerate(prs.slides):
    print(f"\n--- Slide {i+1} ---")
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                print(para.text)

# Edit text in a slide
slide = prs.slides[0]
for shape in slide.shapes:
    if shape.has_text_frame:
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                if "old text" in run.text:
                    run.text = run.text.replace("old text", "new text")

# Add a new slide
layout = prs.slide_layouts[1]  # 0=title, 1=title+content
new_slide = prs.slides.add_slide(layout)
new_slide.shapes.title.text = "New Slide Title"

prs.save("modified.pptx")
```

---

## Reading presentation content

```bash
python -m markitdown presentation.pptx
```

---

## Visual QA (required for any presentation)

Convert to images and inspect before declaring done:

```bash
# Requires: LibreOffice + poppler (pdftoppm)
soffice --headless --convert-to pdf output.pptx
rm -f slide-*.jpg
pdftoppm -jpeg -r 150 output.pdf slide
ls "$PWD"/slide-*.jpg
```

Then visually inspect each slide image. Look for: overlapping elements, text overflow, uneven margins, low contrast, leftover placeholder text, inconsistent spacing, missing visual elements.

**Use a [[System/Skills/Workflows/Use Subagents|subagent]] for visual QA**, you will miss things you just wrote. A fresh perspective catches more issues.

---

## Output location

Save final files to `Ideaverse/Outputs/` or the path the user specifies. Naming: `YYYY-MM-DD - [Title].pptx`.

---

## Related

[[Maps & Manuals/Me|Me]] (Proactive file creation) | [[Maps & Manuals/Skill Map|Skill Map]] | [[System/Skills/Workflows/Use Subagents|Use Subagents]] | [[System/Skills/Tools/Create PDF|Create PDF]]
