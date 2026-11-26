"""Community dynamics in the Reddit tech-employment corpus (read-only).

E. How fast cscq's language changes, and what is new each month
   (month-to-month Jensen-Shannon divergence; each month vs the previous 3 months with Fightin' Words).
F. Who adopts new vocabulary first: heavy vs occasional cscq commenters
   (after Danescu-Niculescu-Mizil et al. 2013, "No country for old members").
G. What style of comment rises within its thread (after Goyal et al., ICWSM, upvotes as community values):
   OLS of within-thread score percentile on simple style features, thread-clustered standard errors.
H. What sources each community links to (domains and subreddits in comment URLs).

Writes to outputs/11_dynamics/. Does not modify the database.
Run:  .venv-eda/bin/python scripts/explore_dynamics.py
"""
import collections, csv, json, math, re, sqlite3, sys, time
from pathlib import Path
from urllib.parse import urlparse
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from explore_language import tokens, STOP, fightin_words, CAND, SHARED_END  # reuse the same tokenizer and method

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data/processed/reddit.sqlite'
OUT = ROOT / 'outputs/11_dynamics'

def write(name, rows, header=None):
    p = OUT / name; p.parent.mkdir(parents=True, exist_ok=True); rows = list(rows)
    header = header or (list(rows[0].keys()) if rows else [])
    with p.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction='ignore'); w.writeheader(); w.writerows(rows)

ADOPT = {  # vocabulary tracked for F
    'slop': r"\bslop\w*\b", 'agents / agentic': r"\bagent(s|ic)\b", 'vibe coding': r"\bvibe[- ]?cod\w*\b",
    'claude': r"\bclaude\b", '"cooked"': r"\bcooked\b", 'cope / copium': r"\b(cope|copium|coping)\b",
    'H-1B': r"\bh-?1-?bs?\b",
    'AI-washing / AI as excuse': r"\bai[- ]?wash\w*\b|\b(excuse|scapegoat\w*|pretext|cover)\b[^.!?]{0,60}\bai\b|\bai\b[^.!?]{0,60}\b(excuse|scapegoat\w*|pretext)\b",
}

