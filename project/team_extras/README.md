# Team extras

Working material for the team. It is **not part of the course submission**: the zips given to the teacher on 26 Nov 2026 do not contain this folder.

| Folder | What it is |
|---|---|
| `document_build/report/` | `build.py` writes the final report (`.docx`); `img/` holds the figures and Tableau crops it embeds |
| `document_build/deck/` | `build.py` writes the 16-slide deck (`.pptx`); `tabcheck/` holds the four full-resolution Tableau screenshots it crops |
| `document_build/insights_and_matrix/` | `build.py` writes the final insights (`.md`, `.docx`, `.pdf`) and the draft contribution matrix (`.docx`, `.pdf`) |
| `tableau_check_screenshots/` | Screenshots of the four dashboards taken in Tableau Desktop 2026.3 on 26 Nov 2026 (22:29–22:45 IST), when the workbook was checked. The v1 captures show an outdated "Colours:" line, fixed in the final workbook; v2 shows the redrawn R2a panel |

## Regenerating the final documents

Small wording changes are easier to make directly in the `.docx`/`.pptx` files in `deliverables/final/`. To regenerate from the scripts instead:

```bash
# from the project root, in a virtual environment with: pip install python-docx python-pptx pillow
python3 team_extras/document_build/deck/build.py                     # writes deliverables/final/*.pptx
python3 team_extras/document_build/report/build.py team_extras/document_build/report/img deliverables/final/CSMA_Final_Report_Solidarity_or_Blame.docx
python3 team_extras/document_build/insights_and_matrix/build.py      # writes the insights and the matrix draft (incl. PDFs via LibreOffice)

# PDFs of the report and deck (LibreOffice must be installed)
soffice --headless --convert-to pdf --outdir deliverables/final deliverables/final/CSMA_Final_Report_Solidarity_or_Blame.docx
soffice --headless --convert-to pdf --outdir deliverables/final deliverables/final/CSMA_Final_Presentation_Solidarity_or_Blame.pptx
```

Set `CSMA_OUT=<folder>` to write the deck or the insights somewhere else (for a test run), or `CSMA_ARCH=<project root>` if you run the deck script from another location. The scripts overwrite the files in `deliverables/final/`, including any edits made by hand.

## Still to do (team)

1. **Human label check.** Guide: `docs/HUMAN_CHECK_GUIDE.md`. Coder workbooks: `annotations/human_check/` (2 coders × 240 rows, or 4 coders split 1–120 / 121–240). Score with `python3 scripts/score_human_check.py`. Until then, results are "Supported", not "Findings", and the provisional precision figures are an AI-assisted first pass, not a human check.
2. **Confirm the contribution matrix** (`deliverables/final/CSMA_Contribution_Matrix_DRAFT.docx`).
3. **Read the handbook** before presenting: `docs/PROJECT_HANDBOOK.pdf` (page 1 has a 15-minute reading path).
