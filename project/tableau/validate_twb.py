#!/usr/bin/env python3
"""Validate the generated Tableau workbook and write EXPECTED_VALUES.md.

Checks (no Tableau needed):
  1. Both .twb files parse (standalone and the one inside the .twbx).
  2. Every field used in shelves, encodings, filters, sorts and calc formulas exists in its datasource's
     CSV header or calculated-field list.
  3. Every column-instance used in a worksheet is declared in that worksheet's datasource-dependencies,
     and its derivation/type match its name.
  4. Dashboards, filter zones and story points reference existing worksheets / dashboards; zone ids are
     unique per dashboard; there is one window per sheet/dashboard and exactly one maximized window.
  5. The .twbx holds the .twb at its root plus every referenced CSV at Data/16_tableau/<file>, byte-identical
     to outputs/16_tableau; the standalone .twb's relative directory resolves to outputs/16_tableau.
Then computes, with pandas, the numbers each view should show (same filters as the generator) and writes
tableau/EXPECTED_VALUES.md for the GUI check.

Usage: PYTHONDONTWRITEBYTECODE=1 python3 -B tableau/validate_twb.py   (exit code 1 on any failure)
"""
from __future__ import annotations

import io
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.dirname(HERE)
EXTRACTS = os.path.join(ARCH, "outputs", "16_tableau")
NAME = "CSMA_Solidarity_or_Blame"
U = "{http://www.tableausoftware.com/xml/user}"
DERIV = {"none": "None", "sum": "Sum", "avg": "Avg", "usr": "User", "attr": "Attribute"}
ITYPE = {"nk": "nominal", "ok": "ordinal", "qk": "quantitative"}
REF = re.compile(r"\[([^\[\]]+)\]\.\[([a-z]+):([^\]]+):([a-z]{2})\]")

errors: list[str] = []
notes: list[str] = []


def err(msg):
    errors.append(msg)