# ---------------------------------------------------------------------------
def part_EF(c):
    """One pass over all cscq comments: monthly unigram counts (E) and term use by author activity (F)."""
    act = dict(c.execute("""select f.author_key, count(*) from features f join records r on r.kind=f.kind and r.id=f.id
                            where r.kind='comments' and r.subreddit='cscareerquestions' and f.author_key is not null group by 1"""))
    def tier(a):
        n = act.get(a)
        if n is None: return None
        return 'heavy (50+ comments)' if n >= 50 else 'regular (10-49)' if n >= 10 else 'occasional (<10)'
    pats = {k: re.compile(p, re.I) for k, p in ADOPT.items()}
    month_words = collections.defaultdict(collections.Counter); ncom = collections.Counter()
    use = collections.defaultdict(collections.Counter); den = collections.Counter()   # (tier, month) -> term counts
    q = """select r.created_month, f.author_key, f.own_text from records r join features f on f.kind=r.kind and f.id=r.id
           where r.kind='comments' and r.subreddit='cscareerquestions' and f.likely_bot=0"""
    for m, a, t in c.execute(q):
        t = t or ''; ncom[m] += 1
        cw = month_words[m]
        for w in tokens(t):
            if w not in STOP and len(w) > 1: cw[w] += 1
        tr = tier(a)
        if tr:
            den[(tr, m)] += 1
            for k, p in pats.items():
                if p.search(t): use[(tr, m)][k] += 1
    months = sorted(ncom)

    # E1. month-to-month Jensen-Shannon divergence on a shared vocabulary
    total = collections.Counter()
    for m in months: total.update(month_words[m])
    vocab = [w for w, n in total.items() if n >= 100]; idx = {w: i for i, w in enumerate(vocab)}
    def vec(cn):
        v = np.full(len(vocab), 0.5)  # add-half smoothing
        for w, n in cn.items():
            i = idx.get(w)
            if i is not None: v[i] += n
        return v / v.sum()
    P = {m: vec(month_words[m]) for m in months}
    def jsd(p, q):
        mm = 0.5 * (p + q); return float(0.5 * np.sum(p * np.log2(p / mm)) + 0.5 * np.sum(q * np.log2(q / mm)))
    rows = [{'month': m, 'comments': ncom[m], 'jsd_vs_previous_month': round(jsd(P[m], P[months[i-1]]), 5) if i else ''} for i, m in enumerate(months)]
    write('E_language_change/cscq_monthly_jsd.csv', rows)

    # E2. what is new each month: month vs the pooled previous three months
    nov = []
    for i, m in enumerate(months):
        if i < 3: continue
        prev = collections.Counter()
        for pm in months[i-3:i]: prev.update(month_words[pm])
        fw, _, _ = fightin_words(month_words[m], prev, min_count=40)
        top = [r for r in fw if r['count_a'] >= 30][:10]
        nov.append({'month': m, 'new_this_month': ', '.join(f"{r['term']} ({r['z']:.0f})" for r in top)})
    write('E_language_change/cscq_whats_new_each_month.csv', nov)

    # F. adoption by author activity tier
    tiers = ['heavy (50+ comments)', 'regular (10-49)', 'occasional (<10)']
    fr = []
    for k in ADOPT:
        for tr in tiers:
            row = {'term': k, 'tier': tr}
            for m in months: row[m] = round(1e4 * use[(tr, m)][k] / den[(tr, m)], 2) if den[(tr, m)] else ''
            fr.append(row)
    write('F_adoption/cscq_term_rate_by_author_tier.csv', fr, ['term', 'tier', *months])
    # half-year summary: heavy vs occasional rate ratio
    def half(m): return m[:4] + ('H1' if m[5:] <= '06' else 'H2')
    halves = sorted({half(m) for m in months})
    summ = []
    for k in ADOPT:
        for h in halves:
            ms = [m for m in months if half(m) == h]
            r = {}
            for tr in tiers:
                n = sum(use[(tr, m)][k] for m in ms); d = sum(den[(tr, m)] for m in ms); r[tr] = 1e4 * n / d if d else float('nan')
            summ.append({'term': k, 'half': h, **{f'{t.split()[0]}_per_10k': round(r[t], 2) for t in tiers},
                         'heavy_vs_occasional_ratio': round(r[tiers[0]] / r[tiers[2]], 2) if r[tiers[2]] else ''})
    write('F_adoption/cscq_heavy_vs_occasional_by_half.csv', summ)
    write('F_adoption/author_tiers.csv', [{'tier': t, 'authors': sum(1 for a in act if tier(a) == t),
          'comments': sum(n for a, n in act.items() if tier(a) == t)} for t in tiers])
    return months, rows, fr

# ---------------------------------------------------------------------------
FEAT = {
    'first_person_singular': re.compile(r"\b(i|me|my|mine|i'm|i've|i'd|i'll|im|ive)\b", re.I),
    'second_person': re.compile(r"\b(you|your|you're|youre|yours)\b", re.I),
    'question': re.compile(r"\?"),
    'number_or_amount': re.compile(r"\d"),
    'profanity': re.compile(r"\b(fuck\w*|shit\w*|damn|crap|bullshit|wtf)\b", re.I),
    'certainty': re.compile(r"\b(definitely|always|never|obviously|clearly|literally|100%|guaranteed|no way)\b", re.I),
    'hedging': re.compile(r"\b(maybe|probably|perhaps|might|i think|i guess|seems|imo|imho)\b", re.I),
    'humour_marker': re.compile(r"\b(lol|lmao|rofl|haha\w*)\b|😂|🤣", re.I),
}

