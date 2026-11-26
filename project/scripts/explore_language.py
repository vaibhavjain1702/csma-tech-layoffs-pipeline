"""Language analysis of the Reddit tech-employment corpus (read-only).

Part 1 - distinctive vocabulary ("Fightin' Words", Monroe, Colaresi & Quinn 2008):
  A. each community vs the other two (employment candidate comments, <= 2025-06)
  B. r/cscareerquestions Jan-Sep 2025 vs Jan-Sep 2026 (all comments, 25% fixed sample)
  C. upvoted vs downvoted inside the same threads (cscq, employment candidates)
Part 2 - community vocabulary over time (all cscq comments, per month) plus a
  cross-community snapshot for Jan-Jun 2025.

Writes CSVs and PNGs to outputs/10_language/. Does not modify the database.
Run:  .venv-eda/bin/python scripts/explore_language.py
"""
import collections, csv, json, math, random, re, sqlite3, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data/processed/reddit.sqlite'
OUT = ROOT / 'outputs/10_language'
SEED = 20261115
random.seed(SEED)
SHARED_END = '2025-06'
# career_transition is excluded from the candidate definition because of the "quite" matching bug
CAND = "(d.layoffs=1 or d.hiring_conditions=1 or d.ai_work_change=1 or d.corporate_restructuring=1 or d.economic_policy=1)"

STOP = set("""a about above after again against all almost also although always am among an and any anyone anything are aren't around as at
back be because been before being below between both but by can can't cannot could couldn't did didn't do does doesn't doing don't down during
each either else even ever every few for from further get gets getting go goes going gone got gotten had hadn't has hasn't have haven't having
he he'd he'll he's her here here's hers herself him himself his how how's however i i'd i'll i'm i've if in into is isn't it it's its itself
just let let's like lot lots made make makes making many may me might more most much must mustn't my myself need no nor not nothing now of off
often on once one only or other others our ours ourselves out over own per probably pretty put quite rather really right said same say says see
seem seems she she'd she'll she's should shouldn't since so some something still such sure take than that that's the their theirs them themselves
then there there's these they they'd they'll they're they've thing things think this those though through thus to too under until up upon us
use used using very via want wants was wasn't way we we'd we'll we're we've well went were weren't what what's whatever when when's where where's
whether which while who who's whom whose why why's will with within without won't would wouldn't yeah yes yet you you'd you'll you're you've your
yours yourself yourselves im ive dont doesnt didnt cant wont isnt arent thats theres youre theyre whats u ur lol also etc ok okay oh gt lt amp nbsp
http https www com org reddit deleted removed edit x s t m d ll re ve""".split())

URL = re.compile(r"https?://\S+|www\.\S+|\[([^\]]*)\]\([^)]*\)")
H1B = re.compile(r"\bh-?1-?b(s)?\b", re.I)
TOK = re.compile(r"[a-z][a-z0-9']*[a-z0-9]|[a-z]")

def tokens(text):
    t = URL.sub(lambda m: m.group(1) or ' ', (text or '').lower())
    t = H1B.sub('h1b', t).replace('’', "'")
    return [w.strip("'") for w in TOK.findall(t)]

def count_into(c, toks):
    """Unigrams and bigrams; stopwords are dropped and never bridged into a bigram."""
    prev = None
    for w in toks:
        if w in STOP or len(w) < 2:
            prev = None; continue
        c[w] += 1
        if prev: c[prev + ' ' + w] += 1
        prev = w
    return c

def fightin_words(ca, cb, prior_share=0.1, min_count=30):
    """Log-odds ratio with an informative Dirichlet prior (Monroe et al. 2008, eq. 16-22).
    Prior = both groups pooled, scaled so total pseudo-counts are prior_share of the pooled corpus.
    Returns rows sorted by z (positive = group a)."""
    na, nb = sum(ca.values()), sum(cb.values())
    bg = ca + cb; nbg = na + nb; a0 = prior_share * nbg
    rows = []
    for w, t in bg.items():
        if t < min_count: continue
        aw = a0 * t / nbg; ya, yb = ca.get(w, 0), cb.get(w, 0)
        d = math.log((ya + aw) / (na + a0 - ya - aw)) - math.log((yb + aw) / (nb + a0 - yb - aw))
        z = d / math.sqrt(1 / (ya + aw) + 1 / (yb + aw))
        rows.append({'term': w, 'z': round(z, 2), 'log_odds': round(d, 3), 'count_a': ya, 'count_b': yb,
                     'per_10k_a': round(1e4 * ya / na, 2), 'per_10k_b': round(1e4 * yb / nb, 2)})
    rows.sort(key=lambda r: -r['z'])
    return rows, na, nb

