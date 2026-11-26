"""Four exploratory directions, each a question with a rival a single number can separate.

D1 (H2, rival R4 selection)  Same author, two communities: does framing follow the person or the room?
D2 (H3 consequence)          After a first own-layoff story, do authors who got sympathy come back more?
D3 (R8 event shock)          H-1B proclamation (19 Sep 2025): spike or lasting shift, and did the framing change?
D4 (core vs periphery)       Are story-sharers newcomers and blamers regulars?
Read-only. Output: outputs/14_directions/.  Run: .venv-eda/bin/python scripts/explore_directions.py
"""
import csv, sys, random, datetime as dt
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from explore_leads import M, connect, short

OUT = Path(__file__).resolve().parents[1] / 'outputs/14_directions'; OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20261119); random.seed(20261119)
DAY = 86400

def write(name, rows):
    with (OUT / name).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f'\n== {name}'); [print(r) for r in rows[:40]]

def boot_ci(x, reps=2000):
    x = np.asarray(x, float)
    if len(x) < 2: return (float('nan'),) * 2
    m = rng.choice(x, size=(reps, len(x))).mean(1); return tuple(float(v) for v in np.percentile(m, [2.5, 97.5]))

c = connect()
TYPES = {'experience': 'first_person_layoff', 'mentions_execs': 'exec_blame', 'mentions_offshore': 'offshore_h1b',
         'ai_excuse': 'ai_pretext', 'doom': 'realism'}
def kinds(t): return [k for k, m in TYPES.items() if M[m].search(t)]

# ---------------- D1: same author in cscq and r/technology, Jan-Jun 2025, screened comments
q = """select r.subreddit, f.author_key, f.own_text, d.layoffs from disruption_screen d join records r on r.kind=d.kind and r.id=d.id
       join features f on f.kind=d.kind and f.id=d.id
       where d.kind='comments' and r.created_month between '2025-01' and '2025-06' and f.likely_bot=0 and f.author_unknown=0
       and r.subreddit in ('cscareerquestions','technology')"""
per = defaultdict(lambda: defaultdict(Counter))   # author -> sub -> counts
for s, a, t, lay in c.execute(q):
    t = t or ''; d = per[a][s]; d['n'] += 1
    d['execs'] += bool(M['exec_blame'].search(t)); d['offshore'] += bool(M['offshore_h1b'].search(t))
    d['consequence'] += bool(M['consequence'].search(t)); d['ai'] += bool(M['ai_any'].search(t))
    if lay: d['lay'] += 1; d['own_story'] += bool(M['first_person_layoff'].search(t))
both = [a for a, v in per.items() if v['cscareerquestions']['n'] >= 2 and v['technology']['n'] >= 2]
rows = []
for feat in ('execs', 'offshore', 'consequence', 'ai'):
    # all authors (pooled) vs the same authors in each room (author-level means, each author weighted equally)
    pooled = {s: sum(v[s][feat] for v in per.values()) / max(sum(v[s]['n'] for v in per.values()), 1) for s in ('cscareerquestions', 'technology')}
    cs = [per[a]['cscareerquestions'][feat] / per[a]['cscareerquestions']['n'] for a in both]
    te = [per[a]['technology'][feat] / per[a]['technology']['n'] for a in both]
    diff = np.array(te) - np.array(cs)
    rows.append({'marker': feat, 'all_authors_cscq_pct': round(100 * pooled['cscareerquestions'], 1),
                 'all_authors_tech_pct': round(100 * pooled['technology'], 1),
                 'same_authors_n': len(both), 'same_authors_cscq_pct': round(100 * np.mean(cs), 1),
                 'same_authors_tech_pct': round(100 * np.mean(te), 1),
                 'within_author_diff_tech_minus_cscq_pp': round(100 * diff.mean(), 1),
                 'ci95_pp': tuple(round(100 * v, 1) for v in boot_ci(diff))})
write('D1_same_author_two_rooms.csv', rows)

# ---------------- load all cscq comments (author timeline) once
q = """select r.id, r.created_utc, r.link_id, f.author_key, f.author_unknown, f.likely_bot, (d.id is not null), d.layoffs,
              case when d.id is not null then f.own_text end
       from records r join features f on f.kind=r.kind and f.id=r.id
       left join disruption_screen d on d.kind=r.kind and d.id=r.id
       where r.kind='comments' and r.subreddit='cscareerquestions'"""
cs_rows = c.execute(q).fetchall()
END = max(r[1] for r in cs_rows)
times = defaultdict(list)
for rid, ts, link, a, unk, bot, scr, lay, t in cs_rows:
    if not unk and not bot: times[a].append(ts)
for a in times: times[a].sort()
def count_between(a, lo, hi):
    tl = times.get(a, []); return int(np.searchsorted(tl, hi, 'left') - np.searchsorted(tl, lo, 'right'))