def ols_cluster(X, y, g):
    """OLS with standard errors clustered by thread (sandwich estimator)."""
    XtX_inv = np.linalg.inv(X.T @ X); b = XtX_inv @ X.T @ y; e = y - X @ b
    order = np.argsort(g, kind='stable'); gs = g[order]; Xe = X[order] * e[order, None]
    cuts = np.flatnonzero(np.r_[True, gs[1:] != gs[:-1], True])
    S = np.add.reduceat(Xe, cuts[:-1], axis=0)
    G = len(cuts) - 1; n, k = X.shape
    meat = S.T @ S * (G / (G - 1)) * ((n - 1) / (n - k))
    se = np.sqrt(np.diag(XtX_inv @ meat @ XtX_inv))
    return b, se, G

def part_G(c):
    c.execute("create temp table links as select distinct r.link_id from disruption_screen d join records r on r.kind=d.kind and r.id=d.id where d.kind='comments'")
    c.execute("create temp table wr(id text primary key, pr real, tr real, n integer) without rowid")
    c.execute("""insert into wr select id, percent_rank() over (partition by link_id order by score),
                 percent_rank() over (partition by link_id order by created_utc), count(*) over (partition by link_id)
                 from records where kind='comments' and link_id in (select link_id from links)""")
    q = f"""select r.subreddit, r.created_month, r.link_id, w.pr, w.tr, e.parent_kind, f.own_text, f.urls_json, f.word_count
            from disruption_screen d join records r on r.kind=d.kind and r.id=d.id join features f on f.kind=d.kind and f.id=d.id
            join wr w on w.id=d.id left join reply_edges e on e.child_id=d.id
            where d.kind='comments' and {CAND} and f.likely_bot=0 and w.n>=10 and coalesce(f.word_count,0)>=3"""
    data = collections.defaultdict(list)
    for sub, m, link, pr, tr, pk, t, u, wc in c.execute(q):
        if sub != 'cscareerquestions' and m > SHARED_END: continue
        t = t or ''; wc = wc or len(t.split())
        f = {k: float(bool(p.search(t))) for k, p in FEAT.items()}
        f['has_link'] = float(u not in (None, '', '[]'))
        f['log2_words'] = math.log2(max(wc, 1))
        f['early_arrival'] = float(tr <= 0.2); f['reply_to_post'] = float(pk == 'posts')
        data[sub].append((pr, link, f))
    names = list(FEAT) + ['has_link', 'log2_words', 'early_arrival', 'reply_to_post']
    rows = []; desc = []
    for sub, D in data.items():
        y = np.array([d[0] for d in D]); g = np.array([hash(d[1]) for d in D])
        X = np.column_stack([np.ones(len(D))] + [[d[2][k] for d in D] for k in names])
        b, se, G = ols_cluster(X, y, g)
        for i, k in enumerate(['intercept'] + names):
            rows.append({'subreddit': sub, 'feature': k, 'coef': round(b[i], 4), 'ci_lo': round(b[i] - 1.96*se[i], 4), 'ci_hi': round(b[i] + 1.96*se[i], 4),
                         'n_comments': len(D), 'n_threads': G})
        for k in names:
            if k == 'log2_words': continue
            col = X[:, 1 + names.index(k)]
            desc.append({'subreddit': sub, 'feature': k, 'share_with_feature_pct': round(100*col.mean(), 1),
                         'mean_pct_with': round(y[col == 1].mean(), 3) if col.any() else '', 'mean_pct_without': round(y[col == 0].mean(), 3)})
        # length deciles
        lw = X[:, 1 + names.index('log2_words')]; qs = np.quantile(lw, np.linspace(0, 1, 11))
        for j in range(10):
            sel = (lw >= qs[j]) & ((lw < qs[j+1]) if j < 9 else (lw <= qs[j+1]))
            desc.append({'subreddit': sub, 'feature': f'length_decile_{j+1} ({int(2**qs[j])}-{int(2**qs[j+1])} words)',
                         'share_with_feature_pct': round(100*sel.mean(), 1), 'mean_pct_with': round(y[sel].mean(), 3), 'mean_pct_without': ''})
    write('G_style_and_votes/ols_within_thread_percentile.csv', rows)
    write('G_style_and_votes/descriptives.csv', desc)
    return rows