def write(name, rows, header=None):
    p = OUT / name; p.parent.mkdir(parents=True, exist_ok=True); rows = list(rows)
    header = header or (list(rows[0].keys()) if rows else [])
    with p.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction='ignore'); w.writeheader(); w.writerows(rows)

def kwic(texts, terms, per_term=3, width=90):
    """A few keyword-in-context snippets per term, so each term can be interpreted from real usage."""
    pats = {t: re.compile(r"\b" + r"\W+".join(map(re.escape, t.split())) + r"\b", re.I) for t in terms}
    pools = {t: [] for t in terms}
    for txt in texts:
        clean = ' '.join(H1B.sub('h1b', URL.sub(' ', txt or '')).split())
        for t, p in pats.items():
            m = p.search(clean)
            if m:
                pools[t].append('…' + clean[max(0, m.start() - width):m.end() + width] + '…')
    out = []
    for t in terms:
        for s in random.sample(pools[t], min(per_term, len(pools[t]))):
            out.append({'term': t, 'snippet': s})
    return out

# ---------------------------------------------------------------------------
def part1(c):
    res = {}
    # A. communities, employment candidates, shared window
    q = f"""select r.subreddit, f.own_text from disruption_screen d join records r on r.kind=d.kind and r.id=d.id
            join features f on f.kind=d.kind and f.id=d.id
            where d.kind='comments' and {CAND} and f.likely_bot=0 and r.created_month<='{SHARED_END}'"""
    cnt = collections.defaultdict(collections.Counter); texts = collections.defaultdict(list); ndoc = collections.Counter()
    for sub, t in c.execute(q):
        count_into(cnt[sub], tokens(t)); texts[sub].append(t); ndoc[sub] += 1
    subs = sorted(cnt)
    snippets = []
    for s in subs:
        rest = collections.Counter()
        for o in subs:
            if o != s: rest += cnt[o]
        rows, na, nb = fightin_words(cnt[s], rest)
        write(f'A_communities/{s}_vs_rest.csv', rows)
        res[f'A_{s}'] = {'comments': ndoc[s], 'tokens': na, 'rest_tokens': nb, 'top': [r['term'] for r in rows[:15]]}
        snippets += [{'community': s, **k} for k in kwic(texts[s], [r['term'] for r in rows[:10]])]
    write('A_communities/examples_in_context.csv', snippets)
    del texts

    # B. cscq 2025 vs 2026, same months (Jan-Sep), all comments, fixed 25% sample (created_utc % 4 = 0)
    q = """select r.created_month, f.own_text from records r join features f on f.kind=r.kind and f.id=r.id
           where r.kind='comments' and r.subreddit='cscareerquestions' and f.likely_bot=0 and (r.created_utc % 4)=0
           and substr(r.created_month,6,2) between '01' and '09'"""
    cb = {'2025': collections.Counter(), '2026': collections.Counter()}; nB = collections.Counter(); keep = {'2025': [], '2026': []}
    for m, t in c.execute(q):
        y = m[:4]; count_into(cb[y], tokens(t)); nB[y] += 1
        if len(keep[y]) < 60000: keep[y].append(t)
        elif random.random() < 0.05: keep[y][random.randrange(60000)] = t
    rows, na, nb = fightin_words(cb['2026'], cb['2025'], min_count=50)
    write('B_cscq_2025_vs_2026/terms.csv', rows)
    top26 = [r['term'] for r in rows[:12]]; top25 = [r['term'] for r in rows[::-1][:12]]
    write('B_cscq_2025_vs_2026/examples_in_context.csv',
          [{'side': '2026', **k} for k in kwic(keep['2026'], top26)] + [{'side': '2025', **k} for k in kwic(keep['2025'], top25)])
    res['B'] = {'comments_2025': nB['2025'], 'comments_2026': nB['2026'], 'tokens_2026': na, 'tokens_2025': nb,
                'top_2026': top26, 'top_2025': top25}
    del keep, cb

    # C. upvoted vs downvoted within the same threads (cscq, employment candidates, threads >= 10 comments)
    c.execute("create temp table cand_links as select distinct r.link_id from disruption_screen d join records r on r.kind=d.kind and r.id=d.id where d.kind='comments' and r.subreddit='cscareerquestions'")
    c.execute("create temp table wr(id text primary key, pr real, n integer) without rowid")
    c.execute("""insert into wr select id, percent_rank() over (partition by link_id order by score), count(*) over (partition by link_id)
                 from records where kind='comments' and link_id in (select link_id from cand_links)""")
    q = f"""select w.pr, r.score, f.own_text from disruption_screen d join records r on r.kind=d.kind and r.id=d.id
            join features f on f.kind=d.kind and f.id=d.id join wr w on w.id=d.id
            where d.kind='comments' and r.subreddit='cscareerquestions' and {CAND} and f.likely_bot=0 and w.n>=10"""
    up, down = collections.Counter(), collections.Counter(); tu, td = [], []
    for pr, sc, t in c.execute(q):
        if pr >= 0.9 and sc > 1: count_into(up, tokens(t)); tu.append(t)
        elif sc < 0: count_into(down, tokens(t)); td.append(t)
    rows, na, nb = fightin_words(up, down, min_count=25)
    write('C_cscq_upvoted_vs_downvoted/terms.csv', rows)
    tu_terms = [r['term'] for r in rows[:12]]; td_terms = [r['term'] for r in rows[::-1][:12]]
    write('C_cscq_upvoted_vs_downvoted/examples_in_context.csv',
          [{'side': 'upvoted', **k} for k in kwic(tu, tu_terms)] + [{'side': 'downvoted', **k} for k in kwic(td, td_terms)])
    res['C'] = {'upvoted_comments': len(tu), 'downvoted_comments': len(td), 'tokens_up': na, 'tokens_down': nb,
                'top_up': tu_terms, 'top_down': td_terms}
    return res

