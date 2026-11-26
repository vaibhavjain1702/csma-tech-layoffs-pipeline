"""R4: the social structure behind R3 (r/cscareerquestions, Jan-Jun 2025, read-only)

Question: do story-sharers, blame-talkers and helpers occupy distinct positions in the cscq reply
network, and do sympathy, agreement and challenge flow between them in patterned ways? Is solidarity
given by a few central helpers to peripheral story-sharers, and does challenge stay inside the
blame-talker group or cross out of it?

Coverage limit: the database holds no cscq posts, so replies to original posts (top-level comments)
have no parent author and drop out. The graph is comment-to-comment conversation only.

Expectation stated before running (from H3, outputs/12_replies):
  story-sharers are on the edge and receive more than they give, and they get sympathy;
  helpers are hubs (high out-degree, betweenness, PageRank);
  blame-talkers reply to each other, with agreement and challenge staying inside the group.

Network: directed, weighted author graph, replier -> parent author, weight = number of replies.
Bots, unknown/deleted authors and self-replies are excluded. The analysis uses the largest weakly
connected component (LWCC).
Markers: PARENT and REPLY from explore_replies.py (no new regexes).
Outputs go to outputs/15_network/. Nothing in the database or other outputs is changed.
Run:  .venv-eda/bin/python scripts/explore_network.py   (numpy, scipy, networkx, scikit-learn, matplotlib)
"""
import csv, json, math, random, resource, sys, time
from collections import Counter
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from scipy.sparse import csgraph
import networkx as nx
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram

sys.path.insert(0, str(Path(__file__).resolve().parent))
from explore_leads import connect, short
from explore_replies import PARENT, REPLY, CAND

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/15_network'
SEED = 20261125
rng = np.random.default_rng(SEED); random.seed(SEED)
SUB, M0, M1 = 'cscareerquestions', '2025-01', '2025-06'

CONTENT = ['experience', 'mentions_execs', 'mentions_offshore', 'ai_excuse', 'doom']   # on employment comments
BLAME = ['mentions_execs', 'mentions_offshore', 'ai_excuse']                            # "blame topics" (topic, not stance)
RFUN = ['sympathy', 'advice', 'agree', 'challenge']                                     # on every reply
TYPES = ['story-sharer', 'blame-talker', 'helper', 'other', 'low-activity']
TYPED = 4  # first four are profiled types

# ---- rule thresholds (stated in NETWORK_NOTES.md) ----
N_MIN = 5            # comments in the window to be profiled
EMP_MIN = 2          # employment comments needed for the content rules
BLAME_MIN, BLAME_SHARE = 2, 0.25
HELP_GIVEN_MIN, HELP_SHARE = 5, 0.11   # replies given; share matching advice or sympathy = upper quartile (0.30 was above p90)
K_BTW, K_CLOSE, K_PATH = 1000, 2000, 500

# palette: dataviz reference, categorical slots in fixed order
COL = {'story-sharer': '#257de0', 'blame-talker': '#f47230', 'helper': '#00b894', 'other': '#f2a600', 'low-activity': '#9c9c9c'}
INK, INK2 = '#191919', '#666666'

def write(name, rows, header=None):
    p = OUT / name; p.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows); header = header or (list(rows[0].keys()) if rows else [])
    with p.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction='ignore'); w.writeheader(); w.writerows(rows)

def log(msg, t0=[time.time()]): print(f'[{time.time()-t0[0]:6.0f}s] {msg}', flush=True)

def boot_median(x, reps=1000):
    x = np.asarray(x, float)
    if len(x) < 5: return float('nan'), float('nan')
    idx = rng.integers(0, len(x), size=(reps, len(x))) if len(x) <= 20000 else None
    if idx is None:  # large group: chunk to keep memory small
        m = np.array([np.median(x[rng.integers(0, len(x), len(x))]) for _ in range(reps)])
    else:
        m = np.median(x[idx], axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))

def thread_boot_share(flag, thread, reps=1000):
    """CI for a share, resampling whole threads."""
    flag = np.asarray(flag, float)
    if len(flag) < 5: return float('nan'), float('nan')
    u, ti = np.unique(thread, return_inverse=True)
    s = np.bincount(ti, weights=flag, minlength=len(u)); n = np.bincount(ti, minlength=len(u))
    idx = rng.integers(0, len(u), size=(reps, len(u)))
    est = s[idx].sum(1) / np.maximum(n[idx].sum(1), 1)
    return float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))

# ---------------------------------------------------------------------------
def load():
    c = connect(); c.execute('pragma temp_store=memory')
    cand = CAND.replace('d.', 'd.')
    q = f"""select r.id, f.author_key, r.link_id, f.likely_bot, f.author_unknown, coalesce(f.own_text,''), coalesce(f.word_count,0),
        case when d.id is not null and {cand} then 1 else 0 end,
        e.parent_kind, e.parent_author_key, e.parent_fullname, pf.likely_bot, pf.author_unknown
        from records r join features f on f.kind='comments' and f.id=r.id
        left join disruption_screen d on d.kind='comments' and d.id=r.id
        left join reply_edges e on e.child_id=r.id
        left join features pf on pf.kind=e.parent_kind and pf.id=substr(e.parent_fullname,4)
        where r.kind='comments' and r.subreddit=? and r.created_month between ? and ?"""
    rows = c.execute(q, (SUB, M0, M1)).fetchall()
    log(f'window comments {len(rows):,}')
    human = [r for r in rows if r[3] == 0 and r[4] == 0]
    drop = Counter()
    for r in human:
        pk, pa, pb, pu = r[8], r[9], r[11], r[12]
        if pb is None and pk == 'posts': drop['parent is a post (no cscq posts collected)'] += 1
        elif pb is None: drop['parent comment not collected'] += 1
        elif pa is None: drop['parent author deleted'] += 1
        elif pb == 1: drop['parent bot'] += 1
        elif pu == 1: drop['parent unknown'] += 1
        elif pa == r[1]: drop['self'] += 1
    return c, rows, human, drop

def build(human):
    authors = sorted({r[1] for r in human} | {r[9] for r in human if r[9] is not None})
    aix = {a: i for i, a in enumerate(authors)}
    threads = sorted({r[2] for r in human}); tix = {t: i for i, t in enumerate(threads)}
    n = len(human)
    D = dict(
        id=np.array([r[0] for r in human]), author=np.array([aix[r[1]] for r in human]),
        thread=np.array([tix[r[2]] for r in human]), words=np.array([r[6] for r in human]),
        emp=np.array([r[7] == 1 for r in human]), text=[r[5] for r in human],
        pkind=np.array([r[8] or '' for r in human]), pfull=np.array([r[10] or '' for r in human]),
        parent=np.array([aix[r[9]] if r[9] is not None else -1 for r in human]))
    D['edge'] = np.array([r[9] is not None and r[11] == 0 and r[12] == 0 and r[9] != r[1] for r in human])
    D['C'] = np.zeros((n, len(CONTENT)), bool); D['R'] = np.zeros((n, len(RFUN)), bool)
    for i, t in enumerate(D['text']):
        if not t: continue
        if D['emp'][i]:
            for j, k in enumerate(CONTENT): D['C'][i, j] = bool(PARENT[k].search(t))
        if D['edge'][i]:
            for j, k in enumerate(RFUN): D['R'][i, j] = bool(REPLY[k].search(t))
    return authors, threads, D