# ---------------------------------------------------------------------------
ALIAS = {'youtu.be': 'youtube.com', 'redd.it': 'reddit.com', 'x.com': 'twitter.com', 'amp.cnn.com': 'cnn.com', 'nytimes.com': 'nytimes.com'}
def domain(u):
    try: h = urlparse(u).netloc.lower()
    except ValueError: return None
    h = re.sub(r"^(www\d?|m|old|new|np|amp|mobile|en|i|preview)\.", '', h); h = h.split(':')[0]
    return ALIAS.get(h, h) or None

def part_H(c):
    q = f"""select r.subreddit, r.created_month, f.urls_json from disruption_screen d join records r on r.kind=d.kind and r.id=d.id
            join features f on f.kind=d.kind and f.id=d.id where d.kind='comments' and {CAND} and f.likely_bot=0"""
    dom = collections.defaultdict(collections.Counter); subs = collections.defaultdict(collections.Counter)
    ncom = collections.Counter(); nlink = collections.Counter(); cs_month = collections.defaultdict(collections.Counter); cs_den = collections.Counter()
    for sub, m, u in c.execute(q):
        shared = m <= SHARED_END
        if shared: ncom[sub] += 1
        if sub == 'cscareerquestions': cs_den[m] += 1
        if u in (None, '', '[]'): continue
        try: urls = json.loads(u)
        except ValueError: continue
        ds = {domain(x) for x in urls} - {None}
        if not ds: continue
        if shared:
            nlink[sub] += 1
            for d in ds: dom[sub][d] += 1
        if sub == 'cscareerquestions':
            cs_month[m]['_any'] += 1
            for d in ds: cs_month[m][d] += 1
        for x in urls:
            mm = re.search(r"reddit\.com/r/([A-Za-z0-9_]+)", x)
            if mm and shared: subs[sub]['r/' + mm.group(1).lower()] += 1
    out = []
    for sub in sorted(dom):
        for d, n in dom[sub].most_common(30):
            out.append({'subreddit': sub, 'domain': d, 'comments_linking': n, 'pct_of_link_comments': round(100*n/nlink[sub], 1),
                        'per_10k_employment_comments': round(1e4*n/ncom[sub], 1)})
    write('H_sources/top_domains_by_community_le_2025-06.csv', out)
    write('H_sources/link_rate_by_community_le_2025-06.csv', [{'subreddit': s, 'employment_comments': ncom[s], 'with_link': nlink[s],
          'pct_with_link': round(100*nlink[s]/ncom[s], 2)} for s in sorted(ncom)])
    write('H_sources/subreddits_linked_le_2025-06.csv', [{'from': s, 'to': t, 'comments': n} for s in sorted(subs) for t, n in subs[s].most_common(15)])
    months = sorted(cs_den); topd = [d for d, _ in sum((cs_month[m] for m in months), collections.Counter()).most_common(16) if d != '_any'][:15]
    write('H_sources/cscq_domains_monthly_per_10k.csv', [{'month': m, 'employment_comments': cs_den[m], 'any_link_per_10k': round(1e4*cs_month[m]['_any']/cs_den[m], 1),
          **{d: round(1e4*cs_month[m][d]/cs_den[m], 2) for d in topd}} for m in months])
    return out

