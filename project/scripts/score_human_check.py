#!/usr/bin/env python3
"""Score the human check of the 240 keyword-rule labels.

Reads the coder workbooks/CSVs in annotations/human_check/, validates them against
outputs/12_replies/check_sheet.csv and writes precision, agreement (Cohen's kappa),
consensus and disagreement tables plus a slide-ready SUMMARY.md to outputs/18_human_check/.

Run from the project root:  python3 scripts/score_human_check.py
"""
import argparse
import itertools
import math
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "annotations" / "human_check"
DEFAULT_OUT = ROOT / "outputs" / "18_human_check"
DEFAULT_REF = ROOT / "outputs" / "12_replies" / "check_sheet.csv"

COMMENT_LABELS = ["experience", "mentions_execs", "mentions_offshore", "blames_workers",
                  "ai_excuse", "ai_replaces", "doom", "none"]
REPLY_LABELS = ["sympathy", "advice", "agree", "challenge"]
LABELS = COMMENT_LABELS + REPLY_LABELS
BLAME_LABELS = ["mentions_execs", "mentions_offshore", "ai_excuse", "blames_workers"]
COLUMNS = ["row_id", "unit", "machine_label", "label_meaning", "text",
           "label_correct", "blamed_target", "notes", "id"]
REQUIRED = ["row_id", "machine_label", "id", "label_correct", "blamed_target"]
ALLOWED = {"label_correct": {"yes", "no", "unsure", ""},
           "blamed_target": {"yes", "no", "unsure", "na", ""}}
ALIASES = {"n/a": "na", "y": "yes", "n": "no"}
CODED = {"yes", "no", "unsure"}
ALL_NOTE = "pooled over a 20-per-label sample; not a corpus-level rate"
PREFIX = "check_sheet_coder_"


# ---------------------------------------------------------------- statistics
def wilson(k, n, z=1.959963984540054):
    """Wilson score interval for k successes out of n."""
    if not n:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def cohen_kappa(a, b):
    """(kappa, percent agreement as a fraction, reason) for two lists of yes/no."""
    n = len(a)
    if n == 0:
        return (None, None, "no rows both coded yes/no")
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in ("yes", "no"))
    if abs(1 - pe) < 1e-12:
        return (None, po, "both coders gave the same answer on every row, so kappa is undefined")
    return ((po - pe) / (1 - pe), po, "")


def tally(vals):
    vals = list(vals)
    return vals.count("yes"), vals.count("no"), vals.count("unsure")


def stat_row(field, source, label, vals, note=""):
    yes, no, unsure = tally(vals)
    lo, hi = wilson(yes, yes + no)
    return {"field": field, "source": source, "label": label, "n_coded": yes + no + unsure,
            "yes": yes, "no": no, "unsure": unsure,
            "precision": yes / (yes + no) if yes + no else None,
            "ci_lo": lo, "ci_hi": hi, "n_single": "", "n_disagree_pending": "",
            "n_adjudicated": "", "note": note}


# ------------------------------------------------------------------- loading
def read_reference(path):
    ref = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    for c in ("unit", "machine_label", "id"):
        if c not in ref.columns:
            raise ValueError(f"{path}: reference is missing column '{c}'")
    return ref.reset_index(drop=True)


def _norm(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    v = str(v).strip().lower()
    return ALIASES.get(v, v)


def _read_csv(path):
    """CSV as all-strings; falls back from UTF-8 for files re-saved by Excel in a legacy encoding.
    Only ASCII columns (row_id, machine_label, id, answers) are used, so the fallback is safe."""
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, dtype=str, keep_default_na=False, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"{Path(path).name}: cannot decode the file")


def read_raw(path):
    path = Path(path)
    if path.suffix.lower() == ".xlsx":
        df = pd.read_excel(path, sheet_name="Coding", engine="openpyxl", dtype=str,
                           keep_default_na=False)
    else:
        df = _read_csv(path)
    df.columns = [str(c).strip().lstrip("\ufeff") for c in df.columns]
    return df


