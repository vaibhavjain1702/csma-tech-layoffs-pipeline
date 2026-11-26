# Running and extending the analysis

A Python workflow for profiling, preprocessing, descriptive social-media analysis, manual qualitative coding, and Gephi exports. Python 3.10+ and its standard library are sufficient for the core workflow. Optional static EDA plotting uses Matplotlib. There is no web app or server.

The study examines experiences, explanations, uncertainty, support, and competing narratives about technology employment, including layoffs, hiring conditions, AI, restructuring, and economic or policy change. Separate lexical screens broaden candidate retrieval; relevance and qualitative interpretations still require review. The [research design](RESEARCH_DESIGN.md) records the project brief and research questions.

## Install

The core workflow needs only the Python standard library. The analysis, Tableau and Gephi scripts added in November need packages, pinned to the versions on the project Mac (Python 3.12) in `requirements.txt`:

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Leave out the "optional heavy NLP" block (torch, transformers) if you only want to read or re-plot results. `requirements-eda.txt` is the older plotting-only list and is unchanged.

## Run

Run commands from the project root. The review ZIP contains scripts and selected outputs, but omits raw JSON, the working database, and large full-corpus tables. Rebuilding those outputs requires the original collection in `raw/YYYY-MM/`. You can read results, use Gephi CSVs, edit supplied annotations, and run unit tests without the full collection.

```bash
# Run from the folder containing README.md
python scripts/run_pipeline.py
```

The pipeline reuses the existing profile, completed preprocessing, and unchanged screening rules, then regenerates tables, summaries, the employment reading sample, and Gephi exports. It preserves raw files and annotation working copies.

For selected stages:

```bash
python scripts/run_pipeline.py --stages analysis gephi
```

For the broader employment screens and reading sample only:

```bash
python scripts/run_pipeline.py --stages screen sample
```

## Stages

| Step | Script | Outputs |
|---|---|---|
| 1. Profile files, schema, coverage, duplicate IDs, and missing text | `profile_data.py` | `outputs/01_profile/` |
| 2. Prepare text, author keys, conversation structure, and derived fields | `preprocess_data.py` | `data/processed/reddit.sqlite`, `outputs/02_preprocessing/` |
| 3. Screen broader employment topics with inspectable matching evidence | `screen_disruption.py` | Candidate CSV, monthly counts, rule manifests |
| 4. Export flat analysis-ready tables | `export_tables.py` | `outputs/03_tables/` |
| 5. Analyze coverage, text, engagement, vocabulary, and discussions | `summarize_data.py`, `preliminary_analysis.py` | `outputs/04_analysis/` |
| Optional: plot descriptive EDA | `plot_eda.py` | `outputs/04_analysis/figures/` |
| 6. Generate a reproducible reading sample with full text and context | `sample_data.py` | `outputs/05_sample/employment/`, initial annotation CSV |
| 7. Export Gephi node/edge CSVs | `export_gephi.py` | `gephi/exports/` |
| 8. Summarize human-provided qualitative codes | `summarize_annotations.py` | `outputs/07_annotations/` |

Run individual stages after their prerequisites:

```bash
python scripts/profile_data.py       # only to create the initial index
python scripts/preprocess_data.py
python scripts/screen_disruption.py
python scripts/export_tables.py
python scripts/summarize_data.py
python scripts/preliminary_analysis.py
python scripts/sample_data.py
python gephi/scripts/export_gephi.py
```

The profile script refuses to replace an existing database unless given `--rebuild`. That option regenerates the database and requires rerunning preparation. Normal pipeline runs reuse the current dataset.

## Structure

```text
raw/YYYY-MM/                 original Arctic Shift JSON batches
scripts/                     stage scripts and shared Python helpers
data/processed/reddit.sqlite  structured working dataset
outputs/
  01_profile/                inventory, schema, counts, quality findings
  02_preprocessing/          preparation audit and build summary
  03_tables/                 main tables plus disruption_candidates.csv.gz
  04_analysis/               descriptive statistics, lexical counts, report; figures/ has static plots
  05_sample/employment/      current reading sample and context packet
  07_annotations/            human-code summaries when run
gephi/                       separate network workflow; see gephi/README.md
  input/                     user's Gephi metrics CSV
  exports/                   original node/edge CSVs and network manifests
  analysis/                  findings, tables, settings, validation, figures
  rankings/                  standalone author top-20 tables
  projects/                  saved Gephi projects and manual notes
  scripts/, tests/           network workflow code and method checks
annotations/                 current editable employment working-label CSV
docs/                        methodology, dictionary, starter SQL
tests/                       preparation, statistics, and graph checks
.cache/                      disposable stage logs and plotting caches
```

