"""H3: what kind of comment gets what kind of reply? (r/cscareerquestions, read-only)

Question: when someone in cscq writes an employment comment of a given kind
(their own layoff, blame aimed at executives, blame aimed sideways at other
workers, "AI is the excuse", "AI will replace you", market doom), how do
other people reply to it?

Expectation stated before running (from outputs/09-11):
  experience -> more sympathy/advice replies;
  offshore/immigration talk and blaming workers -> more challenge replies;
  talk about executives -> more agreement.

Outputs go to outputs/12_replies/. Nothing in the database or other outputs is changed.
Run:  .venv-eda/bin/python scripts/explore_replies.py
"""
import csv, json, random, re, resource, sqlite3, sys, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from explore_leads import M, connect, short  # reuse the checked marker patterns

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/12_replies'
SEED = 20261119
rng = np.random.default_rng(SEED); random.seed(SEED)
CAND = "(d.layoffs=1 or d.hiring_conditions=1 or d.ai_work_change=1 or d.corporate_restructuring=1 or d.economic_policy=1)"

def rx(p): return re.compile(p, re.I)

# ---- parent types: what the comment does (multi-label) ----
PARENT = {
    'experience':     M['first_person_layoff'],
    # NOTE: the next three are TOPIC markers (what is mentioned), not stance. Checked 2026-11-19:
    # ~95% of the old combined 'blame_sideways' was offshoring/H-1B/visa mentions of any stance.
    'mentions_execs':     M['exec_blame'],
    'mentions_offshore':  M['offshore_h1b'],
    'blames_workers':     M['individual_blame'],
    'ai_excuse':      M['ai_pretext'],
    'ai_replaces':    M['ai_inevitable'],
    'doom':           M['realism'],
}
# ---- reply types: how the reply responds (multi-label) ----
REPLY = {
    'sympathy':  M['empathy_reply'],
    'advice':    rx(r"\b(you should|you need to|i'?d (recommend|suggest)|i would (recommend|suggest)|try (to|applying|reaching|looking)|have you (tried|considered)"
                    r"|my advice|focus on|reach out|update your resume|tailor|apply (to|for|anyway)|network(ing)?)\b"),
    'agree':     rx(r"^\W*(this|exactly|agreed?|so true|100%|same|yep|yup|facts|well said|preach|truth)\b|\bi (completely |totally |fully )?agree\b|\bspot on\b|\bcouldn'?t agree more\b|\bthis is (so )?(true|right)\b"),
    'challenge': M['challenge_reply'],
}

def write(name, rows, header=None):
    p = OUT / name; p.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows); header = header or (list(rows[0].keys()) if rows else [])
    with p.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction='ignore'); w.writeheader(); w.writerows(rows)

def thread_boot(flag, thread_idx, n_threads, reps=1000):
    """95% CI for a proportion, resampling whole threads (replies in one thread are not independent)."""
    s = np.bincount(thread_idx, weights=flag, minlength=n_threads); n = np.bincount(thread_idx, minlength=n_threads)
    keep = n > 0; s, n = s[keep], n[keep]
    idx = rng.integers(0, len(s), size=(reps, len(s)))
    est = s[idx].sum(1) / np.maximum(n[idx].sum(1), 1)
    return float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))

