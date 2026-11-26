# First exploration: Reddit collection

This first pass describes all records in `raw/`. It does not assume that every record is layoff-related. The owner reports that a teammate was tasked with collecting layoff-related Reddit posts using Arctic Shift; the actual queries and settings are unknown.

## Arrangement and size

- 29,821 JSON files, 5.74 GiB, in 21 monthly folders.
- 115,213 posts and 2,859,037 comments; 2,974,250 records total.
- Each raw batch is a JSON array with posts and comments stored separately. The preprocessing stage reconstructs collected thread structure and reply edges from their structural links.
- Post fields include `id`, `created_utc`, `subreddit`, `title`, `selftext`, `score`, `num_comments`, and `is_self`. Comment fields include `id`, `body`, `link_id`, `parent_id`, `created_utc`, `subreddit`, and `score`.
- `link_id = t3_<post-id>` connects a comment to its submission. `parent_id = t1_<comment-id>` identifies a reply to a comment, while `t3_` identifies a top-level reply to a post.

## Coverage

All dates below are UTC. “No rows” means absent from this collection, not absent from Reddit.

| Community | Record type | Records | First date | Last date | Explicit layoff mentions |
|---|---|---:|---|---|---:|
| r/cscareerquestions | comments | 962,337 | 2025-01-01 | 2026-09-23 | 23,836 (2.48%) |
| r/programming | comments | 238,800 | 2025-01-01 | 2025-12-12 | 839 (0.35%) |
| r/technology | comments | 1,657,900 | 2025-01-01 | 2025-06-09 | 3,402 (0.21%) |
| r/programming | posts | 38,431 | 2025-01-01 | 2026-09-23 | 53 (0.14%) |
| r/technology | posts | 76,782 | 2025-01-01 | 2026-09-24 | 601 (0.78%) |

Posts cover r/programming and r/technology across the full period. There are **no r/cscareerquestions posts**. Comments cover three communities, but r/technology ends on June 9, 2025 and r/programming ends on December 12, 2025. Only r/cscareerquestions comments extend into 2026. September 2026 is partial, ending on September 23 for comments and September 24 for posts.

**Interpretation:** pooled comment counts and keyword shares cannot be read as a consistent time series. Their subreddit composition changes sharply. Compare within communities and treat boundary months separately; even then collection completeness is unverified.

## Data quality and conversation coverage

- JSON parse errors: 0. Duplicate `(kind,id)` records: 0. Creation-month/folder mismatches: 0.
- Available comment body text: 2,705,044 (94.61%). Removed: 145,840; deleted: 8,152; empty: 1.
- Post bodies: 10,316 available, 93,751 empty, 10,610 removed, 536 deleted. Empty `selftext` is expected for link posts and should not automatically be treated as missing data. Only 955 posts (0.83%) have `is_self=true`.
- Posts without a title: 0. Comments missing either `link_id` or `parent_id`: 0.
- 1,885,815 comments (65.96%) connect to a stored post; 973,222 do not.
- 26,364 posts (22.88%) have at least one collected comment. A reported `num_comments` value does not guarantee those comments were downloaded.
- Of 1,836,296 replies to comments, 1,823,984 (99.33%) have their parent comment in the collection.

## A first layoff-related subset

The explicit keyword screen searches post titles/bodies and comment bodies for “layoff(s)”, “laid off”, “lay off”, and “laying off”, including some spacing/hyphen variants. This measures explicit language, not validated relevance.

- Posts matching: 654 (0.57%). The broader keyword screen raises this to 767 (0.67%).
- Comments matching: 28,077 (0.98%). The broader screen raises this to 30,549 (1.07%).
- 23,836 of the explicit matching comments (84.90%) are from r/cscareerquestions, whose posts are absent.
- Explicit matching posts have 13,206 collected comments, including replies that do not themselves repeat a keyword.
- Only 929 explicitly matching comments connect to an explicitly matching stored post. Keyword-matching comments and discussions under keyword-matching posts are different units of analysis.

The collection appears broader than a curated layoff-post corpus. Many relevant experiences may be in career comments without their original post context; stored posts largely represent links/news from technology and programming communities. News discussion and personal experience should therefore be sampled and interpreted separately.

## Engagement at the saved snapshot

| Record type | Median score | 75th percentile | 90th percentile | 99th percentile | Mean score |
|---|---:|---:|---:|---:|---:|
| posts | 1 | 38 | 713 | 16758.8 | 655.2 |
| comments | 1 | 4 | 15 | 190 | 13.61 |

Scores and reported comment counts reflect retrieval snapshots, not necessarily final engagement. Quantiles use linear interpolation over observed, non-null scores. Popularity-weighted examples favor unusually visible conversations.

## Next steps toward qualitative analysis

Use the generated employment reading sample and its bounded context packet to pilot relevance and coding across layoffs, hiring conditions, AI/work change, restructuring, economic/policy discussion, career transitions, and nonmatching background records. Retain missing-context indicators and irrelevant keyword hits as evidence for refining retrieval. Broader screening results are reported separately in disruption_summary.csv and disruption_monthly.csv; this report retains the original layoff-screen statistics.

From those readings, develop a provisional codebook for contribution types, employment experiences, explanations, future expectations, emotions, and response functions. See docs/CODING_STARTER.md. These are questions to investigate, not findings or assigned labels. Validate the categories against human readings before scaling annotation or comparing rates. Avoid treating keyword counts or sentiment scores as measurements of actual layoffs or population attitudes.

The collection query, selected subreddits, pagination settings, and reasons for comment cutoffs are the most useful provenance details to obtain from the teammate.

## Reproducibility

`scripts/profile_data.py` builds `data/processed/reddit.sqlite` and profile CSVs from the untouched raw files. `scripts/summarize_data.py` produces this report, coverage tables, and descriptive statistics. `docs/explore.sql` contains starter queries. The working index retains reduced fields; raw records remain the authoritative source.
