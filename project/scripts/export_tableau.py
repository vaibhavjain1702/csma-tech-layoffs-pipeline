"""Tableau extracts for the five results (R1-R5). Read-only.

Writes tidy CSVs at several levels (day, thread, comment, reply pair, author, type flow, network
layout, robustness) to outputs/16_tableau/, plus TABLEAU_GUIDE.md describing each file.

Privacy: no comment text, no usernames, no Reddit ids, no author hashes. Authors and threads get
neutral sequential ids (p..., t...) that cannot be reversed. R4 files keep the network ids (a.../n...)
from outputs/15_network, which are a separate scheme.

Markers are reused from explore_leads.M and explore_replies.PARENT/REPLY (no new regexes).
Run: .venv-eda/bin/python scripts/export_tableau.py   (needs outputs/15_network from explore_network.py)
"""
import csv, sys, time, math
from datetime import date, timedelta
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from explore_leads import M, connect
from explore_replies import PARENT, REPLY, CAND

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/16_tableau'
NET = ROOT / 'outputs/15_network'
SEED = 20261125
FACETS = ['layoffs', 'hiring_conditions', 'ai_work_change', 'corporate_restructuring', 'economic_policy', 'career_transition']
CONTENT_M = ['first_person_layoff', 'exec_blame', 'offshore_h1b', 'ethnic_ref', 'individual_blame', 'ai_pretext', 'ai_inevitable',
             'ai_any', 'macro', 'overhiring', 'consequence', 'realism']
# plain-language names for Tableau (same order as CONTENT_M)
CONTENT_NAME = ['own_layoff_story', 'mentions_execs', 'mentions_offshore_visa', 'ethnic_reference', 'blames_workers', 'ai_is_excuse',
                'ai_will_replace', 'mentions_ai', 'macro_economy', 'overhiring', 'consequences', 'doom']
RTYPES = list(REPLY)
SHARED = ('2025-01', '2025-06')
t0 = time.time()

def log(m): print(f'[{time.time()-t0:5.0f}s] {m}', flush=True)

def write(name, rows, header=None):
    p = OUT / name; p.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows); header = header or (list(rows[0].keys()) if rows else [])
    with p.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    log(f'{name}: {len(rows):,} rows')
    return len(rows)

def in_window(month): return int(SHARED[0] <= month <= SHARED[1])

class Ids:
    """Neutral sequential ids, assigned in first-seen order."""
    def __init__(self, prefix): self.p, self.d = prefix, {}
    def __call__(self, key):
        if key is None: return ''
        if key not in self.d: self.d[key] = f'{self.p}{len(self.d)}'
        return self.d[key]

def words_band(w):
    return '0-29' if w < 30 else '30-149' if w < 150 else '150-399' if w < 400 else '400+'

# ---------------------------------------------------------------------------
def r1_daily(c):
    """R1 + R5 coverage: one row per day x community x kind."""
    q = f"""select date(r.created_utc,'unixepoch') d, r.created_month, r.subreddit, r.kind, count(*),
        sum(f.likely_bot), sum(f.author_unknown), sum(r.text_state='available'), sum(r.text_state in ('deleted','removed')),
        {','.join(f'sum(coalesce(s.{x},0))' for x in FACETS)},
        sum(case when s.id is not null and {CAND.replace('d.', 's.')} then 1 else 0 end)
        from records r left join features f on f.kind=r.kind and f.id=r.id
        left join disruption_screen s on s.kind=r.kind and s.id=r.id
        group by 1,2,3,4"""
    rows = []
    for d, mth, sub, kind, n, bot, unk, avail, gone, *fac in c.execute(q):
        emp = fac.pop()
        dd = date.fromisoformat(d)
        row = dict(date=d, week_start=(dd - timedelta(days=dd.weekday())).isoformat(), month=mth,  # weeks start Monday
                   subreddit=sub, kind=kind, in_shared_window=in_window(mth), records=n, bot_records=bot or 0, unknown_author_records=unk or 0,
                   text_available=avail or 0, text_deleted_or_removed=gone or 0, employment_screened=emp)
        row.update({f'facet_{x}': v for x, v in zip(FACETS, fac)})
        rows.append(row)
    return write('r1_daily_by_community.csv', rows)