def check_twb(label: str, xml_bytes: bytes, base_dir: str | None):
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        err(f"[{label}] XML does not parse: {e}")
        return None
    if root.tag != "workbook" or root.get("version") != "18.1":
        err(f"[{label}] root is not <workbook version='18.1'>")

    # ---- datasources: header + calcs
    ds_fields, ds_files = {}, {}
    for ds in root.find("datasources"):
        name = ds.get("name")
        conn = ds.find("connection/named-connections/named-connection/connection")
        rel = ds.find("connection/relation")
        directory, fname = conn.get("directory"), conn.get("filename")
        ds_files[name] = (directory, fname)
        if rel.get("table") != f"[{fname[:-4]}#csv]" or rel.get("type") != "table":
            err(f"[{label}] {name}: relation table/type mismatch")
        src = os.path.join(EXTRACTS, fname)
        csv_header = list(pd.read_csv(src, nrows=0).columns)
        declared = [c.get("name") for c in rel.find("columns")]
        if declared != csv_header:
            err(f"[{label}] {name}: relation columns differ from CSV header of {fname}")
        mrs = ds.findall("connection/metadata-records/metadata-record")
        remote = [m.findtext("remote-name") for m in mrs]
        if remote != csv_header:
            err(f"[{label}] {name}: metadata-record remote-names differ from CSV header of {fname}")
        # Tableau field names = metadata local-names (may differ from the CSV header, e.g. N -> N (not relevant))
        header = [m.findtext("local-name")[1:-1] for m in mrs]
        low = [h.lower() for h in header]
        dups = sorted({h for h in header if low.count(h.lower()) > 1})
        if dups:
            err(f"[{label}] {name}: field names differ only by case {dups}; give one a distinct local-name")
        renamed = [(r, h) for r, h in zip(remote, header) if r != h]
        if renamed:
            notes.append(f"[{label}] {name}: CSV columns exposed under another field name {renamed}")
        cmap = ds.find("connection/cols")
        if renamed and cmap is None:
            err(f"[{label}] {name}: renamed fields need a <cols> map (as Superstore.twb has)")
        if cmap is not None:
            got = {m.get("key"): m.get("value") for m in cmap.findall("map")}
            want = {f"[{h}]": f"[{rel.get('name')}].[{r}]" for r, h in zip(remote, header)}
            if got != want:
                err(f"[{label}] {name}: <cols> map does not match local-name -> [relation].[remote-name]")
        base_cols = {c.get("name")[1:-1] for c in ds.findall("column") if c.find("calculation") is None}
        if base_cols - set(header):
            err(f"[{label}] {name}: <column> names not among local-names: {sorted(base_cols - set(header))}")
        calcs = {}
        for col in ds.findall("column"):
            calc = col.find("calculation")
            if calc is not None:
                calcs[col.get("name")[1:-1]] = calc.get("formula")
        for cid, formula in calcs.items():
            for ref in re.findall(r"\[([^\]]+)\]", formula):
                if ref not in header and ref not in calcs:
                    err(f"[{label}] {name}: calc {cid} references unknown field [{ref}]")
        ds_fields[name] = (set(header), calcs)
        if base_dir is not None:
            p = os.path.normpath(os.path.join(base_dir, directory, fname))
            if not os.path.isfile(p):
                err(f"[{label}] {name}: data file not found at {p}")

    # ---- worksheets
    sheets = {}
    for ws in root.find("worksheets"):
        wname = ws.get("name")
        view = ws.find("table/view")
        dsn = view.find("datasources/datasource").get("name")
        header, calcs = ds_fields[dsn]
        dep = view.find("datasource-dependencies")
        dep_cols = {c.get("name")[1:-1] for c in dep.findall("column")}
        dep_inst = {}
        for ci in dep.findall("column-instance"):
            dep_inst[ci.get("name")] = ci
        used = set()
        blobs = []
        for el in ws.iter():
            for k, v in el.attrib.items():
                if k in ("column", "using", "field", "param", "level") or k == "member":
                    blobs.append(v)
            if el.tag in ("rows", "cols", "column", "run") and el.text:   # run: <[ds].[field]> in titles
                blobs.append(el.text)
        for b in blobs:
            for dsref, d, f, t in REF.findall(b):
                if dsref != dsn:
                    err(f"[{label}] {wname}: reference to other datasource {dsref}")
                used.add((d, f, t))
        for el in view.findall("filter/groupfilter") + view.findall("filter/groupfilter/groupfilter"):
            lvl = el.get("level")
            if lvl:
                m = re.fullmatch(r"\[([a-z]+):([^\]]+):([a-z]{2})\]", lvl)
                used.add((m.group(1), m.group(2), m.group(3)))
        for d, f, t in sorted(used):
            iname = f"[{d}:{f}:{t}]"
            if f not in header and f not in calcs:
                err(f"[{label}] {wname}: field [{f}] not in {dsn} header or calcs")
            if f not in dep_cols:
                err(f"[{label}] {wname}: column [{f}] used but not declared in datasource-dependencies")
            ci = dep_inst.get(iname)
            if ci is None:
                err(f"[{label}] {wname}: column-instance {iname} used but not declared")
            elif ci.get("derivation") != DERIV[d] or ci.get("type") != ITYPE[t] or ci.get("column") != f"[{f}]":
                err(f"[{label}] {wname}: column-instance {iname} has wrong derivation/type/column")
            if f in calcs:
                for ref in re.findall(r"\[([^\]]+)\]", calcs[f]):
                    if ref not in dep_cols:
                        err(f"[{label}] {wname}: calc {f} needs [{ref}] declared in dependencies")
        for ci in dep_inst:
            m = re.fullmatch(r"\[([a-z]+):([^\]]+):([a-z]{2})\]", ci)
            if (m.group(1), m.group(2), m.group(3)) not in used:
                notes.append(f"[{label}] {wname}: declared but unused instance {ci}")
        if not (ws.find("table/rows").text or ws.find("table/cols").text):
            err(f"[{label}] {wname}: both shelves empty")
        mark = ws.find("table/panes/pane/mark").get("class")
        if mark not in ("Bar", "Line", "Circle", "Square", "Automatic", "Area", "Text"):
            err(f"[{label}] {wname}: unusual mark class {mark}")
        sheets[wname] = dsn

    # ---- dashboards & story
    dashes = {}
    dbs = root.find("dashboards")
    if dbs is not None:
        for db in dbs:
            dashes[db.get("name")] = db
        for dname, db in dashes.items():
            ids = [z.get("id") for z in db.iter("zone")]
            if len(ids) != len(set(ids)):
                err(f"[{label}] dashboard {dname}: duplicate zone ids")
            for z in db.iter("zone"):
                n = z.get("name")
                if n is not None and n not in sheets:
                    err(f"[{label}] dashboard {dname}: zone names unknown sheet {n}")
                if z.get("type") == "filter":
                    m = REF.fullmatch(z.get("param", ""))
                    if not m or m.group(1) != sheets.get(n):
                        err(f"[{label}] dashboard {dname}: filter zone param not in sheet's datasource")
                for k in ("x", "y", "w", "h"):
                    v = int(z.get(k))
                    if not 0 <= v <= 100000:
                        err(f"[{label}] dashboard {dname}: zone {z.get('id')} {k}={v} off grid")
                if z.get("type") is None and z.get("name") is None:
                    err(f"[{label}] dashboard {dname}: zone {z.get('id')} has neither type nor name")
            fz = [z for z in db.iter("zone") if z.get("type") == "filter"]
            deps = {(dd.get("datasource"), ci.get("name")) for dd in db.findall("datasource-dependencies")
                    for ci in dd.findall("column-instance")}
            for z in fz:
                m = REF.fullmatch(z.get("param", ""))
                if m and (m.group(1), f"[{m.group(2)}:{m.group(3)}:{m.group(4)}]") not in deps:
                    err(f"[{label}] dashboard {dname}: filter zone field {z.get('param')} not declared in "
                        "dashboard datasource-dependencies")
            for sp in db.iter("story-point"):
                if sp.get("captured-sheet") not in dashes and sp.get("captured-sheet") not in sheets:
                    err(f"[{label}] story {dname}: point refers to unknown {sp.get('captured-sheet')}")
    # ---- windows
    wins = root.find("windows")
    if wins is None:
        err(f"[{label}] no <windows> element")
    else:
        wnames = [w.get("name") for w in wins]
        for n in list(sheets) + list(dashes):
            if wnames.count(n) != 1:
                err(f"[{label}] window count for {n} is {wnames.count(n)}")
        if sum(1 for w in wins if w.get("maximized") == "true") != 1:
            err(f"[{label}] expected exactly one maximized window")
    return root, sheets, dashes, ds_files


