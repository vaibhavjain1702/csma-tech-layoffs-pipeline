# csma-tech-layoffs-pipeline

Reddit data-collection and pseudonymization pipeline for studying tech-layoff discourse, built for a Computational Social Media course project. It pulls posts and comments for selected subreddits from the Arctic Shift archive, filters by keywords, deduplicates, hashes author names, and produces a QA report.

## Layout

- `main.py` - CLI entry point (`--mode smoke|collect|process|qa|full`)
- `config/collection_config.yaml` - subreddits, date range, keywords, rate limits
- `src/` - collector, processor, privacy (pseudonymization), QA, orchestrator
- `docs/RUNBOOK.md` - how to run each phase
- `reports/QA_REPORT.md` - QA output from the original collection run
- `data/README.md` - how to obtain the data (none is included) and the required `CSMA_SALT` setting

## Quick start

```bash
pip install -r requirements.txt
export CSMA_SALT="<your-own-secret-string>"
python main.py --mode full
```

The downstream analysis (preprocessing, screening, network exports) was done in a separate team repository and is not part of this one.