def r1_threads(c, tid):
    """R1: one row per thread (comments only; cscq has no posts in the database)."""
    q = f"""select r.link_id, r.subreddit, min(r.created_month), count(*), count(distinct f.author_key),
        sum(coalesce(s.layoffs,0)), sum(case when s.id is not null and {CAND.replace('d.', 's.')} then 1 else 0 end),
        sum(coalesce(s.ai_work_change,0)), min(r.created_utc), max(r.created_utc), max(t.post_present)
        from records r left join features f on f.kind='comments' and f.id=r.id
        left join disruption_screen s on s.kind='comments' and s.id=r.id
        left join threads t on t.thread_id=r.link_id
        where r.kind='comments' group by r.link_id, r.subreddit"""
    rows = []
    for link, sub, mth, n, auth, lay, emp, ai, a, b, pp in c.execute(q):
        band = '1-9' if n < 10 else '10-49' if n < 50 else '50-199' if n < 200 else '200-999' if n < 1000 else '1000+'
        rows.append(dict(thread_id=tid(link), subreddit=sub, first_month=mth, in_shared_window=in_window(mth), comments=n,
                         distinct_authors=auth, size_band=band, layoff_comments=lay, employment_comments=emp, ai_work_comments=ai,
                         layoff_share=round(lay / n, 4), has_layoff_talk=int(lay > 0), active_hours=round((b - a) / 3600, 1),
                         post_in_database=pp or 0))
    return write('r1_threads.csv', rows)

def r2_comments(c, pid, tid):
    """R2 (and R3 parent side): one row per employment-screened comment, with marker flags."""
    c.execute("create temp table if not exists wr(id text primary key, pr real, tr real) without rowid")
    c.execute("""insert or ignore into wr select id, percent_rank() over (partition by link_id order by score),
                 percent_rank() over (partition by link_id order by created_utc) from records where kind='comments'""")
    log('within-thread ranks done')
    q = f"""select r.id, r.subreddit, date(r.created_utc,'unixepoch'), r.created_month, r.score, w.pr, w.tr, r.link_id,
        f.author_key, f.likely_bot, f.author_unknown, coalesce(f.own_text,''), coalesce(f.word_count,0), e.parent_kind, e.depth,
        {','.join('s.' + x for x in FACETS)}, case when {CAND.replace('d.', 's.')} then 1 else 0 end
        from disruption_screen s join records r on r.kind='comments' and r.id=s.id
        join features f on f.kind='comments' and f.id=s.id left join wr w on w.id=s.id
        left join reply_edges e on e.child_id=s.id where s.kind='comments'"""
    # replies received per comment (human, non-self)
    rows, cid = [], {}
    for (i, sub, d, mth, score, pr, tr, link, ak, bot, unk, txt, wc, pk, depth, *fac) in c.execute(q):
        emp = fac.pop()
        if bot or not txt: continue
        cid['t1_' + i] = len(rows)
        row = dict(comment_id=f'c{len(rows)}', subreddit=sub, date=d, month=mth, in_shared_window=in_window(mth),
                   author_id=pid(ak) if not unk else '', thread_id=tid(link), score=score,
                   score_pct_in_thread=round(pr, 3) if pr is not None else '', arrival_pct_in_thread=round(tr, 3) if tr is not None else '',
                   early_arrival=int(tr is not None and tr <= 0.2), top_level=int(pk == 'posts'), depth=depth if depth is not None else '',
                   words=wc, words_band=words_band(wc), employment_core=emp)
        row.update({f'facet_{x}': v for x, v in zip(FACETS, fac)})
        for k, nm in zip(CONTENT_M, CONTENT_NAME): row[nm] = int(bool(M[k].search(txt)))
        row['any_blame_topic'] = int(row['mentions_execs'] or row['mentions_offshore_visa'] or row['ai_is_excuse'])
        rows.append(row)
    log(f'comments labelled {len(rows):,}')
    n_rep = Counter()
    for (pf,) in c.execute("""select e.parent_fullname from reply_edges e join features f on f.kind='comments' and f.id=e.child_id
                              where e.parent_kind='comments' and f.likely_bot=0 and f.author_unknown=0 and e.child_author_key<>coalesce(e.parent_author_key,'')"""):
        j = cid.get(pf)
        if j is not None: n_rep[j] += 1
    for j, r in enumerate(rows): r['human_replies_received'] = n_rep.get(j, 0)
    write('r2_employment_comments.csv', rows)
    return rows, cid

def r2_rates(rows):
    """R2: marker rates by community x month x base (long format)."""
    agg = defaultdict(Counter)
    for r in rows:
        bases = ['all_screened'] + (['employment_core'] if r['employment_core'] else []) + (['layoff_comments'] if r['facet_layoffs'] else [])
        for b in bases:
            k = (r['subreddit'], r['month'], b); agg[k]['n'] += 1
            for m in CONTENT_NAME + ['any_blame_topic']: agg[k][m] += r[m]
    out = []
    for (sub, mth, b), cnt in sorted(agg.items()):
        for m in CONTENT_NAME + ['any_blame_topic']:
            out.append(dict(subreddit=sub, month=mth, in_shared_window=in_window(mth), base=b, marker=m, hits=cnt[m], base_comments=cnt['n'],
                            rate=round(cnt[m] / cnt['n'], 4)))
    write('r2_marker_rates_long.csv', out)

