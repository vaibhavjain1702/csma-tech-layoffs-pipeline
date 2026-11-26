"""Step-4 checks for docs/INTERPRETATION_ROUTINE.md: numbers that tell rival explanations apart.

C1 (H1) Is r/technology's lower layoff rate because layoff talk there only happens in a few news threads?
        -> spread of layoff-matching comments across threads, Jan-Jun 2025.
C3 (time) Did "AI is the excuse" grow, or did AI talk just grow?
        -> share of ai_pretext among AI-mentioning cscq comments, by half-year.
Read-only. Output: outputs/13_interpretation/.
Run: .venv-eda/bin/python scripts/check_interpretations.py
"""
import csv, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from explore_leads import M, connect

OUT = Path(__file__).resolve().parents[1] / 'outputs/13_interpretation'; OUT.mkdir(parents=True, exist_ok=True)

def write(name, rows):
    with (OUT / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for r in rows: print(r)

c = connect()
# C1: thread spread of layoff-facet comments, shared window
q = """select r.subreddit, r.link_id, d.layoffs from records r join features f on f.kind=r.kind and f.id=r.id
       left join disruption_screen d on d.kind=r.kind and d.id=r.id
       where r.kind='comments' and r.created_month between '2025-01' and '2025-06' and f.likely_bot=0"""
tot, lay = defaultdict(Counter), defaultdict(Counter)
for s, l, x in c.execute(q):
    tot[s][l] += 1
    if x: lay[s][l] += 1
rows = []
for s in sorted(tot):
    n_lay = sum(lay[s].values()); big = [l for l, n in tot[s].items() if n >= 50]
    top10 = sum(n for _, n in lay[s].most_common(10))
    # rate inside threads that contain any layoff talk at all
    in_lay_threads = sum(tot[s][l] for l in lay[s])
    rows.append({'subreddit': s, 'comments': sum(tot[s].values()), 'layoff_comments': n_lay, 'threads': len(tot[s]),
                 'threads_with_layoff_talk': len(lay[s]),
                 'pct_threads_50plus_with_layoff_talk': round(100 * sum(1 for l in big if lay[s][l]) / max(len(big), 1), 1),
                 'top10_threads_share_of_layoff_comments_pct': round(100 * top10 / max(n_lay, 1), 1),
                 'layoff_rate_pct_all': round(100 * n_lay / sum(tot[s].values()), 2),
                 'layoff_rate_pct_inside_threads_with_any': round(100 * n_lay / max(in_lay_threads, 1), 2)})
write('C1_h1_thread_spread.csv', rows)

# C3: AI-as-excuse relative to AI talk, cscq, by half-year
q = """select r.created_month, f.own_text from disruption_screen d join records r on r.kind=d.kind and r.id=d.id
       join features f on f.kind=d.kind and f.id=d.id where d.kind='comments' and r.subreddit='cscareerquestions' and f.likely_bot=0"""
cnt = defaultdict(Counter)
for m, t in c.execute(q):
    t = t or ''; h = m[:4] + ('-H1' if m[5:7] <= '06' else '-H2')
    cnt[h]['all'] += 1
    if M['ai_any'].search(t):
        cnt[h]['ai'] += 1
        cnt[h]['excuse'] += bool(M['ai_pretext'].search(t)); cnt[h]['replaces'] += bool(M['ai_inevitable'].search(t))
write('C3_ai_excuse_vs_ai_talk.csv', [{'half': h, 'candidate_comments': v['all'], 'ai_comments': v['ai'],
      'ai_share_pct': round(100 * v['ai'] / v['all'], 1), 'excuse_per_1000_ai': round(1000 * v['excuse'] / v['ai'], 1),
      'replaces_per_1000_ai': round(1000 * v['replaces'] / v['ai'], 1)} for h, v in sorted(cnt.items())])
