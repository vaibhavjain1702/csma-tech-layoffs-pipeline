"""Score comments with off-the-shelf text models (sentiment and zero-shot stance). Read-only on the database.

This is an EXTRA SIGNAL, not a validated label: no model here was trained or checked on our data. The
models run locally on the GPU; no text leaves the machine. Scores are cached in
data/processed/model_scores.sqlite (git-ignored) so the analysis script can be rerun without the GPU.

Models (downloaded from the Hugging Face hub on first run):
  VADER            - word-list sentiment with social-media rules (compound score, -1..1).
  SENT_MODEL       - RoBERTa trained on ~124M tweets and fine-tuned for 3-class sentiment.
  NLI_MODEL        - DeBERTa-v3 trained for zero-shot classification: for each (text, hypothesis) it gives the
                     probability that the text implies the hypothesis. No training on our data.

Text sets (all human, non-empty own_text, Jan-Jun 2025 = the shared window):
  sentiment     : every cscq comment, plus employment comments in r/technology and r/programming.
  blame stance  : employment comments in all three communities (5 screens, no career_transition).
  reply stance  : cscq replies whose parent is a collected human comment (the R4 edge set).
Hypotheses are fixed below, written before looking at any result; the decision cut-off (0.5) is fixed too.

Run: .venv-eda/bin/python scripts/score_text_models.py [--only sentiment|blame|reply] [--limit N]
"""
import argparse, sqlite3, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from explore_leads import connect
from explore_replies import CAND

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'data/processed/model_scores.sqlite'
M0, M1 = '2025-01', '2025-06'
SENT_MODEL = 'cardiffnlp/twitter-roberta-base-sentiment-latest'
NLI_MODEL = 'MoritzLaurer/deberta-v3-base-zeroshot-v2.0'

# ---- comment-level hypotheses: whom does the comment blame? (stance toward a target, not topic) ----
BLAME_HYP = {
    'blames_execs':    'The author blames company executives, management or shareholders for layoffs or the bad job market.',
    'blames_offshore': 'The author blames offshoring or foreign workers on visas such as H-1B for layoffs or the bad job market.',
    'blames_ai':       'The author blames AI for taking jobs.',
    'ai_is_excuse':    'The author says companies use AI as an excuse for layoffs.',
    'blames_macro':    'The author blames the economy, interest rates or government policy for layoffs or the bad job market.',
    'blames_workers':  'The author blames job seekers themselves, such as their skills or effort, for not finding work.',
    # convergent check against the 'experience' regex (no stance; should agree with the marker if the model reads well)
    'own_job_loss':    'The author says they were laid off or lost their job.',
}
# ---- reply-level hypotheses: premise = parent + reply ----
REPLY_HYP = {
    'agrees':    'The reply agrees with the comment.',
    'disagrees': 'The reply disagrees with the comment.',
    'sympathy':  'The reply expresses sympathy or emotional support for the author of the comment.',
}

def log(msg, t0=[time.time()]): print(f'[{time.time()-t0[0]:6.0f}s] {msg}', flush=True)
def clip(t, n): t = ' '.join((t or '').split()); return t[:n]

# ---------------------------------------------------------------------------
def texts(limit=None):
    c = connect(); lim = f' limit {int(limit)}' if limit else ''
    base = "f.likely_bot=0 and f.author_unknown=0 and coalesce(f.own_text,'')<>''"
    cscq = c.execute(f"""select r.id, f.own_text from records r join features f on f.kind='comments' and f.id=r.id
        where r.kind='comments' and r.subreddit='cscareerquestions' and r.created_month between ? and ? and {base}{lim}""", (M0, M1)).fetchall()
    emp = c.execute(f"""select r.id, f.own_text from disruption_screen d join records r on r.kind=d.kind and r.id=d.id
        join features f on f.kind=d.kind and f.id=d.id
        where d.kind='comments' and {CAND} and r.created_month between ? and ? and {base}{lim}""", (M0, M1)).fetchall()
    pairs = c.execute(f"""select r.id, pf.own_text, f.own_text from records r join features f on f.kind='comments' and f.id=r.id
        join reply_edges e on e.child_id=r.id join features pf on pf.kind='comments' and pf.id=substr(e.parent_fullname,4)
        where r.kind='comments' and r.subreddit='cscareerquestions' and r.created_month between ? and ? and {base}
        and e.parent_kind='comments' and pf.likely_bot=0 and pf.author_unknown=0 and coalesce(pf.own_text,'')<>''
        and pf.author_key<>f.author_key{lim}""", (M0, M1)).fetchall()
    # also score the comments already coded (provisionally) in 09_leads/manual, so the zero-shot labels can be
    # compared with them even when they fall outside the window
    import csv
    ids = set()
    for f in CHECK_CODES:
        ids |= {r['id'] for r in csv.DictReader(open(ROOT / 'outputs/09_leads/manual' / f, encoding='utf-8'))}
    q = ','.join('?' * len(ids))
    checks = c.execute(f"select id, own_text from features where kind='comments' and id in ({q}) and coalesce(own_text,'')<>''", sorted(ids)).fetchall()
    sent = dict(cscq); sent.update(emp)
    emp = dict(emp); emp.update(checks)
    return sent, emp, pairs