def check_package():
    twb_path = os.path.join(HERE, NAME + ".twb")
    twbx_path = os.path.join(HERE, NAME + ".twbx")
    with open(twb_path, "rb") as fh:
        r1 = check_twb("twb", fh.read(), HERE)
    with zipfile.ZipFile(twbx_path) as z:
        names = z.namelist()
        if names[0] != NAME + ".twb":
            err(f"[twbx] first entry is {names[0]}, expected {NAME}.twb at the root")
        inner = z.read(NAME + ".twb")
        r2 = check_twb("twbx", inner, None)
        if r2:
            for dsn, (directory, fname) in r2[3].items():
                if directory != "Data/16_tableau":
                    err(f"[twbx] {dsn}: directory {directory!r} is not Data/16_tableau")
                entry = f"{directory}/{fname}"
                if entry not in names:
                    err(f"[twbx] missing {entry}")
                else:
                    with open(os.path.join(EXTRACTS, fname), "rb") as fh:
                        if z.read(entry) != fh.read():
                            err(f"[twbx] {entry} differs from outputs/16_tableau/{fname}")
            extra = set(names) - {NAME + ".twb"} - {f"{d}/{f}" for d, f in r2[3].values()}
            if extra:
                err(f"[twbx] unexpected entries {sorted(extra)}")
        if z.testzip() is not None:
            err("[twbx] zip CRC error")
    if r1 and r2:
        if set(r1[1]) != set(r2[1]) or set(r1[2]) != set(r2[2]):
            err("twb and twbx differ in sheets/dashboards")
    return r2