Read [the methodology](METHODOLOGY.md) and [the data dictionary](DATA_DICTIONARY.md) before interpreting outputs.

The [process and preliminary-results report](PROCESS_REPORT.md) documents completed work, current findings, verification, and the qualitative and Gephi analyses still pending.

## Load tables

The standard library can stream gzip-compressed CSVs:

```python
import csv, gzip

with gzip.open('outputs/03_tables/comments.csv.gz', 'rt', encoding='utf-8', newline='') as f:
    for comment in csv.DictReader(f):
        pass  # process one record at a time
```

If pandas is installed in your environment:

```python
import pandas as pd

posts = pd.read_csv('outputs/03_tables/posts.csv.gz', low_memory=False)
comments = pd.read_csv('outputs/03_tables/comments.csv.gz', chunksize=100_000)
```

Use SQLite for joins and large scoped analyses. Starter SQL is in `docs/explore.sql` and `docs/research_queries.sql`. `source_file` points back to the authoritative raw batch.

## Gephi

```bash
python gephi/scripts/export_gephi.py --network authors --scope keyword-comments --match direct
python gephi/scripts/export_gephi.py --network conversations --scope keyword-posts --match direct
python gephi/scripts/export_gephi.py --subreddit cscareerquestions --start 2025-01-01 --end 2026-01-01
```

Each export contains UTF-8 `nodes.csv`, `edges.csv`, and a manifest documenting scope, direction, weights, and exclusions. Author edges point replying author → parent author, weighted by reply count. Conversation edges point replying comment → parent, with weight 1.

`--match broad` expands retrieval terms. Other scopes include `candidate-threads`, `sample-threads`, and `all`. Candidate-thread exports can be large because they include other collected comments in matching discussions.

The user's Gephi metrics export is `gephi/input/authors_keyword-comments.csv`. All related material is grouped under [gephi/](../gephi/README.md). Analyze it with:

```bash
python gephi/scripts/analyze_gephi.py
```

Core analysis needs only the standard library. For four static network figures, use the existing Matplotlib environment:

```bash
.venv-eda/bin/python gephi/scripts/analyze_gephi.py --plots
```

Results, recorded settings, and source hashes are in `gephi/analysis/`. Start with [FINDINGS.md](../gephi/analysis/FINDINGS.md). The script verifies the full node set, degrees/weights, and weak/strong components against the original author export and preserves the user's centralities. It does not rerun community detection or silently normalize the centrality scores. Reported settings can be maintained in `run_settings.json` in the results folder.

## Qualitative coding

The current sample is `outputs/05_sample/employment/reading_sample.csv`, with its JSONL context packet alongside it. Edit `annotations/reading_labels_employment.csv`. Generated samples are refreshed; working copies are created only when absent and are never overwritten. Use `(kind,id)` to join labels to records; sample IDs are local to a sample.

The broader sample has 40 layoff, 40 hiring-condition, 30 AI/work-change, 20 restructuring, 20 economic/policy, 20 career-transition, and 30 nonmatching background records. Facet groups overlap in eligibility; global deduplication selects each record once and retains all its matching flags. Selection balances community, quarter, record kind, and score band. Group membership is a sampling decision, not a research finding.

Relevance values are `relevant`, `irrelevant`, `uncertain`, or blank. Separate multiple codes with semicolons. New blank fields are `experiences`, `explanations`, and `future_expectations`; the existing themes, emotions, and response-function fields remain. No qualitative labels are assigned automatically. See [the coding starter](CODING_STARTER.md).

```bash
python scripts/summarize_annotations.py
```

The balanced reading sample is exploratory; its label frequencies are not population prevalence estimates.

The superseded original layoff sample and its untouched blank working template were removed during cleanup. If needed, `python scripts/sample_data.py --focus layoffs` recreates them separately. Its small SQLite membership table remains for the existing `sample-threads` Gephi scope; the current employment pilot uses `reading_sample_employment`.

## Broader employment screens

Rules in `scripts/disruption_rules.py` screen layoffs, hiring conditions, AI/work change, restructuring, economic/policy discussion, and career transitions. AI and other contextual screens require employment language in the same title or body. URLs and line-marked body quotations are excluded. Co-occurrence can span sentences and include denials. The screens do not establish technology-worker identity, relevance, or causal explanations.

`outputs/03_tables/disruption_candidates.csv.gz` contains matching records only, keyed by `(kind,id)`, with all six flags and JSON matching evidence. Join it to the main tables for full text. Its separate `disruption_manifest.json` records the rule version, fingerprint, fields, and full-corpus scan count. `outputs/04_analysis/disruption_summary.csv` and `disruption_monthly.csv` summarize overlapping candidates within community/type/period, using all collected records as the denominator. Unmatched records may still be relevant.

