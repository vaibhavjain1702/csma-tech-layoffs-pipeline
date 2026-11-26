"""Sentiment and zero-shot stance as an extra signal (Jan-Jun 2025, read-only).

Reads the cached model scores from scripts/score_text_models.py (data/processed/model_scores.sqlite) and asks
four questions that already exist in the project. None of the model labels has been checked by a person,
so every result here is at most a Lead; the cut-off for a model label is fixed at 0.5 and never tuned.

  S1 (layer 7, "sentiment is not stance"): do story comments and blame-topic comments differ in sentiment?
       If both are negative, sentiment cannot separate solidarity from blame.
  S2 (R3 rival): does negativity, rather than telling your story, explain the extra sympathy?
       Compare story vs unmarked comments inside the same parent-sentiment band.
  S3 (R4 N3, the "affective" part): are blame-talkers' replies to each other more negative or more
       disagreeing than other replies?
  T1 (layer 3): how many topic-marker hits does the stance model read as blame, and how much blame does it
       find that the markers miss? Also agreement with the provisional codes in 09_leads/manual.
  T2 (R2, D1): blame stance by community, and within the same authors in cscq and r/technology.
  T3 (R3, agree marker): does the model read marker "agree" replies as agreement? How do replies respond
       to blame when read by the model? Do repliers who blame the same target disagree less (Lead)?

Outputs: outputs/17_sentiment_stance/ (CSVs, figure, examples.txt which holds verbatim text and is git-ignored).
Run: .venv-eda/bin/python scripts/explore_sentiment_stance.py
"""
import csv, re, sqlite3, sys, time
from collections import defaultdict
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from explore_leads import connect, short
from explore_replies import PARENT, REPLY, CAND
import explore_network as N

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/17_sentiment_stance'
CACHE = ROOT / 'data/processed/model_scores.sqlite'
SEED = 20261126
rng = np.random.default_rng(SEED)
CUT = 0.5
M0, M1 = '2025-01', '2025-06'
TOPIC_TO_STANCE = [('mentions_execs', 'blames_execs'), ('mentions_offshore', 'blames_offshore'),
                   ('ai_excuse', 'ai_is_excuse'), ('blames_workers', 'blames_workers'), ('experience', 'own_job_loss')]
STANCE = ['blames_execs', 'blames_offshore', 'blames_ai', 'ai_is_excuse', 'blames_macro', 'blames_workers']
THIS_START = re.compile(r'^\W*this\b', re.I)

def write(name, rows, header=None):
    p = OUT / name; p.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if header is None:  # union of keys, in first-seen order (sections of one table have different columns)
        header = []
        for r in rows: header += [k for k in r if k not in header]
    with p.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction='ignore'); w.writeheader(); w.writerows(rows)

def log(msg, t0=[time.time()]): print(f'[{time.time()-t0[0]:6.0f}s] {msg}', flush=True)
def pct(x): x = np.asarray(x, float); return round(100 * x.mean(), 2) if len(x) else float('nan')

def tboot(flag, thread, reps=1000):
    """95% CI for a share, resampling whole threads."""
    flag = np.asarray(flag, float)
    if len(flag) < 20: return float('nan'), float('nan')
    u, ti = np.unique(thread, return_inverse=True)
    s = np.bincount(ti, weights=flag); n = np.bincount(ti)
    idx = rng.integers(0, len(u), size=(reps, len(u)))
    est = s[idx].sum(1) / np.maximum(n[idx].sum(1), 1)
    return round(100 * float(np.percentile(est, 2.5)), 2), round(100 * float(np.percentile(est, 97.5)), 2)