# ---------------------------------------------------------------------------
TERMS = {  # community vocabulary; label -> pattern (matched on own text, case-insensitive)
    'Market mood': {
        '"cooked"': r"\bcooked\b",
        'doom / doomer': r"\bdoom\w*\b",
        'cope / copium': r"\b(cope|copium|coping)\b",
        'ghosted': r"\bghost(ed|ing)\b",
    },
    'Explanations': {
        'AI-washing / AI as excuse': r"\bai[- ]?wash\w*\b|\b(excuse|scapegoat\w*|pretext|cover)\b[^.!?]{0,60}\bai\b|\bai\b[^.!?]{0,60}\b(excuse|scapegoat\w*|pretext)\b",
        'offshoring / outsourcing': r"\boffshor\w*\b|\boutsourc\w*\b",
        'H-1B': r"\bh-?1-?bs?\b",
        'ZIRP / interest rates / 174': r"\bzirp\b|\binterest rates?\b|\bsection 174\b",
        'overhiring': r"\bover-?\s?hir\w*\b",
    },
    'AI at work': {
        'vibe coding': r"\bvibe[- ]?cod\w*\b",
        'agents / agentic': r"\bagent(s|ic)\b",
        'named AI tools': r"\b(chatgpt|copilot|cursor|claude|codex|gemini)\b",
        'mandate(d)': r"\bmandat\w*\b",
        'slop': r"\bslop\w*\b",
    },
    'Career moves': {
        'layoff / laid off': r"\blay-?offs?\b|\blaid off\b",
        'new grad / entry level / junior': r"\bnew grads?\b|\bentry[- ]level\b|\bjuniors?\b",
        'leave tech / trades / career change': r"\btrade schools?\b|\bthe trades\b|\bleav\w* (the )?(field|industry|tech)\b|\bget(ting)? out of (tech|the field|the industry)\b|\bcareer (change|switch)\b|\bswitch\w* careers?\b",
        'union(ize)': r"(?<!soviet )(?<!european )(?<!credit )\bunion(s|i[sz]\w*)?\b",
    },
}

