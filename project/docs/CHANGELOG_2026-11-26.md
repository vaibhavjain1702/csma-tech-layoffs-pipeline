# Changelog: 26 November 2026 (final submission day)

*Everything added or changed on the day the project zip was due (26 Nov 2026, 23:59 IST). Backups from before the changes: `Archive.zip` (full snapshot at 19:14) and `_backup_before_final_2026-11-26/` (every Archive `.md`, `.txt` and `.sql` file and the label sheets), both in the subject folder next to this folder. No result number was changed except the documented corrections in section 5. No new Reddit data was downloaded, and nothing was removed or redacted for privacy.*

## 1. New: Gephi projects and figures (`gephi/`)

Built with the **Gephi Toolkit 0.11.4** (the engine behind Gephi Desktop), run headless with JDK 23. Not yet tested in the Gephi Desktop GUI (the app on this Mac is 0.11.3).

- `gephi/projects/`: four saved projects (`author_replies.gephi`, `r4_cscq_author_types.gephi`, `type_network_lift.gephi`, `conversations.gephi`), three `.gexf` fallbacks, and `analysis_notes.md` (version, settings, statistics, captions, interpretation, how to open).
- `gephi/figures/`: PDF, PNG and SVG (no SVG for R4) of the figures, plus a `*_slide.png` version of each for the presentation.
- `gephi/stats/`: Gephi's statistics as CSVs, its HTML reports, layout settings and run logs.
- `gephi/toolkit/`: `run.sh`, `src/GephiRun.java`, `pdf_to_png.py`, `make_slides.py`, and the Toolkit jar (88 MB; `run.sh` downloads it again and checks its SHA-256 if it is left out of a zip).
- Checks: every statistic of the October author network matches the earlier Python baseline (14,507 nodes, 15,427 edges, weight 15,977, 2,199 weak components, largest 9,330 = 64.31%). All four projects were re-opened in a fresh JVM with matching counts. A separate check ran independently. Fix round after that check: regeneration defaults, empty full-network layouts, grey for the 58 small groups in the largest-component figure, and slide captions.
- Known limits: Gephi's Modularity and ForceAtlas2 are not bit-for-bit repeatable, so do not re-run `authors`, `r4`, `conv` or `all` casually. Gephi's Q = 0.27 for R4 is on the 10,778 profiled authors and is not comparable to the Louvain Q = 0.43 on all 30,976 authors.

## 2. New: Tableau workbook (`tableau/`)

- `CSMA_Solidarity_or_Blame.twbx` (open this one) and `.twb`: 11 worksheets (R1a to R5c), 4 dashboards and a story, built from 10 of the 15 extracts in `outputs/16_tableau/`.
- `build_workbook.py` (deterministic generator), `validate_twb.py` (structural checks), `EXPECTED_VALUES.md` (the numbers each view should show, recomputed with pandas), `README.md`.
- Checked by script and against Tableau's own sample workbooks; **opened and checked in Tableau Desktop 2026.3 on 26 Nov, 22:29-22:45 IST**; R2a layout, dashboard 3-4 layout and colour-key fixes followed (see `tableau/README.md`).

## 3. New: data-collection provenance (`collection/`)

- Exact copies (checked byte for byte) of the October collector code, config, 5 checkpoints, run book, QA report, requirements list, the October complete guide and the original brief PDF.
- `PROVENANCE.md`: the API and settings (Arctic Shift, full-subreddit pulls, limit 100, sort asc, no keyword filter at collection), 3 of 7 configured subreddits collected, a measured timeline over all 29,821 raw files (23 and 24 Sep 2026, two runs), the early pilot dataset, where the raw data lives, and known issues.
- `verify_raw_timeline.py` (read-only): re-derives the coverage table, the run split and the gaps from the raw files.
- `README.md`: what is in the folder and how to run the collector safely (copy it first).
- Finding: coverage differs because the collector stops silently on API errors or the run was interrupted; no logs were kept, so the cause cannot be confirmed. The team decided not to collect more data.

## 4. New: environment and human-check kit

