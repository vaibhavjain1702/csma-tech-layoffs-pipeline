#!/usr/bin/env python3
"""Export analysis-ready CSV tables without loading the corpus into memory."""
import argparse
import csv
import gzip
import json
from datetime import datetime,timezone
from project import research_db,TABLES,ensure_dirs


def export_table(db,name,query,compressed=True):
    destination=TABLES/(name+'.csv.gz' if compressed else name+'.csv')
    temp=destination.with_name(destination.name+'.tmp')
    cursor=db.execute(query);columns=[field[0] for field in cursor.description]
    count=0
    handle=gzip.open(temp,'wt',encoding='utf-8',newline='',compresslevel=1) if compressed else temp.open('w',encoding='utf-8',newline='')
    with handle as f:
        writer=csv.writer(f);writer.writerow(columns)
        for row in cursor:writer.writerow(row);count+=1
    temp.replace(destination)
    print(f'{name}: {count:,} rows -> {destination.name}',flush=True)
    return {'file':destination.name,'rows':count,'columns':columns,'bytes':destination.stat().st_size}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tables',nargs='+',choices=['posts','comments','threads','reply_edges'],default=['posts','comments','threads','reply_edges'])
    args=parser.parse_args();ensure_dirs()
    queries={
        'posts':'''SELECT p.id,p.subreddit,p.created_utc,p.created_month,p.author_key,
            p.author_unknown,p.likely_bot,p.title,p.text AS raw_body,p.text_state,
            p.clean_text,p.own_text,p.quoted_text,p.word_count,p.char_count,
            p.urls_json,p.source_url,p.domain,p.is_self,p.score,p.num_comments AS reported_comments,
            p.direct_layoff AS direct_keyword_match,p.broad_layoff AS broad_keyword_match,
            t.collected_comment_count,p.retrieved_utc,p.source_file
            FROM posts p JOIN threads t ON t.thread_id='t3_'||p.id ORDER BY p.id''',
        'comments':'''SELECT c.id,c.link_id AS thread_id,c.parent_id,c.subreddit,
            c.created_utc,c.created_month,c.author_key,c.author_unknown,c.likely_bot,
            c.text AS raw_body,c.text_state,c.clean_text,c.own_text,c.quoted_text,
            c.word_count,c.char_count,c.urls_json,c.score,
            c.direct_layoff AS direct_keyword_match,c.broad_layoff AS broad_keyword_match,
            t.post_present,e.parent_present,e.same_thread AS parent_same_thread,
            e.depth,e.depth_status,e.reply_delay_seconds,c.retrieved_utc,c.source_file
            FROM comments c JOIN threads t ON t.thread_id=c.link_id
            JOIN reply_edges e ON e.child_id=c.id ORDER BY c.id''',
        'threads':'''SELECT *,CASE WHEN first_comment_utc IS NOT NULL
            THEN last_comment_utc-first_comment_utc ELSE NULL END AS observed_duration_seconds
            FROM threads ORDER BY thread_id''',
        'reply_edges':'SELECT * FROM reply_edges ORDER BY child_id'
    }
    entries=[]
    with research_db() as db:
        for name in args.tables:entries.append(export_table(db,name,queries[name],name!='threads'))
    manifest={'generated_utc':datetime.now(timezone.utc).isoformat(),'encoding':'UTF-8','separator':',',
        'timestamps':'Unix seconds in UTC; nulls exported as empty cells',
        'compression':'gzip level 1 for large tables; readable directly by pandas read_csv',
        'tables':entries,'raw_files_modified':False}
    (TABLES/'manifest.json').write_text(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
