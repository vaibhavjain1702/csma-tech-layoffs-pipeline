#!/usr/bin/env python3
"""Chase the exploratory leads with reproducible, read-only checks.

Reads data/processed/reddit.sqlite (read-only), the reading sample, and the Gephi
author export. Writes only to outputs/09_leads/. Does not alter the database,
screens, labels, or any other stage's outputs.

Every lexical marker below is a *retrieval device* whose precision is checked by
reading (see precision_samples/ and manual/). Scores are snapshots; comparisons use
the within-thread score percentile and stratify by reply depth and arrival order.

Run: .venv-eda/bin/python scripts/explore_leads.py   (numpy; matplotlib optional)
"""
import csv, json, re, sqlite3, random, collections, math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data/processed/reddit.sqlite'
OUT = ROOT / 'outputs/09_leads'
SHARED_END = '2025-06'          # last month all three communities have comments
SUBS = ('cscareerquestions', 'programming', 'technology')
FACETS = ('layoffs', 'hiring_conditions', 'ai_work_change', 'corporate_restructuring', 'economic_policy', 'career_transition')
rng = np.random.default_rng(20261114)
random.seed(20261114)

def rx(p): return re.compile(p, re.I)
# ---- markers (author's own text only; quoted lines already removed by preprocessing) ----
M = {
    'ai_pretext': rx(r"\b(excuse|scapegoat\w*|pretext|smokescreen|cover (story|for)|ai[- ]?washing)\b"
                     r"|\bblam\w* (it )?on (the )?ai\b|\b(not|isn'?t|wasn'?t|aren'?t|weren'?t) (really )?(because of|due to|about|caused by|replaced by) ai\b"
                     r"|\busing ai as (an? )?(excuse|cover|reason|justification)\b|\bai is (just )?(the|an) (excuse|cover)\b"),
    'ai_inevitable': rx(r"\b(ai|llms?|it|agents?) (will|is going to|are going to|gonna) (soon )?(replace|take|eliminate|automate|wipe out|make .{0,20}obsolete)\b"
                        r"|\bjobs (will be|are) (gone|obsolete|dead)\b|\badapt or (die|get left)\b|\b(get|be|being) left behind\b"
                        r"|\byou(?:'ll| will) be replaced\b|\breplaced by (someone|people) (who|using)\b"),
    'exec_blame': rx(r"\b(greed\w*|shareholders?|stock (price|buybacks?)|buybacks?|executives?|execs|c-suite|ceos?|wall street|investors?)\b"),
    'offshore_h1b': rx(r"\b(offshor\w*|outsourc\w*|h-?1-?bs?|visas?)\b"),
    'ethnic_ref': rx(r"\b(india\w*|chinese|desi|brown people|white people)\b"),
    'macro': rx(r"\b(interest rates?|zirp|recession|economy|tariffs?|section 174)\b"),
    'overhiring': rx(r"\bover-?\s?hir\w*\b"),
    'individual_blame': rx(r"\b(low performers?|skill issue|not good enough|unqualified|lazy|deadweight|underperform\w*|git gud)\b"),
    'ai_any': rx(r"\b(ai|a\.i\.|chatgpt|llms?|gpt-?\d?|automation|copilot|cursor|claude|agents?)\b"),
    'first_person_layoff': rx(r"\b(i was|i got|i've been|i have been|i'm being|i am being|i just got|we were|we got|my (whole )?team (was|got))\b[^.!?]{0,30}\b(laid off|let go|rif'?d|riffed|cut)\b"
                              r"|\b(laid me off|let me go)\b|\bsince (i|my) (was |got )?(layoff|laid off)\b"),
    'consequence': rx(r"\b(insurance|cobra|savings|severance|mortgage|rent|bills|visa|green card|kids?|baby|wife|husband|family|months? (of|without|unemployed)|unemploy\w*|runway|applications?|ghosted)\b"),
    'empathy_reply': rx(r"\b(sorry|good luck|best of luck|hang in|rooting for|feel for you|that sucks|you got this|wishing you|congrat\w*|glad you|hugs)\b"),
    'challenge_reply': rx(r"\b(source\??|citation|not true|wrong|disagree|nonsense|bullshit|cope|delusional|no it|that's not|this is false|lol no)\b"),
    'realism': rx(r"\b(market is (really )?(bad|terrible|brutal|awful|cooked|rough|trash)|it (really )?is that bad|not lying|in denial|denial|stop (coping|pretending)|cooked|bloodbath|tech depression)\b"),
}
THEMES_AI = {  # Lead 3: what AI talk is about
    'replacement': rx(r"\b(laid off|layoffs?|replac\w*|headcount|job losses|eliminat\w*)\b"),
    'hiring_gate': rx(r"\b(interviews?|resumes?|recruit\w*|applicants?|ats|cheat\w*|applications?)\b"),
    'tools_named': rx(r"\b(cursor|copilot|claude|agents?|agentic|vibe ?cod\w*|codex|windsurf)\b"),
    'mandate_tracking': rx(r"\b(mandat\w*|forced to use|required to use|requir\w* (us )?to use|track\w* (our )?(usage|tokens?)|token usage|usage metrics|ai adoption|kpis?|okrs?)\b"),
    'quality_slop': rx(r"\b(slop|tech debt|quality|bugs?|broken)\b"),
}
FP_MANDATE = rx(r"\b(my|our) (company|employer|manager|org|team|leadership|boss|director|cto|ceo|work)\b[^.!?]{0,80}\b(mandat\w*|requir\w*|forc\w*|push\w*|track\w*|measur\w*|expect\w*)\b[^.!?]{0,60}\b(ai|llms?|cursor|copilot|claude|tokens?|agents?)\b"
                r"|\b(my|our) (company|employer|manager|org|team|leadership|boss|director|cto|ceo)\b[^.!?]{0,80}\b(ai|llms?|cursor|copilot|claude|tokens?)\b[^.!?]{0,60}\b(mandat\w*|requir\w*|forc\w*|track\w*|measur\w*)\b")