def graph(D, n_auth, keep=None):
    """Weighted directed adjacency (replier -> parent author) and LWCC mask."""
    m = D['edge'] if keep is None else (D['edge'] & keep)
    s, d = D['author'][m], D['parent'][m]
    A = sp.csr_matrix((np.ones(len(s)), (s, d)), shape=(n_auth, n_auth)); A.sum_duplicates()
    present = np.zeros(n_auth, bool); present[s] = True; present[d] = True
    ncomp, lab = csgraph.connected_components(A, directed=True, connection='weak')
    sizes = np.bincount(lab[present], minlength=ncomp); big = sizes.argmax()
    lw = (lab == big) & present
    return A, present, lw, int((sizes > 0).sum()), sizes

# ---------------------------------------------------------------------------
def profiles(D, n_auth):
    a = D['author']; e = D['edge']; emp = D['emp']; C = D['C']; R = D['R']
    P = dict(comments=np.bincount(a, minlength=n_auth),
             threads=np.array([0]*n_auth),
             emp=np.bincount(a, weights=emp, minlength=n_auth),
             given=np.bincount(a, weights=e, minlength=n_auth),
             received=np.bincount(D['parent'][e], minlength=n_auth).astype(float))
    pairs = np.unique(np.stack([a, D['thread']]), axis=1); P['threads'] = np.bincount(pairs[0], minlength=n_auth)
    for j, k in enumerate(CONTENT): P['n_' + k] = np.bincount(a, weights=C[:, j] & emp, minlength=n_auth)
    P['n_blame'] = np.bincount(a, weights=(C[:, [CONTENT.index(b) for b in BLAME]].any(1)) & emp, minlength=n_auth)
    for j, k in enumerate(RFUN):
        P['gave_' + k] = np.bincount(a, weights=R[:, j] & e, minlength=n_auth)
        P['got_' + k] = np.bincount(D['parent'][e], weights=R[e, j], minlength=n_auth)
    P['gave_help'] = np.bincount(a, weights=(R[:, 0] | R[:, 1]) & e, minlength=n_auth)
    return P

def assign_types(P, n_min=N_MIN, help_share=HELP_SHARE):
    n = len(P['comments']); t = np.full(n, 4)
    prof = P['comments'] >= n_min
    content_ok = prof & (P['emp'] >= EMP_MIN)
    story = content_ok & (P['n_experience'] >= 1) & (P['n_experience'] >= P['n_blame'])
    blame = content_ok & (P['n_blame'] >= BLAME_MIN) & (P['n_blame'] >= BLAME_SHARE * np.maximum(P['emp'], 1))
    helper = prof & (P['given'] >= HELP_GIVEN_MIN) & (P['gave_help'] >= help_share * np.maximum(P['given'], 1))
    t[prof] = 3
    t[helper] = 2; t[blame] = 1; t[story] = 0   # priority: story > blame > helper
    overlap = {'story&blame_rule': int((story & ((P['n_blame'] >= BLAME_MIN) & content_ok)).sum()),
               'story&helper': int((story & helper).sum()), 'blame&helper': int((blame & helper & ~story).sum()),
               'blame_rule&not_story': int((blame & ~story).sum())}
    return t, overlap

# ---------------------------------------------------------------------------
def mixing(src_t, dst_t, k=5):
    Mx = np.zeros((k, k)); np.add.at(Mx, (src_t, dst_t), 1)
    T = Mx.sum(); exp = np.outer(Mx.sum(1), Mx.sum(0)) / max(T, 1)
    return Mx, np.divide(Mx, exp, out=np.full_like(Mx, np.nan), where=exp > 0)

def assortativity(Mx):
    e = Mx / Mx.sum(); a, b = e.sum(1), e.sum(0); ab = (a * b).sum()
    return float((np.trace(e) - ab) / (1 - ab))

def key_stats(t, D, lw, cent=None):
    """The numbers every rival check re-computes."""
    e = D['edge'] & lw[D['author']]
    s, d, R, th = D['author'][e], D['parent'][e], D['R'][e], D['thread'][e]
    st, dt = t[s], t[d]
    out = {}
    Mx, L = mixing(st, dt)
    typed = (st < TYPED) & (dt < TYPED)
    out['assort_all'] = assortativity(Mx); out['assort_typed'] = assortativity(Mx[:TYPED, :TYPED])
    for a_, b_ in [(1, 1), (0, 0), (2, 0), (2, 2), (0, 1), (1, 0)]:
        out[f'lift_{TYPES[a_]}->{TYPES[b_]}'] = float(L[a_, b_])
    base = R.mean(0)
    for j, f in enumerate(RFUN):
        out[f'base_{f}'] = float(base[j])
    cell = lambda a_, b_: (st == a_) & (dt == b_)
    for (a_, b_), f in [((2, 0), 'sympathy'), ((2, 3), 'sympathy'), ((3, 0), 'sympathy'), ((3, 3), 'sympathy'), ((2, 0), 'advice'), ((1, 1), 'challenge'), ((1, 1), 'agree'),
                        ((3, 1), 'challenge'), ((1, 3), 'challenge')]:
        m = cell(a_, b_); out[f'pct_{f}_{TYPES[a_]}->{TYPES[b_]}'] = float(R[m, RFUN.index(f)].mean()) if m.any() else float('nan')
    for ty in range(TYPED):
        m = dt == ty
        for f in ('sympathy', 'challenge', 'agree'):
            out[f'pct_{f}_received_by_{TYPES[ty]}'] = float(R[m, RFUN.index(f)].mean()) if m.any() else float('nan')
    # where blame-talkers' challenges go, against where all their replies go
    bm = st == 1; bc = bm & R[:, RFUN.index('challenge')]
    out['blame_replies_to_blame_pct'] = float((dt[bm] == 1).mean()) if bm.any() else float('nan')
    out['blame_challenges_to_blame_pct'] = float((dt[bc] == 1).mean()) if bc.any() else float('nan')
    rc = (dt == 1) & R[:, RFUN.index('challenge')]
    out['challenges_received_by_blame_from_blame_pct'] = float((st[rc] == 1).mean()) if rc.any() else float('nan')
    if cent is not None:
        for ty in range(len(TYPES)):
            m = lw & (t == ty)
            for k in ('ratio_recv_given', 'pagerank', 'betweenness', 'out_degree', 'in_degree'):
                out[f'median_{k}_{TYPES[ty]}'] = float(np.median(cent[k][m])) if m.any() else float('nan')
    for ty in range(len(TYPES)): out[f'n_{TYPES[ty]}'] = int((lw & (t == ty)).sum())
    return out