def main():
    t0 = time.time(); c = connect(); c.execute("pragma temp_store=memory")
    # 1. parents: cscq employment comments, human, text available
    c.execute("create temp table par(fn text primary key, id text, link text, author text, score int, month text, words int, txt text) without rowid")
    c.execute(f"""insert into par select 't1_'||r.id, r.id, r.link_id, f.author_key, r.score, r.created_month, f.word_count, f.own_text
        from disruption_screen d join records r on r.kind=d.kind and r.id=d.id join features f on f.kind=d.kind and f.id=d.id
        where d.kind='comments' and r.subreddit='cscareerquestions' and {CAND} and f.likely_bot=0 and f.author_unknown=0
        and coalesce(f.own_text,'')<>''""")
    parents = {fn: dict(id=i, link=l, author=a, score=s, month=m, words=w or 0, text=t)
               for fn, i, l, a, s, m, w, t in c.execute("select * from par")}
    print(f'parents {len(parents):,}  ({time.time()-t0:.0f}s)')
    # 2. direct replies to those parents (any content), excluding bots, self-replies, empty text
    kids = defaultdict(list)
    q = """select e.parent_fullname, e.child_id, f.author_key, r.score, f.own_text from reply_edges e join par p on p.fn=e.parent_fullname
           join records r on r.kind='comments' and r.id=e.child_id join features f on f.kind='comments' and f.id=e.child_id
           where f.likely_bot=0 and f.author_unknown=0 and coalesce(f.own_text,'')<>'' and f.author_key<>p.author"""
    for pfn, cid, a, s, t in c.execute(q): kids[pfn].append(dict(id=cid, author=a, score=s, text=t))
    print(f'replies {sum(map(len, kids.values())):,}  ({time.time()-t0:.0f}s)')

    # 3. label
    ptypes = list(PARENT) + ['none']; rtypes = list(REPLY)
    for fn, p in parents.items():
        p['types'] = [k for k, r in PARENT.items() if r.search(p['text'])] or ['none']
        p['kids'] = kids.get(fn, [])
        for k in p['kids']: k['types'] = [n for n, r in REPLY.items() if r.search(k['text'])]
    threads = {l: i for i, l in enumerate({p['link'] for p in parents.values()})}

    # 4. reply table. Unit = one reply. Baseline = replies to 'none' parents (employment comments with no marker).
    def rows_for(ptype, words_lo=0, words_hi=10**9):
        ps = [p for p in parents.values() if ptype in p['types'] and words_lo <= p['words'] < words_hi]
        rep = [(threads[p['link']], k) for p in ps for k in p['kids']]
        return ps, rep
    table, summary = [], []
    base_ps, base_rep = rows_for('none')
    base_rate = {rt: np.mean([rt in k['types'] for _, k in base_rep]) for rt in rtypes}
    for pt in ptypes:
        ps, rep = rows_for(pt)
        ti = np.array([t for t, _ in rep]); n_rep = len(rep)
        summary.append({'parent_type': pt, 'parents': len(ps), 'replies': n_rep,
                        'pct_with_any_reply': round(100*np.mean([bool(p['kids']) for p in ps]), 1),
                        'replies_per_parent': round(n_rep/len(ps), 2),
                        'median_words': int(np.median([p['words'] for p in ps])),
                        'median_parent_score': float(np.median([p['score'] for p in ps])),
                        'pct_parent_score_below_0': round(100*np.mean([p['score'] < 0 for p in ps]), 1)})
        for rt in rtypes:
            f = np.array([rt in k['types'] for _, k in rep], float)
            lo, hi = thread_boot(f, ti, len(threads))
            # length check: same comparison inside the middle word-count band (30-150 words)
            _, rep_m = rows_for(pt, 30, 150); _, base_m = rows_for('none', 30, 150)
            lm = np.mean([rt in k['types'] for _, k in rep_m]) / max(np.mean([rt in k['types'] for _, k in base_m]), 1e-9)
            table.append({'parent_type': pt, 'reply_type': rt, 'replies': n_rep, 'pct': round(100*f.mean(), 2),
                          'ci95_lo': round(100*lo, 2), 'ci95_hi': round(100*hi, 2), 'baseline_pct': round(100*base_rate[rt], 2),
                          'lift_vs_none': round(f.mean()/base_rate[rt], 2), 'lift_30_150_words': round(lm, 2)})
    write('reply_table.csv', table); write('parent_summary.csv', summary)
    print(f'table done ({time.time()-t0:.0f}s)')

    # 5. reply score: are sympathy/challenge replies themselves upvoted? (within each parent type)
    sc = []
    for pt in ptypes:
        ps = [p for p in parents.values() if pt in p['types']]
        for rt in rtypes:
            a = [k['score'] for p in ps for k in p['kids'] if rt in k['types']]
            b = [k['score'] for p in ps for k in p['kids'] if rt not in k['types']]
            if len(a) >= 30:
                sc.append({'parent_type': pt, 'reply_type': rt, 'n': len(a), 'median_score_this_type': float(np.median(a)),
                           'median_score_other_replies': float(np.median(b)), 'pct_below_0_this_type': round(100*np.mean(np.array(a) < 0), 1),
                           'pct_below_0_other': round(100*np.mean(np.array(b) < 0), 1)})
    write('reply_scores.csv', sc)

    # 6. same people? authors with >=5 employment comments: who tells experiences, who blames sideways
    by_auth = defaultdict(Counter)
    for p in parents.values():
        by_auth[p['author']]['n'] += 1
        for t in p['types']: by_auth[p['author']][t] += 1
    act = {a: v for a, v in by_auth.items() if v['n'] >= 5}
    role = {a: ('experience' if v['experience'] and not v['mentions_offshore'] else 'mentions_offshore' if v['mentions_offshore'] and not v['experience']
                else 'both' if v['experience'] else 'neither') for a, v in act.items()}
    rc = Counter(role.values())
    # who replies to whom between these roles (all retained replies to employment parents)
    cross = Counter()
    for p in parents.values():
        if p['author'] not in role: continue
        for k in p['kids']:
            if k['author'] in role: cross[(role[k['author']], role[p['author']])] += 1
    write('author_roles.csv', [{'role': r, 'authors': n} for r, n in rc.most_common()])
    write('author_role_replies.csv', [{'replier_role': a, 'parent_author_role': b, 'replies': n} for (a, b), n in cross.most_common()])

    # 7. Gephi: type -> type network (lift as weight), 10 nodes
    OUTG = OUT / 'gephi'
    write('gephi/type_nodes.csv', [{'Id': f'P:{t}', 'Label': t, 'side': 'comment'} for t in ptypes] +
          [{'Id': f'R:{t}', 'Label': t + ' reply', 'side': 'reply'} for t in rtypes])
    write('gephi/type_edges.csv', [{'Source': f"P:{r['parent_type']}", 'Target': f"R:{r['reply_type']}", 'Type': 'Directed',
                                    'Weight': r['lift_vs_none'], 'pct': r['pct'], 'replies': r['replies']} for r in table])

    # 8. examples: real parent -> reply pairs for each notable cell, plus a check sheet
    ex = []
    for pt in ptypes:
        for rt in rtypes:
            pairs = [(p, k) for p in parents.values() if pt in p['types'] for k in p['kids'] if rt in k['types']]
            for p, k in random.sample(pairs, min(4, len(pairs))):
                ex.append({'parent_type': pt, 'reply_type': rt, 'parent_score': p['score'], 'parent': short(p['text'], 350),
                           'reply_score': k['score'], 'reply': short(k['text'], 250), 'parent_id': p['id'], 'reply_id': k['id']})
    write('examples_pairs.csv', ex)
    chk = []
    for pt in ptypes:
        pool = [p for p in parents.values() if pt in p['types']]
        for p in random.sample(pool, min(20, len(pool))):
            chk.append({'unit': 'comment', 'machine_label': pt, 'id': p['id'], 'text': short(p['text'], 500), 'human_label_correct_yes_no': ''})
    allk = [k for p in parents.values() for k in p['kids']]
    for rt in rtypes:
        pool = [k for k in allk if rt in k['types']]
        for k in random.sample(pool, 20):
            chk.append({'unit': 'reply', 'machine_label': rt, 'id': k['id'], 'text': short(k['text'], 400), 'human_label_correct_yes_no': ''})
    write('check_sheet.csv', chk)

    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    json.dump({'question': __doc__.split('\n')[2], 'parents': len(parents), 'replies': len(allk), 'threads': len(threads),
               'author_roles_min_comments': 5, 'seed': SEED, 'seconds': round(time.time()-t0), 'peak_mb': round(peak)},
              (OUT / 'manifest.json').open('w'), indent=2)
    print(f'done {time.time()-t0:.0f}s, peak {peak:.0f} MB')

if __name__ == '__main__':
    main()
