#!/usr/bin/env python3
"""Export reproducible node/edge CSVs for Gephi, using Python's standard library.

Default: author replies originating in explicit keyword-matching comments.
python gephi/scripts/export_gephi.py
python gephi/scripts/export_gephi.py --network conversations --scope keyword-posts
"""
import argparse
import csv
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from project import DB_PATH,GEPHI,ensure_dirs


def write_csv(path,columns,rows):
    count=0
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(columns)
        for row in rows:writer.writerow(row);count+=1
    return count


def iso(timestamp):
    return datetime.fromtimestamp(timestamp,timezone.utc).isoformat() if timestamp is not None else ''


def select_scope(db,scope,match,subreddit=None,start=None,end=None):
    flag='direct_layoff' if match=='direct' else 'broad_layoff'
    db.execute('CREATE TEMP TABLE selected_threads(thread_id TEXT PRIMARY KEY) WITHOUT ROWID')
    if scope in ('keyword-posts','candidate-threads'):
        where=f'post_{flag}=1'
        if scope=='candidate-threads':where+=f' OR {"direct" if match=="direct" else "broad"}_comment_count>0'
        db.execute(f'INSERT INTO selected_threads SELECT thread_id FROM threads WHERE {where}')
    elif scope=='sample-threads':
        db.execute("INSERT INTO selected_threads SELECT DISTINCT CASE WHEN r.kind='posts' THEN 't3_'||r.id ELSE r.link_id END FROM reading_sample s JOIN records r USING(kind,id)")
    elif scope=='all':
        db.execute('INSERT INTO selected_threads SELECT thread_id FROM threads')
    elif scope!='keyword-comments':
        raise ValueError('Unknown scope')
    filters=[];values=[]
    if scope=='keyword-comments':filters.append(f'r.{flag}=1')
    else:filters.append('e.thread_id IN (SELECT thread_id FROM selected_threads)')
    if subreddit:filters.append('r.subreddit=?');values.append(subreddit)
    if start:filters.append('r.created_utc>=?');values.append(start)
    if end:filters.append('r.created_utc<?');values.append(end)
    db.execute('''CREATE TEMP TABLE selected_edges AS SELECT e.*,r.subreddit,r.created_utc,
        r.score,r.text_state,r.direct_layoff,r.broad_layoff
        FROM reply_edges e JOIN records r ON r.kind='comments' AND r.id=e.child_id
        WHERE '''+' AND '.join(filters),values)
    if scope=='keyword-comments':
        db.execute('INSERT INTO selected_threads SELECT DISTINCT thread_id FROM selected_edges')
    elif subreddit or start or end:
        # Filtered thread scope includes only threads with selected comments.
        db.execute('DELETE FROM selected_threads WHERE thread_id NOT IN (SELECT thread_id FROM selected_edges)')
    db.execute('CREATE INDEX selected_edge_threads ON selected_edges(thread_id)')