def centralities(A, lw, k_btw=K_BTW, k_close=K_CLOSE, seed=SEED):
    idx = np.where(lw)[0]; sub = A[idx][:, idx].tocsr()
    n = len(idx); out = {}
    B = (sub > 0).astype(float)
    out['out_degree'] = np.asarray(B.sum(1)).ravel(); out['in_degree'] = np.asarray(B.sum(0)).ravel()
    out['degree'] = out['out_degree'] + out['in_degree']
    out['out_weight'] = np.asarray(sub.sum(1)).ravel(); out['in_weight'] = np.asarray(sub.sum(0)).ravel()
    out['ratio_recv_given'] = (out['in_weight'] + 1) / (out['out_weight'] + 1)
    G = nx.from_scipy_sparse_array(sub, create_using=nx.DiGraph, edge_attribute='weight')
    pr = nx.pagerank(G, weight='weight'); out['pagerank'] = np.array([pr[i] for i in range(n)]) * n  # 1 = average node
    bt = nx.betweenness_centrality(G, k=min(k_btw, n), seed=seed, normalized=True)
    out['betweenness'] = np.array([bt[i] for i in range(n)])
    # harmonic closeness from sampled sources: incoming = how easily others' reply chains reach you
    src = np.random.default_rng(seed).choice(n, size=min(k_close, n), replace=False)
    hin = np.zeros(n); hout = np.zeros(n)
    for lo in range(0, len(src), 250):
        ch = src[lo:lo+250]
        d = csgraph.shortest_path(B, directed=True, unweighted=True, indices=ch)
        with np.errstate(divide='ignore'): inv = np.where(np.isfinite(d) & (d > 0), 1 / d, 0)
        hin += inv.sum(0)
        d = csgraph.shortest_path(B.T.tocsr(), directed=True, unweighted=True, indices=ch)
        with np.errstate(divide='ignore'): inv = np.where(np.isfinite(d) & (d > 0), 1 / d, 0)
        hout += inv.sum(0)
    out['closeness_in'] = hin / len(src); out['closeness_out'] = hout / len(src)
    full = {k: np.full(A.shape[0], np.nan) for k in out}
    for k in out: full[k][idx] = out[k]
    return full, G, idx