CHECK_CODES = ['offshore_blame_target_codes.csv', 'ai_pretext_codes.csv', 'first_person_layoff_codes.csv']

def batches(items, lengths, bs):
    """Length-sorted batches: far less padding, so much faster on the GPU."""
    order = np.argsort(lengths)
    for lo in range(0, len(order), bs): yield [items[i] for i in order[lo:lo+bs]]

def cache():
    k = sqlite3.connect(CACHE)
    k.executescript("""create table if not exists sentiment(id text primary key, vader real, neg real, neu real, pos real);
        create table if not exists stance(id text, hyp text, p real, primary key(id, hyp)) without rowid;
        create table if not exists reply_stance(id text, hyp text, p real, primary key(id, hyp)) without rowid;
        create table if not exists meta(k text primary key, v text);""")
    return k

def done(k, table, hyp=None):
    q = f'select id from {table}' + (' where hyp=?' if hyp else '')
    return {r[0] for r in k.execute(q, (hyp,) if hyp else ())}

# ---------------------------------------------------------------------------
def run_sentiment(k, sent):
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    todo = [i for i in sent if i not in done(k, 'sentiment')]
    log(f'sentiment: {len(todo):,} to score')
    if not todo: return
    va = SentimentIntensityAnalyzer()
    tok = AutoTokenizer.from_pretrained(SENT_MODEL)
    mdl = AutoModelForSequenceClassification.from_pretrained(SENT_MODEL).half().cuda().eval()
    lab = {v.lower(): int(i) for i, v in mdl.config.id2label.items()}  # negative / neutral / positive
    lens = [len(sent[i]) for i in todo]; n = 0
    for b in batches(todo, lens, 128):
        tx = [clip(sent[i], 1500) for i in b]
        enc = tok(tx, truncation=True, max_length=256, padding=True, return_tensors='pt').to('cuda')
        with torch.no_grad(): p = torch.softmax(mdl(**enc).logits.float(), -1).cpu().numpy()
        k.executemany('insert or replace into sentiment values (?,?,?,?,?)',
                      [(i, va.polarity_scores(t)['compound'], float(r[lab['negative']]), float(r[lab['neutral']]), float(r[lab['positive']]))
                       for i, t, r in zip(b, tx, p)])
        n += len(b)
        if n % 20000 < 128: k.commit(); log(f'  sentiment {n:,}/{len(todo):,}')
    k.commit()

def nli_setup():
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    tok = AutoTokenizer.from_pretrained(NLI_MODEL)
    mdl = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL).half().cuda().eval()
    ent = [i for i, v in mdl.config.id2label.items() if v.lower().startswith('entail')][0]
    return torch, tok, mdl, int(ent)

def run_nli(k, table, premises, hyps, max_len, bs):
    torch, tok, mdl, ent = nli_setup()
    for h, hyp in hyps.items():
        have = done(k, table, h); todo = [i for i in premises if i not in have]
        log(f'{table}/{h}: {len(todo):,} to score')
        lens = [len(premises[i]) for i in todo]; n = 0
        for b in batches(todo, lens, bs):
            enc = tok([premises[i] for i in b], [hyp] * len(b), truncation='only_first', max_length=max_len,
                      padding=True, return_tensors='pt').to('cuda')
            with torch.no_grad(): p = torch.softmax(mdl(**enc).logits.float(), -1)[:, ent].cpu().numpy()
            k.executemany(f'insert or replace into {table} values (?,?,?)', [(i, h, float(x)) for i, x in zip(b, p)])
            n += len(b)
            if n % 20000 < bs: k.commit(); log(f'  {h} {n:,}/{len(todo):,}')
        k.commit()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--only'); ap.add_argument('--limit', type=int)
    a = ap.parse_args()
    k = cache()
    sent, emp, pairs = texts(a.limit)
    log(f'texts: sentiment {len(sent):,}  blame {len(emp):,}  reply pairs {len(pairs):,}')
    import transformers, torch, vaderSentiment
    k.executemany('insert or replace into meta values (?,?)', [
        ('sent_model', SENT_MODEL), ('nli_model', NLI_MODEL), ('torch', torch.__version__),
        ('transformers', transformers.__version__), ('window', f'{M0}..{M1}'), ('cutoff', '0.5'),
        *[(f'hyp_{h}', t) for h, t in {**BLAME_HYP, **REPLY_HYP}.items()]]); k.commit()
    if a.only in (None, 'sentiment'): run_sentiment(k, sent)
    if a.only in (None, 'blame'):
        run_nli(k, 'stance', {i: clip(t, 1500) for i, t in emp.items()}, BLAME_HYP, 320, 64)
    if a.only in (None, 'reply'):
        prem = {i: f'Comment: {clip(p, 700)}\n\nReply: {clip(r, 700)}' for i, p, r in pairs}
        run_nli(k, 'reply_stance', prem, REPLY_HYP, 384, 48)
    log('done')

if __name__ == '__main__':
    main()