def r2_cross_posters(rows):
    """R2 / D1: authors with >= 2 employment comments in both cscq and r/technology, Jan-Jun 2025."""
    by = defaultdict(lambda: defaultdict(Counter))
    for r in rows:
        if r['author_id'] and r['in_shared_window'] and r['employment_core'] and r['subreddit'] in ('cscareerquestions', 'technology'):
            cc = by[r['author_id']][r['subreddit']]; cc['n'] += 1
            for m in CONTENT_NAME: cc[m] += r[m]
    out = []
    for a, d in by.items():
        if all(d[s]['n'] >= 2 for s in ('cscareerquestions', 'technology')):
            for s in ('cscareerquestions', 'technology'):
                out.append(dict(author_id=a, subreddit=s, employment_comments=d[s]['n'],
                                **{f'rate_{m}': round(d[s][m] / d[s]['n'], 4) for m in CONTENT_NAME}))
    write('r2_cross_posters_same_author.csv', out)

def r3_pairs(c, rows, cid, pid):
    """R3: one row per human reply to a cscq employment comment (H3 definition)."""
    q = """select e.parent_fullname, f.author_key, r.score, coalesce(f.own_text,''), coalesce(f.word_count,0), e.reply_delay_seconds,
           e.parent_author_key
           from reply_edges e join records r on r.kind='comments' and r.id=e.child_id join features f on f.kind='comments' and f.id=e.child_id
           where e.parent_kind='comments' and f.likely_bot=0 and f.author_unknown=0 and coalesce(f.own_text,'')<>''"""
    out = []
    parents_txt = {}
    for pf, ak, score, txt, wc, delay, pak in c.execute(q):
        j = cid.get(pf)
        if j is None: continue
        p = rows[j]
        if p['subreddit'] != 'cscareerquestions' or not p['employment_core'] or not p['author_id'] or pid(ak) == p['author_id']: continue
        rr = dict(pair_id=f'r{len(out)}', parent_comment_id=p['comment_id'], month=p['month'], in_shared_window=p['in_shared_window'],
                  thread_id=p['thread_id'], parent_author_id=p['author_id'], replier_author_id=pid(ak), parent_score=p['score'],
                  parent_words_band=p['words_band'], parent_early_arrival=p['early_arrival'], reply_score=score, reply_words=wc,
                  reply_delay_hours=round(delay / 3600, 2) if delay is not None else '')
        rr.update({f'reply_{k}': int(bool(REPLY[k].search(txt))) for k in RTYPES})
        rr['reply_any_marker'] = int(any(rr[f'reply_{k}'] for k in RTYPES))
        out.append(rr)
    # parent comment types need the PARENT markers (same patterns as M, named as in H3)
    pmap = {'experience': 'own_layoff_story', 'mentions_execs': 'mentions_execs', 'mentions_offshore': 'mentions_offshore_visa',
            'blames_workers': 'blames_workers', 'ai_excuse': 'ai_is_excuse', 'ai_replaces': 'ai_will_replace', 'doom': 'doom'}
    byc = {r['comment_id']: r for r in rows}
    for rr in out:
        p = byc[rr['parent_comment_id']]
        types = [k for k, nm in pmap.items() if p[nm]]
        for k in pmap: rr[f'parent_{k}'] = int(k in types)
        rr['parent_type_primary'] = types[0] if types else 'none'
        rr['parent_n_types'] = len(types)
    write('r3_reply_pairs.csv', out)
    # long lift table: parent type x reply type (multi-label parents counted once per type)
    cnt = defaultdict(Counter)
    for rr in out:
        pts = [k for k in pmap if rr[f'parent_{k}']] or ['none']
        for pt in pts:
            cnt[pt]['n'] += 1
            for k in RTYPES: cnt[pt][k] += rr[f'reply_{k}']
    base = {k: cnt['none'][k] / cnt['none']['n'] for k in RTYPES}
    lt = []
    for pt, cc in cnt.items():
        for k in RTYPES:
            pct = cc[k] / cc['n']
            lt.append(dict(parent_type=pt, reply_type=k, replies=cc['n'], hits=cc[k], pct=round(100 * pct, 2),
                           baseline_pct_none=round(100 * base[k], 2), lift_vs_none=round(pct / base[k], 3) if base[k] else ''))
    write('r3_reply_type_lift.csv', lt)

