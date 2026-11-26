#!/usr/bin/env python3
"""Generate an exploratory reading sample and offline context packet.

Employment and legacy layoff samples have separate outputs and working labels.
"""
import argparse
import csv
import heapq
import hashlib
import json
import sqlite3
from collections import Counter,defaultdict
from datetime import datetime,timezone
from project import DB_PATH,SAMPLE,ANNOTATIONS,ensure_dirs
from preprocess_data import complete
from disruption_rules import FACETS,VERSION,FINGERPRINT


def sample(db, focus, seed, out):
    quotas = ({'keyword_post':70,'keyword_comment':90,'background_post':20,'background_comment':20}
        if focus=='layoffs' else {'layoffs':40,'hiring_conditions':40,'ai_work_change':30,
        'corporate_restructuring':20,'economic_policy':20,'career_transition':20,'background':30})
    pools = defaultdict(lambda: defaultdict(list))
    counts = defaultdict(Counter)
    query = '''SELECT r.kind,r.id,r.subreddit,r.created_month,r.created_utc,r.score,
        r.direct_layoff,r.broad_layoff,r.link_id,r.text_state,r.title,
        substr(f.clean_text,1,260),t.collected_comment_count,t.post_present,'''
    query += ','.join(f'coalesce(s.{facet},0)' for facet in FACETS) + ''',s.evidence_json
        FROM records r JOIN features f USING(kind,id)
        JOIN threads t ON t.thread_id=CASE WHEN r.kind='posts' THEN 't3_'||r.id ELSE r.link_id END
        LEFT JOIN disruption_screen s USING(kind,id)
        WHERE r.kind='posts' OR r.text_state='available' '''
    for row in db.execute(query):
        kind,id,sub,month,created,score,direct,broad,link,state,title,preview,ncomments,post_present = row[:14]
        if focus=='layoffs':
            groups=[('keyword_' if broad else 'background_') + ('post' if kind=='posts' else 'comment')]
        else:
            groups=[facet for facet,flag in zip(FACETS,row[14:20]) if flag] or ['background']
        quarter = month[:4]+'-Q'+str((int(month[5:])-1)//3+1)
        engagement = 'low' if (score or 0)<=1 else 'middle' if (score or 0)<=(713 if kind=='posts' else 15) else 'high'
        stratum = '|'.join((sub,quarter,engagement) if focus=='layoffs' else (sub,quarter,kind,engagement))
        priority = int.from_bytes(hashlib.sha256(f'{seed}|{kind}|{id}'.encode()).digest()[:8], 'big')
        item = (-priority,id,row)
        for group in groups:
            counts[group][stratum] += 1
            pool = pools[group][stratum]
            capacity = quotas[group] * (3 if focus=='employment' else 1)
            if len(pool) < capacity:heapq.heappush(pool,item)
            elif item > pool[0]:heapq.heapreplace(pool,item)
    selected = []
    manifest = {'seed':seed,'focus':focus,'target_size':200,
        'method':'Balanced round-robin over community × UTC quarter × score band'+(' × record kind' if focus=='employment' else '')+' within retrieval groups; deterministic hash ordering; at most one selected record per thread within each group. Exploratory, not population-representative.',
        'score_bands':{'posts':{'low':'<=1','middle':'2–713','high':'>713'},'comments':{'low':'<=1','middle':'2–15','high':'>15'}},
        'groups':{},'created_utc':datetime.now(timezone.utc).isoformat()}
    if focus=='employment':
        manifest.update({'screen_version':VERSION,'rule_fingerprint':FINGERPRINT,
            'group_overlap':'Eligible facet groups overlap. Fixed quota order and global record deduplication assign each selected record to one sampling group; all its flags are retained. Group is not a qualitative label.',
            'background':'No broader screen matched. This does not establish irrelevance.',
            'eligibility':'All posts (titles retained), and comments with available bodies; missing roots retained explicitly.'})
    selected_keys=set()
    for group, quota in quotas.items():
        strata = sorted(pools[group],key=lambda s:hashlib.sha256(f'{seed}|{group}|{s}'.encode()).hexdigest())
        ordered = {s: sorted(pools[group][s],reverse=True) for s in strata}
        seen_threads, chosen = set(), []
        while len(chosen)<quota:
            changed = False
            for stratum in strata:
                while ordered[stratum]:
                    _,_,row = ordered[stratum].pop(0)
                    thread = 't3_'+row[1] if row[0]=='posts' else row[8]
                    key=(row[0],row[1])
                    if thread in seen_threads or key in selected_keys:continue
                    seen_threads.add(thread);selected_keys.add(key)
                    chosen.append((row,stratum));changed=True;break
                if len(chosen)==quota:break
            if not changed:break
        manifest['groups'][group]={'target':quota,'selected':len(chosen),'eligible':sum(counts[group].values()),'eligible_strata':dict(counts[group]),'selected_strata':dict(Counter(s for r,s in chosen))}
        for row,stratum in chosen:
            kind,id,sub,month,created,score,direct,broad,link,state,title,preview,ncomments,post_present=row[:14]
            bodies=db.execute('''SELECT r.text,f.own_text,f.quoted_text FROM records r
                JOIN features f USING(kind,id) WHERE r.kind=? AND r.id=?''',(kind,id)).fetchone()
            item={'sample_id':f'{"E" if focus=="employment" else "S"}{len(selected)+1:03d}','kind':kind,'id':id,
                'group':group,'stratum':stratum,'subreddit':sub,'created_month':month,
                'created_utc':created,'score':score,'direct_layoff':direct,'broad_layoff':broad,
                'thread_id':'t3_'+id if kind=='posts' else link,'post_present':post_present,
                'collected_comments':ncomments,'title':title,'preview':preview,
                'raw_body':bodies[0],'own_body':bodies[1],'quoted_body':bodies[2]}
            if focus=='employment':
                item.update(dict(zip(FACETS,row[14:20])))
                item['screen_evidence_json']=row[20] or '{}'
            item.update({'relevance':'','document_type':'','themes':'','emotions':'','response_function':'','notes':''})
            if focus=='employment':
                item.update({'experiences':'','explanations':'','future_expectations':''})
            selected.append(item)
    if len(selected)!=200:raise ValueError(f'Only {len(selected)} records selected; inspect eligible frames')
    out.mkdir(parents=True,exist_ok=True)
    (out/'reading_sample.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2))
    (out/'sample_manifest.json').write_text(json.dumps(manifest,indent=2))
    with (out/'reading_sample.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(selected[0]));writer.writeheader();writer.writerows(selected)
    table='reading_sample' if focus=='layoffs' else 'reading_sample_employment'
    db.execute(f'CREATE TABLE IF NOT EXISTS {table}(sample_id TEXT PRIMARY KEY,kind TEXT,id TEXT,group_name TEXT,stratum TEXT,UNIQUE(kind,id))')
    db.execute(f'DELETE FROM {table}')
    db.executemany(f'INSERT INTO {table} VALUES (?,?,?,?,?)',[(r['sample_id'],r['kind'],r['id'],r['group'],r['stratum']) for r in selected])
    complete(db,'sample_v1' if focus=='layoffs' else 'sample_employment_v1')
    print(f'Reading sample ({focus}): 200 records',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--focus',choices=['employment','layoffs'],default='employment')
    parser.add_argument('--seed',default=None)
    args=parser.parse_args();ensure_dirs()
    seed=args.seed or ('csma-reading-v1-2026-10-04' if args.focus=='layoffs' else 'csma-employment-reading-v1-2026-10-04')
    out=SAMPLE if args.focus=='layoffs' else SAMPLE/'employment'
    with sqlite3.connect(DB_PATH) as db:
        db.execute('PRAGMA cache_size=-16384')
        build=db.execute('SELECT fingerprint FROM screening_builds WHERE version=?',(VERSION,)).fetchone()
        if not build or build[0]!=FINGERPRINT:raise ValueError('Run screen_disruption.py with current rules before sampling')
        sample(db,args.focus,seed,out)
    # Generated samples can be refreshed; working labels are never overwritten.
    labels=ANNOTATIONS/('reading_labels.csv' if args.focus=='layoffs' else 'reading_labels_employment.csv')
    if not labels.exists():
        import shutil
        shutil.copyfile(out/'reading_sample.csv',labels)
    from export_reading_packet import export_packet
    export_packet(out)


if __name__=='__main__':main()