The `screen` stage generates these broader outputs. Existing lexical and engagement summaries and default Gephi exports retain their layoff scope. External events and indicators are a later extension.

## EDA figures

Five static figures show monthly collection coverage, body availability, direct layoff shares, broader candidate counts, and saved-score distributions. Each has a PNG and vector SVG, with interpretation notes and source provenance in `outputs/04_analysis/figures/`. Read [EDA_NOTES.md](../outputs/04_analysis/figures/EDA_NOTES.md) for the figures and their preliminary insights.

An isolated `.venv-eda` environment has been prepared for plotting. To regenerate the figures:

```bash
.venv-eda/bin/python scripts/run_pipeline.py --stages plots
```

For a fresh setup:

```bash
python -m venv .venv-eda
.venv-eda/bin/python -m pip install -r requirements-eda.txt
.venv-eda/bin/python scripts/plot_eda.py
```

The `plots` stage is optional and is omitted from the default core pipeline. Regenerate it after updating analysis inputs. These are descriptive plots; inferential tests, human qualitative coding, and Gephi graph analysis are separate work.

## Collector (Arctic Shift)

The collector code and its provenance record are in `collection/`. To collect again, copy that folder first and follow [`collection/docs/RUNBOOK.md`](../collection/docs/RUNBOOK.md); do **not** run it inside `collection/` (it writes checkpoints and `data/` next to its code). The team decided not to collect more data, so this is only needed to reproduce the October collection. `python3 collection/verify_raw_timeline.py` (read-only) re-checks the timeline of an existing `raw/` folder. See [`collection/README.md`](../collection/README.md) and `collection/PROVENANCE.md`.

## Gephi projects (headless Gephi Toolkit)

`gephi/toolkit/run.sh MODE` compiles and runs `gephi/toolkit/src/GephiRun.java` against the Gephi Toolkit 0.11.4 jar (it downloads the jar if missing and checks its SHA-256). It needs a JDK 17+ (tested with JDK 23). Modes `type`, `authors`, `r4`, `conv` and `verify` are described at the top of `run.sh`. **Do not re-run `authors`, `r4`, `conv` or `all` casually**: Modularity and ForceAtlas2 are not bit-for-bit repeatable and these modes overwrite `gephi/projects/`, `gephi/figures/` and `gephi/stats/`. `./run.sh verify` does not change any project: it re-opens the saved projects, prints their node and edge counts. The saved output of a run is in `gephi/stats/run_verify.log`. To rebuild PNGs and slides from the PDFs: `python -B gephi/toolkit/pdf_to_png.py 4000 gephi/figures/<name>.pdf` (needs `pymupdf`, see `requirements.txt`), then `python -B gephi/toolkit/make_slides.py` (needs Pillow). Details: [`gephi/projects/analysis_notes.md`](../gephi/projects/analysis_notes.md).

## Tableau workbook

```bash
python3 -B tableau/build_workbook.py    # rebuilds tableau/CSMA_Solidarity_or_Blame.twb and .twbx from outputs/16_tableau/
python3 -B tableau/validate_twb.py      # structural checks; rewrites tableau/EXPECTED_VALUES.md
```

The output is deterministic. Rebuilding overwrites any edits saved from the Tableau GUI. See [`tableau/README.md`](../tableau/README.md).

## Human label check

After the coder files in `annotations/human_check/` are filled in (see [`HUMAN_CHECK_GUIDE.md`](HUMAN_CHECK_GUIDE.md)):

```bash
python3 scripts/score_human_check.py
```

It reads the coder files and `outputs/12_replies/check_sheet.csv` and writes precision, agreement and a summary to `outputs/18_human_check/`. Its tests are in `tests/test_score_human_check.py`.

## Verify

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s gephi/tests -v
python scripts/validate_outputs.py
```

On 26 Nov 2026 `tests/` had 34 tests (15 in `test_research.py` and the rest for the human-check scorer; it needs pandas and openpyxl) and `gephi/tests` had 3.

Collection settings and the reasons for the coverage gaps are documented in `collection/PROVENANCE.md`. The actual data includes broader discussion; keyword matches are retrieval flags rather than validated relevance. Community coverage changes over time, and missing conversation context is retained explicitly.

## Directory cleanup

Cleanup on 5 October 2026 reclaimed approximately 620 MiB by removing superseded sample files, obsolete logs, bytecode/font caches, empty annotation-summary outputs, and unused SQLite storage. Current stage logs live in `.cache/logs/`; plotting caches use `.cache/matplotlib/`. Annotation summaries are regenerated when manual codes are available. SQLite integrity and row counts, all 15 tests, and full output validation passed after cleanup. The raw collection, active labels, analysis-ready tables, EDA figures, Gephi exports, scripts, tests, and research documentation remain the project assets.
