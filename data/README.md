# Data

No data is included in this repository. The raw and processed corpora are not redistributed, in line with Reddit and Arctic Shift terms and to protect user privacy. Regenerate them with the pipeline.

## Source

Reddit posts and comments from the [Arctic Shift](https://arctic-shift.photon-reddit.com) historical archive, queried through its public API (`posts/search` and `comments/search`) by `src/collector.py`.

## Scope (from `config/collection_config.yaml`)

- Subreddits: technology, cscareerquestions, programming, ExperiencedDevs, antiwork, jobs, careerguidance
- Date range: 2025-01-01 to 2026-12-31 (collection stops at the latest available data)
- Posts and comments are filtered by layoff-related keywords (see the config)

## Pseudonymization salt

Author names are replaced by a salted SHA-256 hash (`author_hash`). Set a private salt before running the pipeline, and keep it out of version control:

```bash
export CSMA_SALT="<your-own-secret-string>"
```

The pipeline refuses to pseudonymize without it. Use the same value across runs so hashes stay consistent.

## Reproducing

```bash
pip install -r requirements.txt
python main.py --mode collect   # raw JSON -> data/raw/YYYY-MM/ (resumable via checkpoints/)
python main.py --mode process   # filter, dedupe -> data/processed/
python main.py --mode qa        # writes reports/QA_REPORT.md
```

Expected layout after a run: `data/raw/` (JSON batches) and `data/processed/posts.csv`, `data/processed/comments.csv`.