# ---------------- D2: first own-layoff story -> sympathy? -> return within 90 days
first = {}
for rid, ts, link, a, unk, bot, scr, lay, t in cs_rows:
    if scr and not unk and not bot and t and M['first_person_layoff'].search(t):
        if a not in first or ts < first[a][1]: first[a] = (rid, ts, t)
first = {a: v for a, v in first.items() if v[1] <= END - 90 * DAY}
c.execute('create temp table fs(fn text primary key)')
c.executemany('insert into fs values (?)', [('t1_' + v[0],) for v in first.values()])
rep = defaultdict(lambda: Counter())
for fn, ca, txt in c.execute("""select e.parent_fullname, e.child_author_key, f.own_text from reply_edges e join fs on fs.fn=e.parent_fullname
                                join features f on f.kind='comments' and f.id=e.child_id where f.likely_bot=0"""):
    rep[fn[3:]]['any'] += 1; rep[fn[3:]]['sym'] += bool(M['empathy_reply'].search(txt or ''))
groups = defaultdict(list); ex = defaultdict(list)
for a, (rid, ts, t) in first.items():
    r = rep.get(rid, Counter())
    g = 'sympathy' if r['sym'] else ('reply_no_sympathy' if r['any'] else 'no_reply')
    prior = count_between(a, ts - 90 * DAY, ts)
    band = '0 prior' if prior == 0 else ('1-5 prior' if prior <= 5 else '6+ prior')
    after = count_between(a, ts + DAY, ts + 90 * DAY)   # skip the same-day thread conversation
    groups[(band, g)].append(after > 0); groups[('all', g)].append(after > 0)
    if len(ex[g]) < 4 and 15 < len(t.split()) < 80: ex[g].append(short(t, 220))
rows = []
for band in ('all', '0 prior', '1-5 prior', '6+ prior'):
    for g in ('sympathy', 'reply_no_sympathy', 'no_reply'):
        x = groups.get((band, g), [])
        if x: rows.append({'prior_activity_90d': band, 'first_story_got': g, 'authors': len(x),
                           'returned_within_90d_pct': round(100 * np.mean(x), 1), 'ci95': tuple(round(100 * v, 1) for v in boot_ci(x))})
write('D2_sympathy_and_return.csv', rows)

# ---------------- D3: H-1B proclamation, cscq daily, screened comments
EV = dt.datetime(2025, 9, 19, tzinfo=dt.timezone.utc).timestamp()
win = defaultdict(Counter); exs = []
for rid, ts, link, a, unk, bot, scr, lay, t in cs_rows:
    if not scr or bot or not t: continue
    wk = int((ts - EV) // (7 * DAY))
    if -8 <= wk <= 16:
        w = win[wk]; w['screened'] += 1
        if M['offshore_h1b'].search(t):
            w['offshore'] += 1; w['off_execs'] += bool(M['exec_blame'].search(t)); w['off_ethnic'] += bool(M['ethnic_ref'].search(t))
            if 0 <= wk <= 1 and len(exs) < 6 and 15 < len(t.split()) < 70: exs.append(short(t, 220))
rows = [{'week_from_19sep2025': k, 'screened': w['screened'], 'offshore_pct': round(100 * w['offshore'] / w['screened'], 1),
         'of_offshore_also_execs_pct': round(100 * w['off_execs'] / max(w['offshore'], 1), 1),
         'of_offshore_also_ethnic_ref_pct': round(100 * w['off_ethnic'] / max(w['offshore'], 1), 1)} for k, w in sorted(win.items())]
write('D3_h1b_shock_weekly.csv', rows)

# ---------------- D4: who writes each kind of comment (prior 180-day activity in cscq)
acts = defaultdict(list); unk_share = Counter(); tot = Counter()
for rid, ts, link, a, unk, bot, scr, lay, t in cs_rows:
    if not scr or bot or not t: continue
    ks = kinds(t) or ['none']
    for k in ks:
        tot[k] += 1; unk_share[k] += unk
        if not unk: acts[k].append(count_between(a, ts - 180 * DAY, ts))
rows = []
for k in list(TYPES) + ['none']:
    x = np.array(acts[k])
    rows.append({'comment_kind': k, 'comments': tot[k], 'deleted_or_unknown_author_pct': round(100 * unk_share[k] / tot[k], 1),
                 'median_prior_180d_comments': int(np.median(x)), 'newcomer_pct_0_prior': round(100 * np.mean(x == 0), 1),
                 'regular_pct_50plus_prior': round(100 * np.mean(x >= 50), 1)})
write('D4_core_periphery.csv', rows)

with (OUT / 'examples.txt').open('w') as f:
    for g, v in ex.items(): f.write(f'# D2 first story, got {g}\n' + '\n'.join('- ' + s for s in v) + '\n\n')
    f.write('# D3 offshore comments in the first 2 weeks after 19 Sep 2025\n' + '\n'.join('- ' + s for s in exs) + '\n')
print(open(OUT / 'examples.txt').read())
