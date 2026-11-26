# CSMA: Technology employment disruption on Reddit

This project studies how online communities discuss layoffs, hiring difficulties, AI and changing work, restructuring, and the future of technology employment. We examine experiences, explanations, uncertainty, support, and interactions between participants.

**Current stage (final submission, 26 November 2026):** data preparation, the midterm ("Solidarity or Blame"), the exploration rounds, the Gephi network work and the Tableau workbook are done. H1–H3 have **supported** results. The one step still open is the human check of the keyword labels. The check kit is ready (see the table below); the coding itself is for the team to do.

## Start here

| What you want | Open this |
|---|---|
| **Everything on one page: problem, data, team, progress, open tasks** | [Master project reference](docs/PROJECT_REFERENCE.md) |
| **The current results, as layers from data to concepts** | [Project in layers](docs/PROJECT_REFERENCE_2.md) |
| How to turn a number into a finding (the routine we use) | [Interpretation routine](docs/INTERPRETATION_ROUTINE.md) |
| H3: what kind of comment gets what kind of reply | [Reply notes](outputs/12_replies/REPLY_NOTES.md) |
| **The human label check: how to do it (guide for coders)** | [Human check guide](docs/HUMAN_CHECK_GUIDE.md) |
| The human label check: the coder files, and the scoring script | [`annotations/human_check/`](annotations/human_check/), [`scripts/score_human_check.py`](scripts/score_human_check.py) |
| The 240 rows being checked | [`outputs/12_replies/check_sheet.csv`](outputs/12_replies/check_sheet.csv) |
| **Tableau workbook** (11 sheets, 4 dashboards, 1 story) | [`tableau/`](tableau/README.md): open `CSMA_Solidarity_or_Blame.twbx`. Numbers to compare with: `tableau/EXPECTED_VALUES.md` |
| **Gephi projects and figures** (`.gephi` files, figures, slide versions, statistics) | [`gephi/projects/`](gephi/projects/analysis_notes.md) (notes: `analysis_notes.md`), [`gephi/figures/`](gephi/figures/), [`gephi/stats/`](gephi/stats/) |
| **How the data was collected** (API, settings, timeline, why coverage differs) and the collector code | [`collection/PROVENANCE.md`](collection/PROVENANCE.md), [`collection/README.md`](collection/README.md) |
| Python packages (exact versions) | [`requirements.txt`](requirements.txt) |
| What changed on the final day | [Changelog, 26 Nov 2026](docs/CHANGELOG_2026-11-26.md) |
| What every output folder is | [outputs/README.md](outputs/README.md) |
| Midterm report and slides | [`deliverables/`](deliverables/) |
| **Final report, slides, insights, contribution matrix (draft)** | [`deliverables/final/`](deliverables/final/) |
| Network (Gephi) findings | [Author-network findings](gephi/analysis/FINDINGS.md) and the [Gephi guide](gephi/README.md) |
| Background exploration | [Language notes](outputs/10_language/LANGUAGE_NOTES.md), [dynamics notes](outputs/11_dynamics/DYNAMICS_NOTES.md) |
| Project overview as of October | [Project summary](docs/PROJECT_BRIEF.md), [process report](docs/PROCESS_REPORT.md), [research design](docs/RESEARCH_DESIGN.md) |
| Run or extend the Python workflow | [Running guide](docs/RUNNING.md) |

## Corpus facts (from the October data audit)

- **The collection is large:** 115,213 posts and 2,859,037 comments across three communities.
- **Coverage is uneven:** technology comments end in June 2025, programming comments in December 2025, and career-question comments in September 2026. Pooled trends need care.
- **Most comment text is usable:** 94.61% of comment bodies are available. Many post bodies are empty because they are link posts; titles remain available.
- **Explicit layoff language is concentrated in career discussions:** r/cscareerquestions contributes 84.90% of directly matching comments, but its original submissions are absent.
- **The broader study has material to review:** six employment-disruption screens retrieve 177,808 distinct candidates. Matching terms are retrieval aids, not confirmed themes or causes.
- **Engagement is skewed:** median scores are 1 for both record types, while means are 655.2 for posts and 13.61 for comments.