def connect():
    return sqlite3.connect(f'file:{DB}?mode=ro', uri=True)

def write(name, rows, header=None):
    path = OUT / name; path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if header is None: header = list(rows[0].keys()) if rows else []
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    return path

def short(t, n=400): return ' '.join((t or '').split())[:n]

BIG = 2000  # above this n, use the normal approximation (bounded variables, CLT holds) to keep memory small

def _boot_means(x, reps):
    out = np.empty(reps); step = max(1, 2_000_000 // len(x))  # chunk so each draw matrix is <= ~16 MB
    for i in range(0, reps, step):
        k = min(step, reps - i); out[i:i+k] = rng.choice(x, size=(k, len(x))).mean(1)
    return out

def boot_ci(x, reps=2000):
    x = np.asarray(x, float)
    if len(x) < 5: return (float('nan'), float('nan'))
    if len(x) > BIG:
        se = x.std(ddof=1) / np.sqrt(len(x)); return (float(x.mean() - 1.96*se), float(x.mean() + 1.96*se))
    m = _boot_means(x, reps)
    return (float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)))

def boot_diff(a, b, reps=2000):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 5 or len(b) < 5: return (float('nan'),) * 3
    d0 = float(a.mean() - b.mean())
    if min(len(a), len(b)) > BIG:  # Welch normal interval
        se = np.sqrt(a.var(ddof=1)/len(a) + b.var(ddof=1)/len(b)); return (d0, d0 - 1.96*se, d0 + 1.96*se)
    d = _boot_means(a, reps) - (_boot_means(b, reps) if len(b) <= BIG else rng.normal(b.mean(), b.std(ddof=1)/np.sqrt(len(b)), reps))
    return (d0, float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5)))

# ---------------------------------------------------------------------------
def load_candidates(c):
    """Screen-candidate comments with within-thread score/time percentiles and reply depth."""
    # keyed temp table (id primary key) so the join below is a lookup, not a scan
    c.execute("create temp table wr(id text primary key, pr real, tr real, n_thread integer) without rowid")
    c.execute("""insert into wr select id,
        percent_rank() over (partition by link_id order by score) as pr,
        percent_rank() over (partition by link_id order by created_utc) as tr,
        count(*) over (partition by link_id) as n_thread
        from records where kind='comments'""")
    q = f"""select r.id,r.subreddit,r.created_month,r.created_utc,r.score,r.link_id,f.author_key,f.likely_bot,f.own_text,
        {','.join('d.'+x for x in FACETS)},d.evidence_json,r.direct_layoff,w.pr,w.tr,w.n_thread,e.depth,e.parent_kind,r.text_state
        from disruption_screen d join records r on r.kind=d.kind and r.id=d.id
        join features f on f.kind=d.kind and f.id=d.id join wr w on w.id=d.id
        left join reply_edges e on e.child_id=d.id where d.kind='comments'"""
    cols = ['id','sub','month','utc','score','link','author','bot','text',*FACETS,'ev','direct','pr','tr','n_thread','depth','parent_kind','text_state']
    rows = [dict(zip(cols, r)) for r in c.execute(q)]
    for r in rows:
        r['text'] = r['text'] or ''
        r['top_level'] = r['parent_kind'] == 'posts'
        r['early'] = (r['tr'] or 0) <= 0.2
        for k, p in M.items(): r[k] = bool(p.search(r['text']))
    return rows

