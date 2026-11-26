#!/usr/bin/env python3
"""Preprocess the profiled corpus and derive collected conversation structure.

Run after profile_data.py. Raw batches are preserved; derived stages resume safely.
Stages commit atomically and can be resumed after interruption.
"""
import itertools
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from research_common import author_key, domain_of, prepare_text, thread_depths

ROOT = Path(__file__).resolve().parents[1]
from project import DB_PATH,PREPROCESS as OUT,ensure_dirs


def connect():
    db = sqlite3.connect(DB_PATH)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=NORMAL')
    db.execute('PRAGMA cache_size=-32768')
    db.execute('CREATE TABLE IF NOT EXISTS research_builds(stage TEXT PRIMARY KEY, completed_utc TEXT)')
    db.commit()
    return db


def finished(db, stage):
    return db.execute('SELECT 1 FROM research_builds WHERE stage=?', (stage,)).fetchone() is not None


def complete(db, stage):
    db.execute('INSERT OR REPLACE INTO research_builds VALUES (?,?)', (stage, datetime.now(timezone.utc).isoformat()))
    db.commit()
    print('Completed:', stage, flush=True)


def features(db):
    if finished(db, 'features_v1'):
        return
    db.execute('''CREATE TABLE IF NOT EXISTS features(
        feature_id INTEGER PRIMARY KEY, kind TEXT NOT NULL, id TEXT NOT NULL,
        author_key TEXT, author_unknown INTEGER NOT NULL, likely_bot INTEGER NOT NULL,
        clean_text TEXT, own_text TEXT, quoted_text TEXT, urls_json TEXT,
        word_count INTEGER, char_count INTEGER, source_url TEXT, domain TEXT,
        UNIQUE(kind,id))''')
    db.execute('CREATE TABLE IF NOT EXISTS feature_files(source_file TEXT PRIMARY KEY)')
    db.commit()
    existing = {r[0] for r in db.execute('SELECT source_file FROM feature_files')}
    for folder in sorted((ROOT / 'raw').iterdir()):
        if not folder.is_dir():
            continue
        done = 0
        for path in sorted(folder.glob('*.json')):
            source = str(path.relative_to(ROOT))
            if source in existing:
                continue
            kind = path.name.split('_batch_')[0]
            if kind not in ('posts', 'comments'):
                continue
            retained = {r[0] for r in db.execute('SELECT id FROM records WHERE source_file=?', (source,))}
            # source_file is indexed before this stage; chosen snapshots alone are enriched.
            batch = []
            data = json.loads(path.read_text())
            if isinstance(data, dict):
                data = data.get('data', data.get(kind, []))
            for record in data:
                if str(record.get('id')) not in retained:
                    continue
                text = record.get('selftext' if kind == 'posts' else 'body') or ''
                available = text.strip().lower() not in {'[removed]', '[deleted]'}
                prepared = prepare_text(text, available)
                author = record.get('author')
                key = author_key(author)
                # This is a name-based screening flag, not a verified bot classification.
                bot = int(bool(author and (author.lower() == 'automoderator' or author.lower().endswith('bot'))))
                source_url = record.get('url') if kind == 'posts' else None
                batch.append((kind, str(record['id']), key, int(key is None), bot,
                    prepared['clean_text'], prepared['own_text'], prepared['quoted_text'],
                    json.dumps(prepared['urls'], ensure_ascii=False), prepared['word_count'],
                    prepared['char_count'], source_url, domain_of(source_url)))
            db.executemany('''INSERT OR REPLACE INTO features(kind,id,author_key,author_unknown,
                likely_bot,clean_text,own_text,quoted_text,urls_json,word_count,char_count,
                source_url,domain) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', batch)
            db.execute('INSERT INTO feature_files VALUES (?)', (source,))
            done += len(batch)
            if done and done % 10000 < 100:
                db.commit()
        db.commit()
        print(f'Features {folder.name}: {done:,} records', flush=True)
    db.execute('CREATE INDEX IF NOT EXISTS feature_authors ON features(author_key)')
    db.execute('''CREATE VIEW IF NOT EXISTS posts AS SELECT r.*, f.author_key,
        f.author_unknown,f.likely_bot,f.clean_text,f.own_text,f.quoted_text,
        f.urls_json,f.word_count,f.char_count,f.source_url,f.domain
        FROM records r JOIN features f USING(kind,id) WHERE r.kind='posts' ''')
    db.execute('''CREATE VIEW IF NOT EXISTS comments AS SELECT r.*, f.author_key,
        f.author_unknown,f.likely_bot,f.clean_text,f.own_text,f.quoted_text,
        f.urls_json,f.word_count,f.char_count
        FROM records r JOIN features f USING(kind,id) WHERE r.kind='comments' ''')
    complete(db, 'features_v1')


def conversations(db):
    if finished(db, 'conversations_v1'):
        return
    db.execute('''CREATE TABLE IF NOT EXISTS threads(
        thread_id TEXT PRIMARY KEY,post_id TEXT,subreddit TEXT,post_present INTEGER,
        collected_comment_count INTEGER,available_comment_count INTEGER,
        distinct_known_authors INTEGER,unknown_author_comments INTEGER,
        first_comment_utc INTEGER,last_comment_utc INTEGER,
        direct_comment_count INTEGER,broad_comment_count INTEGER,
        top_level_count INTEGER,max_resolved_depth INTEGER,unresolved_depth_count INTEGER,
        missing_comment_parent_count INTEGER,reported_comment_count INTEGER,
        post_direct_layoff INTEGER,post_broad_layoff INTEGER) WITHOUT ROWID''')
    db.execute('''CREATE TABLE IF NOT EXISTS reply_edges(
        child_id TEXT PRIMARY KEY,thread_id TEXT,parent_fullname TEXT,parent_kind TEXT,
        parent_present INTEGER,same_thread INTEGER,child_author_key TEXT,parent_author_key TEXT,
        reply_delay_seconds INTEGER,depth INTEGER,depth_status TEXT) WITHOUT ROWID''')
    db.execute('CREATE INDEX IF NOT EXISTS edges_thread ON reply_edges(thread_id)')
    db.commit()
    # One transaction for the whole stage: no partial graph is exposed on interruption.
    db.execute('DELETE FROM reply_edges')
    db.execute('DELETE FROM threads')
    posts = {r[0]: r[1:] for r in db.execute("SELECT id,subreddit,num_comments,direct_layoff,broad_layoff FROM records WHERE kind='posts'")}
    post_authors = {r[0]: r[1:] for r in db.execute("SELECT r.id,f.author_key,r.created_utc FROM records r JOIN features f USING(kind,id) WHERE r.kind='posts'")}
    query = '''SELECT r.id,r.link_id,r.parent_id,r.subreddit,r.created_utc,
        r.text_state,r.direct_layoff,r.broad_layoff,f.author_key
        FROM records r JOIN features f USING(kind,id) WHERE r.kind='comments' ORDER BY r.link_id'''
    cursor = db.execute(query)
    columns = [r[0] for r in cursor.description]
    count = 0
    seen = set()
    for thread_id, group in itertools.groupby(cursor, lambda r: r[1]):
        members = [dict(zip(columns, row)) for row in group]
        if not thread_id:
            raise ValueError('Comment without link_id')
        seen.add(thread_id)
        lookup = {r['id']: r for r in members}
        depths = thread_depths(members, thread_id)
        post_id = thread_id[3:] if thread_id.startswith('t3_') else None
        post = posts.get(post_id)
        edges = []
        missing = 0
        for r in members:
            parent_name = r['parent_id'] or ''
            parent_kind = 'comments' if parent_name.startswith('t1_') else 'posts' if parent_name.startswith('t3_') else None
            parent_id = parent_name[3:]
            parent_author = None
            parent_time = None
            present, same = 0, None
            if parent_kind == 'comments':
                parent = lookup.get(parent_id)
                if parent:
                    present, same = 1, 1
                    parent_author, parent_time = parent['author_key'], parent['created_utc']
                else:
                    other = db.execute("SELECT r.link_id,r.created_utc,f.author_key FROM records r JOIN features f USING(kind,id) WHERE r.kind='comments' AND r.id=?", (parent_id,)).fetchone()
                    if other:
                        present, same = 1, int(other[0] == thread_id)
                        parent_time, parent_author = other[1], other[2]
                    else:
                        missing += 1
            elif parent_kind == 'posts':
                parent = post_authors.get(parent_id)
                same = int(parent_name == thread_id)
                if parent:
                    present = 1
                    parent_author, parent_time = parent
            delay = r['created_utc'] - parent_time if parent_time is not None else None
            depth, status = depths[r['id']]
            edges.append((r['id'],thread_id,parent_name,parent_kind,present,same,
                r['author_key'],parent_author,delay,depth,status))
        db.executemany('INSERT INTO reply_edges VALUES (?,?,?,?,?,?,?,?,?,?,?)', edges)
        timestamps = [r['created_utc'] for r in members]
        known_authors = {r['author_key'] for r in members if r['author_key']}
        resolved = [d for d,s in depths.values() if d is not None]
        db.execute('INSERT INTO threads VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            thread_id,post_id,post[0] if post else members[0]['subreddit'],int(post is not None),
            len(members),sum(r['text_state']=='available' for r in members),len(known_authors),
            sum(r['author_key'] is None for r in members),min(timestamps),max(timestamps),
            sum(r['direct_layoff'] for r in members),sum(r['broad_layoff'] for r in members),
            sum(r['parent_id']==thread_id for r in members),max(resolved) if resolved else None,
            len(members)-len(resolved),missing,post[1] if post else None,
            post[2] if post else None,post[3] if post else None))
        count += 1
        if count % 10000 == 0:
            print(f'Conversations: {count:,} threads', flush=True)
    for post_id, post in posts.items():
        fullname = 't3_' + post_id
        if fullname not in seen:
            db.execute('INSERT INTO threads VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
                fullname,post_id,post[0],1,0,0,0,0,None,None,0,0,0,None,0,0,post[1],post[2],post[3]))
    db.execute('''CREATE VIEW IF NOT EXISTS author_reply_edges AS
        SELECT child_author_key AS source_author,parent_author_key AS target_author,
        count(*) AS reply_count,count(DISTINCT thread_id) AS thread_count
        FROM reply_edges WHERE parent_present=1 AND same_thread=1
        AND child_author_key IS NOT NULL AND parent_author_key IS NOT NULL
        AND child_author_key != parent_author_key
        GROUP BY child_author_key,parent_author_key''')
    complete(db, 'conversations_v1')


def main():
    ensure_dirs()
    db=connect()
    db.execute('CREATE INDEX IF NOT EXISTS records_source ON records(source_file)')
    db.execute('CREATE INDEX IF NOT EXISTS records_time ON records(created_utc DESC,kind,id)')
    db.commit()
    features(db)
    conversations(db)
    counts={name:db.execute(f'SELECT count(*) FROM {name}').fetchone()[0] for name in ['features','threads','reply_edges']}
    (OUT/'build_summary.json').write_text(json.dumps(counts,indent=2))
    db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    db.close()
    print(json.dumps(counts,indent=2))


if __name__=='__main__':main()