# ---------------------------------------------------------------------------
def figures(months, jrows, frows, grows):
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    except ImportError:
        return
    fd = OUT / 'figures'; fd.mkdir(parents=True, exist_ok=True)
    # E
    x = [r['month'] for r in jrows[1:]]; y = [r['jsd_vs_previous_month'] for r in jrows[1:]]
    fig, ax = plt.subplots(figsize=(9, 3.4)); ax.plot(x, y, marker='o', color='#2563eb')
    ax.set_ylabel('JS divergence vs previous month'); ax.set_title('r/cscareerquestions: how much the vocabulary changed from one month to the next', fontsize=10)
    ax.tick_params(axis='x', rotation=60, labelsize=7); ax.grid(alpha=.3); ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout(); fig.savefig(fd / 'E_cscq_language_change.png', dpi=160); plt.close(fig)
    # F
    terms = list(ADOPT); cols = 4; rws = math.ceil(len(terms) / cols)
    fig, axes = plt.subplots(rws, cols, figsize=(13, 2.6 * rws), sharex=True)
    colors = {'heavy (50+ comments)': '#dc2626', 'regular (10-49)': '#f59e0b', 'occasional (<10)': '#2563eb'}
    xi = np.arange(len(months))
    for ax, k in zip(axes.flat, terms):
        for r in frows:
            if r['term'] == k:
                ax.plot(xi, [float(r[m] or 0) for m in months], color=colors[r['tier']], lw=1.4, label=r['tier'])
        ax.set_title(k, fontsize=9, loc='left'); ax.tick_params(labelsize=6.5); ax.spines[['top', 'right']].set_visible(False); ax.grid(axis='y', alpha=.25)
    ticks = [i for i, m in enumerate(months) if m.endswith(('-01', '-07'))]
    for ax in axes[-1]: ax.set_xticks(ticks); ax.set_xticklabels([months[i] for i in ticks], rotation=45, fontsize=7)
    axes.flat[0].legend(fontsize=7, frameon=False)
    fig.suptitle('r/cscareerquestions: who uses the new words? (comments containing term per 10,000 comments, by commenter activity)', fontsize=10)
    fig.tight_layout(); fig.savefig(fd / 'F_adoption_by_author_tier.png', dpi=160); plt.close(fig)
    # G
    feats = [k for k in list(FEAT) + ['has_link', 'log2_words', 'early_arrival', 'reply_to_post']]
    subs = sorted({r['subreddit'] for r in grows})
    fig, ax = plt.subplots(figsize=(8, 5.5)); off = {s: (i - 1) * 0.25 for i, s in enumerate(subs)}
    for s, col in zip(subs, ['#2563eb', '#16a34a', '#9333ea']):
        rr = {r['feature']: r for r in grows if r['subreddit'] == s}
        for j, k in enumerate(feats):
            r = rr[k]; ax.errorbar(r['coef'], j + off[s], xerr=[[r['coef'] - r['ci_lo']], [r['ci_hi'] - r['coef']]], fmt='o', ms=4, color=col, capsize=2,
                                   label=f'r/{s}' if j == 0 else None)
    ax.axvline(0, color='k', lw=.8); ax.set_yticks(range(len(feats))); ax.set_yticklabels(feats, fontsize=8); ax.invert_yaxis()
    ax.set_xlabel('change in within-thread score percentile (OLS, 95% CI clustered by thread)', fontsize=8)
    ax.set_title('Which comment styles sit higher in their thread? (employment comments)', fontsize=10); ax.legend(fontsize=8, frameon=False)
    ax.spines[['top', 'right']].set_visible(False); fig.tight_layout(); fig.savefig(fd / 'G_style_coefficients.png', dpi=160); plt.close(fig)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(f'file:{DB}?mode=ro', uri=True); t0 = time.time()
    months, jrows, frows = part_EF(c); print(f'E/F done {time.time()-t0:.0f}s', flush=True)
    grows = part_G(c); print(f'G done {time.time()-t0:.0f}s', flush=True)
    part_H(c); print(f'H done {time.time()-t0:.0f}s', flush=True)
    figures(months, jrows, frows, grows)
    (OUT / 'manifest.json').write_text(json.dumps({'script': 'scripts/explore_dynamics.py', 'database': 'read-only',
        'adoption_terms': ADOPT, 'style_features': {k: p.pattern for k, p in FEAT.items()},
        'references': ['Danescu-Niculescu-Mizil et al. 2013, No country for old members (WWW)',
                       'Zhang et al. 2017, Community identity and user engagement (ICWSM)',
                       'Goyal et al., Uncovering the Internet\'s hidden values (ICWSM; arXiv 2410.13036)',
                       'Monroe, Colaresi & Quinn 2008, Fightin\' Words (Political Analysis)']}, indent=2))
    print('wrote', OUT)

if __name__ == '__main__':
    main()