def in_scope(r):  # cross-community rule
    return r['sub'] == 'cscareerquestions' or r['month'] <= SHARED_END

# ---------------------------------------------------------------------------
def screen_audit(c):
    """Quantify the 'quite' artefact and per-facet top terms."""
    only = collections.Counter(); hits = collections.Counter(); solo = 0
    for (ev,) in c.execute("select evidence_json from disruption_screen"):
        e = json.loads(ev)
        if 'career_transition' in e:
            ts = {t.lower() for i in e['career_transition'] for t in i['terms']}
            hits['career_transition'] += 1
            if ts <= {'quite'}:
                only['career_transition'] += 1
                if list(e) == ['career_transition']: solo += 1
    rows = [{'measure': 'career_transition_records', 'value': hits['career_transition']},
            {'measure': 'career_transition_matched_only_by_quite', 'value': only['career_transition']},
            {'measure': 'share_only_quite_percent', 'value': round(100*only['career_transition']/hits['career_transition'], 2)},
            {'measure': 'candidates_retrieved_solely_by_quite', 'value': solo}]
    write('screen_audit/quite_artifact.csv', rows)
    # manual audit summary (coded by Claude, provisional; see manual/screen_audit_codes.csv)
    p = OUT / 'manual/screen_audit_codes.csv'
    if p.exists():
        codes = list(csv.DictReader(p.open()))
        tab = collections.defaultdict(collections.Counter)
        for r in codes: tab[r['group']][r['code']] += 1
        out = []
        for g, cn in tab.items():
            n = sum(cn.values())
            out.append({'group': g, 'n': n, 'R': cn['R'], 'P': cn['P'], 'N': cn['N'], 'precision_R_percent': round(100*cn['R']/n, 1)})
        write('screen_audit/manual_precision_by_group.csv', out)

# ---------------------------------------------------------------------------
def lead1_reward(rows):
    """Which explanations sit high/low within their own thread? Visibility-controlled."""
    base = [r for r in rows if in_scope(r) and not r['bot'] and (r['layoffs'] or r['ai_work_change'] or r['hiring_conditions'])
            and r['n_thread'] >= 10 and len(r['text'].split()) >= 8]
    out = []; strata = []
    markers = ['ai_pretext', 'ai_inevitable', 'exec_blame', 'offshore_h1b', 'ethnic_ref', 'macro', 'overhiring', 'individual_blame']
    for sub in SUBS:
        sb = [r for r in base if r['sub'] == sub]
        for m in markers:
            a = [r for r in sb if r[m]]; b = [r for r in sb if not r[m]]
            if len(a) < 10: continue
            d, lo, hi = boot_diff([r['pr'] for r in a], [r['pr'] for r in b])
            out.append({'subreddit': sub, 'marker': m, 'n_marked': len(a), 'n_unmarked': len(b),
                        'mean_pct_marked': round(np.mean([r['pr'] for r in a]), 3), 'mean_pct_unmarked': round(np.mean([r['pr'] for r in b]), 3),
                        'diff': round(d, 3), 'ci_lo': round(lo, 3), 'ci_hi': round(hi, 3),
                        'top_decile_marked_pct': round(100*np.mean([r['pr'] >= .9 for r in a]), 1), 'top_decile_unmarked_pct': round(100*np.mean([r['pr'] >= .9 for r in b]), 1),
                        'negative_marked_pct': round(100*np.mean([r['score'] < 0 for r in a]), 1), 'negative_unmarked_pct': round(100*np.mean([r['score'] < 0 for r in b]), 1)})
            # robustness: same comparison inside depth x arrival strata
            for tl in (True, False):
                for ea in (True, False):
                    aa = [r['pr'] for r in a if r['top_level'] == tl and r['early'] == ea]
                    bb = [r['pr'] for r in b if r['top_level'] == tl and r['early'] == ea]
                    if len(aa) >= 20:
                        d2, l2, h2 = boot_diff(aa, bb, 1000)
                        strata.append({'subreddit': sub, 'marker': m, 'top_level': tl, 'early_arrival': ea, 'n_marked': len(aa),
                                       'diff': round(d2, 3), 'ci_lo': round(l2, 3), 'ci_hi': round(h2, 3)})
    write('lead1_reward/marker_within_thread_percentile.csv', out)
    write('lead1_reward/marker_strata.csv', strata)
    # precision samples for the two key markers, for reading
    for m in ('ai_pretext', 'ai_inevitable'):
        pool = [r for r in base if r[m]]
        samp = random.sample(pool, min(30, len(pool)))
        write(f'precision_samples/{m}.csv', [{'id': r['id'], 'subreddit': r['sub'], 'score': r['score'], 'pct': round(r['pr'], 2),
               'match': M[m].search(r['text']).group(0), 'text': short(r['text'], 450), 'stance_ok': ''} for r in samp])
    return base