def part2(c):
    pats = {(g, k): re.compile(p, re.I) for g, d in TERMS.items() for k, p in d.items()}
    monthly = collections.defaultdict(collections.Counter); den = collections.Counter()
    snap = collections.defaultdict(collections.Counter); sden = collections.Counter()
    q = """select r.subreddit, r.created_month, f.own_text from records r join features f on f.kind=r.kind and f.id=r.id
           where r.kind='comments' and f.likely_bot=0 and (r.subreddit='cscareerquestions'
           or r.created_month between '2025-01' and '2025-06')"""
    for sub, m, t in c.execute(q):
        t = t or ''
        hits = [k for k, p in pats.items() if p.search(t)]
        if sub == 'cscareerquestions':
            den[m] += 1
            for k in hits: monthly[m][k] += 1
        if '2025-01' <= m <= '2025-06':
            sden[sub] += 1
            for k in hits: snap[sub][k] += 1
    months = sorted(den)
    rows = []
    for (g, k) in pats:
        row = {'group': g, 'term': k, 'pattern': TERMS[g][k]}
        for m in months: row[m] = round(1e4 * monthly[m][(g, k)] / den[m], 2)
        rows.append(row)
    write('D_vocabulary_over_time/cscq_monthly_per_10k_comments.csv', rows, ['group', 'term', 'pattern', *months])
    write('D_vocabulary_over_time/cscq_monthly_comment_counts.csv', [{'month': m, 'comments': den[m]} for m in months])
    subs = sorted(sden)
    write('D_vocabulary_over_time/communities_jan_jun_2025_per_10k.csv',
          [{'group': g, 'term': k, **{s: round(1e4 * snap[s][(g, k)] / sden[s], 2) for s in subs}} for (g, k) in pats],
          ['group', 'term', *subs])
    # change summary: Jan-Jun 2025 vs Jan-Jun 2026 (same season)
    h = lambda y: [m for m in months if m.startswith(y) and m[5:] <= '06']
    ch = []
    for (g, k) in pats:
        a = sum(monthly[m][(g, k)] for m in h('2025')) / sum(den[m] for m in h('2025'))
        b = sum(monthly[m][(g, k)] for m in h('2026')) / sum(den[m] for m in h('2026'))
        ch.append({'group': g, 'term': k, 'per_10k_2025H1': round(1e4 * a, 2), 'per_10k_2026H1': round(1e4 * b, 2),
                   'ratio_2026_vs_2025': round(b / a, 2) if a else ''})
    write('D_vocabulary_over_time/cscq_change_2025H1_vs_2026H1.csv', ch)
    return months, rows, sden

