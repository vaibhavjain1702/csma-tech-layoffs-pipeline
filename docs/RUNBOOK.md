# CSMA Tech Layoffs Data Pipeline Runbook

## Overview
This pipeline collects Reddit posts and comments related to tech layoffs from the Arctic Shift historical data archive. It processes, filters, deduplicates, and pseudonymizes the data.

## Setup
1. Open a terminal in the project directory.
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Configuration
Edit `config/collection_config.yaml` to modify:
- Subreddits to track
- Date range
- Keywords
- API rate limits and retries

## Environment Variables
- `CSMA_SALT`: Set this environment variable to a secret string to ensure consistent and secure hashing of author names. It is required: pseudonymization aborts if it is not set.

## Running the Pipeline

You can run specific phases or the entire pipeline using the `--mode` argument in `main.py`.

### 1. Collect Data (Phase 4)
Fetches raw JSON data from Arctic Shift and saves it in `data/raw/YYYY-MM/`.
```bash
python main.py --mode collect
```
*Note: This will resume from checkpoints stored in `checkpoints/` if interrupted.*

### 2. Process Data (Phase 5)
Filters the raw data by keywords, normalizes it, deduplicates it, and saves to `data/processed/`.
```bash
python main.py --mode process
```

### 3. QA Audit (Phase 6)
Runs quality assurance checks on the processed data and generates a report in `reports/QA_REPORT.md`.
```bash
python main.py --mode qa
```

### 4. Run Everything
To run all phases in sequence:
```bash
python main.py --mode full
```

## Outputs
- **Raw Data**: `data/raw/` (JSON)
- **Processed Data**: `data/processed/posts.csv`, `data/processed/comments.csv`
- **QA Report**: `reports/QA_REPORT.md`
- **Logs**: Output to the console.