def r4(pid_unused=None):
    """R4: authors, flows, communities, and a 2-D layout of the network core for Tableau path charts."""
    prof = list(csv.DictReader((NET / 'author_profiles.csv').open()))
    for r in prof:
        n = int(r['comments']); r['activity_band'] = '1-4' if n < 5 else '5-9' if n < 10 else '10-19' if n < 20 else '20-49' if n < 50 else '50+'
        r['profiled'] = int(n >= 5)
    write('r4_authors.csv', prof)
    write('r4_type_flows.csv', list(csv.DictReader((NET / 'mixing_matrix.csv').open())))
    write('r4_communities.csv', list(csv.DictReader((NET / 'communities.csv').open())))
    write('r4_centrality_by_type.csv', list(csv.DictReader((NET / 'centrality_by_type.csv').open())))
    G = nx.read_gexf(NET / 'network_profiled.gexf')
    U = nx.Graph()
    for u, v, d in G.edges(data=True):
        w = d.get('weight', 1)
        U.add_edge(u, v, weight=U[u][v]['weight'] + w if U.has_edge(u, v) else w)
    core = sorted(U.degree, key=lambda x: -x[1])[:1500]
    H = U.subgraph([n for n, _ in core]).copy()
    pos = nx.spring_layout(H, seed=SEED, weight='weight', iterations=100)
    nodes = []
    for n in H:
        a = G.nodes[n]
        nodes.append(dict(node_id=n, x=round(float(pos[n][0]), 4), y=round(float(pos[n][1]), 4), type=a.get('type'), cluster=a.get('cluster'),
                          community=a.get('community'), comments=a.get('comments'), degree_in_core=H.degree(n),
                          pagerank=round(float(a.get('pagerank', 0)), 4), betweenness=a.get('betweenness')))
    write('r4_network_core_nodes.csv', nodes)
    edges = []
    for k, (u, v, d) in enumerate(H.edges(data=True)):
        tu, tv = G.nodes[u].get('type'), G.nodes[v].get('type')
        pair = ' - '.join(sorted([tu, tv]))
        for order, n in ((1, u), (2, v)):
            edges.append(dict(edge_id=k, path_order=order, node_id=n, x=round(float(pos[n][0]), 4), y=round(float(pos[n][1]), 4),
                              weight=d['weight'], type_pair=pair, same_type=int(tu == tv)))
    write('r4_network_core_edges_path.csv', edges)

def r5():
    """R5: every robustness check in one long table, plus marker precision."""
    out = []
    for r in csv.DictReader((NET / 'rivals.csv').open()):
        out.append(dict(source='15_network/rivals', check=r['rival'], variant=r['variant'], statistic=r['statistic'], value=r['value'],
                        lo=r.get('lo', ''), hi=r.get('hi', ''), n=r.get('n', '')))
    for r in csv.DictReader((NET / 'null_models.csv').open()):
        out.append(dict(source='15_network/null_models', check=f"null: {r['null']}", variant='observed vs null mean', statistic=r['statistic'],
                        value=r['observed'], lo=r['null_mean'], hi=r['null_sd'], n='', z=r['z'], p_emp=r['p_emp']))
    for r in csv.DictReader((NET / 'sensitivity_N.csv').open()):
        out.append(dict(source='15_network/sensitivity_N', check='threshold N', variant=f"N={r['N']}", statistic=r['statistic'], value=r['value']))
    rt = ROOT / 'outputs/12_replies/reply_table.csv'
    if rt.exists():
        for r in csv.DictReader(rt.open()):
            out.append(dict(source='12_replies/reply_table', check='R3 thread-clustered CI and length band', variant=r['parent_type'],
                            statistic=f"{r['reply_type']} pct (lift vs none; lift in 30-150 words)", value=r['pct'], lo=r['ci95_lo'], hi=r['ci95_hi'],
                            n=r['replies'], lift=r['lift_vs_none'], lift_30_150_words=r['lift_30_150_words']))
    write('r5_robustness_long.csv', out, header=['source', 'check', 'variant', 'statistic', 'value', 'lo', 'hi', 'n', 'z', 'p_emp', 'lift', 'lift_30_150_words'])
    mp = ROOT / 'outputs/09_leads/screen_audit/manual_precision_by_group.csv'
    if mp.exists(): write('r5_marker_precision.csv', list(csv.DictReader(mp.open())))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c = connect(); c.execute('pragma temp_store=memory')
    pid, tid = Ids('p'), Ids('t')
    r1_daily(c)
    r1_threads(c, tid)
    rows, cid = r2_comments(c, pid, tid)
    r2_rates(rows); r2_cross_posters(rows)
    r3_pairs(c, rows, cid, pid)
    r4(); r5()
    log('done')

if __name__ == '__main__':
    main()