def load_coder_file(path, reference_df):
    """Load + validate one coder file; returns DataFrame sorted by row_id (row i = row_id i+1)."""
    path = Path(path)
    name = path.name
    n_ref = len(reference_df)
    df = read_raw(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"{name}: required columns missing: {', '.join(missing)}")
    if len(df) != n_ref:
        raise ValueError(f"{name}: expected exactly {n_ref} rows, found {len(df)}")
    ids = []
    for raw in df["row_id"]:
        try:
            f = float(str(raw).strip())
            if f != int(f):
                raise ValueError
            ids.append(int(f))
        except ValueError:
            raise ValueError(f"{name}: row_id '{raw}' is not an integer") from None
    if len(set(ids)) != len(ids):
        dups = sorted({i for i in ids if ids.count(i) > 1})
        raise ValueError(f"{name}: row_id values are not unique (duplicated: {dups[:5]})")
    if set(ids) != set(range(1, n_ref + 1)):
        raise ValueError(f"{name}: row_id must be exactly 1..{n_ref}")
    df = df.copy()
    df["row_id"] = ids
    df = df.sort_values("row_id").reset_index(drop=True)
    for i, r in df.iterrows():
        rid = int(r["row_id"])
        ref = reference_df.iloc[i]
        if str(r["machine_label"]).strip() != str(ref["machine_label"]).strip():
            raise ValueError(f"{name}: row_id {rid} machine_label '{r['machine_label']}' differs "
                             f"from reference '{ref['machine_label']}'")
        if str(r["id"]).strip() != str(ref["id"]).strip():
            raise ValueError(f"{name}: row_id {rid} id '{r['id']}' differs from reference "
                             f"'{ref['id']}'")
    for col in ("label_correct", "blamed_target"):
        df[col] = df[col].map(_norm)
        for rid, v in zip(df["row_id"], df[col]):
            if v not in ALLOWED[col]:
                raise ValueError(f"{name}: row_id {rid}, column {col}: bad value '{v}' "
                                 f"(allowed: {sorted(x for x in ALLOWED[col] if x)} or blank)")
    df["machine_label"] = df["machine_label"].str.strip()
    df["unit"] = reference_df["unit"].values
    df["id"] = df["id"].str.strip()
    return df[["row_id", "unit", "machine_label", "id", "label_correct", "blamed_target"]]


def has_coded(df):
    return bool(df["label_correct"].isin(CODED).any() or df["blamed_target"].isin(CODED).any())


def discover_coders(directory, reference_df):
    """{coder: (DataFrame, Path)} for coders with something coded."""
    directory = Path(directory)
    found = {}
    if not directory.is_dir():
        return found
    files = {}
    for p in sorted(directory.iterdir()):
        if p.name.startswith("~$") or not p.name.startswith(PREFIX):
            continue
        ext = p.suffix.lower()
        if ext in (".xlsx", ".csv"):
            files.setdefault(p.stem[len(PREFIX):], {})[ext] = p
    for coder in sorted(files):
        loaded = {ext: (load_coder_file(p, reference_df), p) for ext, p in files[coder].items()}
        coded = {ext: v for ext, v in loaded.items() if has_coded(v[0])}
        if not coded:
            print(f"coder {coder}: nothing coded yet, skipped")
            continue
        if ".xlsx" in coded and ".csv" in coded:
            print(f"WARNING: coder {coder}: both xlsx and csv contain coded cells; using the xlsx")
        found[coder] = coded.get(".xlsx") or coded[".csv"]
    return found


def effective(df, field):
    """Answers used for stats: '' when not coded (and, for blamed_target, outside blame labels)."""
    s = df[field].where(df[field].isin(CODED), "")
    if field == "blamed_target":
        s = s.where(df["machine_label"].isin(BLAME_LABELS), "")
    return s.tolist()


def field_labels(field):
    return LABELS if field == "label_correct" else BLAME_LABELS