# ---------------------------------------------------------------------------
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c, rows, human, drop = load()
    authors, threads, D = build(human); n_auth = len(authors)
    log(f'human comments {len(human):,}  edges kept {D["edge"].sum():,}  dropped {dict(drop)}')
    A, present, lw, ncomp, sizes = graph(D, n_auth)
    nn, nlw = int(present.sum()), int(lw.sum())
    pairs_all = A.nnz; Alw = A[lw][:, lw]
    rep_all = int(A.sum()); rep_lw = int(Alw.sum())
    log(f'graph nodes {nn:,} pairs {pairs_all:,} replies {rep_all:,} | LWCC nodes {nlw:,} ({100*nlw/nn:.1f}%) '
        f'pairs {Alw.nnz:,} ({100*Alw.nnz/pairs_all:.1f}%) replies {rep_lw:,} ({100*rep_lw/rep_all:.1f}%) | components {ncomp}')
    structure = [dict(measure='window_comments', value=len(rows)), dict(measure='human_comments', value=len(human)),
                 *[dict(measure=f'dropped_{k}', value=v) for k, v in drop.items()],
                 dict(measure='nodes', value=nn), dict(measure='directed_pairs', value=pairs_all), dict(measure='replies', value=rep_all),
                 dict(measure='components', value=ncomp), dict(measure='lwcc_nodes', value=nlw), dict(measure='lwcc_node_share', value=round(nlw/nn, 4)),
                 dict(measure='lwcc_pairs', value=Alw.nnz), dict(measure='lwcc_reply_share', value=round(rep_lw/rep_all, 4)),
                 dict(measure='second_component_size', value=int(np.sort(sizes)[-2]) if len(sizes) > 1 else 0)]

    # ---- 2. profiles and types ----
    P = profiles(D, n_auth)
    prof = lw & (P['comments'] >= N_MIN)
    hs = P['gave_help'][prof & (P['given'] >= HELP_GIVEN_MIN)] / P['given'][prof & (P['given'] >= HELP_GIVEN_MIN)]
    log(f'help share among profiled authors with >=5 replies: median {np.median(hs):.2f}, p75 {np.percentile(hs,75):.2f}, p90 {np.percentile(hs,90):.2f}')
    t, overlap = assign_types(P)
    t[~lw] = 4
    log(f'types (LWCC): ' + ', '.join(f'{TYPES[i]} {(lw & (t==i)).sum():,}' for i in range(5)) + f'  overlap {overlap}')

    # ---- 4. centralities ----
    cent, G, idx = centralities(A, lw)
    log('centralities done')

    # ---- 3b. k-means on profiled authors with content defined ----
    cl_mask = prof & (P['emp'] >= EMP_MIN)
    ci = np.where(cl_mask)[0]
    feat_names = ['log_comments'] + [f'rate_{k}' for k in CONTENT] + [f'gave_{k}' for k in RFUN] + ['log_recv_given']
    X = np.column_stack([np.log1p(P['comments'][ci])] + [P['n_' + k][ci] / P['emp'][ci] for k in CONTENT] +
                        [P['gave_' + k][ci] / np.maximum(P['given'][ci], 1) for k in RFUN] + [np.log(cent['ratio_recv_given'][ci])])
    Z = (X - X.mean(0)) / X.std(0)
    ks = []
    sil_idx = np.random.default_rng(SEED).choice(len(Z), size=min(4000, len(Z)), replace=False)
    for k in range(2, 9):
        km = KMeans(k, n_init=10, random_state=SEED).fit(Z)
        ks.append(dict(k=k, inertia=round(float(km.inertia_), 1), silhouette=round(float(silhouette_score(Z[sil_idx], km.labels_[sil_idx])), 4)))
    write('kmeans_selection.csv', ks)
    best_k = max(ks, key=lambda r: r['silhouette'])['k']
    # k=2 is a coarse split; rule stated in advance: if silhouette picks 2, use the best k in 3..8 (reported alongside)
    k_use = best_k if best_k > 2 else max([r for r in ks if r['k'] >= 3], key=lambda r: r['silhouette'])['k']
    km = KMeans(k_use, n_init=20, random_state=SEED).fit(Z)
    cluster = np.full(n_auth, -1); cluster[ci] = km.labels_
    centers = km.cluster_centers_
    log(f'k-means: silhouette best k={best_k}, used k={k_use}; selection {ks}')
    ari_rule_km = adjusted_rand_score(t[ci], km.labels_)
    ct = Counter(zip(t[ci], km.labels_))
    crosstab = [dict(rule_type=TYPES[a_], **{f'cluster_{j}': ct.get((a_, j), 0) for j in range(k_use)}) for a_ in range(TYPED)]
    write('kmeans_vs_rules_crosstab.csv', crosstab)
    write('kmeans_centers.csv', [dict(cluster=j, n=int((km.labels_ == j).sum()), **{f: round(float(centers[j, i]), 3) for i, f in enumerate(feat_names)},
                                      **{f'raw_{f}': round(float(X[km.labels_ == j, i].mean()), 4) for i, f in enumerate(feat_names)}) for j in range(k_use)])
    # Ward (C)
    Lw = linkage(Z, method='ward')
    ward = fcluster(Lw, k_use, criterion='maxclust')
    ari_ward_km = adjusted_rand_score(km.labels_, ward); ari_ward_rule = adjusted_rand_score(t[ci], ward)
    log(f'ARI rules~kmeans {ari_rule_km:.3f}  ward~kmeans {ari_ward_km:.3f}  ward~rules {ari_ward_rule:.3f}')

    # ---- profiles csv ----
    prow = []
    # neutral ids instead of the hashed author keys (hashes of usernames can be confirmed by guessing)
    pnodes = np.where(prof)[0]; nid = {int(i): f'a{k}' for k, i in enumerate(pnodes)}
    nid.update({int(i): f'n{k}' for k, i in enumerate(np.where(lw & ~prof)[0])})
    for i in np.where(lw)[0]:
        r = dict(author=nid[int(i)], type=TYPES[t[i]], cluster=int(cluster[i]), comments=int(P['comments'][i]), threads=int(P['threads'][i]),
                 employment_comments=int(P['emp'][i]), replies_given=int(P['given'][i]), replies_received=int(P['received'][i]))
        for k in CONTENT: r['rate_' + k] = round(P['n_' + k][i] / P['emp'][i], 3) if P['emp'][i] >= EMP_MIN else ''
        for k in RFUN:
            r['gave_' + k] = round(P['gave_' + k][i] / P['given'][i], 3) if P['given'][i] else ''
            r['got_' + k] = round(P['got_' + k][i] / P['received'][i], 3) if P['received'][i] else ''
        for k in ('in_degree', 'out_degree', 'in_weight', 'out_weight', 'ratio_recv_given', 'pagerank', 'betweenness', 'closeness_in', 'closeness_out'):
            r[k] = round(float(cent[k][i]), 6)
        prow.append(r)
    write('author_profiles.csv', prow)

    # ---- 4. centrality by type ----
    MEAS = ['degree', 'in_degree', 'out_degree', 'in_weight', 'out_weight', 'ratio_recv_given', 'pagerank', 'betweenness', 'closeness_in', 'closeness_out']
    crow = []
    for ty in range(5):
        m = lw & (t == ty)
        for k in MEAS:
            x = cent[k][m]; lo, hi = boot_median(x)
            crow.append(dict(type=TYPES[ty], measure=k, n=int(m.sum()), median=round(float(np.median(x)), 6), ci95_lo=round(lo, 6), ci95_hi=round(hi, 6),
                             mean=round(float(x.mean()), 6), pct_zero=round(100*float((x == 0).mean()), 1)))
    # story vs other, helper vs other: median difference with bootstrap CI
    for a_ in (0, 1, 2):
        for k in ('ratio_recv_given', 'betweenness', 'pagerank', 'out_degree', 'in_degree', 'closeness_in'):
            xa, xb = cent[k][lw & (t == a_)], cent[k][lw & (t == 3)]
            dd = [np.median(xa[rng.integers(0, len(xa), len(xa))]) - np.median(xb[rng.integers(0, len(xb), len(xb))]) for _ in range(1000)]
            crow.append(dict(type=f'{TYPES[a_]} minus other', measure=k, n=len(xa), median=round(float(np.median(xa) - np.median(xb)), 6),
                             ci95_lo=round(float(np.percentile(dd, 2.5)), 6), ci95_hi=round(float(np.percentile(dd, 97.5)), 6)))
    write('centrality_by_type.csv', crow)
    log('centrality by type written')

    # ---- 5. mixing ----
    e = D['edge'] & lw[D['author']]
    s_, d_, R, th = D['author'][e], D['parent'][e], D['R'][e], D['thread'][e]
    st, dt = t[s_], t[d_]
    Mx, L = mixing(st, dt)
    assert int(Mx.sum()) == rep_lw, (Mx.sum(), rep_lw)
    mrow = []
    for fn in ['all'] + RFUN:
        m = np.ones(len(st), bool) if fn == 'all' else R[:, RFUN.index(fn)]
        Mf, Lf = mixing(st[m], dt[m])
        for a_ in range(5):
            for b_ in range(5):
                cell = (st == a_) & (dt == b_)
                r = dict(reply_function=fn, replier_type=TYPES[a_], parent_author_type=TYPES[b_], replies=int(Mf[a_, b_]),
                         lift_vs_random_mixing=round(float(Lf[a_, b_]), 3))
                if fn != 'all':
                    f = R[cell, RFUN.index(fn)]; base = R[:, RFUN.index(fn)].mean()
                    lo, hi = thread_boot_share(f, th[cell]) if cell.sum() >= 30 else (float('nan'),) * 2
                    r.update(pct_of_cell=round(100*float(f.mean()), 2) if cell.any() else '', ci95_lo=round(100*lo, 2), ci95_hi=round(100*hi, 2),
                             overall_pct=round(100*float(base), 2), share_lift=round(float(f.mean()/base), 3) if cell.any() else '')
                mrow.append(r)
    write('mixing_matrix.csv', mrow, header=['reply_function', 'replier_type', 'parent_author_type', 'replies', 'lift_vs_random_mixing',
                                             'pct_of_cell', 'ci95_lo', 'ci95_hi', 'overall_pct', 'share_lift'])
    obs = key_stats(t, D, lw, cent)
    log(f'assortativity all {obs["assort_all"]:.3f} typed {obs["assort_typed"]:.3f}')

    # ---- 7d. structural nulls: (i) degree-preserving stub shuffle, (ii) within-thread shuffle ----
    nulls = {'stub_shuffle': [], 'within_thread': []}
    order = np.argsort(th, kind='stable'); th_sorted = th[order]
    bounds = np.flatnonzero(np.diff(th_sorted)) + 1; groups = np.split(order, bounds)
    for rep in range(200):
        perm = rng.permutation(len(d_)); dp = d_[perm]; okm = dp != s_
        Mn, Ln = mixing(st[okm], t[dp[okm]])
        nulls['stub_shuffle'].append((assortativity(Mn), assortativity(Mn[:TYPED, :TYPED]), Ln))
        dp2 = d_.copy()
        for g in groups:
            if len(g) > 1: dp2[g] = d_[rng.permutation(g)]
        okm = dp2 != s_
        Mn, Ln = mixing(st[okm], t[dp2[okm]])
        nulls['within_thread'].append((assortativity(Mn), assortativity(Mn[:TYPED, :TYPED]), Ln))
    nrow = []
    for nm, vals in nulls.items():
        aa = np.array([v[0] for v in vals]); at = np.array([v[1] for v in vals]); LL = np.array([v[2] for v in vals])
        for lab_, o, arr in [('assortativity_all', obs['assort_all'], aa), ('assortativity_typed', obs['assort_typed'], at)]:
            nrow.append(dict(null=nm, statistic=lab_, observed=round(o, 4), null_mean=round(float(arr.mean()), 4), null_sd=round(float(arr.std()), 4),
                             z=round(float((o - arr.mean()) / max(arr.std(), 1e-12)), 1), p_emp=round(float((arr >= o).mean()), 3)))
        for a_ in range(TYPED):
            for b_ in range(TYPED):
                arr = LL[:, a_, b_]; o = L[a_, b_]
                nrow.append(dict(null=nm, statistic=f'lift {TYPES[a_]}->{TYPES[b_]}', observed=round(float(o), 3), null_mean=round(float(np.nanmean(arr)), 3),
                                 null_sd=round(float(np.nanstd(arr)), 3), z=round(float((o - np.nanmean(arr)) / max(np.nanstd(arr), 1e-12)), 1),
                                 p_emp=round(float((arr >= o).mean()), 3)))
    write('null_models.csv', nrow)
    log('nulls done')

    # ---- 6. communities (Louvain) on the undirected weighted projection ----
    U = nx.Graph()
    sub = Alw.tocoo()
    Us = (Alw + Alw.T).tocoo()
    U.add_nodes_from(range(nlw))
    U.add_weighted_edges_from((int(i), int(j), float(w)) for i, j, w in zip(Us.row, Us.col, Us.data) if i < j)
    comms = nx.community.louvain_communities(U, weight='weight', seed=SEED, resolution=1.0)
    Q = nx.community.modularity(U, comms, weight='weight')
    comm = np.full(n_auth, -1)
    for j, cm in enumerate(sorted(comms, key=len, reverse=True)):
        for v in cm: comm[idx[v]] = j
    tl = t[lw]; overall = np.bincount(tl[tl < TYPED], minlength=TYPED) / max((tl < TYPED).sum(), 1)
    H0 = -sum(p*math.log2(p) for p in overall if p > 0)
    crow2 = []
    for j in range(comm.max() + 1):
        m = comm == j; sz = int(m.sum())
        if sz < 50: continue
        tt = t[m]; ty_ = tt[tt < TYPED]; sh = np.bincount(ty_, minlength=TYPED) / max(len(ty_), 1)
        H = -sum(p*math.log2(p) for p in sh if p > 0)
        crow2.append(dict(community=j, authors=sz, profiled=len(ty_), **{f'share_{TYPES[k]}': round(float(sh[k]), 3) for k in range(TYPED)},
                          **{f'lift_{TYPES[k]}': round(float(sh[k]/overall[k]), 2) if overall[k] else '' for k in range(TYPED)},
                          type_entropy_bits=round(H, 3), overall_entropy_bits=round(H0, 3),
                          threads_spanned=int(len(np.unique(D['thread'][np.isin(D['author'], np.where(m)[0])])))))
    write('communities.csv', crow2)
    both = (comm >= 0) & (cluster >= 0)
    ari_comm_km = adjusted_rand_score(comm[both], cluster[both]); nmi_comm_km = normalized_mutual_info_score(comm[both], cluster[both])
    pt = prof & (comm >= 0)
    ari_comm_rule = adjusted_rand_score(comm[pt], t[pt]); nmi_comm_rule = normalized_mutual_info_score(comm[pt], t[pt])
    sizes_c = sorted((len(x) for x in comms), reverse=True)
    log(f'Louvain: {len(comms)} communities, Q={Q:.3f}, top sizes {sizes_c[:8]}; ARI comm~kmeans {ari_comm_km:.3f} NMI {nmi_comm_km:.3f}')

    # ---- 6b. Girvan-Newman on a high-degree core (D) ----
    deg_u = np.array([U.degree(v) for v in range(nlw)])
    core = np.argsort(-deg_u)[:300]
    Gc = U.subgraph(core.tolist()).copy()
    Gc.remove_nodes_from([v for v in list(Gc) if Gc.degree(v) == 0])
    gn_best, gn_Q, tgn = None, -1, time.time()
    gen = nx.community.girvan_newman(Gc)
    for level, part in enumerate(gen):
        q = nx.community.modularity(Gc, part)
        if q > gn_Q: gn_Q, gn_best = q, part
        if len(part) >= 40 or time.time() - tgn > 240: break
    lv_core = nx.community.louvain_communities(Gc, seed=SEED)
    lab_gn = {v: j for j, p in enumerate(gn_best) for v in p}; lab_lv = {v: j for j, p in enumerate(lv_core) for v in p}
    nodes_c = list(Gc)
    ari_gn_lv = adjusted_rand_score([lab_gn[v] for v in nodes_c], [lab_lv[v] for v in nodes_c])
    q_lv_core = nx.community.modularity(Gc, lv_core)
    ck = [v for v in nodes_c if cluster[idx[v]] >= 0]
    ari_gn_km = adjusted_rand_score([lab_gn[v] for v in ck], [cluster[idx[v]] for v in ck]) if len(ck) > 10 else float('nan')
    ari_lv_km = adjusted_rand_score([lab_lv[v] for v in ck], [cluster[idx[v]] for v in ck]) if len(ck) > 10 else float('nan')
    log(f'GN core {Gc.number_of_nodes()} nodes {Gc.number_of_edges()} edges: best Q {gn_Q:.3f} ({len(gn_best)} groups) vs Louvain Q {q_lv_core:.3f} ({len(lv_core)}); ARI {ari_gn_lv:.3f}')

    # ---- 8. structural baseline (A) ----
    Us_simple = nx.Graph(U)
    trans = nx.transitivity(Us_simple); avgc = nx.average_clustering(Us_simple)
    Bu = (sp.csr_matrix((Alw + Alw.T)) > 0).astype(float)
    srcs = np.random.default_rng(SEED).choice(nlw, size=K_PATH, replace=False)
    dist = csgraph.shortest_path(Bu, directed=False, unweighted=True, indices=srcs)
    fin = dist[np.isfinite(dist) & (dist > 0)]
    degs = deg_u[deg_u > 0]
    xmin = 10; tail = degs[degs >= xmin]; alpha = 1 + len(tail) / np.log(tail / (xmin - 0.5)).sum()
    tc = time.time(); cl_sizes = Counter(); maxc = 0
    for q_ in nx.find_cliques(Us_simple):
        cl_sizes[len(q_)] += 1; maxc = max(maxc, len(q_))
        if time.time() - tc > 120: break
    structure += [dict(measure='density_directed', value=round(Alw.nnz / (nlw*(nlw-1)), 8)),
                  dict(measure='undirected_edges', value=Us_simple.number_of_edges()),
                  dict(measure='reciprocity', value=round(nx.reciprocity(G), 4)),
                  dict(measure='degree_median', value=float(np.median(degs))), dict(measure='degree_max', value=int(degs.max())),
                  dict(measure='degree_tail_alpha_xmin10', value=round(float(alpha), 3)),
                  dict(measure='top1pct_authors_share_of_degree', value=round(float(np.sort(degs)[-len(degs)//100:].sum() / degs.sum()), 3)),
                  dict(measure='transitivity_global', value=round(trans, 4)), dict(measure='avg_local_clustering', value=round(avgc, 4)),
                  dict(measure='avg_shortest_path_sampled', value=round(float(fin.mean()), 3)),
                  dict(measure='diameter_lower_bound_sampled', value=int(fin.max())),
                  dict(measure='max_clique', value=maxc), dict(measure='cliques_size_ge4', value=sum(v for k, v in cl_sizes.items() if k >= 4)),
                  dict(measure='louvain_communities', value=len(comms)), dict(measure='louvain_modularity', value=round(Q, 4)),
                  dict(measure='louvain_largest5', value=' '.join(map(str, sizes_c[:5]))),
                  dict(measure='communities_ge50', value=len(crow2)),
                  dict(measure='ari_rules_kmeans', value=round(ari_rule_km, 4)), dict(measure='ari_ward_kmeans', value=round(ari_ward_km, 4)),
                  dict(measure='ari_ward_rules', value=round(ari_ward_rule, 4)), dict(measure='kmeans_k', value=k_use),
                  dict(measure='ari_community_kmeans', value=round(ari_comm_km, 4)), dict(measure='nmi_community_kmeans', value=round(nmi_comm_km, 4)),
                  dict(measure='ari_community_rules', value=round(ari_comm_rule, 4)), dict(measure='nmi_community_rules', value=round(nmi_comm_rule, 4)),
                  dict(measure='gn_core_nodes', value=Gc.number_of_nodes()), dict(measure='gn_core_edges', value=Gc.number_of_edges()),
                  dict(measure='gn_best_modularity', value=round(gn_Q, 4)), dict(measure='gn_groups', value=len(gn_best)),
                  dict(measure='louvain_core_modularity', value=round(q_lv_core, 4)), dict(measure='louvain_core_groups', value=len(lv_core)),
                  dict(measure='ari_gn_louvain_core', value=round(ari_gn_lv, 4)), dict(measure='ari_gn_kmeans_core', value=round(ari_gn_km, 4)),
                  dict(measure='ari_louvain_kmeans_core', value=round(ari_lv_km, 4)),
                  dict(measure='type_overlap', value=json.dumps(overlap)), dict(measure='help_share_p75', value=round(float(np.percentile(hs, 75)), 3))]
    log('structure done')

    # ---- 9. bipartite author-thread check (B) ----
    pi = np.where(prof)[0]; pmap = -np.ones(n_auth, int); pmap[pi] = np.arange(len(pi))
    mm = prof[D['author']]
    I = sp.csr_matrix((np.ones(mm.sum()), (pmap[D['author'][mm]], D['thread'][mm])), shape=(len(pi), len(threads)))
    I.sum_duplicates(); Ib = (I > 0).astype(float)
    t_auth = np.asarray(Ib.sum(0)).ravel(); cut = np.percentile(t_auth[t_auth > 0], 99)
    Ik = Ib[:, np.where(t_auth <= cut)[0]]
    Pj = (Ik @ Ik.T).tocsr(); Pj.setdiag(0); Pj.eliminate_zeros()
    Pj2 = Pj.multiply(Pj >= 2).tocsr(); Pj2.eliminate_zeros()
    Gb = nx.from_scipy_sparse_array(Pj2, edge_attribute='weight')
    prb = nx.pagerank(Gb, weight='weight'); prb = np.array([prb[i] for i in range(len(pi))]) * len(pi)
    cb = nx.community.louvain_communities(Gb, weight='weight', seed=SEED)
    lab_b = np.full(len(pi), -1)
    for j, cm in enumerate(cb):
        for v in cm: lab_b[v] = j
    nonisol = np.asarray((Pj2 > 0).sum(1)).ravel() > 0
    ari_b_reply = adjusted_rand_score(lab_b[nonisol], comm[pi][nonisol])
    brow = [dict(measure='incidence_authors', value=len(pi)), dict(measure='incidence_threads', value=int((t_auth > 0).sum())),
            dict(measure='incidence_density', value=round(Ib.nnz / (len(pi) * max((t_auth > 0).sum(), 1)), 6)),
            dict(measure='threads_dropped_top1pct_authors_gt', value=float(cut)),
            dict(measure='projection_pairs_shared_ge1', value=Pj.nnz // 2), dict(measure='projection_pairs_shared_ge2', value=Pj2.nnz // 2),
            dict(measure='projection_louvain_communities', value=len(cb)),
            dict(measure='projection_modularity', value=round(nx.community.modularity(Gb, cb, weight='weight'), 4)),
            dict(measure='ari_projection_vs_reply_louvain', value=round(ari_b_reply, 4))]
    for ty in range(TYPED):
        m = t[pi] == ty
        lo, hi = boot_median(prb[m]); brow.append(dict(measure=f'projection_pagerank_median_{TYPES[ty]}', value=round(float(np.median(prb[m])), 4), lo=round(lo, 4), hi=round(hi, 4)))
        brow.append(dict(measure=f'reply_pagerank_median_{TYPES[ty]}', value=round(float(np.median(cent['pagerank'][pi][m])), 4)))
    write('bipartite_check.csv', brow, header=['measure', 'value', 'lo', 'hi'])
    log('bipartite done')

    # ---- 7. rivals ----
    rv = []
    def add(rival, variant, ks):
        for k, v in ks.items():
            if isinstance(v, float) and math.isnan(v): continue
            rv.append(dict(rival=rival, variant=variant, statistic=k, value=round(v, 4) if isinstance(v, float) else v))
    add('observed', 'main', obs)
    # (a) activity bands
    bands = [(5, 10), (10, 20), (20, 50), (50, 10**9)]
    for lo_, hi_ in bands:
        m = lw & (P['comments'] >= lo_) & (P['comments'] < hi_)
        for ty in range(TYPED):
            mm_ = m & (t == ty)
            for k in ('ratio_recv_given', 'pagerank', 'betweenness', 'out_degree', 'in_degree'):
                if mm_.sum() >= 10:
                    rv.append(dict(rival='activity_band', variant=f'{lo_}-{hi_ if hi_ < 10**9 else "+"}', statistic=f'median_{k}_{TYPES[ty]}',
                                   value=round(float(np.median(cent[k][mm_])), 6), n=int(mm_.sum())))
    # matched comparison: each story-sharer / helper / blame-talker vs an 'other' author with the same comment count bin
    bins = np.digitize(P['comments'], [5, 6, 7, 8, 10, 12, 15, 20, 30, 50, 100, 200])
    for a_ in (0, 1, 2):
        A_ = np.where(lw & (t == a_))[0]; O_ = np.where(lw & (t == 3))[0]
        pool = {b: O_[bins[O_] == b] for b in np.unique(bins[O_])}
        diffs = {k: [] for k in ('ratio_recv_given', 'pagerank', 'betweenness', 'out_degree')}
        for i in A_:
            p_ = pool.get(bins[i]);
            if p_ is None or not len(p_): continue
            j = p_[rng.integers(len(p_))]
            for k in diffs: diffs[k].append(cent[k][i] - cent[k][j])
        for k, v in diffs.items():
            v = np.array(v); b_ = [np.median(v[rng.integers(0, len(v), len(v))]) for _ in range(1000)]
            rv.append(dict(rival='activity_matched', variant=f'{TYPES[a_]} vs matched other', statistic=f'median_paired_diff_{k}',
                           value=round(float(np.median(v)), 6), n=len(v), lo=round(float(np.percentile(b_, 2.5)), 6), hi=round(float(np.percentile(b_, 97.5)), 6),
                           pct_positive=round(100*float((v > 0).mean()), 1)))
    log('activity rival done')
    # (b) drop the top 1% largest threads
    tsize = np.bincount(D['thread'], minlength=len(threads)); big = tsize >= np.percentile(tsize, 99)
    keep = ~big[D['thread']]
    A2, pr2, lw2, _, _ = graph(D, n_auth, keep)
    D2 = dict(D); D2['edge'] = D['edge'] & keep
    cent2, _, _ = centralities(A2, lw2, k_btw=300, k_close=500)
    t2 = t.copy(); t2[~lw2] = 4  # types fixed from full data
    add('megathreads_dropped', f'top 1% threads (>= {int(np.percentile(tsize, 99))} comments, {int(big.sum())} threads, {100*tsize[big].sum()/tsize.sum():.1f}% of comments)',
        key_stats(t2, D2, lw2, cent2))
    log('megathread rival done')
    # (c) label noise: drop true hits (false positives) and add random hits (false negatives), reclassify
    # fn_ = missed hits as a share of the observed hits (recall ~ 1/(1+fn_)), added at random among eligible comments
    rateC = D['C'][D['emp']].mean(0); rateR = D['R'][D['edge']].mean(0)
    for fp, fn_ in [(0.10, 0.0), (0.25, 0.0), (0.0, 0.25), (0.0, 0.50), (0.25, 0.25)]:
        acc = []
        for rep in range(10):
            Dn = dict(D)
            Cn = D['C'] & (rng.random(D['C'].shape) >= fp); Rn = D['R'] & (rng.random(D['R'].shape) >= fp)
            Cn |= (rng.random(D['C'].shape) < fn_ * rateC) & D['emp'][:, None]; Rn |= (rng.random(D['R'].shape) < fn_ * rateR) & D['edge'][:, None]
            Dn['C'], Dn['R'] = Cn, Rn
            Pn = profiles(Dn, n_auth); tn, _ = assign_types(Pn); tn[~lw] = 4
            acc.append(key_stats(tn, Dn, lw, cent))
        for k in acc[0]:
            v = np.array([a[k] for a in acc], float)
            if np.all(np.isnan(v)): continue
            rv.append(dict(rival='label_noise', variant=f'drop {int(fp*100)}% of hits + add missed hits = {int(fn_*100)}% of observed (10 reps)', statistic=k,
                           value=round(float(np.nanmean(v)), 4), lo=round(float(np.nanmin(v)), 4), hi=round(float(np.nanmax(v)), 4)))
    log('label noise rival done')
    write('rivals.csv', rv, header=['rival', 'variant', 'statistic', 'value', 'n', 'lo', 'hi', 'pct_positive'])

    # ---- sensitivity to N ----
    sens = []
    for Nn in (3, 5, 10, 20):
        tn, _ = assign_types(P, n_min=Nn); tn[~lw] = 4
        for k, v in key_stats(tn, D, lw, cent).items():
            sens.append(dict(N=Nn, statistic=k, value=round(v, 4) if isinstance(v, float) else v))
    write('sensitivity_N.csv', sens)
    log('sensitivity done')
    write('structure.csv', structure)

    # ---- examples (no ids, no usernames) ----
    text_of = dict(zip(D['id'], D['text']))
    ex = []
    flows = [('helper -> story-sharer, sympathy', 2, 0, 'sympathy'), ('helper -> story-sharer, advice', 2, 0, 'advice'),
             ('other -> story-sharer, sympathy', 3, 0, 'sympathy'), ('blame-talker -> blame-talker, challenge', 1, 1, 'challenge'),
             ('blame-talker -> blame-talker, agree', 1, 1, 'agree'), ('other -> blame-talker, challenge', 3, 1, 'challenge'),
             ('other -> blame-talker, agree', 3, 1, 'agree'), ('story-sharer -> other, advice (story-sharers also give)', 0, 3, 'advice')]
    eids = D['id'][e]; pfull = D['pfull'][e]; pkind = D['pkind'][e]
    for name, a_, b_, fn in flows:
        cand = np.where((st == a_) & (dt == b_) & R[:, RFUN.index(fn)] & (pkind == 'comments'))[0]
        for i in rng.choice(cand, size=min(8, len(cand)), replace=False):
            ptxt = text_of.get(pfull[i][3:], '')
            if not ptxt:
                rr = c.execute("select own_text from features where kind='comments' and id=?", (pfull[i][3:],)).fetchone(); ptxt = (rr or [''])[0] or ''
            ex.append(f'[{name}]\n  PARENT: {short(ptxt, 300)}\n  REPLY:  {short(text_of[eids[i]], 220)}\n')
    (OUT / 'examples.txt').write_text('Verbatim excerpts for reading only (no ids or usernames). Quote briefly or paraphrase in reports.\n\n' + '\n'.join(ex), encoding='utf-8')

    # ---- GEXF: profiled authors (N >= 5) in the LWCC, induced subgraph ----
    pm = -np.ones(n_auth, int); pm[pnodes] = np.arange(len(pnodes))
    Ap = A[pnodes][:, pnodes].tocoo()
    Gx = nx.DiGraph()
    for k_, i in enumerate(pnodes):
        Gx.add_node(f'a{k_}', label=f'a{k_}', type=TYPES[t[i]], cluster=int(cluster[i]), community=int(comm[i]), comments=int(P['comments'][i]),
                    **{k: float(cent[k][i]) for k in ('in_degree', 'out_degree', 'pagerank', 'betweenness', 'closeness_in', 'ratio_recv_given')},
                    **{'rate_' + k: float(P['n_' + k][i] / P['emp'][i]) if P['emp'][i] >= EMP_MIN else -1.0 for k in CONTENT})
    for i, j, w in zip(Ap.row, Ap.col, Ap.data): Gx.add_edge(f'a{i}', f'a{j}', weight=float(w))
    nx.write_gexf(Gx, OUT / 'network_profiled.gexf')
    log(f'gexf: {Gx.number_of_nodes()} nodes, {Gx.number_of_edges()} edges')

    figures(cent, t, lw, mrow, centers, feat_names, k_use, Lw, deg_u)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    json.dump({'question': __doc__.split('\n')[0], 'window': [M0, M1], 'seed': SEED, 'lwcc_nodes': nlw, 'lwcc_replies': rep_lw,
               'thresholds': dict(N_MIN=N_MIN, EMP_MIN=EMP_MIN, BLAME_MIN=BLAME_MIN, BLAME_SHARE=BLAME_SHARE, HELP_GIVEN_MIN=HELP_GIVEN_MIN, HELP_SHARE=HELP_SHARE),
               'sampling': dict(betweenness_sources=K_BTW, closeness_sources=K_CLOSE, path_sources=K_PATH),
               'packages': {'networkx': nx.__version__, 'scipy': __import__('scipy').__version__, 'sklearn': __import__('sklearn').__version__},
               'seconds': round(time.time() - log.__defaults__[0][0]), 'peak_mb': round(peak)}, (OUT / 'manifest.json').open('w'), indent=2)
    log(f'done, peak {peak:.0f} MB')

# ---------------------------------------------------------------------------
def figures(cent, t, lw, mrow, centers, feat_names, k_use, Lw, deg_u):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
    plt.rcParams.update({'font.size': 9, 'axes.edgecolor': INK2, 'axes.labelcolor': INK, 'xtick.color': INK2, 'ytick.color': INK2,
                         'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': '#e6e6e6', 'grid.linewidth': 0.6})
    div = LinearSegmentedColormap.from_list('div', ['#1757ac', '#84b9f3', '#efefef', '#f18a59', '#b8430f'])
    # 1. centrality by type
    meas = [('ratio_recv_given', 'Replies received / given (+1 each)'), ('out_degree', 'Out-degree (people replied to)'),
            ('in_degree', 'In-degree (people who replied)'), ('pagerank', 'PageRank (1 = average)'),
            ('betweenness', 'Betweenness (sampled)'), ('closeness_in', 'Harmonic closeness, incoming')]
    fig, axs = plt.subplots(2, 3, figsize=(11, 6.4))
    for ax, (k, lab) in zip(axs.ravel(), meas):
        data = [cent[k][lw & (t == ty)] for ty in range(5)]
        pos = 1e-7 if k == 'betweenness' else None
        if k in ('betweenness',): data = [np.maximum(x, 1e-7) for x in data]
        bp = ax.boxplot(data, showfliers=False, widths=0.55, patch_artist=True, medianprops=dict(color=INK, linewidth=2))
        for patch, ty in zip(bp['boxes'], TYPES): patch.set_facecolor(COL[ty]); patch.set_edgecolor('#ffffff'); patch.set_alpha(0.9)
        if k not in ('closeness_in',): ax.set_yscale('log')
        ax.set_xticks(range(1, 6), [x.replace('-', '-\n') for x in TYPES], fontsize=8); ax.set_title(lab, fontsize=9, color=INK, loc='left')
    fig.suptitle('Network position by author type, r/cscareerquestions Jan-Jun 2025 (box = IQR, line = median)', fontsize=10, color=INK, x=0.01, ha='left')
    fig.tight_layout(); fig.savefig(OUT / 'fig_centrality_by_type.png', dpi=160); plt.close(fig)
    # 2. mixing lift heatmaps: all replies (lift vs random mixing) and function share lift
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.4))
    for ax, (fn, key, title) in zip(axs, [('all', 'lift_vs_random_mixing', 'Who replies to whom (lift vs random mixing)'),
                                          ('sympathy', 'share_lift', 'Sympathy share of the cell / overall'),
                                          ('challenge', 'share_lift', 'Challenge share of the cell / overall')]):
        Mt = np.full((5, 5), np.nan); Nn = np.zeros((5, 5))
        for r in mrow:
            if r['reply_function'] != fn: continue
            a_, b_ = TYPES.index(r['replier_type']), TYPES.index(r['parent_author_type'])
            v = r.get(key); Mt[a_, b_] = float(v) if v not in ('', None) else np.nan
            Nn[a_, b_] = r['replies']
        lg = np.log2(np.clip(Mt, 1/4, 4))
        im = ax.imshow(lg, cmap=div, norm=TwoSlopeNorm(0, -2, 2))
        for a_ in range(5):
            for b_ in range(5):
                if not np.isnan(Mt[a_, b_]): ax.text(b_, a_, f'{Mt[a_, b_]:.2f}', ha='center', va='center', fontsize=8,
                                                     color='#ffffff' if abs(lg[a_, b_]) > 1.3 else INK)
        ax.set_xticks(range(5), [x.replace('-', '-\n') for x in TYPES], fontsize=8)
        ax.set_yticks(range(5), TYPES if ax is axs[0] else [''] * 5, fontsize=8)
        ax.set_xlabel('replied to (parent author type)'); ax.set_ylabel('replier type' if ax is axs[0] else '')
        ax.set_title(title, fontsize=9, loc='left', color=INK); ax.grid(False)
    cb = fig.colorbar(im, ax=axs, shrink=0.8, ticks=[-2, -1, 0, 1, 2]); cb.ax.set_yticklabels(['1/4', '1/2', '1', '2', '4'])
    fig.savefig(OUT / 'fig_mixing_lift.png', dpi=160, bbox_inches='tight'); plt.close(fig)
    # 3. k-means profile
    fig, ax = plt.subplots(figsize=(9, 0.6 + 0.45*k_use))
    im = ax.imshow(centers, cmap=div, norm=TwoSlopeNorm(0, -2.5, 2.5), aspect='auto')
    for i in range(centers.shape[0]):
        for j in range(centers.shape[1]): ax.text(j, i, f'{centers[i, j]:+.1f}', ha='center', va='center', fontsize=7, color=INK)
    ax.set_xticks(range(len(feat_names)), feat_names, rotation=35, ha='right', fontsize=8); ax.set_yticks(range(k_use), [f'cluster {j}' for j in range(k_use)])
    ax.set_title('k-means cluster centres (standard deviations from the mean)', fontsize=9, loc='left', color=INK); ax.grid(False)
    fig.colorbar(im, ax=ax, shrink=0.8); fig.tight_layout(); fig.savefig(OUT / 'fig_kmeans_profiles.png', dpi=160); plt.close(fig)
    # 4. dendrogram
    fig, ax = plt.subplots(figsize=(9, 3.5))
    dendrogram(Lw, truncate_mode='lastp', p=40, ax=ax, color_threshold=None, above_threshold_color=INK2, no_labels=True)
    ax.set_title('Ward hierarchical clustering of author profiles (last 40 merges)', fontsize=9, loc='left', color=INK); ax.grid(False)
    fig.tight_layout(); fig.savefig(OUT / 'fig_dendrogram.png', dpi=160); plt.close(fig)
    # 5. degree CCDF
    d = np.sort(deg_u[deg_u > 0]); y = 1 - np.arange(len(d)) / len(d)
    fig, ax = plt.subplots(figsize=(5, 3.8)); ax.loglog(d, y, color=COL['story-sharer'], linewidth=2)
    ax.set_xlabel('undirected degree (distinct people)'); ax.set_ylabel('share of authors with degree >= x')
    ax.set_title('Degree distribution (CCDF, log-log)', fontsize=9, loc='left', color=INK)
    fig.tight_layout(); fig.savefig(OUT / 'fig_degree_ccdf.png', dpi=160); plt.close(fig)

if __name__ == '__main__':
    main()
