"""Record and bounded-context access for offline analysis; no web dependencies."""
import json
from project import research_db


def record(db,kind,id):
    row=db.execute('''SELECT r.*,f.author_key,f.author_unknown,f.likely_bot,
        f.clean_text,f.own_text,f.quoted_text,f.urls_json,f.word_count,f.char_count,
        f.source_url,f.domain,e.depth,e.depth_status,e.parent_present,e.reply_delay_seconds,
        s.sample_id,s.group_name AS sample_group,s.stratum
        FROM records r JOIN features f USING(kind,id)
        LEFT JOIN reply_edges e ON r.kind='comments' AND e.child_id=r.id
        LEFT JOIN reading_sample s ON s.kind=r.kind AND s.id=r.id
        WHERE r.kind=? AND r.id=?''',(kind,id)).fetchone()
    if not row:
        return None
    result=dict(row)
    result['urls']=json.loads(result.pop('urls_json') or '[]')
    result['thread_id']='t3_'+id if kind=='posts' else result['link_id']
    return result



def context(db,focus,max_ancestors=30):
    """Context is explicit and bounded; it never claims thread completeness."""
    root=record(db,'posts',focus['thread_id'][3:])
    ancestors=[]
    seen={focus['id']}
    parent=focus.get('parent_id') if focus['kind']=='comments' else None
    missing_parent=None
    while parent and parent.startswith('t1_') and len(ancestors)<max_ancestors:
        parent_id=parent[3:]
        if parent_id in seen:
            missing_parent={'id':parent,'reason':'cycle'};break
        seen.add(parent_id)
        found=record(db,'comments',parent_id)
        if not found:
            missing_parent={'id':parent,'reason':'not_collected'};break
        if found['thread_id']!=focus['thread_id']:
            missing_parent={'id':parent,'reason':'different_thread'};break
        ancestors.append(found);parent=found['parent_id']
    truncated=bool(parent and parent.startswith('t1_') and len(ancestors)>=max_ancestors)
    child_parent=('t1_' if focus['kind']=='comments' else 't3_')+focus['id']
    child_ids=db.execute('''SELECT child_id FROM reply_edges WHERE thread_id=? AND parent_fullname=?
        ORDER BY child_id LIMIT 41''',(focus['thread_id'],child_parent)).fetchall()
    children=[record(db,'comments',r[0]) for r in child_ids[:40]]
    return {'post':root,'ancestors':list(reversed(ancestors)),'children':children,
            'more_children':len(child_ids)>40,'missing_parent':missing_parent,
            'ancestors_truncated':truncated}