def children(c, parent_ids):
    """Direct replies (own text) to the given comment ids."""
    want = {'t1_' + i for i in parent_ids}; kids = collections.defaultdict(list)
    for child, parent in c.execute("select child_id,parent_fullname from reply_edges where parent_kind='comments'"):
        if parent in want: kids[parent[3:]].append(child)
    texts = {}
    ids = [k for v in kids.values() for k in v]
    for i in range(0, len(ids), 900):
        chunk = ids[i:i+900]
        for cid, t, s in c.execute(f"select f.id,f.own_text,r.score from features f join records r using(kind,id) where f.kind='comments' and f.id in ({','.join('?'*len(chunk))})", chunk):
            texts[cid] = (t or '', s)
    return {p: [texts[k] for k in v if k in texts] for p, v in kids.items()}

def lead2_proximity(c, rows):
    """First-person layoff accounts vs other layoff comments: explanation and reception."""
    lay = [r for r in rows if r['layoffs'] and in_scope(r) and not r['bot'] and len(r['text'].split()) >= 8]
    kids = children(c, [r['id'] for r in lay])
    out = []
    groups = [('cscq_all_months', lambda r: r['sub'] == 'cscareerquestions')] + [(f'{s}_le_{SHARED_END}', (lambda s: lambda r: r['sub'] == s and r['month'] <= SHARED_END)(s)) for s in SUBS]
    for name, f in groups:
        g = [r for r in lay if f(r)]
        for fp in (True, False):
            h = [r for r in g if r['first_person_layoff'] == fp]
            if not h: continue
            ks = [k for r in h for k in kids.get(r['id'], [])]
            row = {'group': name, 'first_person': fp, 'n': len(h)}
            for m in ('ai_any', 'ai_pretext', 'exec_blame', 'offshore_h1b', 'macro', 'consequence'):
                v = [r[m] for r in h]; lo, hi = boot_ci(v, 1000)
                row[f'{m}_pct'] = round(100*np.mean(v), 1); row[f'{m}_ci'] = f'{100*lo:.1f}-{100*hi:.1f}'
            row['mean_within_thread_pct'] = round(np.mean([r['pr'] for r in h]), 3)
            row['replies'] = len(ks)
            row['replies_per_comment'] = round(len(ks)/len(h), 2)
            row['reply_empathy_pct'] = round(100*np.mean([bool(M['empathy_reply'].search(t)) for t, s in ks]), 1) if ks else ''
            row['reply_challenge_pct'] = round(100*np.mean([bool(M['challenge_reply'].search(t)) for t, s in ks]), 1) if ks else ''
            out.append(row)
    write('lead2_proximity/first_person_vs_other.csv', out)
    pool = [r for r in lay if r['sub'] == 'cscareerquestions' and r['first_person_layoff']]
    samp = random.sample(pool, min(40, len(pool)))
    write('precision_samples/first_person_layoff.csv', [{'id': r['id'], 'month': r['month'], 'score': r['score'], 'text': short(r['text'], 500),
          'replies': ' || '.join(short(t, 160) for t, s in kids.get(r['id'], [])[:3]), 'is_first_person': '', 'what_they_talk_about': ''} for r in samp])
    return kids