# ---------------------------------------------------------------------------
def figures(res, months, trows):
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    except ImportError:
        return
    fd = OUT / 'figures'; fd.mkdir(parents=True, exist_ok=True)
    INK, A, B = '#1f2937', '#2563eb', '#dc2626'

    def diverging(path, rows, la, lb, title, k=18):
        top, bot = rows[:k], rows[::-1][:k]
        fig, axes = plt.subplots(1, 2, figsize=(10, 0.32 * k + 1.4))
        for ax, sel, col, lab in ((axes[0], bot, B, lb), (axes[1], top, A, la)):
            ax.barh(range(len(sel))[::-1], [abs(r['z']) for r in sel], color=col, alpha=.85)
            ax.set_yticks(range(len(sel))[::-1]); ax.set_yticklabels([r['term'] for r in sel], fontsize=8)
            ax.set_title(f'more typical of {lab}', fontsize=9, color=col); ax.set_xlabel('z-score (log-odds, informative prior)', fontsize=7)
            ax.tick_params(axis='x', labelsize=7); ax.spines[['top', 'right']].set_visible(False)
        fig.suptitle(title, fontsize=10, color=INK); fig.tight_layout(); fig.savefig(fd / path, dpi=160); plt.close(fig)

    # A: one panel per community
    subs = [k[2:] for k in res if k.startswith('A_')]
    fig, axes = plt.subplots(1, len(subs), figsize=(4.0 * len(subs), 5.6))
    for ax, s in zip(axes, subs):
        rows = list(csv.DictReader((OUT / f'A_communities/{s}_vs_rest.csv').open()))[:20]
        ax.barh(range(len(rows))[::-1], [float(r['z']) for r in rows], color=A, alpha=.85)
        ax.set_yticks(range(len(rows))[::-1]); ax.set_yticklabels([r['term'] for r in rows], fontsize=8)
        ax.set_title(f'r/{s}', fontsize=10); ax.set_xlabel('z vs other two communities', fontsize=7)
        ax.tick_params(axis='x', labelsize=7); ax.spines[['top', 'right']].set_visible(False)
    fig.suptitle('Most distinctive words in employment-related comments, Jan 2025 – Jun 2025', fontsize=10)
    fig.tight_layout(); fig.savefig(fd / 'A_communities_distinctive_terms.png', dpi=160); plt.close(fig)

    rb = list(csv.DictReader((OUT / 'B_cscq_2025_vs_2026/terms.csv').open()))
    for r in rb: r['z'] = float(r['z'])
    diverging('B_cscq_2025_vs_2026.png', rb, 'Jan–Sep 2026', 'Jan–Sep 2025', 'r/cscareerquestions: how the vocabulary changed (all comments, 25% sample)')
    rc = list(csv.DictReader((OUT / 'C_cscq_upvoted_vs_downvoted/terms.csv').open()))
    for r in rc: r['z'] = float(r['z'])
    diverging('C_cscq_upvoted_vs_downvoted.png', rc, 'upvoted (top 10% of thread)', 'downvoted (score < 0)',
              'r/cscareerquestions employment comments: words in upvoted vs downvoted comments')

    # D: small multiples, one panel per term
    allt = [r for r in trows]
    n = len(allt); cols = 4; rws = math.ceil(n / cols)
    fig, axes = plt.subplots(rws, cols, figsize=(13, 2.1 * rws), sharex=True)
    x = np.arange(len(months)); ev = months.index('2025-09') if '2025-09' in months else None
    for ax, r in zip(axes.flat, allt):
        y = [r[m] for m in months]
        ax.plot(x, y, color=A, lw=1.6); ax.fill_between(x, y, color=A, alpha=.12)
        if ev is not None: ax.axvline(ev, color='#9ca3af', lw=.8, ls=':')
        ax.set_title(r['term'], fontsize=8.5, loc='left'); ax.tick_params(labelsize=6.5); ax.set_ylim(bottom=0)
        ax.spines[['top', 'right']].set_visible(False); ax.grid(axis='y', alpha=.25)
    for ax in list(axes.flat)[n:]: ax.axis('off')
    ticks = [i for i, m in enumerate(months) if m.endswith(('-01', '-04', '-07', '-10'))]
    for ax in axes[-1]: ax.set_xticks(ticks); ax.set_xticklabels([months[i] for i in ticks], rotation=60, fontsize=6.5)
    fig.suptitle('r/cscareerquestions vocabulary over time (comments containing term, per 10,000 comments; dotted line = Sep 2025)', fontsize=10)
    fig.tight_layout(); fig.savefig(fd / 'D_cscq_vocabulary_over_time.png', dpi=160); plt.close(fig)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(f'file:{DB}?mode=ro', uri=True); t0 = time.time()
    res = part1(c); print(f'part1 done {time.time()-t0:.0f}s', flush=True)
    months, trows, sden = part2(c); print(f'part2 done {time.time()-t0:.0f}s', flush=True)
    figures(res, months, trows)
    res['D'] = {'months': len(months), 'snapshot_comments_jan_jun_2025': dict(sden)}
    (OUT / 'manifest.json').write_text(json.dumps({'script': 'scripts/explore_language.py', 'database': 'read-only', 'seed': SEED,
        'candidate_definition': CAND, 'method': "Fightin' Words: log-odds with informative Dirichlet prior (pooled, 10% weight); terms with z>|1.96| differ at ~5% (no multiple-comparison correction; use as ranking).",
        'summary': res, 'vocabulary_patterns': TERMS}, indent=2))
    print(json.dumps(res, indent=1))

if __name__ == '__main__':
    main()
