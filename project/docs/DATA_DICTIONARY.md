# Data dictionary

## SQLite objects

`data/processed/reddit.sqlite` contains `records` (original reduced-field snapshots), `features` (prepared text/author metadata), joined `posts`/`comments` views, `threads`, `reply_edges`, an aggregated `author_reply_edges` view, `reading_sample`, and preparation bookkeeping. Records/features use `(kind,id)`; threads use full `t3_` IDs; reply edges use child comment IDs.

The steering extension adds `disruption_screen` (matching records only), `screening_builds` (rule provenance and scan completion), and `reading_sample_employment` (broader sample). None replaces the original tables or layoff flags.

## Flat-table fields

| Field | Meaning |
|---|---|
| `id` | Reddit record ID; retain post/comment kind when combining datasets |
| `thread_id`, `parent_id` | Comment's structural root and immediate parent fullname |
| `subreddit` | Community name |
| `created_utc`, `created_month` | Unix creation seconds and `YYYY-MM`, both UTC |
| `author_key`, `author_unknown` | Stable known-author pseudonym, or unknown flag |
| `likely_bot` | Unverified name-based flag; not an exclusion |
| `title` | Submission title |
| `raw_body` | Original retained body |
| `text_state` | Available, empty, removed, or deleted body |
| `clean_text` | HTML-decoded, whitespace-normalized body |
| `own_text`, `quoted_text` | Body without line-marked quotations; extracted quote lines |
| `word_count`, `char_count` | Whitespace-delimited words and Unicode code points |
| `urls_json` | JSON list of body URLs |
| `source_url`, `domain`, `is_self` | Submission link, hostname, self-post flag |
| `score`, `reported_comments` | Retrieval-snapshot engagement metadata |
| `direct_keyword_match`, `broad_keyword_match` | Regex retrieval flags; not relevance judgments |
| `collected_comment_count` | Comments actually present beneath a submission |
| `post_present`, `parent_present`, `parent_same_thread` | Context/linkage flags |
| `depth`, `depth_status` | Resolved structural depth or unresolved reason |
| `reply_delay_seconds` | Child minus parent creation time; empty if unknown |
| `retrieved_utc`, `source_file` | Snapshot selection timestamp and authoritative raw batch |

Flags use 0/1. Null values become empty CSV cells. The large tables are gzip-compressed. Thread records additionally include body/author counts, first/last observed comment times, observed duration, top-level count, maximum resolved depth, missing/unresolved ancestry counts, and post/comment keyword flags. Reply edges include child/parent author keys and parent kind.

## Samples and annotations

Sample CSVs contain IDs, group/stratum, metadata, preview, full raw/own/quoted bodies, and blank relevance/type/theme/emotion/response/notes fields. The JSONL packet adds bounded surrounding context. Use semicolons between multiple codes. The annotation summarizer normalizes label case/spacing for counting but preserves the input file.

The current broader sample is under `05_sample/employment/` with working labels in `annotations/reading_labels_employment.csv`. It additionally includes the six screen flags, `screen_evidence_json`, and blank `experiences`, `explanations`, `future_expectations` fields. Sampling group is distinct from a coded interpretation. The superseded layoff sample files were removed during cleanup; `sample_data.py --focus layoffs` recreates that optional sample. Its membership metadata remains in SQLite.

## Broader candidate fields

`03_tables/disruption_candidates.csv.gz` includes `(kind,id)`, thread/community/date metadata, text state, original layoff flags, and six overlapping binary screens: `layoffs`, `hiring_conditions`, `ai_work_change`, `corporate_restructuring`, `economic_policy`, `career_transition`. These names refer to lexical retrieval facets, not confirmed experiences or themes. `evidence_json` maps each matching facet to field-specific matched terms, plus the employment anchor for contextual rules. The version and rule fingerprint are in the separate manifest. Only matches are exported; join on both kind and ID to obtain full text or attach flags to the main tables.

## Analysis outputs

| File | Contents |
|---|---|
| `01_profile/profile.json` | Totals, dates, raw schema frequencies, linkage, errors |
| `01_profile/schema_fields.csv` | Field-presence counts/percentages by record kind |
| `01_profile/files.csv` | Batch inventory |
| `02_preprocessing/audit.csv` | Preparation counts and consistency checks |
| `02_preprocessing/screening_manifest.json` | Broader-screen rules, fingerprint, scan completion, and limitations |
| `03_tables/manifest.json` | Table columns, exported row counts, encoding/compression |
| `03_tables/disruption_manifest.json` | Separate candidate-export schema, counts, and screen provenance |
| `04_analysis/coverage.csv` | Community/type date boundaries and matches |
| `04_analysis/monthly_summary.csv` | Counts, availability, author flags, and means |
| `04_analysis/engagement_summary.csv` | Saved-score distributions by community/type/direct-match flag |
| `04_analysis/thread_summary.csv` | Collected discussion sizes and depths |
| `04_analysis/reply_quality.csv` | Parent/author/ancestry/timestamp quality |
| `04_analysis/terms_direct.csv` | Exploratory unigram/bigram frequencies |
| `04_analysis/analysis_manifest.json` | Parameters and interpretation limits |
| `04_analysis/disruption_summary.csv` | Broader candidate and facet counts by community/type |
| `04_analysis/disruption_monthly.csv` | Long-form facet counts and percentages against all collected records by community/type/month |
| `04_analysis/disruption_manifest.json` | Screen provenance, denominators, and coverage limits |
| `04_analysis/figures/*.png`, `*.svg` | Five static descriptive EDA figures |
| `04_analysis/figures/EDA_NOTES.md` | Figure gallery, preliminary insights, and interpretation limits |
| `04_analysis/figures/text_availability.csv` | Aggregated body-state counts and percentages used in the figure |
| `04_analysis/figures/score_bands.csv` | Saved-score band frequencies and percentages by record type |
| `04_analysis/figures/manifest.json` | Figure provenance, input hashes, runtime versions, and notes |
| `05_sample/employment/sample_manifest.json` | Broader pilot quotas, overlapping eligibility, rule fingerprint, and selection strata |
| `07_annotations/` | Manual review progress and human-code counts when generated after coding |

Gephi files are separate from `outputs/`, with paths relative to the project root:

| File | Purpose |
|---|---|
| `gephi/input/authors_keyword-comments.csv` | User's Gephi-calculated author metrics |
| `gephi/exports/*/manifest.json` | Original network scope, weights, exclusions, validation |
| `gephi/analysis/` | Python network findings, distributions, rankings, groups, settings, and figures |
| `gephi/rankings/` | Four standalone top-20 retained-count tables |
