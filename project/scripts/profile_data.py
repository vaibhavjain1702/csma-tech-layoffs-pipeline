#!/usr/bin/env python3
"""Profile Arctic Shift JSON batches and build a deduplicated SQLite index.

Uses only Python's standard library. Raw files are never modified.
Run: python scripts/profile_data.py
"""
import argparse
import csv
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from project import DB_PATH,PROFILE,ensure_dirs
DIRECT = re.compile(r'\b(?:lay[ -]?offs?|laid[ -]+off|laying[ -]+off|lay[ -]+off)\b', re.I)
BROAD = re.compile(r'\b(?:redundan\w*|furlough\w*|downsiz\w*|job cuts?|workforce reductions?|reduction in force)\b', re.I)
MARKERS = {'[deleted]', '[removed]'}


def month_of(timestamp):
    try:
        return datetime.fromtimestamp(float(timestamp), timezone.utc).strftime('%Y-%m')
    except (ValueError, TypeError, OverflowError, OSError):
        return 'unknown'


def write_csv(path, rows):
    if not rows:
        return
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def query_dicts(db, query):
    result = db.execute(query)
    names = [column[0] for column in result.description]
    return [dict(zip(names, row)) for row in result]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rebuild', action='store_true', help='Rebuild the generated index')
    args = parser.parse_args()
    ensure_dirs()
    out = PROFILE
    db_path = DB_PATH
    if db_path.exists() and not args.rebuild:
        raise SystemExit('Index already exists. Use --rebuild to regenerate derived outputs.')
    if db_path.exists():
        db_path.unlink()
    db = sqlite3.connect(db_path)
    db.execute('PRAGMA journal_mode=OFF')
    db.execute('PRAGMA synchronous=OFF')
    db.execute('PRAGMA cache_size=-65536')
    db.execute('''CREATE TABLE records (
        kind TEXT NOT NULL, id TEXT NOT NULL, folder_month TEXT, created_utc INTEGER,
        created_month TEXT, subreddit TEXT, title TEXT, text TEXT, text_state TEXT,
        score INTEGER, num_comments INTEGER, link_id TEXT, parent_id TEXT,
        is_self INTEGER, direct_layoff INTEGER, broad_layoff INTEGER,
        retrieved_utc INTEGER, source_file TEXT, PRIMARY KEY(kind,id)
    ) WITHOUT ROWID''')
    insert = '''INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(kind,id) DO UPDATE SET
        folder_month=excluded.folder_month, created_utc=excluded.created_utc,
        created_month=excluded.created_month, subreddit=excluded.subreddit,
        title=excluded.title, text=excluded.text, text_state=excluded.text_state,
        score=excluded.score, num_comments=excluded.num_comments,
        link_id=excluded.link_id, parent_id=excluded.parent_id, is_self=excluded.is_self,
        direct_layoff=excluded.direct_layoff, broad_layoff=excluded.broad_layoff,
        retrieved_utc=excluded.retrieved_utc, source_file=excluded.source_file
        WHERE excluded.retrieved_utc > records.retrieved_utc'''
    raw = defaultdict(Counter)
    files = []
    errors = []
    fields = defaultdict(Counter)
    for folder in sorted((ROOT / 'raw').iterdir()):
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob('*.json')):
            kind = path.name.split('_batch_')[0]
            if kind not in ('posts', 'comments'):
                errors.append({'file': str(path.relative_to(ROOT)), 'error': 'Unknown filename type'})
                continue
            try:
                data = json.loads(path.read_text())
                if isinstance(data, dict):
                    data = data.get('data', data.get(kind))
                if not isinstance(data, list):
                    raise ValueError('Expected an array of records')
            except Exception as e:
                errors.append({'file': str(path.relative_to(ROOT)), 'error': str(e)})
                continue
            counter = raw[(folder.name, kind)]
            for key in ('invalid_records', 'missing_id', 'folder_date_mismatch',
                        'text_available', 'text_empty', 'text_deleted', 'text_removed',
                        'direct_layoff'):
                counter.setdefault(key, 0)
            counter['files'] += 1
            counter['bytes'] += path.stat().st_size
            counter['rows'] += len(data)
            batch = []
            for record in data:
                if not isinstance(record, dict):
                    counter['invalid_records'] += 1
                    continue
                fields[kind].update(record.keys())
                record_id = record.get('id')
                if not record_id:
                    counter['missing_id'] += 1
                    continue
                timestamp = record.get('created_utc')
                created_month = month_of(timestamp)
                if created_month != folder.name:
                    counter['folder_date_mismatch'] += 1
                title = record.get('title') or ''
                body = record.get('selftext' if kind == 'posts' else 'body') or ''
                if body.strip().lower() in MARKERS:
                    state = body.strip().lower()[1:-1]
                else:
                    state = 'empty' if not body.strip() else 'available'
                counter['text_' + state] += 1
                combined = title + '\n' + (body if state == 'available' else '')
                direct = int(bool(DIRECT.search(combined)))
                broad = int(bool(direct or BROAD.search(combined)))
                counter['direct_layoff'] += direct
                retrieved = max(
                    [int(v) for v in [record.get('retrieved_on'),
                     (record.get('_meta') or {}).get('retrieved_2nd_on')] if isinstance(v, (int, float))]
                    or [0])
                batch.append((kind, str(record_id), folder.name, timestamp, created_month,
                    record.get('subreddit'), title, body, state, record.get('score'),
                    record.get('num_comments'), record.get('link_id'), record.get('parent_id'),
                    int(bool(record.get('is_self'))) if kind == 'posts' else None,
                    direct, broad, retrieved, str(path.relative_to(ROOT))))
            db.executemany(insert, batch)
            files.append({'file': str(path.relative_to(ROOT)), 'kind': kind,
                          'rows': len(data), 'bytes': path.stat().st_size})
        db.commit()
        print(f'{folder.name}: read {sum(v["rows"] for (m,k),v in raw.items() if m == folder.name):,} rows', flush=True)
    db.execute('CREATE INDEX records_month ON records(kind,created_month)')
    db.execute('CREATE INDEX records_subreddit ON records(kind,subreddit)')
    db.execute("CREATE INDEX comments_link ON records(link_id) WHERE kind='comments'")
    db.commit()
    totals = query_dicts(db, '''SELECT kind, count(*) AS unique_records,
        min(created_utc) AS first_created_utc, max(created_utc) AS last_created_utc,
        sum(direct_layoff) AS direct_layoff_mentions, sum(broad_layoff) AS broad_layoff_mentions,
        sum(text_state='available') AS available_text, sum(text_state='empty') AS empty_text,
        sum(text_state='deleted') AS deleted_text, sum(text_state='removed') AS removed_text
        FROM records GROUP BY kind''')
    for row in totals:
        kind = row['kind']
        row['raw_records'] = sum(v['rows'] for (m,k),v in raw.items() if k == kind)
        row['duplicate_records'] = row['raw_records'] - row['unique_records'] - sum(v['missing_id'] + v['invalid_records'] for (m,k),v in raw.items() if k == kind)
        for field in ['first_created_utc', 'last_created_utc']:
            row[field.replace('_utc', '_iso')] = datetime.fromtimestamp(row[field], timezone.utc).isoformat() if row[field] else None
    monthly = query_dicts(db, '''SELECT created_month AS month, kind, count(*) AS records,
        sum(direct_layoff) AS direct_layoff_mentions, sum(broad_layoff) AS broad_layoff_mentions,
        sum(text_state='available') AS available_text,
        sum(text_state IN ('deleted','removed')) AS unavailable_text
        FROM records GROUP BY created_month,kind ORDER BY created_month,kind''')
    subreddits = query_dicts(db, '''SELECT subreddit, kind, count(*) AS records,
        sum(direct_layoff) AS direct_layoff_mentions, sum(broad_layoff) AS broad_layoff_mentions,
        sum(text_state IN ('deleted','removed')) AS unavailable_text
        FROM records GROUP BY subreddit,kind ORDER BY kind,records DESC''')
    folder_rows = [{'folder_month': m, 'kind': k, **dict(c)} for (m,k),c in sorted(raw.items())]
    all_columns = list(dict.fromkeys(key for row in folder_rows for key in row))
    folder_rows = [{col: row.get(col, 0) for col in all_columns} for row in folder_rows]
    linkage = dict(db.execute('''SELECT
        'comments_with_post_in_collection',count(*) FROM records c
        JOIN records p ON p.kind='posts' AND c.link_id='t3_' || p.id WHERE c.kind='comments'
        UNION ALL SELECT 'comments_with_direct_layoff_post',count(*) FROM records c
        JOIN records p ON p.kind='posts' AND c.link_id='t3_' || p.id
        WHERE c.kind='comments' AND p.direct_layoff=1
        UNION ALL SELECT 'posts_with_any_collected_comment',count(*) FROM records p
        WHERE p.kind='posts' AND EXISTS (SELECT 1 FROM records c WHERE c.kind='comments' AND c.link_id='t3_' || p.id)'''))
    examples = query_dicts(db, '''SELECT id,created_month,subreddit,title,score,num_comments,
        'https://www.reddit.com/comments/' || id AS url
        FROM records WHERE kind='posts' AND direct_layoff=1
        ORDER BY coalesce(num_comments,0) DESC LIMIT 30''')
    overview = {'totals': totals, 'linkage': linkage, 'parse_errors': errors,
        'file_count': len(files), 'size_bytes': sum(f['bytes'] for f in files),
        'direct_pattern': DIRECT.pattern, 'broad_additional_pattern': BROAD.pattern,
        'deduplication': 'One record per (kind,id); retain snapshot with greatest retrieved_on/retrieved_2nd_on. Ties retain the first file in sorted path order.',
        'schema_field_counts': dict(fields)}
    (out / 'profile.json').write_text(json.dumps(overview, indent=2))
    schema_rows=[]
    for kind,frequencies in fields.items():
        raw_count=next(r['raw_records'] for r in totals if r['kind']==kind)
        for field,count in sorted(frequencies.items()):
            schema_rows.append({'kind':kind,'field':field,'present_records':count,
                'raw_records':raw_count,'presence_percent':round(100*count/raw_count,3)})
    write_csv(out / 'schema_fields.csv',schema_rows)
    write_csv(out / 'monthly.csv', monthly)
    write_csv(out / 'subreddits.csv', subreddits)
    write_csv(out / 'raw_folders.csv', folder_rows)
    write_csv(out / 'files.csv', files)
    write_csv(out / 'layoff_post_examples.csv', examples)
    db.close()
    print(json.dumps({'totals': totals, 'linkage': linkage, 'parse_errors': errors}, indent=2), flush=True)


if __name__ == '__main__':
    main()