def lead3_ai_shift(c, rows):
    """cscq only: monthly AI themes per 1,000 comments, with a tool-name-free variant."""
    den = dict(c.execute("select created_month,count(*) from records where kind='comments' and subreddit='cscareerquestions' group by 1"))
    cs = [r for r in rows if r['sub'] == 'cscareerquestions' and r['ai_work_change'] and not r['bot']]
    by = collections.defaultdict(list)
    for r in cs: by[r['month']].append(r)
    out = []
    for m in sorted(den):
        g = by.get(m, []); row = {'month': m, 'all_comments': den[m], 'ai_candidates': len(g), 'ai_per_1000': round(1000*len(g)/den[m], 2)}
        for k, p in THEMES_AI.items():
            n = sum(bool(p.search(r['text'])) for r in g)
            row[f'{k}_per_1000'] = round(1000*n/den[m], 3); row[f'{k}_share_of_ai'] = round(100*n/max(1, len(g)), 1)
        n = sum(bool(FP_MANDATE.search(r['text'])) for r in g)
        row['first_person_mandate_n'] = n; row['first_person_mandate_per_10000'] = round(10000*n/den[m], 2)
        out.append(row)
    write('lead3_ai_shift/cscq_monthly_ai_themes.csv', out)
    pool = [r for r in cs if FP_MANDATE.search(r['text'])]
    # first-hand mandate accounts by half-year, with crude 'quantified expectation' and negative-word shares
    Q = rx(r"\b(metrics?|track\w*|tokens?|kpis?|okrs?|usage (stats|numbers|data)|dashboards?|performance reviews?|\d+x|quota|minimum|leaderboard)\b")
    NEG = rx(r"\b(hate|garbage|slop|worse|stress\w*|burn\w*|insane|ridiculous|dumb|fear|afraid|unsafe|terrible|awful|exhaust\w*)\b")
    mh = collections.defaultdict(lambda: [0, 0, 0])
    for r in pool:
        h = r['month'][:4] + ('H1' if r['month'][5:] <= '06' else 'H2')
        mh[h][0] += 1; mh[h][1] += bool(Q.search(r['text'])); mh[h][2] += bool(NEG.search(r['text']))
    write('lead3_ai_shift/cscq_mandate_quantified_by_half.csv', [{'half': h, 'first_person_mandate_comments': a, 'quantified_expectation_n': b,
          'quantified_pct': round(100*b/a, 1), 'negative_word_pct': round(100*e/a, 1)} for h, (a, b, e) in sorted(mh.items())])
    write('precision_samples/first_person_mandate.csv', [{'id': r['id'], 'month': r['month'], 'score': r['score'], 'text': short(r['text'], 500), 'is_real_workplace_mandate': '', 'reaction': ''}
          for r in sorted(random.sample(pool, min(40, len(pool))), key=lambda r: r['month'])])
    return out