- `requirements.txt`: exact package versions read from this Mac (Python 3.12.2). Covers `scripts/`, `gephi/scripts`, `tableau/`, `tests/` and the Gephi toolkit helpers (Pillow; optional `pymupdf`).
- Human label-check kit: `docs/HUMAN_CHECK_GUIDE.md` (guide for coders), `annotations/human_check/` (coder workbooks A to D as `.xlsx` with CSV twins), `scripts/build_human_check_workbooks.py`, `scripts/score_human_check.py` (precision, Cohen's kappa, disagreements; writes to `outputs/18_human_check/` when run) and `tests/test_score_human_check.py`. The coding is **not done yet**.
- Tests on 26 Nov: `tests/` 34 tests, `gephi/tests` 3 tests, both passing (run on a scratch copy).

## 5. Docs updated (stale text corrected)

| File | Change |
|---|---|
| `README.md` | Stage line "Final submission, 26 Nov 2026". Gephi paragraph rewritten (projects exist; the old text said the conversation network had not been analyzed). New Start-here rows (Tableau, Gephi projects and figures, collection and provenance, requirements, human check guide and kit, this changelog). "Collection settings and completeness are unknown" replaced by the documented settings and the cause of the coverage gaps. Share-ZIP note: `share/csma-review.zip` is a stale 6 Oct snapshot, superseded by the final submission zip. Layout table gained `tableau/`, `collection/`, `requirements.txt` |
| `docs/PROJECT_REFERENCE.md` | Date, stage, next action (human check using the kit), deadline and presentation date (replaced "Unknown"). Section 5: source settings now known, coverage-cause note. Section 7: 26 Nov rows. Section 8: R3 window stated (all cscq months, Jan 2025 to Sep 2026; Jan to Jun 2025 alone is 4.42% vs 1.93%, x2.29), and the "slightly more agreement" bullet corrected to "less support and no extra agreement". Section 9: collection row replaced. Section 10: #5 and #9 done, #8 superseded, new #10. New section "Application / use cases". Section 11: new files |
| `docs/PROJECT_REFERENCE_2.md` | Date. Layer 0: settings known, PROVENANCE link, cause of the gaps, open item becomes "state the limit up front". Layer 3: kit pointer. Layer 5: R3 window. Layer 6: Gephi projects and figures, and the Q comparison. "Before committing or sharing": removed "sentiment and stance work is not committed yet" and the branch note; added that the public GitHub repo `lazinWolf/csma-layoff-sentiment` reflects 26 Nov 03:15 and lacks tonight's additions. "Next steps" marked done where done. Folder table gained new folders |
| `outputs/12_replies/REPLY_NOTES.md` | Dated correction note: "Talk about executives gets agreement" is superseded (blame topics draw less support and no extra agreement; the agree marker over-fires on replies starting with "This"). Original bullets kept and marked. Data section states the window (all cscq months, Jan 2025 to Sep 2026). "11-node" corrected to "12-node (8 comment kinds incl. none + 4 reply kinds)" |
| `gephi/README.md` | New "Status (26 Nov 2026)" section at the top (what was produced, how, how to open in Gephi Desktop). Original guide kept below it; the `projects/` row updated |
| `outputs/16_tableau/TABLEAU_GUIDE.md` | Pointer to the workbook in `tableau/` |
| `outputs/README.md` | New table of related folders: `tableau/`, `gephi/projects/` and `gephi/figures/`, `collection/`, `annotations/human_check/` |
| `docs/RUNNING.md` | Install from `requirements.txt`; the collector (pointer to `collection/docs/RUNBOOK.md`); `gephi/toolkit/run.sh`; `tableau/build_workbook.py` and `validate_twb.py`; `scripts/score_human_check.py`; test counts; "collection settings remain unknown" replaced |
| `docs/CHANGELOG_2026-11-26.md` | This file |

## 5b. New: final documents (`deliverables/final/`)

- `CSMA_Final_Report_Solidarity_or_Blame` (.docx, .pdf), `CSMA_Final_Presentation_Solidarity_or_Blame` (.pptx, .pdf), `CSMA_Final_Insights` (.md, .docx, .pdf) and `CSMA_Contribution_Matrix_DRAFT` (.docx, .pdf; for the team to confirm).
- Built from the verified figures in this changelog and the project docs, then fact-checked; the checker's corrections were applied. The human label check is described as pending throughout; no agreement or kappa figure is reported.
- Task 5 in `docs/PROJECT_REFERENCE.md` (Gephi slide) is marked as done in this final build session, not by its assigned owner.

## 6. Not changed

- The database (`data/processed/*.sqlite`), `outputs/03_tables/`, every existing result table in `outputs/` (the only `outputs/` files edited are the notes and index files listed above), and the label sheets (not edited tonight) (`annotations/reading_labels_employment.csv`, `outputs/12_replies/check_sheet.csv`).
- Privacy: author keys and raw usernames are as before (the owner asked to ignore privacy for now). `collection/PROVENANCE.md` sections 8, 9 and 11 describe the state.
- The contribution matrix, the final report and the presentation (written by others).
