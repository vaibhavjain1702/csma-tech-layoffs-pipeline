# collection/ - the data-collection code

This folder is the **provenance record** of how the Reddit data was collected. It holds exact copies (checked byte for byte with `cmp` on 26 Nov 2026) of the code, configuration and checkpoints from the October `Project/` folder. The code is not edited; known problems are listed in `PROVENANCE.md`, section 11.

Start with **`PROVENANCE.md`**: what was collected, the API used, coverage gaps, the collection timeline, and why r/cscareerquestions has no posts and the r/technology and r/programming comments end early.

## What is here

| Path | What it is |
|---|---|
| `PROVENANCE.md` | Evidence-based account of the collection (read this first) |
| `verify_raw_timeline.py` | New, read-only script that re-derives the timeline and coverage tables from the raw files |
| `main.py` | Entry point: `--mode smoke|collect|process|qa|full` |
| `src/collector.py` | `ArcticShiftCollector`: calls `posts/search` and `comments/search`, writes `data/raw/YYYY-MM/*_batch_<epoch-ms>.json`, keeps checkpoints |
| `src/processor.py` | Keyword filter, normalisation and de-duplication into `data/processed/posts.csv` and `comments.csv` (used for the small pilot only) |
| `src/privacy.py` | Salted SHA-256 hashing of author names (pilot only; the Archive uses its own `author_key`) |
| `src/qa.py`, `src/orchestrator.py`, `src/utils.py` | QA report, mode dispatcher, config and logging helpers |
| `config/collection_config.yaml` | 7 configured subreddits (3 collected), date range 2025-01-01 to 2026-12-31, 23 keywords (pilot only), rate limits |
| `checkpoints/*.json` | The 5 checkpoints left at the end of collection (cscareerquestions has no posts checkpoint) |
| `docs/RUNBOOK.md` | The original run instructions |
| `reports/QA_REPORT.md` | QA output of the pilot dataset (4,376 posts, 1,915 comments) |
| `requirements-collection.txt` | The original unpinned package list (note: `tqdm`, `duckdb`, `pyarrow` are not imported by any of the code) |
| `CSMA_Project_Complete_Guide.md` | The October guide to the whole project, including the collection role |
| `Documents/CSMA_Tech_Layoffs_Agentic_Reddit_Data_Collection_Prompt.pdf` | The original brief used to set up the collection |

Not included, on purpose: `venv/`, `data/` (the raw JSON, 6.16 GB, is kept outside the Archive folder; see `PROVENANCE.md` section 8 for where) and `logs/` (it was empty: no log file was ever written).

## How to run it (only if you really want to collect again)

**Do not run it inside this folder.** The scripts resolve every path from their own location (`src/utils.py:get_project_root`), so running here would overwrite the shipped checkpoints and `reports/QA_REPORT.md` and create `data/` inside the submission. Copy the folder first:

```
cp -R collection /tmp/csma_collect && cd /tmp/csma_collect
python3 -m venv venv && source venv/bin/activate
pip install requests pyyaml pandas          # the three packages the code actually imports
export CSMA_SALT="<your own secret string>"  # only needed for the privacy step
python main.py --mode smoke                  # tiny test: one batch of 10 posts and one of 10 comments for the first subreddit, then process, privacy and QA
python main.py --mode collect                # full collection, resumes from checkpoints/ if present
```

The steps and modes are described in `docs/RUNBOOK.md`. Remarks:

- Run from the folder that contains `config/` (the config path is relative, `src/utils.py:6`).
- To start from scratch, delete the copied `checkpoints/*.json`. With the shipped checkpoints a run continues from the points where the original run ended (r/technology comments from 2025-06-09, r/programming comments from 2025-12-12), which is the way to finish the missing comment ranges.
- The collector stops silently when the API fails (`PROVENANCE.md` sections 6 and 11). Watch the console, because nothing is written to a log file, and compare the final checkpoint dates with today's date.
- Output goes to `data/raw/YYYY-MM/`. The analysis pipeline in `../scripts/` expects those month folders at `../raw/` (`scripts/project.py:8`).
- This project's data was collected once, on 23-24 Sep 2026, and no new data was downloaded for the final submission.

## How the data reaches the analysis

`collection/` (this folder) -> `raw/YYYY-MM/*.json` -> `scripts/profile_data.py` -> `data/processed/reddit.sqlite` -> the rest of the pipeline (see `../README.md` and `../docs/RUNNING.md`). The pilot CSVs from `processor.py` are not part of that path.