def lead4_offshore(c, rows):
    """Is offshore/H-1B talk polarising? Dispersion of within-thread rank + event window."""
    base = [r for r in rows if r['sub'] == 'cscareerquestions' and not r['bot'] and r['n_thread'] >= 10 and len(r['text'].split()) >= 8]
    out = []
    for name, f in [('offshore_h1b', lambda r: r['offshore_h1b']), ('ethnic_ref', lambda r: r['ethnic_ref']),
                    ('ai_pretext', lambda r: r['ai_pretext']), ('exec_blame', lambda r: r['exec_blame']), ('all_candidates', lambda r: True)]:
        g = [r for r in base if f(r)]; p = np.array([r['pr'] for r in g])
        out.append({'marker': name, 'n': len(g), 'mean_pct': round(p.mean(), 3), 'sd_pct': round(p.std(), 3),
                    'top_decile_pct': round(100*np.mean(p >= .9), 1), 'bottom_decile_pct': round(100*np.mean(p <= .1), 1),
                    'negative_score_pct': round(100*np.mean([r['score'] < 0 for r in g]), 1)})
    write('lead4_offshore/cscq_polarisation.csv', out)
    # daily H-1B mentions around the 19 Sep 2025 proclamation
    import datetime as dt
    day = collections.Counter(); alld = collections.Counter()
    for (u,) in c.execute("select created_utc from records where kind='comments' and subreddit='cscareerquestions' and created_month in ('2025-08','2025-09','2025-10')"):
        alld[dt.datetime.fromtimestamp(u, dt.timezone.utc).date().isoformat()] += 1
    h1 = rx(r"\bh-?1-?bs?\b")
    for r in rows:
        if r['sub'] == 'cscareerquestions' and r['month'] in ('2025-08', '2025-09', '2025-10') and h1.search(r['text']):
            day[dt.datetime.fromtimestamp(r['utc'], dt.timezone.utc).date().isoformat()] += 1
    write('lead4_offshore/cscq_daily_h1b.csv', [{'date': d, 'all_comments': alld[d], 'h1b_mentions': day[d], 'per_1000': round(1000*day[d]/alld[d], 2)} for d in sorted(alld)])
    # spike days (>= 25 per 1,000): concentrated in one thread, or spread across the subreddit?
    byday = collections.defaultdict(list)
    for r in rows:
        if r['sub'] == 'cscareerquestions' and r['month'] in ('2025-08', '2025-09', '2025-10') and h1.search(r['text']):
            byday[dt.datetime.fromtimestamp(r['utc'], dt.timezone.utc).date().isoformat()].append(r)
    sp = []
    for d in sorted(alld):
        if 1000*day[d]/alld[d] < 25: continue
        g = byday[d]; th = collections.Counter(r['link'] for r in g); lk, n = th.most_common(1)[0]
        top = sorted([r for r in g if r['link'] == lk], key=lambda r: -r['score'])[:3]
        sp.append({'date': d, 'h1b_comments': len(g), 'top_thread': lk, 'top_thread_share_pct': round(100*n/len(g), 1), 'n_threads': len(th),
                   'examples': ' || '.join(f"[{r['score']}] " + short(r['text'], 170) for r in top)})
    write('lead4_offshore/cscq_h1b_spike_days.csv', sp)
    # stratified sample for manual blame-target coding
    pool = [r for r in base if r['offshore_h1b'] or r['ethnic_ref']]
    top = [r for r in pool if r['pr'] >= .9]; bot = [r for r in pool if r['pr'] <= .1 or r['score'] < 0]
    samp = [(r, 'top') for r in random.sample(top, min(35, len(top)))] + [(r, 'bottom') for r in random.sample(bot, min(35, len(bot)))]
    random.shuffle(samp)
    write('precision_samples/offshore_blame_targets.csv', [{'id': r['id'], 'month': r['month'], 'stratum': s, 'score': r['score'], 'pct': round(r['pr'], 2),
          'text': short(r['text'], 450), 'blame_target': '', 'stance': ''} for r, s in samp])

def spearman(x, y):
    rx_ = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
    return float(np.corrcoef(rx_, ry)[0, 1])