def auc(a, b):
    """P(score of a random a > random b); 0.5 = cannot tell the groups apart."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if not len(a) or not len(b): return float('nan')
    r = np.argsort(np.argsort(np.concatenate([a, b]))) + 1
    return round(float((r[:len(a)].sum() - len(a) * (len(a) + 1) / 2) / (len(a) * len(b))), 3)

# ---------------------------------------------------------------------------
def load_scores():
    k = sqlite3.connect(f'file:{CACHE}?mode=ro', uri=True)
    sent = {i: (v, ng, nu, po) for i, v, ng, nu, po in k.execute('select * from sentiment')}
    st = defaultdict(dict)
    for i, h, p in k.execute('select * from stance'): st[i][h] = p
    rs = defaultdict(dict)
    for i, h, p in k.execute('select * from reply_stance'): rs[i][h] = p
    meta = dict(k.execute('select * from meta'))
    return sent, st, rs, meta

def sent_label(s):  # argmax of the 3-class model
    return ['negative', 'neutral', 'positive'][int(np.argmax(s[1:]))]

def emp_all_communities():
    c = connect()
    rows = c.execute(f"""select r.id, r.subreddit, f.author_key, r.link_id, f.own_text from disruption_screen d
        join records r on r.kind=d.kind and r.id=d.id join features f on f.kind=d.kind and f.id=d.id
        where d.kind='comments' and {CAND} and r.created_month between ? and ? and f.likely_bot=0 and f.author_unknown=0
        and coalesce(f.own_text,'')<>''""", (M0, M1)).fetchall()
    out = []
    for i, s, a, l, t in rows:
        m = {k: bool(r.search(t)) for k, r in PARENT.items()}
        m['none'] = not any(m.values())
        m['any_blame_topic'] = m['mentions_execs'] or m['mentions_offshore'] or m['ai_excuse']
        out.append(dict(id=i, sub=s, author=a, thread=l, text=t, m=m))
    return out

# ---------------------------------------------------------------------------
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sent, st, rs, meta = load_scores()
    log(f'scores: sentiment {len(sent):,}  stance {len(st):,}  reply stance {len(rs):,}  models {meta.get("sent_model")} / {meta.get("nli_model")}')
    ex = []  # (section, text) - verbatim, reading only
    E = emp_all_communities()
    E = [e for e in E if e['id'] in sent and e['id'] in st and len(st[e['id']]) >= len(STANCE) + 1]
    log(f'employment comments with scores: {len(E):,}')

    # ---- S1: sentiment by comment type and community ----
    s1 = []
    groups = ['experience', 'mentions_execs', 'mentions_offshore', 'ai_excuse', 'ai_replaces', 'doom', 'blames_workers', 'none']
    for sub in ('cscareerquestions', 'technology', 'programming'):
        es = [e for e in E if e['sub'] == sub]
        for g in groups + ['all']:
            gg = es if g == 'all' else [e for e in es if e['m'][g]]
            if not gg: continue
            S = np.array([sent[e['id']] for e in gg])
            s1.append(dict(community=sub, comment_type=g, comments=len(gg), mean_vader=round(float(S[:, 0].mean()), 3),
                           pct_vader_negative=pct(S[:, 0] <= -0.05), pct_model_negative=pct(S[:, 1] > np.maximum(S[:, 2], S[:, 3])),
                           pct_model_positive=pct(S[:, 3] > np.maximum(S[:, 1], S[:, 2])), mean_model_neg_prob=round(float(S[:, 1].mean()), 3)))
        # can sentiment tell a story from a blame-topic comment? AUC of negativity
        a = [sent[e['id']][1] for e in es if e['m']['experience'] and not e['m']['any_blame_topic']]
        b = [sent[e['id']][1] for e in es if e['m']['any_blame_topic'] and not e['m']['experience']]
        s1.append(dict(community=sub, comment_type='AUC_story_vs_blame_topic_model_neg', comments=len(a) + len(b), mean_vader=auc(a, b)))
        a = [sent[e['id']][0] for e in es if e['m']['experience'] and not e['m']['any_blame_topic']]
        b = [sent[e['id']][0] for e in es if e['m']['any_blame_topic'] and not e['m']['experience']]
        s1.append(dict(community=sub, comment_type='AUC_story_vs_blame_topic_vader', comments=len(a) + len(b), mean_vader=auc(a, b)))
    write('S1_sentiment_by_comment_type.csv', s1)
    # agreement between the two sentiment tools
    S = np.array([sent[e['id']] for e in E])
    vneg, mneg = S[:, 0] <= -0.05, S[:, 1] > np.maximum(S[:, 2], S[:, 3])
    tools = dict(n=len(S), pct_both_negative=pct(vneg & mneg), pct_vader_only=pct(vneg & ~mneg), pct_model_only=pct(~vneg & mneg),
                 corr_vader_vs_model_pos_minus_neg=round(float(np.corrcoef(S[:, 0], S[:, 3] - S[:, 1])[0, 1]), 3))
    log(f'S1 done; VADER vs RoBERTa {tools}')

    # ---- cscq window: comments, reply edges, R4 types (same code as explore_network.py) ----
    c, rows, human, drop = N.load()
    authors, threads, D = N.build(human); n_auth = len(authors)
    A, present, lw, ncomp, sizes = N.graph(D, n_auth)
    P = N.profiles(D, n_auth); t, _ = N.assign_types(P); t[~lw] = 4
    log(f'R4 rebuilt: LWCC {int(lw.sum()):,} authors; types ' + ', '.join(f'{N.TYPES[i]} {(lw & (t == i)).sum():,}' for i in range(5)))
    ix = {i: j for j, i in enumerate(D['id'])}
    pidx = np.array([ix.get(f[3:], -1) if f.startswith('t1_') else -1 for f in D['pfull']])
    # parent markers on employment comments (all 7 PARENT types + none), as in R3
    pm = {}
    for j in np.where(D['emp'])[0]:
        tx = D['text'][j]
        if not tx: continue
        m = [k for k, r in PARENT.items() if r.search(tx)]
        pm[j] = m or ['none']
    edge = D['edge'] & (pidx >= 0)
    E_ = np.where(edge)[0]
    E_ = np.array([j for j in E_ if D['id'][j] in rs and len(rs[D['id'][j]]) == 3 and D['id'][j] in sent and D['id'][pidx[j]] in sent])
    log(f'reply edges with both scores: {len(E_):,}')
    rsym = np.array([D['R'][j, N.RFUN.index('sympathy')] for j in E_])
    ragr = np.array([D['R'][j, N.RFUN.index('agree')] for j in E_])
    rchal = np.array([D['R'][j, N.RFUN.index('challenge')] for j in E_])
    nsym = np.array([rs[D['id'][j]]['sympathy'] > CUT for j in E_])
    nagr = np.array([rs[D['id'][j]]['agrees'] > CUT for j in E_])
    ndis = np.array([rs[D['id'][j]]['disagrees'] > CUT for j in E_])
    rneg = np.array([sent_label(sent[D['id'][j]]) == 'negative' for j in E_])
    rvad = np.array([sent[D['id'][j]][0] for j in E_])
    thr = D['thread'][E_]
    par = pidx[E_]
    pband = np.array([sent_label(sent[D['id'][p]]) for p in par])
    ptype = [pm.get(p) for p in par]  # None = parent is not an employment comment

    # ---- S2: does negativity explain the sympathy story comments get? ----
    s2 = []
    def is_t(k): return np.array([pt is not None and k in pt for pt in ptype])
    story, none, doom = is_t('experience'), is_t('none'), is_t('doom')
    for band in ('negative', 'neutral', 'positive', 'all'):
        bm = np.ones(len(E_), bool) if band == 'all' else (pband == band)
        for name, g in (('experience', story), ('doom', doom), ('none', none)):
            m = bm & g
            if m.sum() < 20: continue
            for meas, f in (('sympathy_marker', rsym), ('sympathy_model', nsym)):
                base = f[bm & none].mean() if (bm & none).any() else np.nan
                lo, hi = tboot(f[m], thr[m])
                s2.append(dict(parent_sentiment=band, parent_type=name, replies=int(m.sum()), measure=meas, pct=pct(f[m]), ci95_lo=lo, ci95_hi=hi,
                               pct_none_same_band=round(100 * base, 2), lift_vs_none_same_band=round(f[m].mean() / base, 2) if base else float('nan')))
    # pooled (Mantel-Haenszel) risk ratio over the three bands, vs the crude ratio
    for meas, f in (('sympathy_marker', rsym), ('sympathy_model', nsym)):
        num = den = 0.0
        for band in ('negative', 'neutral', 'positive'):
            a_, b_ = (pband == band) & story, (pband == band) & none
            if a_.sum() and b_.sum():
                nt = a_.sum() + b_.sum(); num += f[a_].sum() * b_.sum() / nt; den += f[b_].sum() * a_.sum() / nt
        s2.append(dict(parent_sentiment='pooled_MH', parent_type='experience', measure=meas, lift_vs_none_same_band=round(num / den, 2) if den else float('nan'),
                       pct_none_same_band=float('nan'), replies=int(story.sum())))
    s2.append(dict(parent_sentiment='share_of_story_parents_negative', parent_type='experience', measure='model', pct=pct(pband[story] == 'negative')))
    s2.append(dict(parent_sentiment='share_of_none_parents_negative', parent_type='none', measure='model', pct=pct(pband[none] == 'negative')))
    write('S2_sympathy_by_parent_sentiment.csv', s2)
    log('S2 done')

    # ---- S3: tone of replies between R4 types (blame-talker cells) ----
    st_, dt_ = t[D['author'][E_]], t[D['parent'][E_]]
    inlw = lw[D['author'][E_]] & lw[D['parent'][E_]]
    BT = N.TYPES.index('blame-talker')
    cells = {'blame->blame': (st_ == BT) & (dt_ == BT), 'blame->other_typed': (st_ == BT) & (dt_ < N.TYPED) & (dt_ != BT),
             'other_typed->blame': (st_ < N.TYPED) & (st_ != BT) & (dt_ == BT),
             'other_typed->other_typed': (st_ < N.TYPED) & (st_ != BT) & (dt_ < N.TYPED) & (dt_ != BT), 'all_LWCC': np.ones(len(E_), bool)}
    s3 = []
    for name, m in cells.items():
        m = m & inlw
        for meas, f in (('reply_negative_model', rneg), ('reply_disagrees_model', ndis), ('reply_agrees_model', nagr),
                        ('reply_challenge_marker', rchal), ('reply_agree_marker', ragr)):
            lo, hi = tboot(f[m], thr[m])
            s3.append(dict(cell=name, replies=int(m.sum()), measure=meas, pct=pct(f[m]), ci95_lo=lo, ci95_hi=hi))
        s3.append(dict(cell=name, replies=int(m.sum()), measure='mean_reply_vader', pct=round(float(rvad[m].mean()), 3) if m.any() else float('nan')))
    # same comparison inside each parent-sentiment band: is it the blame-talkers, or just that their parents are negative?
    for band in ('negative', 'neutral', 'positive'):
        for name in ('blame->blame', 'other_typed->other_typed'):
            m = cells[name] & inlw & (pband == band)
            for meas, f in (('reply_negative_model', rneg), ('reply_agrees_model', nagr)):
                lo, hi = tboot(f[m], thr[m])
                s3.append(dict(cell=f'{name}|parent_{band}', replies=int(m.sum()), measure=meas, pct=pct(f[m]), ci95_lo=lo, ci95_hi=hi))
    # NOTE: 'reply_disagrees_model' is kept in the table but is NOT usable: it fires on ~62% of all replies and, read
    # against examples, mostly marks neutral continuations or advice (see SENTIMENT_STANCE_NOTES.md).
    write('S3_tone_between_types.csv', s3)
    log('S3 done')

    # ---- T1: topic markers vs stance model; agreement with the provisional codes ----
    t1 = []
    for sub in ('all', 'cscareerquestions', 'technology'):
        es = E if sub == 'all' else [e for e in E if e['sub'] == sub]
        for topic, stance in TOPIC_TO_STANCE:
            hit = np.array([e['m'][topic] for e in es]); pos = np.array([st[e['id']][stance] > CUT for e in es])
            t1.append(dict(community=sub, marker=topic, model_label=stance, comments=len(es), marker_hits=int(hit.sum()),
                           pct_hits_model_positive=pct(pos[hit]), pct_nonhits_model_positive=pct(pos[~hit]),
                           model_positives=int(pos.sum()), pct_model_positives_without_marker=pct(~hit[pos]) if pos.any() else float('nan')))
        for stance in ('blames_ai', 'blames_macro'):
            pos = np.array([st[e['id']][stance] > CUT for e in es])
            t1.append(dict(community=sub, marker='(none)', model_label=stance, comments=len(es), model_positives=int(pos.sum())))
    write('T1_topic_marker_vs_stance_model.csv', t1)
    codes = []
    man = ROOT / 'outputs/09_leads/manual'
    spec = [('offshore_blame_target_codes.csv', 'blame_target', 'blames_offshore', {'foreign_workers_as_problem'}),
            ('ai_pretext_codes.csv', 'stance', 'ai_is_excuse', {'asserts'}),
            ('first_person_layoff_codes.csv', 'is_first_person', 'own_job_loss', {'yes'})]
    for f, col, stance, yes in spec:
        rr = [r for r in csv.DictReader(open(man / f, encoding='utf-8')) if r['id'] in st and stance in st[r['id']]]
        for val in sorted({r[col] for r in rr}):
            g = [r for r in rr if r[col] == val]
            codes.append(dict(code_file=f, code=val, counts_as_positive=val in yes, n=len(g), model_label=stance,
                              pct_model_positive=pct([st[r['id']][stance] > CUT for r in g]),
                              mean_model_p=round(float(np.mean([st[r['id']][stance] for r in g])), 3)))
        y = np.array([r[col] in yes for r in rr]); p = np.array([st[r['id']][stance] > CUT for r in rr])
        if len(rr):
            tp = (y & p).sum()
            codes.append(dict(code_file=f, code='SUMMARY', n=len(rr), model_label=stance,
                              pct_model_positive=f'precision {tp / max(p.sum(), 1):.2f} recall {tp / max(y.sum(), 1):.2f} agreement {(y == p).mean():.2f}'))
    write('T1_model_vs_provisional_codes.csv', codes)
    log('T1 done')

    # ---- T2: blame stance by community, and within the same authors (D1) ----
    t2 = []
    for sub in ('cscareerquestions', 'technology', 'programming'):
        es = [e for e in E if e['sub'] == sub]
        th = np.array([e['thread'] for e in es])
        for stance in STANCE + ['own_job_loss']:
            f = np.array([st[e['id']][stance] > CUT for e in es]); lo, hi = tboot(f, th)
            t2.append(dict(group=sub, label=stance, comments=len(es), pct=pct(f), ci95_lo=lo, ci95_hi=hi))
    by = defaultdict(lambda: defaultdict(list))
    for e in E:
        if e['sub'] in ('cscareerquestions', 'technology'): by[e['author']][e['sub']].append(e)
    both = [a for a, d in by.items() if len(d) == 2 and min(len(v) for v in d.values()) >= 2]  # D1 rule: >=2 employment comments in each
    for stance in STANCE + ['own_job_loss']:
        x = np.array([np.mean([st[e['id']][stance] > CUT for e in by[a]['cscareerquestions']]) for a in both])
        y = np.array([np.mean([st[e['id']][stance] > CUT for e in by[a]['technology']]) for a in both])
        d = x - y; bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
        t2.append(dict(group='same_authors_cscq_minus_technology', label=stance, comments=len(both), pct=round(100 * d.mean(), 2),
                       ci95_lo=round(100 * np.percentile(bs, 2.5), 2), ci95_hi=round(100 * np.percentile(bs, 97.5), 2),
                       note=f'cscq {100 * x.mean():.1f}% vs technology {100 * y.mean():.1f}%'))
    write('T2_blame_stance_by_community.csv', t2)
    log(f'T2 done; cross-posters {len(both)}')

    # ---- T3: reply stance ----
    t3 = []
    # (a) is the agree marker agreement? split by replies that start with "This"
    rtext = [D['text'][j] for j in E_]
    this_ = np.array([bool(THIS_START.match(x or '')) for x in rtext])
    for name, m in (('agree_marker', ragr), ('agree_marker_starting_This', ragr & this_), ('agree_marker_other', ragr & ~this_),
                    ('challenge_marker', rchal), ('sympathy_marker', rsym), ('no_marker', ~(ragr | rchal | rsym)), ('all', np.ones(len(E_), bool))):
        t3.append(dict(section='marker_vs_model', group=name, replies=int(m.sum()), pct_model_agrees=pct(nagr[m]),
                       pct_model_disagrees=pct(ndis[m]), pct_model_sympathy=pct(nsym[m]), pct_model_negative=pct(rneg[m])))
    # (b) R3 re-read by the model: reply stance by parent type (employment parents in the window)
    for k in list(PARENT) + ['none']:
        g = is_t(k)
        if g.sum() < 20: continue
        b = none
        for meas, f in (('model_agrees', nagr), ('model_disagrees', ndis), ('model_sympathy', nsym), ('marker_agree', ragr), ('marker_challenge', rchal)):
            lo, hi = tboot(f[g], thr[g])
            t3.append(dict(section='R3_by_parent_type', group=k, replies=int(g.sum()), measure=meas, pct=pct(f[g]), ci95_lo=lo, ci95_hi=hi,
                           lift_vs_none=round(f[g].mean() / f[b].mean(), 2) if f[b].mean() else float('nan')))
    # (c) Lead: polarisation proxy. Parent blames target X (model). Is the replier someone who also blamed X
    #     in their own employment comments (>=2 such comments, >=1 model-positive)? Compare disagreement.
    a_emp = defaultdict(list)
    for j in np.where(D['emp'])[0]:
        i = D['id'][j]
        if i in st and len(st[i]) >= len(STANCE): a_emp[D['author'][j]].append(st[i])
    for stance in ('blames_execs', 'blames_offshore', 'blames_ai', 'ai_is_excuse'):
        ppos = np.array([D['id'][p] in st and st[D['id'][p]].get(stance, 0) > CUT for p in par])
        rep_a = D['author'][E_]
        known = np.array([len(a_emp[a]) >= 2 for a in rep_a])
        same = np.array([known[n_] and any(s[stance] > CUT for s in a_emp[rep_a[n_]]) for n_ in range(len(E_))])
        for name, m in (('replier_also_blames', ppos & same), ('replier_does_not', ppos & known & ~same)):
            lo, hi = tboot(ndis[m], thr[m])
            t3.append(dict(section='same_side_vs_other_side', group=f'{stance}:{name}', replies=int(m.sum()), measure='model_disagrees',
                           pct=pct(ndis[m]), ci95_lo=lo, ci95_hi=hi))
            t3.append(dict(section='same_side_vs_other_side', group=f'{stance}:{name}', replies=int(m.sum()), measure='model_agrees', pct=pct(nagr[m])))
    write('T3_reply_stance.csv', t3)
    write('tool_agreement.csv', [tools])
    log('T3 done')

    # ---- examples (verbatim, reading only; git-ignored) ----
    def add(title, idxs, k=6):
        ex.append(f'\n=== {title} ===')
        for j in idxs[:k]: ex.append('- ' + j)
    sel = rng.permutation(np.where(ragr & this_ & ndis)[0])
    add('agree marker, starts with "This", model says DISAGREES', [f'PARENT: {short(D["text"][pidx[E_[n_]]], 200)}\n  REPLY: {short(rtext[n_], 200)}' for n_ in sel])
    sel = rng.permutation(np.where(ragr & this_ & nagr)[0])
    add('agree marker, starts with "This", model says AGREES', [f'PARENT: {short(D["text"][pidx[E_[n_]]], 200)}\n  REPLY: {short(rtext[n_], 200)}' for n_ in sel])
    for topic, stance in TOPIC_TO_STANCE[:3]:
        hits = [e for e in E if e['m'][topic]]; rng.shuffle(hits)
        add(f'{topic} marker, model says NOT {stance}', [short(e['text'], 300) for e in hits if st[e['id']][stance] <= CUT])
        add(f'{topic} marker, model says {stance}', [short(e['text'], 300) for e in hits if st[e['id']][stance] > CUT])
        miss = [e for e in E if not e['m'][topic] and st[e['id']][stance] > 0.9]; rng.shuffle(miss)
        add(f'NO {topic} marker, model says {stance} (p>0.9)', [short(e['text'], 300) for e in miss])
    miss = [e for e in E if not e['m']['experience'] and st[e['id']]['own_job_loss'] > 0.9]; rng.shuffle(miss)
    add('NO experience marker, model says own_job_loss (p>0.9)', [short(e['text'], 300) for e in miss], k=12)
    sel = rng.permutation(np.where(~(ragr | rchal | rsym) & ndis)[0])
    add('no reply marker, model says DISAGREES (base rate check)', [f'PARENT: {short(D["text"][pidx[E_[n_]]], 200)}\n  REPLY: {short(rtext[n_], 200)}' for n_ in sel], k=10)
    sel = rng.permutation(np.where(story & (pband == 'positive'))[0])
    add('story parent read as POSITIVE by the sentiment model', [short(D['text'][pidx[E_[n_]]], 300) for n_ in sel])
    sel = rng.permutation(np.where(cells['blame->blame'] & inlw & ndis)[0])
    add('blame-talker -> blame-talker, model says DISAGREES', [f'PARENT: {short(D["text"][pidx[E_[n_]]], 200)}\n  REPLY: {short(rtext[n_], 200)}' for n_ in sel])
    (OUT / 'examples.txt').write_text('Verbatim excerpts for reading only. Do not quote in the report; do not publish.\n' + '\n'.join(ex), encoding='utf-8')
    write('manifest.csv', [dict(k=k, v=v) for k, v in {**meta, 'cut': CUT, 'seed': SEED, 'employment_comments': len(E), 'reply_edges': len(E_),
                                                         'cross_posters': len(both)}.items()])
    log('done')

if __name__ == '__main__':
    main()