def load_adjudicated(directory, n_rows):
    p = Path(directory) / "adjudicated.csv"
    out = {"label_correct": {}, "blamed_target": {}}
    if not p.is_file():
        return out
    df = _read_csv(p)
    df.columns = [str(c).strip().lstrip("\ufeff") for c in df.columns]
    if "row_id" not in df.columns:
        raise ValueError(f"{p.name}: column row_id missing")
    for field, col in (("label_correct", "final_label_correct"),
                       ("blamed_target", "final_blamed_target")):
        if col not in df.columns:
            continue
        for raw, val in zip(df["row_id"], df[col]):
            v = _norm(val)
            if v == "":
                continue
            try:
                rid = int(float(raw))
            except ValueError:
                raise ValueError(f"{p.name}: row_id '{raw}' is not an integer") from None
            if not 1 <= rid <= n_rows or v not in ALLOWED[field] - {""}:
                raise ValueError(f"{p.name}: row_id {raw}, column {col}: bad value '{val}'")
            out[field][rid] = v
    return out


# ------------------------------------------------------------------ scoring
def compute(coders, reference_df, adjudicated):
    """coders: {name: df}. Returns (precision_rows, agreement_rows, disagreement_rows, pairs)."""
    n = len(reference_df)
    mlabels = reference_df["machine_label"].tolist()
    names = sorted(coders)
    prec, agree, dis = [], [], []
    pairs = {}  # (a, b, field, label) -> (list_a, list_b)
    cons = {}
    eff = {c: {f: effective(coders[c], f) for f in ALLOWED} for c in names}

    for field in ALLOWED:
        labels = field_labels(field)
        for c in names:
            for lab in labels:
                prec.append(stat_row(field, f"coder_{c}", lab,
                                     [v for v, m in zip(eff[c][field], mlabels) if m == lab]))
            prec.append(stat_row(field, f"coder_{c}", "ALL",
                                 [v for v, m in zip(eff[c][field], mlabels) if m in labels],
                                 ALL_NOTE))
        # pairwise agreement
        for a, b in itertools.combinations(names, 2):
            if not any(eff[a][field][i] and eff[b][field][i] for i in range(n)):
                continue  # no overlapping coded rows (e.g. A vs C in the 4-person split)
            for lab in labels + ["ALL"]:
                ok = [i for i in range(n) if (mlabels[i] == lab if lab != "ALL"
                                              else mlabels[i] in labels)]
                both = [i for i in ok if eff[a][field][i] and eff[b][field][i]]
                yn = [i for i in both if eff[a][field][i] != "unsure"
                      and eff[b][field][i] != "unsure"]
                la = [eff[a][field][i] for i in yn]
                lb = [eff[b][field][i] for i in yn]
                k, po, why = cohen_kappa(la, lb)
                pairs[(a, b, field, lab)] = (la, lb)
                agree.append({"field": field, "coder_a": a, "coder_b": b, "label": lab,
                              "n_overlap": len(both), "n_both_yes_no": len(yn),
                              "n_any_unsure": len(both) - len(yn),
                              "percent_agreement": None if po is None else round(100 * po, 1),
                              "kappa": "n/a" if k is None else round(k, 4),
                              "kappa_note": why})
        # consensus
        if len(names) >= 2:
            cons[field] = []
            for i in range(n):
                yn = [eff[c][field][i] for c in names if eff[c][field][i] in ("yes", "no")]
                if len(yn) >= 2:
                    cons[field].append(yn[0] if len(set(yn)) == 1 else "disagree")
                elif yn:
                    cons[field].append("single")
                else:
                    cons[field].append("")
            adj = adjudicated[field]
            final = [adj.get(i + 1, cons[field][i] if cons[field][i] in ("yes", "no") else "")
                     for i in range(n)]
            for lab in labels + ["ALL"]:
                idx = [i for i in range(n) if (mlabels[i] == lab if lab != "ALL"
                                               else mlabels[i] in labels)]
                note = ALL_NOTE if lab == "ALL" else ""
                cv = [cons[field][i] for i in idx]
                r = stat_row(field, "consensus", lab, [v for v in cv if v in ("yes", "no")], note)
                n_adj = sum(1 for i in idx if (i + 1) in adj)
                r["n_single"] = cv.count("single")
                r["n_adjudicated"] = n_adj
                r["n_disagree_pending"] = sum(1 for i in idx if cons[field][i] == "disagree"
                                              and (i + 1) not in adj)
                prec.append(r)
                r = stat_row(field, "final", lab, [final[i] for i in idx], note)
                r["n_adjudicated"] = n_adj
                r["n_disagree_pending"] = sum(1 for i in idx if cons[field][i] == "disagree"
                                              and (i + 1) not in adj)
                prec.append(r)
            for i in range(n):
                ans = [eff[c][field][i] for c in names if eff[c][field][i]]
                split = len(ans) >= 2 and len(set(ans)) > 1
                if cons[field][i] == "disagree" or (split and "unsure" in ans):
                    kind = "yes_vs_no" if cons[field][i] == "disagree" else "involves_unsure"
                    row = {"row_id": i + 1, "unit": reference_df.iloc[i]["unit"],
                           "machine_label": mlabels[i], "field": field, "kind": kind}
                    for c in names:
                        row[f"coder_{c}"] = eff[c][field][i]
                    row["adjudicated"] = adjudicated[field].get(i + 1, "")
                    dis.append(row)
    return prec, agree, dis, pairs