def lead5_network(c, rows):
    """Robustness of the author graph and what its top positions measure."""
    g = ROOT / 'gephi'
    N = {r['Id']: r for r in csv.DictReader((g/'input/authors_keyword-comments.csv').open())}
    E = [(r['Source'], r['Target'], int(r['Weight'])) for r in csv.DictReader((g/'exports/authors_keyword-comments_direct/edges.csv').open())]
    def comps(nodes, edges):
        p = {n: n for n in nodes}
        def f(x):
            while p[x] != x: p[x] = p[p[x]]; x = p[x]
            return x
        for a, b, *_ in edges: p[f(a)] = f(b)
        cn = collections.Counter(f(n) for n in nodes); return len(cn), (max(cn.values()) if cn else 0)
    def rep(lbl, edges):
        nodes = {x for e in edges for x in e[:2]}; nc, lg = comps(nodes, edges)
        return {'version': lbl, 'users': len(nodes), 'edges': len(edges), 'components': nc, 'largest': lg, 'largest_pct': round(100*lg/max(1, len(nodes)), 1)}
    deg = collections.Counter()
    for a, b, _ in E: deg[a] += 1; deg[b] += 1
    out = [rep('full export', E)]
    for k in (2, 3, 5, 10):
        keep = {n for n, d in deg.items() if d >= k}; out.append(rep(f'both endpoints degree>={k}', [e for e in E if e[0] in keep and e[1] in keep]))
    out.append(rep('repeated ties (weight>=2)', [e for e in E if e[2] >= 2]))
    s = {(a, b) for a, b, _ in E}; out.append(rep('reciprocated ties only', [e for e in E if (e[1], e[0]) in s]))
    write('lead5_network/threshold_robustness.csv', out)
    # what kind of parent does each retained reply point to?
    q = """select e.child_author_key,e.parent_author_key,e.parent_kind,e.thread_id from reply_edges e join records r on r.kind='comments' and r.id=e.child_id
           where r.direct_layoff=1 and e.parent_present=1 and e.same_thread=1 and e.child_author_key is not null and e.parent_author_key is not null and e.child_author_key!=e.parent_author_key"""
    rep_rows = c.execute(q).fetchall()
    to_post = collections.Counter(); recv = collections.Counter(); threads = collections.defaultdict(set)
    for ch, pa, pk, th in rep_rows:
        recv[pa] += 1; to_post[pa] += pk == 'posts'; threads[ch].add(th); threads[pa].add(th)
    top_in = recv.most_common(20)
    posts_n = dict(c.execute("select author_key,count(*) from features where kind='posts' and author_key in (%s) group by 1" % ','.join('?'*len(top_in)), [a for a, _ in top_in]))
    comm_n = dict(c.execute("select author_key,count(*) from features where kind='comments' and author_key in (%s) group by 1" % ','.join('?'*len(top_in)), [a for a, _ in top_in]))
    write('lead5_network/top_in_degree_what_they_are.csv', [{'author': a, 'retained_replies_received': n, 'pct_replies_to_their_posts': round(100*to_post[a]/n, 1),
          'posts_in_corpus': posts_n.get(a, 0), 'comments_in_corpus': comm_n.get(a, 0), 'betweenness': N.get(a, {}).get('betweenesscentrality')} for a, n in top_in])
    tot = sum(recv.values()); tp = sum(to_post.values())
    write('lead5_network/reply_parent_kind.csv', [{'retained_replies': tot, 'replies_to_posts': tp, 'pct_to_posts': round(100*tp/tot, 1),
          'top20_in_share_of_all_received_pct': round(100*sum(n for _, n in top_in)/tot, 1)}])
    # is betweenness mostly 'spans many threads'?
    ids = [a for a in N if a in threads]
    btw = np.array([float(N[a]['betweenesscentrality']) for a in ids]); nth = np.array([len(threads[a]) for a in ids])
    deg_all = np.array([int(N[a]['Degree']) for a in ids])
    pos = btw > 0
    write('lead5_network/betweenness_vs_threads.csv', [
        {'measure': 'spearman(betweenness, distinct threads) all users', 'value': round(spearman(btw, nth), 3), 'n': len(ids)},
        {'measure': 'spearman(betweenness, distinct threads) betweenness>0', 'value': round(spearman(btw[pos], nth[pos]), 3), 'n': int(pos.sum())},
        {'measure': 'spearman(betweenness, degree) betweenness>0', 'value': round(spearman(btw[pos], deg_all[pos]), 3), 'n': int(pos.sum())},
        {'measure': 'median distinct threads, top-20 betweenness', 'value': float(np.median(sorted(nth[np.argsort(-btw)][:20]))), 'n': 20},
        {'measure': 'median distinct threads, all users', 'value': float(np.median(nth)), 'n': len(ids)}])
    # brokers: 'realism' talk rate vs cscq baseline, per broker (all their cscq comments)
    brokers = [r['Id'] for r in sorted(N.values(), key=lambda r: -float(r['betweenesscentrality']))[:10]]
    # deterministic ~5% baseline sample (created_utc mod 20) so reruns give identical numbers
    tot_c = 0; tot = collections.Counter()
    for (t,) in c.execute("select f.own_text from features f join records r using(kind,id) where r.kind='comments' and r.subreddit='cscareerquestions' and (r.created_utc % 20)=0"):
        tot_c += 1
        for k in ('realism', 'ai_any', 'offshore_h1b'): tot[k] += bool(M[k].search(t or ''))
    bo = [{'author': 'cscq baseline (~5% sample, created_utc mod 20)', 'comments': tot_c,
           **{f'{k}_pct': round(100*tot[k]/tot_c, 2) for k in ('realism', 'ai_any', 'offshore_h1b')}}]
    for a in brokers:
        ts = c.execute("select f.own_text,r.created_month from features f join records r using(kind,id) where f.author_key=? and r.kind='comments'", (a,)).fetchall()
        months = sorted({m for _, m in ts})
        bo.append({'author': a, 'comments': len(ts), 'active_months': len(months), 'first': months[0] if months else '', 'last': months[-1] if months else '',
                   'realism_pct': round(100*np.mean([bool(M['realism'].search(t or '')) for t, _ in ts]), 2),
                   'ai_any_pct': round(100*np.mean([bool(M['ai_any'].search(t or '')) for t, _ in ts]), 2),
                   'offshore_h1b_pct': round(100*np.mean([bool(M['offshore_h1b'].search(t or '')) for t, _ in ts]), 2)})
    write('lead5_network/brokers_profile.csv', bo, header=list(bo[1].keys()) if len(bo) > 1 else None)
    return brokers

