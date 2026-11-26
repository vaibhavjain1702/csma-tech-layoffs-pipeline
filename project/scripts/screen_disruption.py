#!/usr/bin/env python3
"""Add modest broader employment screens, joinable candidates, and monthly counts."""
import argparse
import csv
import gzip
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from disruption_rules import VERSION, FINGERPRINT, EMPLOYMENT, RULES, FACETS, screen
from project import DB_PATH, PREPROCESS, TABLES, ANALYSIS, ensure_dirs, export_query


def build_screen(db, rebuild=False):
    db.execute('CREATE TABLE IF NOT EXISTS screening_builds(version TEXT PRIMARY KEY, fingerprint TEXT, records_scanned INTEGER, completed_utc TEXT)')
    previous = db.execute('SELECT fingerprint FROM screening_builds WHERE version=?', (VERSION,)).fetchone()
    if previous and previous[0] == FINGERPRINT and not rebuild:
        print('Employment screen: completed rules reused', flush=True)
        return
    db.commit()
    # Build and replace in one transaction, so readers never see a partial screen.
    db.execute('BEGIN')
    db.execute('DROP TABLE IF EXISTS disruption_screen_new')
    columns = ','.join(f'{facet} INTEGER NOT NULL CHECK({facet} IN (0,1))' for facet in FACETS)
    db.execute(f'CREATE TABLE disruption_screen_new(kind TEXT NOT NULL,id TEXT NOT NULL,{columns},evidence_json TEXT NOT NULL,PRIMARY KEY(kind,id)) WITHOUT ROWID')
    scanned = 0
    batch = []
    cursor = db.execute('SELECT r.kind,r.id,r.title,f.own_text FROM records r JOIN features f USING(kind,id)')
    for kind, id, title, text in cursor:
        evidence = screen(title, text)
        if evidence:
            batch.append((kind, id, *(int(facet in evidence) for facet in FACETS), json.dumps(evidence, ensure_ascii=False)))
        scanned += 1
        if scanned % 25000 == 0:
            db.executemany('INSERT INTO disruption_screen_new VALUES (' + ','.join('?' for _ in range(len(FACETS)+3)) + ')', batch)
            batch.clear()
        if scanned % 250000 == 0:
            print(f'Employment screen: {scanned:,} records scanned', flush=True)
    db.executemany('INSERT INTO disruption_screen_new VALUES (' + ','.join('?' for _ in range(len(FACETS)+3)) + ')', batch)
    expected = db.execute('SELECT count(*) FROM records').fetchone()[0]
    if scanned != expected:
        raise ValueError('Features do not cover every record; run preprocessing first')
    db.execute('DROP TABLE IF EXISTS disruption_screen')
    db.execute('ALTER TABLE disruption_screen_new RENAME TO disruption_screen')
    db.execute('INSERT OR REPLACE INTO screening_builds VALUES (?,?,?,?)', (VERSION, FINGERPRINT, scanned, datetime.now(timezone.utc).isoformat()))
    db.commit()
    print('Employment screen: committed', flush=True)


def export_outputs(db):
    destination = TABLES/'disruption_candidates.csv.gz'
    temp = destination.with_name(destination.name+'.tmp')
    columns = ','.join('s.'+facet for facet in FACETS)
    cursor = db.execute(f'''SELECT s.kind,s.id,CASE WHEN r.kind='posts' THEN 't3_'||r.id ELSE r.link_id END AS thread_id,
        r.subreddit,r.created_utc,r.created_month,r.text_state,r.direct_layoff,r.broad_layoff,
        {columns},s.evidence_json FROM disruption_screen s JOIN records r USING(kind,id) ORDER BY s.kind,s.id''')
    header = [field[0] for field in cursor.description]
    count = 0
    with gzip.open(temp, 'wt', encoding='utf-8', newline='', compresslevel=1) as output:
        writer = csv.writer(output); writer.writerow(header)
        for row in cursor:
            writer.writerow(row); count += 1
    temp.replace(destination)
    build = db.execute('SELECT records_scanned,completed_utc FROM screening_builds WHERE version=?', (VERSION,)).fetchone()
    manifest = {'version': VERSION, 'rule_fingerprint': FINGERPRINT, 'screen_completed_utc': build[1],
        'generated_utc': datetime.now(timezone.utc).isoformat(), 'records_scanned': build[0],
        'candidate_records': count, 'file': destination.name, 'columns': header,
        'text': 'Post title and own_text separately; URLs and line-prefixed body quotations excluded.',
        'rules': RULES, 'employment_anchor_pattern': EMPLOYMENT,
        'interpretation': 'Overlapping lexical screens for review, not validated relevance, causes, experiences, emotions, or worker identity. Same-field co-occurrence may span sentences. Absence means no rule matched, not irrelevant. Sparse table stores matching records only.'}
    (PREPROCESS/'screening_manifest.json').write_text(json.dumps(manifest, indent=2))
    (TABLES/'disruption_manifest.json').write_text(json.dumps(manifest, indent=2))
    aggregates = ','.join(f'sum(coalesce(s.{facet},0)) AS {facet}' for facet in FACETS)
    cursor = db.execute(f'''SELECT r.subreddit,r.kind,r.created_month,count(*) AS records,
        sum(s.id IS NOT NULL) AS candidates,{aggregates}
        FROM records r LEFT JOIN disruption_screen s USING(kind,id)
        GROUP BY r.subreddit,r.kind,r.created_month ORDER BY r.subreddit,r.kind,r.created_month''')
    with (ANALYSIS/'disruption_monthly.csv').open('w', encoding='utf-8', newline='') as output:
        writer = csv.writer(output)
        writer.writerow(['subreddit','kind','month','collected_records','candidate_records','candidate_percent','facet','facet_records','facet_percent'])
        for sub, kind, month, n, candidates, *counts in cursor:
            for facet, total in zip(FACETS, counts):
                writer.writerow([sub,kind,month,n,candidates,round(100*candidates/n,3),facet,total,round(100*total/n,3)])
    facet_rows = export_query(db, ANALYSIS/'disruption_summary.csv', f'''SELECT r.subreddit,r.kind,
        count(*) AS collected_records,sum(s.id IS NOT NULL) AS candidate_records,{aggregates}
        FROM records r LEFT JOIN disruption_screen s USING(kind,id) GROUP BY r.subreddit,r.kind ORDER BY r.subreddit,r.kind''')
    (ANALYSIS/'disruption_manifest.json').write_text(json.dumps({**manifest, 'summary_groups':facet_rows,
        'denominator':'All collected records within community, kind, and month; body availability varies. Facets overlap and must not be added.',
        'coverage':'Changing collection coverage limits time comparisons. These percentages describe collected records only.'}, indent=2))
    print(f'Employment candidates: {count:,}; summaries and joinable CSV exported', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rebuild', action='store_true', help='Recompute derived screens even if identical rules were completed')
    args = parser.parse_args(); ensure_dirs()
    with sqlite3.connect(DB_PATH, timeout=30) as db:
        db.execute('PRAGMA cache_size=-32768')
        build_screen(db, args.rebuild)
        export_outputs(db)


if __name__ == '__main__': main()