The results describe this collected corpus. The collection settings are documented in [collection/PROVENANCE.md](collection/PROVENANCE.md): Arctic Shift, full-subreddit pulls (no keyword filter), 3 of the 7 configured subreddits, run on 23–24 September 2026. The coverage differences come from the collection run: the collector stops silently on API errors, or the run was interrupted, and no logs were kept, so the exact cause cannot be confirmed. The team decided not to collect more data. Qualitative interpretations, population-level conclusions, and causal explanations have not been established.

## Files for the next research steps

**Reading and coding:** begin with `outputs/05_sample/employment/reading_sample.csv`. It contains 200 varied examples. Read `reading_packet.jsonl` alongside it when context is needed, then edit `annotations/reading_labels_employment.csv`. Join records by `(kind,id)`; multiple codes use semicolons. Current labels are blank.

**Gephi:** all related material is in [gephi/](gephi/README.md). The author network has 14,507 nodes and 15,427 directed weighted edges; the conversation network has 13,866 nodes and 13,206 reply edges. Four networks (the October author network, the R4 author-type network, the comment-kind → reply-kind "type network" and the conversation network) were built into saved Gephi projects on 26 November 2026, using the Gephi Toolkit (the engine behind Gephi Desktop) run headless. The projects are in `gephi/projects/` (four `.gephi` files, three `.gexf` fallbacks and `analysis_notes.md`), the figures and slide versions in `gephi/figures/`, and Gephi's statistics tables and reports in `gephi/stats/`. The earlier Python verification of the user's Gephi metrics export is still in [findings](gephi/analysis/FINDINGS.md). Not yet tested: opening the projects in Gephi Desktop 0.11.3 (they were saved by toolkit 0.11.4); the `.gexf` files are the fallback.

**Tableau:** the workbook is in [tableau/](tableau/README.md), built from the extracts in `outputs/16_tableau/` ([guide](outputs/16_tableau/TABLEAU_GUIDE.md)). It was generated and checked structurally by script; whether it opens cleanly in Tableau Desktop is recorded in `tableau/README.md`.

**Methods and definitions:** use [METHODOLOGY.md](docs/METHODOLOGY.md) for processing decisions and [DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) for fields and outputs.

## Share with a collaborator

The final submission is the project zip. **`share/csma-review.zip` is a stale 6 October snapshot, superseded by the final submission zip**; it does not include the November findings, so do not send it. If you ever need it again, rebuild it first. After extraction, open **`csma-review/README.md`**.

The ZIP includes the overview, research/methods reports, five corpus plots and four network plots in PNG and SVG, summary tables, candidate screen results, the current reading sample and working labels, original Gephi CSVs, the user's Gephi metrics export and its Python analysis, Python scripts, and tests. It omits raw JSON, SQLite, the large full-corpus CSVs, caches, logs, and the local Python environment. Reports document the full project; `package_manifest.json` inside the ZIP identifies exactly what the snapshot contains and omits.

To refresh the ZIP after changing results or working labels:

```bash
python scripts/build_share_package.py
```

Building the ZIP does not send or publish anything. Keep each collaborator's edited label file separately and merge coding by record key.

## Working-project layout

| Folder | Purpose |
|---|---|
| `docs/` | Research design, methods, process, coding, and running instructions |
| `outputs/` | All generated results; see [outputs/README.md](outputs/README.md) for what each folder is |
| `gephi/` | Network exports, Gephi input, network analysis/figures, guides, scripts, tests, saved projects (`projects/`), figures (`figures/`), statistics (`stats/`) and the headless toolkit (`toolkit/`) |
| `tableau/` | The Tableau workbook (`.twbx`, `.twb`), its generator and validator, and the expected numbers |
| `collection/` | The data-collection code, config and checkpoints (exact copies from October), and the provenance record |
| `annotations/` | Editable human coding |
| `scripts/`, `tests/` | Reproducible processing and checks |
| `requirements.txt` | Pinned Python packages (Python 3.12) |
| `raw/`, `data/processed/` | Original collection and structured working database; full project only. `raw/` (6.16 GB) is kept outside this folder, in the subject folder; see `collection/PROVENANCE.md` section 8 |
| `share/` | The generated collaborator ZIP |
| `.cache/`, `.venv-eda/` | Local logs/cache and optional plotting environment; excluded from sharing |

For complete processing commands and optional plotting setup, continue with the [running guide](docs/RUNNING.md).