def author_graph(db,destination,min_weight):
    quality={
        'selected_comments':db.execute('SELECT count(*) FROM selected_edges').fetchone()[0],
        'missing_parent':db.execute('SELECT count(*) FROM selected_edges WHERE parent_present=0').fetchone()[0],
        'unknown_child_author':db.execute('SELECT count(*) FROM selected_edges WHERE child_author_key IS NULL').fetchone()[0],
        'unknown_parent_author':db.execute('SELECT count(*) FROM selected_edges WHERE parent_author_key IS NULL').fetchone()[0],
        'self_replies':db.execute('SELECT count(*) FROM selected_edges WHERE child_author_key=parent_author_key').fetchone()[0],
        'cross_thread_parent':db.execute('SELECT count(*) FROM selected_edges WHERE same_thread=0').fetchone()[0],
    }
    db.execute('''CREATE TEMP TABLE pairs AS SELECT child_author_key AS source,
        parent_author_key AS target,count(*) AS weight,count(DISTINCT thread_id) AS thread_count,
        min(created_utc) AS first_utc,max(created_utc) AS last_utc
        FROM selected_edges WHERE parent_present=1 AND same_thread=1
        AND child_author_key IS NOT NULL AND parent_author_key IS NOT NULL
        AND child_author_key!=parent_author_key
        GROUP BY child_author_key,parent_author_key HAVING count(*)>=?''',(min_weight,))
    db.execute('CREATE TEMP TABLE graph_nodes AS SELECT source AS id FROM pairs UNION SELECT target FROM pairs')
    db.execute('CREATE UNIQUE INDEX graph_node_id ON graph_nodes(id)')
    db.execute('CREATE TEMP TABLE node_out AS SELECT source AS id,count(*) AS degree,sum(weight) AS strength FROM pairs GROUP BY source')
    db.execute('CREATE TEMP TABLE node_in AS SELECT target AS id,count(*) AS degree,sum(weight) AS strength FROM pairs GROUP BY target')
    db.execute('CREATE TEMP TABLE node_comments AS SELECT child_author_key AS id,count(*) AS comments FROM selected_edges WHERE child_author_key IS NOT NULL GROUP BY child_author_key')
    query='''SELECT n.id,'Reader '||substr(n.id,3,8),coalesce(c.comments,0),
        coalesce(o.degree,0),coalesce(i.degree,0),coalesce(o.strength,0),coalesce(i.strength,0)
        FROM graph_nodes n LEFT JOIN node_out o USING(id) LEFT JOIN node_in i USING(id)
        LEFT JOIN node_comments c USING(id) ORDER BY n.id'''
    nodes=write_csv(destination/'nodes.csv',['Id','Label','ScopeCommentCount','OutDegreeRetained','InDegreeRetained','OutWeightRetained','InWeightRetained'],db.execute(query))
    def edges():
        for index,r in enumerate(db.execute('SELECT * FROM pairs ORDER BY source,target'),1):
            source,target,weight,threads,first,last=r
            yield f'e{index}',source,target,'Directed',weight,threads,iso(first),iso(last)
    count=write_csv(destination/'edges.csv',['Id','Source','Target','Type','Weight','ThreadCount','FirstReplyUTC','LastReplyUTC'],edges())
    return {'nodes':nodes,'edges':count,'total_retained_replies':db.execute('SELECT coalesce(sum(weight),0) FROM pairs').fetchone()[0],
            'edge_direction':'replying author -> author of parent comment/submission',
            'weight':'Number of selected observed replies from Source to Target',
            'quality_counts_overlapping':quality,'minimum_pair_weight':min_weight,
            'excluded':'Unknown authors, absent parent content, different-thread parents, self-replies, pairs below minimum weight; isolated nodes are not included.'}


def conversation_graph(db,destination):
    db.execute('''CREATE TEMP TABLE graph_nodes(id TEXT PRIMARY KEY) WITHOUT ROWID''')
    db.execute("INSERT INTO graph_nodes SELECT 't1_'||child_id FROM selected_edges")
    db.execute('INSERT OR IGNORE INTO graph_nodes SELECT parent_fullname FROM selected_edges WHERE parent_fullname IS NOT NULL AND parent_fullname!=""')
    db.execute('INSERT OR IGNORE INTO graph_nodes SELECT thread_id FROM selected_threads')
    query='''SELECT n.id,r.kind,r.id,r.subreddit,r.title,r.created_utc,r.score,r.text_state,
        f.author_key,e.depth,e.depth_status,r.direct_layoff,r.broad_layoff,
        substr(f.clean_text,1,200)
        FROM graph_nodes n LEFT JOIN records r ON
        r.kind=CASE WHEN substr(n.id,1,3)='t1_' THEN 'comments' ELSE 'posts' END AND r.id=substr(n.id,4)
        LEFT JOIN features f ON f.kind=r.kind AND f.id=r.id
        LEFT JOIN reply_edges e ON r.kind='comments' AND e.child_id=r.id ORDER BY n.id'''
    def nodes():
        for r in db.execute(query):
            fullname,kind,id,sub,title,created,score,textstate,author,depth,depthstate,direct,broad,preview=r
            present=int(kind is not None)
            node_kind=kind or ('comments' if fullname.startswith('t1_') else 'posts')
            label=title[:100] if title else ('Comment '+fullname[3:] if present else 'Missing '+fullname)
            yield fullname,label,node_kind,present,sub or '',iso(created),score if score is not None else '',textstate or 'not_collected',author or '',depth if depth is not None else '',depthstate or '',direct if direct is not None else '',broad if broad is not None else '',preview or ''
    count=write_csv(destination/'nodes.csv',['Id','Label','RecordKind','Present','Subreddit','CreatedUTC','Score','TextState','AuthorKey','Depth','DepthStatus','DirectMatch','BroadMatch','TextPreview'],nodes())
    def edges():
        for r in db.execute('SELECT child_id,parent_fullname,thread_id,parent_present,reply_delay_seconds,depth_status,same_thread FROM selected_edges ORDER BY child_id'):
            child,parent,thread,present,delay,status,same=r
            if parent:
                yield 'reply_'+child,'t1_'+child,parent,'Directed',1,thread,present,delay if delay is not None else '',status,same if same is not None else ''
    edgecount=write_csv(destination/'edges.csv',['Id','Source','Target','Type','Weight','ThreadId','ParentPresent','ReplyDelaySeconds','DepthStatus','SameThread'],edges())
    return {'nodes':count,'edges':edgecount,'missing_placeholder_nodes':db.execute('''SELECT count(*) FROM graph_nodes n WHERE NOT EXISTS
        (SELECT 1 FROM records r WHERE r.kind=CASE WHEN substr(n.id,1,3)='t1_' THEN 'comments' ELSE 'posts' END AND r.id=substr(n.id,4))''').fetchone()[0],
        'edge_direction':'replying comment -> parent comment/submission',
        'weight':'1 per observed reply relationship',
        'context':'Immediate parent nodes and structural roots are included; keyword-comments scope is not a complete conversation tree. Missing records have Present=0. No inferred edges are added.'}


