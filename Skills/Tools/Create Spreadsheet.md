---
id: create-spreadsheet
type: tool
status: stable
domain: ai_os
updated: 2026-06-18
summary: "How to create, edit, and analyze .xlsx spreadsheets using openpyxl (formulas and formatting) and pandas (data analysis and bulk operations)."
triggers: "spreadsheet, Excel, budget, tracker, financial model, .xlsx"
expose: claude_code
---

# Create Spreadsheet (.xlsx)

Use this whenever the task produces a spreadsheet: budgets, trackers, data tables, financial models, exports, or any tabular deliverable.

**Triggers:** "spreadsheet", "Excel", ".xlsx", "budget", "tracker", "table", "model", "export to Excel", "CSV", or any request where the deliverable is a structured tabular file.

---

## Install

```bash
pip install openpyxl pandas --break-system-packages
```

---

## Creating a new spreadsheet (openpyxl)

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, numbers
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = "Sheet1"

# Headers (bold, colored background)
headers = ["Date", "Description", "Amount", "Category"]
for col, header in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=header)
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", start_color="1E2761")
    cell.alignment = Alignment(horizontal="center")

# Data
ws.append(["2026-06-01", "Example item", 100.00, "Expense"])
ws.append(["2026-06-02", "Another item", 250.00, "Income"])

# Formula (let Excel calculate, never hardcode calculated values)
ws["C4"] = "=SUM(C2:C3)"
ws["C4"].font = Font(bold=True)

# Column widths
ws.column_dimensions["A"].width = 15
ws.column_dimensions["B"].width = 30
ws.column_dimensions["C"].width = 12
ws.column_dimensions["D"].width = 15

wb.save("output.xlsx")
print("Created output.xlsx")
```

---

## Key rules

- **Always use Excel formulas, not hardcoded Python values.** Use `=SUM(B2:B9)` not `sheet['B10'] = total`. The spreadsheet must recalculate when source data changes.
- **Zero formula errors.** Verify all cell references before saving. No `#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, `#NAME?`.
- **Use professional fonts** (Arial or Calibri) consistently throughout.
- **Cell indices are 1-based** in openpyxl (row=1, column=1 = A1).
- **Do not open with `data_only=True` and save**, formulas are permanently replaced with values.

---

## Financial model color conventions

| Color | Meaning |
|---|---|
| Blue text `0,0,255` | Hardcoded inputs users will change for scenarios |
| Black text `0,0,0` | All formulas and calculations |
| Green text `0,128,0` | Links from other worksheets in same workbook |
| Red text `255,0,0` | External links to other files |
| Yellow background `255,255,0` | Key assumptions needing attention |

```python
from openpyxl.styles import Font

# Blue input cell
ws["B5"].font = Font(color="0000FF")

# Black formula cell (default, no change needed)

# Green cross-sheet link
ws["C5"].font = Font(color="008000")
```

---

## Number formatting

```python
from openpyxl.styles.numbers import FORMAT_NUMBER_COMMA_SEPARATED1

ws["C2"].number_format = '$#,##0'           # Currency
ws["D2"].number_format = '0.0%'            # Percentage
ws["E2"].number_format = '0.0x'            # Multiple
ws["F2"].number_format = '$#,##0;($#,##0);-'  # Currency with negative in parens, zero as dash
```

---

## Editing an existing spreadsheet

```python
from openpyxl import load_workbook

wb = load_workbook("existing.xlsx")
ws = wb.active  # or wb["SheetName"]

# Read data
for row in ws.iter_rows(min_row=2, values_only=True):
    print(row)

# Modify
ws["A1"] = "Updated value"
ws.insert_rows(2)   # Insert row at position 2
ws.delete_cols(3)   # Delete column 3

# Add a sheet
new_ws = wb.create_sheet("Summary")
new_ws["A1"] = "Summary data"

wb.save("modified.xlsx")
```

---

## Data analysis with pandas

```python
import pandas as pd

# Read
df = pd.read_excel("file.xlsx")
all_sheets = pd.read_excel("file.xlsx", sheet_name=None)  # All sheets as dict

# Analyze
print(df.head())
print(df.describe())
print(df.info())

# Write
df.to_excel("output.xlsx", index=False)
```

Use pandas for: data analysis, bulk operations, filtering, grouping, merging datasets. Use openpyxl for: formatting, formulas, multi-sheet structures, Excel-specific features.

---

## Verification checklist

Before delivering any spreadsheet:
- [ ] Open the file and verify it opens without errors
- [ ] Check 2-3 sample formula references produce correct values
- [ ] Confirm no formula error codes in any cell (`#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, `#NAME?`)
- [ ] Verify column headers are clear and units are stated where needed (`Revenue ($)`, `Rate (%)`)
- [ ] Confirm row/column alignment: Excel rows are 1-indexed (DataFrame row 5 = Excel row 6)

---

## Output location

Save final files to `Ideaverse/Outputs/` or the path the user specifies. Naming: `YYYY-MM-DD - [Title].xlsx`.

---

## Related

[[Maps & Manuals/Me|Me]] (Proactive file creation) | [[Maps & Manuals/Skill Map|Skill Map]]