# ------------------------------------------------------------------- output
def pct(x):
    return "n/a" if x is None or x == "" else f"{100 * x:.1f}%"


def ci_txt(r):
    if r is None or r["precision"] is None:
        return "n/a"
    return f"{100 * r['precision']:.1f}% ({100 * r['ci_lo']:.1f}–{100 * r['ci_hi']:.1f}%)"


def pick(prec, field, label, names):
    """Row to headline: final (if any yes/no), else consensus, when >=2 coders, else the coder."""
    by = {(r["field"], r["source"], r["label"]): r for r in prec}
    if len(names) >= 2:
        for src in ("final", "consensus"):
            r = by.get((field, src, label))
            if r and r["yes"] + r["no"]:
                return r, src
        return by.get((field, "consensus", label)), "consensus"
    r = by.get((field, f"coder_{names[0]}", label))
    return r, f"coder_{names[0]}"


def pooled(pairs, field, label):
    a, b = [], []
    for (_, _, f, lab), (la, lb) in pairs.items():
        if f == field and lab == label:
            a += la
            b += lb
    return cohen_kappa(a, b), len(a)


def kappa_txt(res):
    k, po, why = res
    return why if k is None else f"{k:.2f}"


def write_summary(path, used, prec, pairs, n_pairs):
    names = sorted(used)
    L = [f"# Human check of keyword-rule labels", "",
         f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "",
         "## Coders used", ""]
    L += [f"- coder {c}: `{used[c].name}`" for c in names]
    L += ["", "## label_correct: did the rule flag the right thing?", "",
          "| label | n | precision % (95% CI) | % agreement | Cohen's kappa |",
          "|---|---|---|---|---|"]
    tmpl = []
    for lab in LABELS + ["ALL"]:
        r, src = pick(prec, "label_correct", lab, names)
        if r is None:
            continue
        (k, po, why), _ = pooled(pairs, "label_correct", lab)
        agr = pct(po)
        kap = "n/a" if len(names) < 2 else (f"{k:.2f}" if k is not None else f"n/a ({why})")
        if len(names) < 2:
            agr = "n/a"
        n_used = r["yes"] + r["no"]
        shown = "ALL (pooled)" if lab == "ALL" else (f"{lab} (baseline purity)" if lab == "none" else lab)
        L.append(f"| {shown} | {n_used} | {ci_txt(r)} | {agr} | {kap} |")
        if lab == "none":
            tmpl.append(f"- Of the unmarked (`none`) comments with a final yes/no answer (n = {n_used} of 20), "
                        f"coders judged {ci_txt(r)} truly free of all seven comment types (baseline purity); "
                        f"agreement between coders was {agr} (kappa {kap}).")
        elif lab != "ALL":
            tmpl.append(f"- Of the `{lab}` rule's hits with a final yes/no answer (n = {n_used} of 20), "
                        f"coders judged {ci_txt(r)} correct; agreement between coders was {agr} (kappa {kap}).")
    L += ["", f"Precision source per row: {'final/consensus (>=2 coders)' if len(names) >= 2 else 'the single coder'}. "
          "Precision = yes / (yes + no); `unsure` is excluded and reported in precision_by_label.csv.", ""]
    L += ["## blamed_target: is the comment actually blaming that target?", "",
          "| label | n | topic rate (label_correct) | blame rate (blamed_target) | n blame |",
          "|---|---|---|---|---|"]
    for lab in BLAME_LABELS:
        t, _ = pick(prec, "label_correct", lab, names)
        b, _ = pick(prec, "blamed_target", lab, names)
        if t is None or b is None:
            continue
        L.append(f"| {lab} | {t['yes'] + t['no']} | {ci_txt(t)} | {ci_txt(b)} | {b['yes'] + b['no']} |")
    L += ["", "## Overall agreement", ""]
    if len(names) < 2:
        L.append("Overall kappa: n/a (only one coder has coded rows).")
    else:
        (k, po, why), nn = pooled(pairs, "label_correct", "ALL")
        L.append(f"Overall kappa (label_correct, all labels, pooled over pairs, {nn} rows both "
                 f"yes/no): {'n/a (' + why + ')' if k is None else f'{k:.2f}'}; "
                 f"agreement {pct(po)}.")
        for (a, b, f, lab), (la, lb) in sorted(pairs.items()):
            if f == "label_correct" and lab == "ALL":
                kk, pp, ww = cohen_kappa(la, lb)
                L.append(f"- coders {a} vs {b}: kappa {'n/a (' + ww + ')' if kk is None else f'{kk:.2f}'}, "
                         f"agreement {pct(pp)}, n={len(la)}")
    L += ["", "## Interpretation template (fill in / edit)", ""] + tmpl
    L += ["", "## Caveats", "",
          "- n=20 per label, so intervals are wide and per-label kappa is jumpy; lead with the overall kappa.",
          "- Precision is for this 20-per-label sample, not a corpus-level rate (the ALL row is pooled over the sample).",
          "- The `none` row is baseline purity: the share of unmarked comments that really contain none of the seven types.",
          "- `blames_workers` label_correct measures the topic (worker skill/effort talk); blamed_target measures actual blame.",
          "- Rows marked `na` or blank in blamed_target are treated as not coded.", ""]
    Path(path).write_text("\n".join(L), encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default=str(DEFAULT_DIR), help="folder with coder files")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="output folder")
    ap.add_argument("--reference", default=str(DEFAULT_REF), help="reference check_sheet.csv")
    args = ap.parse_args(argv)
    try:
        ref = read_reference(args.reference)
        found = discover_coders(args.dir, ref)
        if not found:
            print(f"No coded rows found in {args.dir}. Fill label_correct in the coder "
                  "workbooks, then rerun.")
            return 0
        adjud = load_adjudicated(args.dir, len(ref))
    except (ValueError, OSError) as e:
        print(f"ERROR: {e}")
        return 2
    coders = {c: v[0] for c, v in found.items()}
    used = {c: v[1] for c, v in found.items()}
    prec, agree, dis, pairs = compute(coders, ref, adjud)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    names = sorted(coders)
    pd.DataFrame(prec).round(4).to_csv(out / "precision_by_label.csv", index=False)
    pd.DataFrame(agree, columns=["field", "coder_a", "coder_b", "label", "n_overlap",
                                 "n_both_yes_no", "n_any_unsure", "percent_agreement",
                                 "kappa", "kappa_note"]).to_csv(out / "agreement_by_label.csv",
                                                                index=False)
    pd.DataFrame(dis, columns=["row_id", "unit", "machine_label", "field", "kind"]
                 + [f"coder_{c}" for c in names] + ["adjudicated"]
                 ).to_csv(out / "disagreements.csv", index=False)
    write_summary(out / "SUMMARY.md", used, prec, pairs, len(agree))
    print(f"Coders used: {', '.join(f'{c} ({used[c].name})' for c in names)}")
    for lab in LABELS + ["ALL"]:
        r, src = pick(prec, "label_correct", lab, names)
        if r:
            print(f"  {lab:<18} n={r['yes'] + r['no']:<3} precision {ci_txt(r)}  [{src}]")
    print(f"Rows to adjudicate (yes vs no, or a split involving unsure): {len(dis)}")
    for f in ("precision_by_label.csv", "agreement_by_label.csv", "disagreements.csv", "SUMMARY.md"):
        print(f"Wrote {out / f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