def utc_boundary(value):
    return int(datetime.strptime(value,'%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp()) if value else None


def validate_files(destination):
    with (destination/'nodes.csv').open(newline='') as f:
        node_ids=[r['Id'] for r in csv.DictReader(f)]
    if len(node_ids)!=len(set(node_ids)):raise ValueError('Duplicate node IDs')
    ids=set(node_ids);edge_ids=set();total=0
    with (destination/'edges.csv').open(newline='') as f:
        for edge in csv.DictReader(f):
            if edge['Source'] not in ids or edge['Target'] not in ids:raise ValueError('Dangling edge endpoint')
            if edge['Id'] in edge_ids:raise ValueError('Duplicate edge ID')
            if edge['Type']!='Directed' or float(edge['Weight'])<=0:raise ValueError('Invalid edge type/weight')
            edge_ids.add(edge['Id']);total+=1
    return {'unique_nodes':len(ids),'unique_edges':total,'dangling_endpoints':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--network',choices=['authors','conversations'],default='authors')
    parser.add_argument('--scope',choices=['keyword-comments','keyword-posts','candidate-threads','sample-threads','all'])
    parser.add_argument('--match',choices=['direct','broad'],default='direct')
    parser.add_argument('--subreddit',choices=['technology','programming','cscareerquestions'])
    parser.add_argument('--start',help='Inclusive comment creation date, YYYY-MM-DD UTC')
    parser.add_argument('--end',help='Exclusive comment creation date, YYYY-MM-DD UTC')
    parser.add_argument('--min-weight',type=int,default=1,help='Minimum author-pair reply count; authors network only')
    parser.add_argument('--output',type=Path,help='Output directory; otherwise derived from selected scope')
    args=parser.parse_args()
    if args.min_weight<1:parser.error('--min-weight must be positive')
    if args.network=='conversations' and args.min_weight!=1:parser.error('--min-weight applies only to author networks')
    scope=args.scope or ('keyword-comments' if args.network=='authors' else 'keyword-posts')
    start,end=utc_boundary(args.start),utc_boundary(args.end)
    if start is not None and end is not None and start>=end:parser.error('--start must be before --end')
    suffix=''.join('_'+s for s in [args.subreddit,args.start,args.end] if s)
    if args.min_weight>1:suffix+=f'_weight{args.min_weight}'
    ensure_dirs()
    destination=args.output or GEPHI/f'{args.network}_{scope}_{args.match}{suffix}'
    destination.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(f'file:{DB_PATH}?mode=ro',uri=True)
    db.execute('PRAGMA cache_size=-32768')
    select_scope(db,scope,args.match,args.subreddit,start,end)
    info=author_graph(db,destination,args.min_weight) if args.network=='authors' else conversation_graph(db,destination)
    info.update({'network':args.network,'scope':scope,'match':args.match,'subreddit':args.subreddit,
        'start_inclusive_utc':args.start,'end_exclusive_utc':args.end,
        'selected_threads':db.execute('SELECT count(*) FROM selected_threads').fetchone()[0],
        'selected_comments':db.execute('SELECT count(*) FROM selected_edges').fetchone()[0],
        'validation':validate_files(destination),'encoding':'UTF-8','separator':',',
        'relevance':'Keyword scopes are retrieval heuristics, not validated layoff relevance.',
        'created_utc':datetime.now(timezone.utc).isoformat()})
    (destination/'manifest.json').write_text(json.dumps(info,indent=2))
    db.close();print(json.dumps({'output':str(destination),**info},indent=2))


if __name__=='__main__':main()
