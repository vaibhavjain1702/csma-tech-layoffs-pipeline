#!/usr/bin/env python3
"""Generate the initial descriptive report from the completed SQLite index."""
import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from project import DB_PATH,PROFILE,ANALYSIS as OUT,ensure_dirs


def rows(db, sql):
    query = db.execute(sql)
    columns = [r[0] for r in query.description]
    return [dict(zip(columns, r)) for r in query]


def export(name, records):
    with (OUT / name).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def pct(n, d):
    return f'{100*n/d:.2f}%'


def main():
    ensure_dirs()
    profile = json.loads((PROFILE / 'profile.json').read_text())
    db = sqlite3.connect(DB_PATH)
    db.execute('PRAGMA cache_size=-65536')
    communities = rows(db, '''SELECT subreddit, kind, count(*) AS records,
        min(created_utc) AS first_utc, max(created_utc) AS last_utc,
        sum(direct_layoff) AS direct_mentions, sum(broad_layoff) AS broad_mentions,
        sum(is_self) AS self_posts FROM records GROUP BY subreddit,kind''')
    for row in communities:
        for key in ('first_utc', 'last_utc'):
            row[key] = datetime.fromtimestamp(row[key], timezone.utc).isoformat()
    export('coverage.csv', communities)
    month_sub = rows(db, '''SELECT created_month AS month, subreddit, kind, count(*) AS records,
        sum(direct_layoff) AS direct_mentions FROM records
        GROUP BY created_month,subreddit,kind ORDER BY created_month,kind,subreddit''')
    export('monthly_subreddits.csv', month_sub)
    scores = {}
    for kind in ('posts', 'comments'):
        scores[kind] = rows(db, f'''SELECT count(*) AS known_scores, min(score) AS min_score,
            max(score) AS max_score, round(avg(score),2) AS mean_score,
            sum(score=0) AS zero_score, sum(score<0) AS negative_score
            FROM records WHERE kind='{kind}' AND score IS NOT NULL''')[0]
        # Read the ordered score column once; no full raw records are loaded.
        ordered = [r[0] for r in db.execute('SELECT score FROM records WHERE kind=? AND score IS NOT NULL ORDER BY score', (kind,))]
        for label, q in [('median', .5), ('p75', .75), ('p90', .9), ('p99', .99)]:
            index = (len(ordered)-1)*q
            lower = int(index)
            upper = min(lower+1,len(ordered)-1)
            scores[kind][label] = round(ordered[lower]+(ordered[upper]-ordered[lower])*(index-lower),2)
    additional = rows(db, '''SELECT
        count(*) AS direct_comments, sum(subreddit='cscareerquestions') AS career_comments,
        sum(EXISTS (SELECT 1 FROM records p WHERE p.kind='posts' AND p.id=substr(c.link_id,4))) AS with_post,
        sum(EXISTS (SELECT 1 FROM records p WHERE p.kind='posts' AND p.id=substr(c.link_id,4) AND p.direct_layoff=1)) AS with_direct_post
        FROM records c WHERE c.kind='comments' AND c.direct_layoff=1''')[0]
    other = rows(db, '''SELECT
        sum(kind='posts' AND (title IS NULL OR trim(title)='')) AS posts_without_title,
        sum(kind='posts' AND is_self=1) AS self_posts,
        sum(kind='comments' AND (link_id IS NULL OR parent_id IS NULL)) AS comments_missing_link_fields
        FROM records''')[0]
    parent_coverage = rows(db, '''SELECT
        count(*) AS replies_to_comments,
        sum(EXISTS (SELECT 1 FROM records parent WHERE parent.kind='comments' AND parent.id=substr(c.parent_id,4))) AS with_collected_parent
        FROM records c WHERE c.kind='comments' AND substr(c.parent_id,1,3)='t1_' ''')[0]
    extra = {'scores': scores, 'direct_comment_linkage': additional,
             'other_quality': other, 'parent_coverage': parent_coverage}
    (OUT / 'descriptive_stats.json').write_text(json.dumps(extra, indent=2))
    totals = {r['kind']: r for r in profile['totals']}
    p, c = totals['posts'], totals['comments']
    link = profile['linkage']
    raw_rows = list(csv.DictReader((PROFILE / 'raw_folders.csv').open()))
    mismatches = sum(int(r.get('folder_date_mismatch', 0)) for r in raw_rows)
    report = [
        '# First exploration: Reddit collection',
        '',
        'This first pass describes all records in `raw/`. It does not assume that every record is layoff-related. The owner reports that a teammate was tasked with collecting layoff-related Reddit posts using Arctic Shift; the actual queries and settings are unknown.',
        '',
        '## Arrangement and size',
        '',
        f'- {profile["file_count"]:,} JSON files, {profile["size_bytes"]/1024**3:.2f} GiB, in 21 monthly folders.',
        f'- {p["unique_records"]:,} posts and {c["unique_records"]:,} comments; {p["unique_records"]+c["unique_records"]:,} records total.',
        '- Each raw batch is a JSON array with posts and comments stored separately. The preprocessing stage reconstructs collected thread structure and reply edges from their structural links.',
        '- Post fields include `id`, `created_utc`, `subreddit`, `title`, `selftext`, `score`, `num_comments`, and `is_self`. Comment fields include `id`, `body`, `link_id`, `parent_id`, `created_utc`, `subreddit`, and `score`.',
        '- `link_id = t3_<post-id>` connects a comment to its submission. `parent_id = t1_<comment-id>` identifies a reply to a comment, while `t3_` identifies a top-level reply to a post.',
        '',
        '## Coverage',
        '',
        'All dates below are UTC. “No rows” means absent from this collection, not absent from Reddit.',
        '',
        '| Community | Record type | Records | First date | Last date | Explicit layoff mentions |',
        '|---|---|---:|---|---|---:|',
    ]
    for r in communities:
        report.append(f'| r/{r["subreddit"]} | {r["kind"]} | {r["records"]:,} | {r["first_utc"][:10]} | {r["last_utc"][:10]} | {r["direct_mentions"]:,} ({pct(r["direct_mentions"],r["records"])}) |')
    report += [
        '',
        'Posts cover r/programming and r/technology across the full period. There are **no r/cscareerquestions posts**. Comments cover three communities, but r/technology ends on June 9, 2025 and r/programming ends on December 12, 2025. Only r/cscareerquestions comments extend into 2026. September 2026 is partial, ending on September 23 for comments and September 24 for posts.',
        '',
        '**Interpretation:** pooled comment counts and keyword shares cannot be read as a consistent time series. Their subreddit composition changes sharply. Compare within communities and treat boundary months separately; even then collection completeness is unverified.',
        '',
        '## Data quality and conversation coverage',
        '',
        f'- JSON parse errors: {len(profile["parse_errors"])}. Duplicate `(kind,id)` records: {sum(r["duplicate_records"] for r in profile["totals"]):,}. Creation-month/folder mismatches: {mismatches:,}.',
        f'- Available comment body text: {c["available_text"]:,} ({pct(c["available_text"],c["unique_records"])}). Removed: {c["removed_text"]:,}; deleted: {c["deleted_text"]:,}; empty: {c["empty_text"]:,}.',
        f'- Post bodies: {p["available_text"]:,} available, {p["empty_text"]:,} empty, {p["removed_text"]:,} removed, {p["deleted_text"]:,} deleted. Empty `selftext` is expected for link posts and should not automatically be treated as missing data. Only {other["self_posts"]:,} posts ({pct(other["self_posts"],p["unique_records"])}) have `is_self=true`.',
        f'- Posts without a title: {other["posts_without_title"]:,}. Comments missing either `link_id` or `parent_id`: {other["comments_missing_link_fields"]:,}.',
        f'- {link["comments_with_post_in_collection"]:,} comments ({pct(link["comments_with_post_in_collection"],c["unique_records"])}) connect to a stored post; {c["unique_records"]-link["comments_with_post_in_collection"]:,} do not.',
        f'- {link["posts_with_any_collected_comment"]:,} posts ({pct(link["posts_with_any_collected_comment"],p["unique_records"])}) have at least one collected comment. A reported `num_comments` value does not guarantee those comments were downloaded.',
        f'- Of {parent_coverage["replies_to_comments"]:,} replies to comments, {parent_coverage["with_collected_parent"]:,} ({pct(parent_coverage["with_collected_parent"],parent_coverage["replies_to_comments"])}) have their parent comment in the collection.',
        '',
        '## A first layoff-related subset',
        '',
        'The explicit keyword screen searches post titles/bodies and comment bodies for “layoff(s)”, “laid off”, “lay off”, and “laying off”, including some spacing/hyphen variants. This measures explicit language, not validated relevance.',
        '',
        f'- Posts matching: {p["direct_layoff_mentions"]:,} ({pct(p["direct_layoff_mentions"],p["unique_records"])}). The broader keyword screen raises this to {p["broad_layoff_mentions"]:,} ({pct(p["broad_layoff_mentions"],p["unique_records"])}).',
        f'- Comments matching: {c["direct_layoff_mentions"]:,} ({pct(c["direct_layoff_mentions"],c["unique_records"])}). The broader screen raises this to {c["broad_layoff_mentions"]:,} ({pct(c["broad_layoff_mentions"],c["unique_records"])}).',
        f'- {additional["career_comments"]:,} of the explicit matching comments ({pct(additional["career_comments"],additional["direct_comments"])}) are from r/cscareerquestions, whose posts are absent.',
        f'- Explicit matching posts have {link["comments_with_direct_layoff_post"]:,} collected comments, including replies that do not themselves repeat a keyword.',
        f'- Only {additional["with_direct_post"]:,} explicitly matching comments connect to an explicitly matching stored post. Keyword-matching comments and discussions under keyword-matching posts are different units of analysis.',
        '',
        'The collection appears broader than a curated layoff-post corpus. Many relevant experiences may be in career comments without their original post context; stored posts largely represent links/news from technology and programming communities. News discussion and personal experience should therefore be sampled and interpreted separately.',
        '',
        '## Engagement at the saved snapshot',
        '',
        '| Record type | Median score | 75th percentile | 90th percentile | 99th percentile | Mean score |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for kind, r in scores.items():
        report.append(f'| {kind} | {r["median"]:g} | {r["p75"]:g} | {r["p90"]:g} | {r["p99"]:g} | {r["mean_score"]:g} |')
    report += [
        '',
        'Scores and reported comment counts reflect retrieval snapshots, not necessarily final engagement. Quantiles use linear interpolation over observed, non-null scores. Popularity-weighted examples favor unusually visible conversations.',
        '',
        '## Next steps toward qualitative analysis',
        '',
        'Use the generated employment reading sample and its bounded context packet to pilot relevance and coding across layoffs, hiring conditions, AI/work change, restructuring, economic/policy discussion, career transitions, and nonmatching background records. Retain missing-context indicators and irrelevant keyword hits as evidence for refining retrieval. Broader screening results are reported separately in disruption_summary.csv and disruption_monthly.csv; this report retains the original layoff-screen statistics.',
        '',
        'From those readings, develop a provisional codebook for contribution types, employment experiences, explanations, future expectations, emotions, and response functions. See docs/CODING_STARTER.md. These are questions to investigate, not findings or assigned labels. Validate the categories against human readings before scaling annotation or comparing rates. Avoid treating keyword counts or sentiment scores as measurements of actual layoffs or population attitudes.',
        '',
        'The collection query, selected subreddits, pagination settings, and reasons for comment cutoffs are the most useful provenance details to obtain from the teammate.',
        '',
        '## Reproducibility',
        '',
        '`scripts/profile_data.py` builds `data/processed/reddit.sqlite` and profile CSVs from the untouched raw files. `scripts/summarize_data.py` produces this report, coverage tables, and descriptive statistics. `docs/explore.sql` contains starter queries. The working index retains reduced fields; raw records remain the authoritative source.',
    ]
    (OUT / 'first_pass.md').write_text('\n'.join(report)+'\n')
    db.close()
    print(json.dumps(extra, indent=2))


if __name__ == '__main__':
    main()