# ---------------------------------------------------------------- expected values
def pct(x, nd=2):
    return f"{100 * x:.{nd}f}%"


def expected_values() -> str:
    E = lambda f: pd.read_csv(os.path.join(EXTRACTS, f), low_memory=False)
    L = ["# Expected values for the Tableau GUI check", "",
         "*Generated by `tableau/validate_twb.py` from `outputs/16_tableau/*.csv` with the same filters each "
         "worksheet uses. Compare these with what Tableau shows (hover a mark or read the label).*", ""]

    d = E("r1_daily_by_community.csv")
    c = d[(d.kind == "comments") & (d.in_shared_window == 1)]
    g = c.groupby("subreddit")[["facet_layoffs", "records", "bot_records"]].sum()
    g["share"] = g.facet_layoffs / (g.records - g.bot_records)
    L += ["## R1a Weekly layoff share (filters: kind = comments, in_shared_window = 1)", "",
          "Window totals (not shown on the weekly line; check by removing week_start from Columns):", "",
          "| subreddit | layoff comments | records | bot records | share |", "|---|---:|---:|---:|---:|"]
    for s, r in g.iterrows():
        L.append(f"| {s} | {int(r.facet_layoffs):,} | {int(r.records):,} | {int(r.bot_records):,} | {pct(r.share)} |")
    w = c.groupby(["week_start", "subreddit"])[["facet_layoffs", "records", "bot_records"]].sum()
    w["share"] = w.facet_layoffs / (w.records - w.bot_records)
    p = w.share.unstack()
    L += ["", "Spot checks (hover these points):", "", "| week_start | cscareerquestions | technology | programming |",
          "|---|---:|---:|---:|"]
    for wk in ["2025-04-21", "2025-05-12", "2025-05-19"]:
        r = p.loc[wk]
        L.append(f"| {wk} | {pct(r['cscareerquestions'])} | {pct(r['technology'])} | {pct(r['programming'])} |")
    both = p.dropna(subset=["technology"])
    L += ["", f"- Weeks on the line: {len(p)} (first {p.index.min()}, last {p.index.max()}; the first and last "
          "weeks are partial because the window cuts them).",
          f"- cscq above r/technology in {(both['cscareerquestions'] > both['technology']).sum()} of {len(both)} "
          "weeks where both have data. r/technology's line stops at week 2025-06-09.",
          f"- Top week cscq: {p['cscareerquestions'].idxmax()} ({pct(p['cscareerquestions'].max())}); "
          f"r/technology: {p['technology'].idxmax()} ({pct(p['technology'].max())}); "
          f"r/programming: {p['programming'].idxmax()} ({pct(p['programming'].max())}).", ""]

    t = E("r1_threads.csv")
    t = t[t.in_shared_window == 1]
    tb = t.groupby(["size_band", "subreddit"]).has_layoff_talk.agg(["mean", "count"]).reset_index()
    order = {"1-9": 1, "10-49": 2, "50-199": 3, "200-999": 4, "1000+": 5}
    tb["o"] = tb.size_band.map(order)
    L += ["## R1b Threads with layoff talk (filter: in_shared_window = 1)", "",
          "| thread size | subreddit | threads | share with layoff talk |", "|---|---|---:|---:|"]
    for _, r in tb.sort_values(["o", "subreddit"]).iterrows():
        L.append(f"| {r.size_band} | {r.subreddit} | {r['count']:,} | {pct(r['mean'], 1)} |")
    L.append("")

    m = E("r2_marker_rates_long.csv")
    m = m[(m.base == "employment_core") & (m.in_shared_window == 1)]
    mg = m.groupby(["marker", "subreddit"])[["hits", "base_comments"]].sum()
    mg["rate"] = mg.hits / mg.base_comments
    mr = mg.rate.unstack()
    L += ["## R2a Marker rates (filters: base = employment_core, in_shared_window = 1)", "",
          "| marker | cscareerquestions | technology | programming |", "|---|---:|---:|---:|"]
    for mk, r in mr.iterrows():
        L.append(f"| {mk} | {pct(r['cscareerquestions'], 1)} | {pct(r['technology'], 1)} | "
                 f"{pct(r['programming'], 1)} |")
    base = m.drop_duplicates(["subreddit", "month"]).groupby("subreddit").base_comments.sum()
    L += ["", "Base comments (Jan-Jun 2025): " + ", ".join(f"{k} {v:,}" for k, v in base.items()), ""]

    x = E("r2_cross_posters_same_author.csv")
    xa = x.groupby("subreddit")[["rate_mentions_execs", "rate_mentions_ai"]].mean()
    L += ["## R2b Same authors, two communities (no filter)", "",
          f"Authors: {x.author_id.nunique()} (rows {len(x)}). Each bar should carry only its own number "
          "(mark labels, no text encoding).", "",
          "| subreddit | AVG rate_mentions_execs | AVG rate_mentions_ai |", "|---|---:|---:|"]
    for s, r in xa.iterrows():
        L.append(f"| {s} | {pct(r.rate_mentions_execs)} | {pct(r.rate_mentions_ai)} |")
    L.append("")

    lf = E("r3_reply_type_lift.csv")
    piv = lf.pivot(index="parent_type", columns="reply_type", values="lift_vs_none")
    L += ["## R3 Reply-type lift (no filter; colour centred on 1)", "",
          "| parent_type | " + " | ".join(piv.columns) + " |", "|---|" + "---:|" * len(piv.columns)]
    for pt, r in piv.iterrows():
        L.append(f"| {pt} | " + " | ".join(f"{v:.3f}" for v in r) + " |")
    e = lf[(lf.parent_type == "experience") & (lf.reply_type == "sympathy")].iloc[0]
    n = lf[(lf.parent_type == "none") & (lf.reply_type == "sympathy")].iloc[0]
    L += ["", f"Headline: experience -> sympathy {e.pct:.2f}% vs none {n.pct:.2f}% = x{e.lift_vs_none:.3f} "
          f"(replies {e.replies:,} vs {n.replies:,}). Reply pairs in total: {lf.groupby('parent_type').replies.first().sum():,}"
          " (parent types overlap, so this can exceed 91,229).", ""]

    f = E("r4_type_flows.csv")
    fa = f[f.reply_function == "all"].pivot(index="replier_type", columns="parent_author_type",
                                            values="lift_vs_random_mixing")
    L += ["## R4a Who replies to whom (filter: reply_function = all)", "",
          "Rows = replier type, columns = parent-author type.", "",
          "| replier \\ parent | " + " | ".join(fa.columns) + " |", "|---|" + "---:|" * len(fa.columns)]
    for rt, r in fa.iterrows():
        L.append(f"| {rt} | " + " | ".join(f"{v:.3f}" for v in r) + " |")
    L.append("")

    ce = E("r4_centrality_by_type.csv")
    cp = ce[(ce.measure == "pagerank") & (~ce.type.str.contains("minus"))].sort_values("median", ascending=False)
    L += ["## R4b Centrality by type (filters: measure = pagerank, type = the 5 types)", "",
          "| type | n | median | 95% CI |", "|---|---:|---:|---|"]
    for _, r in cp.iterrows():
        L.append(f"| {r.type} | {r.n:,} | {r['median']:.3f} | {r.ci95_lo:.3f} to {r.ci95_hi:.3f} |")
    L.append("")

    nd = E("r4_network_core_nodes.csv")
    L += ["## R4c Network position map (no filter)", "",
          f"Nodes: {len(nd):,}. By type: " + ", ".join(f"{k} {v}" for k, v in nd.type.value_counts().items()) + ".",
          f"x range {nd.x.min():.3f} to {nd.x.max():.3f}; y range {nd.y.min():.3f} to {nd.y.max():.3f}; "
          f"largest pagerank {nd.pagerank.max():.3f} (node {nd.loc[nd.pagerank.idxmax(), 'node_id']}); "
          f"median {nd.pagerank.median():.3f}.",
          f"Circle size = calc 'Size (sqrt pagerank)' = SQRT(SUM([pagerank])): largest "
          f"{nd.pagerank.max() ** 0.5:.2f}, median {nd.pagerank.median() ** 0.5:.2f} "
          f"(ratio {(nd.pagerank.max() / nd.pagerank.median()) ** 0.5:.1f}x instead of "
          f"{nd.pagerank.max() / nd.pagerank.median():.1f}x).", ""]

    cv = d[d.kind == "comments"]
    cov = cv.groupby("subreddit").agg(first=("date", "min"), last=("date", "max"), records=("records", "sum"))
    L += ["## R5a Coverage (filter: kind = comments, all months)", "",
          "| subreddit | first day | last day | comments |", "|---|---|---|---:|"]
    for s, r in cov.iterrows():
        L.append(f"| {s} | {r['first']} | {r['last']} | {int(r.records):,} |")
    L += ["", f"All comments: {cv.records.sum():,}; posts rows: {d[d.kind == 'posts'].records.sum():,} "
          "(cscq has no posts).", ""]

    pr = E("r5_marker_precision.csv").sort_values("precision_R_percent", ascending=False)
    L += ["## R5b Marker precision (no filter, sorted descending)", "",
          "The CSV column N appears in Tableau as the field `N (not relevant)` (it would otherwise clash with n).", "",
          "| screen | n | R | P | N (not relevant) | precision (R %) |", "|---|---:|---:|---:|---:|---:|"]
    for _, r in pr.iterrows():
        L.append(f"| {r.group} | {r.n} | {r.R} | {r.P} | {r.N} | {r.precision_R_percent:.1f} |")
    L.append("")

    rb = E("r5_robustness_long.csv")
    rs = rb[rb.statistic == "lift_blame-talker->blame-talker"]
    short = {
        "top 1% threads (>= 305 comments, 112 threads, 18.3% of comments)": "top 1% threads dropped",
        "drop 10% of hits + add missed hits = 0% of observed (10 reps)": "noise: drop 10%",
        "drop 25% of hits + add missed hits = 0% of observed (10 reps)": "noise: drop 25%",
        "drop 0% of hits + add missed hits = 25% of observed (10 reps)": "noise: add 25%",
        "drop 0% of hits + add missed hits = 50% of observed (10 reps)": "noise: add 50%",
        "drop 25% of hits + add missed hits = 25% of observed (10 reps)": "noise: drop 25% + add 25%",
    }
    L += ["## R5c Robustness (filter: statistic = lift_blame-talker->blame-talker)", "",
          "Row labels use the calc 'Variant (short)'; the full variant text is in the tooltip.", "",
          "| check | Variant (short) | full variant | value | lo | hi |", "|---|---|---|---:|---:|---:|"]
    for _, r in rs.iterrows():
        lo = "" if pd.isna(r.lo) else f"{r.lo:.4f}"
        hi = "" if pd.isna(r.hi) else f"{r.hi:.4f}"
        L.append(f"| {r.check} | {short.get(r.variant, r.variant)} | {r.variant} | {r.value:.4f} | {lo} | {hi} |")
    L += ["", f"Minimum across checks: {rs.value.min():.4f} (all above 1: {bool((rs.value > 1).all())}).", ""]
    return "\n".join(L)


def main():
    r = check_package()
    if r:
        print(f"worksheets: {len(r[1])}, dashboards+story: {len(r[2])}, datasources: {len(r[3])}")
    md = expected_values()
    out = os.path.join(HERE, "EXPECTED_VALUES.md")
    with open(out + ".tmp", "w", encoding="utf-8") as fh:
        fh.write(md)
    os.replace(out + ".tmp", out)
    print(f"wrote {out}")
    for n in notes:
        print("note:", n)
    if errors:
        print(f"FAIL: {len(errors)} problem(s)")
        for e in errors:
            print("  -", e)
        return 1
    print("PASS: all structural checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
