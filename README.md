# Solidarity or Blame: how Reddit communities discuss disruption in technology employment

Team project for **CSE3729 Computational Social Media Analysis** (BMU, Semester 7, 2026).
Team: Vanshit Ahuja, Vaibhav Jain, Tanya, Krish, Dividh Vijay.

The study compares how r/cscareerquestions, r/technology and r/programming talk about layoffs, a hard hiring market, AI and restructuring, and how other users respond: with solidarity (sympathy, advice) or with blame. It combines Reddit data collection, text screening, reply analysis, network analysis (Gephi) and visual analytics (Tableau).

## Start here (for evaluators)

| What | Where |
|---|---|
| **Final report** (PDF, 12 pages) | [`project/deliverables/final/CSMA_Final_Report_Solidarity_or_Blame.pdf`](project/deliverables/final/CSMA_Final_Report_Solidarity_or_Blame.pdf) |
| **Final presentation** (16 slides) | [`project/deliverables/final/CSMA_Final_Presentation_Solidarity_or_Blame.pptx`](project/deliverables/final/CSMA_Final_Presentation_Solidarity_or_Blame.pptx) ([PDF](project/deliverables/final/CSMA_Final_Presentation_Solidarity_or_Blame.pdf)) |
| Final insights (2 pages) | [`project/deliverables/final/CSMA_Final_Insights.pdf`](project/deliverables/final/CSMA_Final_Insights.pdf) |
| The whole project on one page: problem, data, methods, results, open tasks | [`project/docs/PROJECT_REFERENCE.md`](project/docs/PROJECT_REFERENCE.md) |
| Results as layers, from data to concepts | [`project/docs/PROJECT_REFERENCE_2.md`](project/docs/PROJECT_REFERENCE_2.md) |
| Tableau workbook (11 sheets, 4 dashboards, 1 story) | [`project/tableau/`](project/tableau/) |
| Gephi projects, figures and statistics | [`project/gephi/projects/`](project/gephi/projects/), [`project/gephi/figures/`](project/gephi/figures/) |
| How the data was collected (settings, timeline, known issues) | [`project/collection/PROVENANCE.md`](project/collection/PROVENANCE.md) |
| Midterm report and slides | [`docs/report/`](docs/report/) |
| Everything changed for the final submission | [`project/docs/CHANGELOG_2026-11-26.md`](project/docs/CHANGELOG_2026-11-26.md) |

## Repository layout

| Path | Contents |
|---|---|
| `main.py`, `src/`, `config/`, `docs/RUNBOOK.md`, `reports/` | **Data collection pipeline** (Arctic Shift collector, keyword processing, pseudonymisation, QA). Unchanged from October 2026. |
| `project/` | **The complete analysis project**: processing and analysis scripts, tests, documentation, results, Gephi and Tableau work, human label-check kit, and the midterm and final deliverables. Start with [`project/README.md`](project/README.md). |
| `docs/report/` | Midterm (Phase 2) report and slides. |
| `data/README.md` | How to obtain the data (not stored on GitHub). |

Inside `project/`:

| Folder | Contents |
|---|---|
| `scripts/`, `tests/` | Python pipeline (profiling, preprocessing, screening, exports, analyses R1–R5, network, sentiment/stance) and unit tests |
| `docs/` | Research design, methodology, data dictionary, running guide, interpretation routine, human-check guide, references |
| `outputs/` | All generated results by stage (`01_profile` … `17_sentiment_stance`), including the Tableau extracts in `16_tableau/` |
| `gephi/` | Network exports, Gephi projects (`.gephi`), figures, statistics, the headless Gephi Toolkit runner |
| `tableau/` | Packaged workbook `CSMA_Solidarity_or_Blame.twbx`, its generator and validator, expected values |
| `collection/` | Copy of the October collector with its provenance write-up |
| `annotations/` | Reading-sample labels and the human label-check coder workbooks (to be filled) |
| `deliverables/` | Midterm package and the final report, slides, insights and draft contribution matrix |

## Data

The study uses 115,213 posts and 2,859,037 comments (2,974,250 records) collected from the Arctic Shift Reddit archive:

| Community | Comments | Coverage of comments | Posts |
|---|---:|---|---:|
| r/cscareerquestions | 962,337 | Jan 2025 – 23 Sep 2026 | 0 (not collected) |
| r/technology | 1,657,900 | Jan 2025 – 9 Jun 2025 | 76,782 |
| r/programming | 238,800 | Jan 2025 – 12 Dec 2025 | 38,431 |

Comparisons between communities use the shared window January–June 2025. See [`project/collection/PROVENANCE.md`](project/collection/PROVENANCE.md) for why coverage differs.

**Not stored on GitHub** (each file is over GitHub's 100 MB per-file limit; all are in the data part of the course submission, `CSMA_Submission_Part2_Data.zip`):

| File | Size | What it is |
|---|---:|---|
| `project/data/processed/reddit.sqlite` | 3.9 GB | Working database (records, features, screens, reply edges, threads) |
| `project/outputs/03_tables/comments.csv.gz` | 462 MB | Full-corpus comment export |
| `raw_data/raw_reddit_json_2025-01_to_2026-09.zip` | 623 MB | Original Arctic Shift JSON batches (29,844 files, about 6.1 GB unzipped) |

Also left out of the public repository: the Gephi Toolkit jar (84 MB; `project/gephi/toolkit/run.sh` downloads it and checks its SHA-256), and two files of verbatim comment excerpts (`examples.txt` in `outputs/15_network/` and `outputs/17_sentiment_stance/`), which the project keeps private.

## Reproducing

```bash
# data collection (needs your own CSMA_SALT for pseudonymisation)
pip install -r requirements.txt
export CSMA_SALT="<your-own-secret-string>"
python main.py --mode full

# analysis (Python 3.12)
cd project
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python3 -m unittest discover -s tests          # 34 tests
python3 -m unittest discover -s gephi/tests    # 3 tests
```

The analysis scripts read `project/data/processed/reddit.sqlite` (read-only). Full commands: [`project/docs/RUNNING.md`](project/docs/RUNNING.md).

## Status and limitations

- **Supported, not yet "Findings".** All comment and reply types are keyword rules. Their precision has been checked provisionally by one reader; the two-coder human label check (240 rows) is prepared in [`project/docs/HUMAN_CHECK_GUIDE.md`](project/docs/HUMAN_CHECK_GUIDE.md) and pending.
- The results describe the collected corpus (three subreddits, comments only, 2025–2026). They are not population estimates and make no causal claims.