def figures(lead3):
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    except ImportError:
        return
    fd = OUT / 'figures'; fd.mkdir(parents=True, exist_ok=True)
    m = [r['month'] for r in lead3]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    for k, lbl in [('replacement', 'AI + replacement/layoffs'), ('tools_named', 'AI tools named (Cursor, Copilot, Claude, agents)'),
                   ('mandate_tracking', 'Mandates / usage tracking'), ('hiring_gate', 'AI in hiring/interviews')]:
        ax.plot(m, [r[f'{k}_per_1000'] for r in lead3], marker='o', ms=3, label=lbl)
    ax.set_ylabel('comments per 1,000 cscq comments'); ax.set_title('r/cscareerquestions: what AI talk is about, by month')
    ax.tick_params(axis='x', rotation=60, labelsize=7); ax.legend(fontsize=7, frameon=False); ax.grid(alpha=.3); fig.tight_layout()
    fig.savefig(fd/'lead3_cscq_ai_themes.png', dpi=160); plt.close(fig)
    p = OUT/'lead1_reward/marker_within_thread_percentile.csv'
    rows = [r for r in csv.DictReader(p.open()) if r['marker'] in ('ai_pretext', 'ai_inevitable', 'exec_blame', 'offshore_h1b', 'individual_blame')]
    fig, ax = plt.subplots(figsize=(7.5, 4.2)); y = 0; ticks = []
    for r in rows:
        d, lo, hi = float(r['diff']), float(r['ci_lo']), float(r['ci_hi'])
        ax.errorbar(d, y, xerr=[[d-lo], [hi-d]], fmt='o', color='C0' if d > 0 else 'C3', capsize=3)
        ticks.append(f"{r['subreddit'][:10]} · {r['marker']} (n={r['n_marked']})"); y += 1
    ax.axvline(0, color='k', lw=.8); ax.set_yticks(range(len(ticks))); ax.set_yticklabels(ticks, fontsize=7)
    ax.set_xlabel('difference in mean within-thread score percentile (marked − unmarked), 95% bootstrap CI')
    ax.set_title('Lead 1: which explanations sit higher in their own thread?', fontsize=10); fig.tight_layout()
    fig.savefig(fd/'lead1_marker_percentiles.png', dpi=160); plt.close(fig)
    p = OUT/'lead4_offshore/cscq_daily_h1b.csv'
    rows = list(csv.DictReader(p.open()))
    fig, ax = plt.subplots(figsize=(9, 3.4)); ax.bar([r['date'][5:] for r in rows], [float(r['per_1000']) for r in rows], color='C1')
    ax.set_ylabel('H-1B mentions per 1,000 comments'); ax.set_title('r/cscareerquestions daily H-1B mentions, Aug–Oct 2025 (19 Sep: $100k fee proclamation)', fontsize=9)
    ax.tick_params(axis='x', rotation=90, labelsize=5); fig.tight_layout(); fig.savefig(fd/'lead4_daily_h1b.png', dpi=160); plt.close(fig)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c = connect()
    import time; t0 = time.time()
    def step(name, f, *a):
        out = f(*a); print(f'{name:<16} done at {time.time()-t0:7.1f}s', flush=True); return out
    step('screen_audit', screen_audit, c)
    rows = step('load_candidates', load_candidates, c)
    step('lead1_reward', lead1_reward, rows)
    step('lead2_proximity', lead2_proximity, c, rows)
    l3 = step('lead3_ai_shift', lead3_ai_shift, c, rows)
    step('lead4_offshore', lead4_offshore, c, rows)
    step('lead5_network', lead5_network, c, rows)
    step('figures', figures, l3)
    (OUT/'manifest.json').write_text(json.dumps({'script': 'scripts/explore_leads.py', 'database': 'read-only', 'shared_window_end': SHARED_END,
        'seed': 20261114, 'markers': {k: v.pattern for k, v in M.items()}, 'ai_themes': {k: v.pattern for k, v in THEMES_AI.items()},
        'note': 'Lexical markers are retrieval devices; precision is checked by reading (precision_samples/, manual/). Scores are snapshots; comparisons use within-thread percentiles.'}, indent=2))
    print('wrote', OUT)

if __name__ == '__main__':
    main()
