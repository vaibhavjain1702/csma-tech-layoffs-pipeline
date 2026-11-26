#!/usr/bin/env python3
"""Build the CSMA Tableau workbook (.twb + .twbx) from the extracts in outputs/16_tableau.

Deterministic generator: same inputs give byte-identical outputs. Tableau is never opened.

Usage (from anywhere):
    PYTHONDONTWRITEBYTECODE=1 python3 -B tableau/build_workbook.py
    ... --no-story                 skip the Story (stretch goal) if Tableau rejects it
    ... --no-dashboards            worksheets only
    ... --only R1a,R3              keep only these worksheets (dashboards/story that need others are dropped)
    ... --skip R4b                 drop these worksheets
    ... --out-dir DIR --name NAME  write somewhere else (for bisecting a load error)
    ... --dash-size fixed          dashboards fixed at 1366x768 instead of automatic
    ... --zone-attr type-v2        newer zone dialect (type-v2= + format manifest), if type= is rejected

Format notes. The XML follows the "legacy" dialect of the workbook that Tableau Desktop itself ships
(install/Performance/PerformanceRecording_new.twb, version 18.1): plain <relation>, zone type='...',
no document-format-change-manifest. The textscan (CSV) connection attributes follow the Superstore
sample. Tableau upgrades the file silently when it is saved.

Outputs:
  tableau/CSMA_Solidarity_or_Blame.twb   reads the CSVs from ../outputs/16_tableau (relative)
  tableau/CSMA_Solidarity_or_Blame.twbx  zip: the .twb at its root + Data/16_tableau/<csv> (open this one)
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import zipfile
import xml.etree.ElementTree as ET

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.dirname(HERE)
EXTRACTS = os.path.join(ARCH, "outputs", "16_tableau")
NAME = "CSMA_Solidarity_or_Blame"
TWB_DIR_STANDALONE = "../outputs/16_tableau"   # relative to tableau/
TWB_DIR_PACKAGED = "Data/16_tableau"           # relative to the .twbx root
ZIP_TIME = (2026, 11, 26, 0, 0, 0)

USER_NS = "http://www.tableausoftware.com/xml/user"
ET.register_namespace("user", USER_NS)
U = "{%s}" % USER_NS

# ---------------------------------------------------------------- palette (shared with Gephi)
# Tableau 2026.3 ignores the datasource palette maps below and assigns its default Tableau 10 colours
# alphabetically per field, so the dashboard colour keys use those same colours (checked in the app).
SUB_COLORS = {"cscareerquestions": "#4e79a7", "programming": "#f28e2b", "technology": "#e15759"}
# R4c network map: its 4 types in alphabetical order get Tableau 10 blue, orange, red, teal
TYPE_COLORS = {"blame-talker": "#4e79a7", "helper": "#f28e2b", "other": "#e15759", "story-sharer": "#76b7b2"}
DIVERGING = "orange_blue_diverging_10_0"   # orange below centre, blue above; colour-blind safe
FIVE_TYPES = ["story-sharer", "blame-talker", "helper", "other", "low-activity"]

# ---------------------------------------------------------------- data sources
# key -> (csv file, caption, {column: forced (datatype, role, type)}, palette field or None)
DATE_COLS = {"date", "week_start"}
DIM_INT_COLS = {"in_shared_window"}   # integer flags used as filters -> discrete dimension

DATASOURCES = {
    "r1_daily": ("r1_daily_by_community.csv", "R1/R5 daily volume by community", "subreddit"),
    "r1_threads": ("r1_threads.csv", "R1 threads", "subreddit"),
    "r2_rates": ("r2_marker_rates_long.csv", "R2 marker rates (long)", "subreddit"),
    "r2_cross": ("r2_cross_posters_same_author.csv", "R2 cross-posters (same author)", "subreddit"),
    "r3_lift": ("r3_reply_type_lift.csv", "R3 reply-type lift", None),
    "r4_flows": ("r4_type_flows.csv", "R4 type flows", None),
    "r4_cent": ("r4_centrality_by_type.csv", "R4 centrality by type", "type"),
    "r4_nodes": ("r4_network_core_nodes.csv", "R4 network core nodes", "type"),
    "r5_prec": ("r5_marker_precision.csv", "R5 marker precision", None),
    "r5_rob": ("r5_robustness_long.csv", "R5 robustness (long)", None),
}

# Calculated fields: ds -> list of (id, caption, datatype, role, type, formula, default_format)
CALCS = {
    "r1_daily": [
        ("Calculation_1001000000000001", "Layoff share (non-bot)", "real", "measure", "quantitative",
         "SUM([facet_layoffs]) / (SUM([records]) - SUM([bot_records]))", "p0.00%"),
    ],
    "r1_threads": [
        ("Calculation_1002000000000001", "Thread size", "string", "dimension", "nominal",
         'CASE [size_band] WHEN "1-9" THEN "1) 1-9 comments" WHEN "10-49" THEN "2) 10-49" '
         'WHEN "50-199" THEN "3) 50-199" WHEN "200-999" THEN "4) 200-999" '
         'WHEN "1000+" THEN "5) 1000+" ELSE [size_band] END', None),
        ("Calculation_1002000000000002", "Share of threads with layoff talk", "real", "measure",
         "quantitative", "AVG([has_layoff_talk])", "p0.0%"),
    ],
    "r2_rates": [
        ("Calculation_1003000000000001", "Marker rate", "real", "measure", "quantitative",
         "SUM([hits]) / SUM([base_comments])", "p0.0%"),
    ],
    "r4_cent": [
        ("Calculation_1004000000000001", "Median (95% CI)", "string", "measure", "nominal",
         'STR(ROUND(SUM([median]), 3)) + " (" + STR(ROUND(SUM([ci95_lo]), 3)) + " to " '
         '+ STR(ROUND(SUM([ci95_hi]), 3)) + ")"', None),
    ],
    "r4_nodes": [
        # one node is ~30x the median pagerank; the square root keeps it from covering its neighbours
        ("Calculation_1005000000000001", "Size (sqrt pagerank)", "real", "measure", "quantitative",
         "SQRT(SUM([pagerank]))", None),
    ],
    "r5_rob": [
        # short row labels; any variant not listed keeps its full text
        ("Calculation_1006000000000001", "Variant (short)", "string", "dimension", "nominal",
         'CASE [variant] '
         'WHEN "top 1% threads (>= 305 comments, 112 threads, 18.3% of comments)" THEN "top 1% threads dropped" '
         'WHEN "drop 10% of hits + add missed hits = 0% of observed (10 reps)" THEN "noise: drop 10%" '
         'WHEN "drop 25% of hits + add missed hits = 0% of observed (10 reps)" THEN "noise: drop 25%" '
         'WHEN "drop 0% of hits + add missed hits = 25% of observed (10 reps)" THEN "noise: add 25%" '
         'WHEN "drop 0% of hits + add missed hits = 50% of observed (10 reps)" THEN "noise: add 50%" '
         'WHEN "drop 25% of hits + add missed hits = 25% of observed (10 reps)" THEN "noise: drop 25% + add 25%" '
         'ELSE [variant] END', None),
    ],
}
# CSV columns that get a different Tableau field name (remote-name stays the CSV header).
# r5_marker_precision.csv has both "n" (sampled) and "N" (read as not relevant); Tableau field names
# may be compared without case, so N becomes its own name. The CSV is not touched.
LOCAL_NAMES = {"r5_prec": {"N": "N (not relevant)"}}


def local_name(ds: str, col: str) -> str:
    return LOCAL_NAMES.get(ds, {}).get(col, col)
CALC_BY_CAPTION = {c[1]: (ds, c[0]) for ds, cl in CALCS.items() for c in cl}
LAYOFF_SHARE = CALCS["r1_daily"][0][0]
SIZE_ORDERED = CALCS["r1_threads"][0][0]
THREAD_SHARE = CALCS["r1_threads"][1][0]
MARKER_RATE = CALCS["r2_rates"][0][0]
CI_LABEL = CALCS["r4_cent"][0][0]
NODE_SIZE = CALCS["r4_nodes"][0][0]
VARIANT_SHORT = CALCS["r5_rob"][0][0]

REMOTE_TYPE = {"integer": "20", "real": "5", "string": "129", "date": "133"}
DERIV = {"none": "None", "sum": "Sum", "avg": "Avg", "usr": "User", "attr": "Attribute"}
ITYPE = {"nk": "nominal", "ok": "ordinal", "qk": "quantitative"}


def read_schema(csv_path: str) -> list[tuple[str, str]]:
    """(column, tableau datatype) in file order, from the full file so ints with gaps become real."""
    df = pd.read_csv(csv_path, low_memory=False)
    out = []
    for c in df.columns:
        if c in DATE_COLS:
            t = "date"
        elif pd.api.types.is_integer_dtype(df[c]):
            t = "integer"
        elif pd.api.types.is_float_dtype(df[c]):
            t = "real"
        else:
            t = "string"
        out.append((c, t))
    return out


def col_role(name: str, dtype: str) -> tuple[str, str]:
    if name in DIM_INT_COLS:
        return "dimension", "ordinal"
    if dtype == "date":
        return "dimension", "ordinal"
    if dtype == "string":
        return "dimension", "nominal"
    return "measure", "quantitative"


def inst(deriv: str, field: str, t: str) -> str:
    return f"[{deriv}:{field}:{t}]"


def sub(parent, tag, attrib=None, text=None):
    e = ET.SubElement(parent, tag, attrib or {})
    if text is not None:
        e.text = text
    return e


# ---------------------------------------------------------------- worksheet specs
def F(field, members, mode="checkdropdown", deriv="none", t="nk"):
    """Categorical filter keeping only `members` (strings are quoted, ints are not)."""
    return {"inst": (deriv, field, t), "members": members, "mode": mode}


SHEETS = [
    {
        "name": "R1a Weekly layoff share",
        "key": "R1a", "ds": "r1_daily", "mark": "Line",
        "title": "cscq's layoff share beats r/technology's in all 24 weeks where both have data (2.45% vs 0.20%, Jan-Jun 2025)",
        "caveat": "Comments only, Jan-Jun 2025 (shared window). Share = layoff comments / non-bot comments. "
                  "Keyword marker, not yet human-checked. First and last weeks are partial.",
        "cols": [("none", "week_start", "qk")],
        "rows": [("usr", LAYOFF_SHARE, "qk")],
        "color": ("none", "subreddit", "nk"),
        "tooltip": [("sum", "facet_layoffs", "qk"), ("sum", "records", "qk"), ("sum", "bot_records", "qk")],
        "filters": [F("kind", ["comments"]), F("in_shared_window", [1], t="ok")],
    },
    {
        "name": "R1b Threads with layoff talk",
        "key": "R1b", "ds": "r1_threads", "mark": "Bar",
        "title": "cscq threads of every size are far more likely to contain layoff talk",
        "caveat": "Share of threads with at least one layoff comment, by thread size. Threads that started "
                  "Jan-Jun 2025. Bigger threads are more likely to contain any keyword.",
        "rows": [("none", SIZE_ORDERED, "nk"), ("none", "subreddit", "nk")],
        "cols": [("usr", THREAD_SHARE, "qk")],
        "color": ("none", "subreddit", "nk"),
        "text": [("usr", THREAD_SHARE, "qk")],
        "tooltip": [("sum", "has_layoff_talk", "qk")],
        "filters": [F("in_shared_window", [1], t="ok")],
    },
    {
        "name": "R2a Marker rates by community",
        "key": "R2a", "ds": "r2_rates", "mark": "Bar",
        "title": "How each community frames employment talk: marker rates",
        "caveat": "Base = employment_core comments, Jan-Jun 2025. Rate = SUM(hits)/SUM(base). Topic "
                  "markers, not stance; a comment can carry several markers.",
        "rows": [("none", "marker", "nk")],
        "cols": [("none", "subreddit", "nk"), ("usr", MARKER_RATE, "qk")],
        "color": ("none", "subreddit", "nk"),
        "text": [("usr", MARKER_RATE, "qk")],
        "tooltip": [("sum", "hits", "qk"), ("sum", "base_comments", "qk")],
        "filters": [F("base", ["employment_core"], mode="dropdown"), F("in_shared_window", [1], t="ok")],
    },
    {
        "name": "R2b Same authors two communities",
        "key": "R2b", "ds": "r2_cross", "mark": "Bar",
        "title": "Same people, two communities: the exec-mention gap vanishes, the AI gap stays",
        "caveat": "152 authors active in both cscq and r/technology (Jan-Jun 2025). Mean of per-author "
                  "rates. 152 here vs 160 in D1 (career_transition-only comments excluded).",
        "rows": [("none", "subreddit", "nk")],
        "cols": [("avg", "rate_mentions_execs", "qk"), ("avg", "rate_mentions_ai", "qk")],
        "color": ("none", "subreddit", "nk"),
        # no text encodings: with two measures on one pane each bar would carry both numbers;
        # "labels" switches on mark labels so every bar shows only its own measure
        "labels": True,
        "tooltip": [("sum", "employment_comments", "qk")],
        "filters": [],
    },
    {
        "name": "R3 Reply-type lift",
        "key": "R3", "ds": "r3_lift", "mark": "Square",
        "title": "Personal layoff stories get 2.8x more sympathy replies than unmarked comments",
        "caveat": "cscq, all months (91,229 human reply pairs). Lift vs unmarked ('none') comments; blue > 1 > "
                  "orange. Jan-Jun 2025 alone: 2.29x. Markers not yet human-checked.",
        "rows": [("none", "parent_type", "nk")],
        "cols": [("none", "reply_type", "nk")],
        "color": ("sum", "lift_vs_none", "qk"),
        "text": [("sum", "lift_vs_none", "qk")],
        "tooltip": [("sum", "pct", "qk"), ("sum", "replies", "qk"), ("sum", "hits", "qk")],
        "diverging": {"field": ("sum", "lift_vs_none", "qk"), "min": "0.0", "max": "2.0", "center": "1.0"},
        "filters": [],
    },
    {
        "name": "R4a Who replies to whom",
        "key": "R4a", "ds": "r4_flows", "mark": "Square",
        "title": "Blame-talkers reply to each other 1.7x more than random mixing predicts",
        "caveat": "cscq reply network, Jan-Jun 2025, largest component. Rows = replier type, columns = "
                  "type of the author replied to. Lift vs random mixing; blue > 1 > orange.",
        "rows": [("none", "replier_type", "nk")],
        "cols": [("none", "parent_author_type", "nk")],
        "color": ("sum", "lift_vs_random_mixing", "qk"),
        "text": [("sum", "lift_vs_random_mixing", "qk")],
        "tooltip": [("sum", "replies", "qk")],
        "diverging": {"field": ("sum", "lift_vs_random_mixing", "qk"), "min": "0.5", "max": "1.5",
                      "center": "1.0"},
        "filters": [F("reply_function", ["all"], mode="dropdown")],
    },
    {
        "name": "R4b Centrality by author type",
        "key": "R4b", "ds": "r4_cent", "mark": "Circle",
        "title": "Story-sharers and blame-talkers sit more central than 'other' authors (measure: <[federated.r4_cent].[none:measure:nk]>)",
        "caveat": "Median per type with bootstrap 95% CI in the label. Choose the measure with the filter "
                  "(default pagerank). Differences shrink once activity is held equal (N1).",
        "rows": [("none", "type", "nk")],
        "cols": [("sum", "median", "qk")],
        "color": ("none", "type", "nk"),
        "text": [("usr", CI_LABEL, "nk")],
        "tooltip": [("sum", "ci95_lo", "qk"), ("sum", "ci95_hi", "qk"), ("sum", "n", "qk")],
        "filters": [F("measure", ["pagerank"], mode="dropdown"), F("type", FIVE_TYPES)],
        "sort": {"inst": ("none", "type", "nk"), "using": ("sum", "median", "qk"), "direction": "DESC"},
    },
    {
        "name": "R4c Network position map",
        "key": "R4c", "ds": "r4_nodes", "mark": "Circle",
        "title": "Network core: 1,500 most connected cscq authors, coloured by type",
        "caveat": "Force-directed x/y from the network step; size = square root of pagerank; edges omitted. Types are "
                  "keyword-based author profiles (>=5 comments).",
        "cols": [("sum", "x", "qk")],
        "rows": [("sum", "y", "qk")],
        "color": ("none", "type", "nk"),
        "size": ("usr", NODE_SIZE, "qk"),
        "tooltip": [("sum", "pagerank", "qk"), ("sum", "comments", "qk"), ("sum", "degree_in_core", "qk")],
        "lod": [("none", "node_id", "nk")],
        "filters": [],
    },
    {
        "name": "R5a Coverage over time",
        "key": "R5a", "ds": "r1_daily", "mark": "Line",
        "title": "Coverage differs: r/technology comments stop Jun 2025, r/programming Dec 2025",
        "caveat": "Comments collected per week (sum of daily counts), all months. cscq runs to Sep 2026 and has no posts. "
                  "Compare communities only inside Jan-Jun 2025.",
        "cols": [("none", "week_start", "qk")],
        "rows": [("sum", "records", "qk")],
        "color": ("none", "subreddit", "nk"),
        "tooltip": [("sum", "bot_records", "qk"), ("sum", "text_deleted_or_removed", "qk")],
        "filters": [F("kind", ["comments"])],
    },
    {
        "name": "R5b Marker precision",
        "key": "R5b", "ds": "r5_prec", "mark": "Bar",
        "title": "Screen precision (provisional): layoffs 95%, restructuring/policy 70-75%, rest under 30%",
        "caveat": "Share of sampled hits read as relevant by one reader; n = 20-40 per screen. "
                  "Provisional until the human label check is finished.",
        "rows": [("none", "group", "nk")],
        "cols": [("sum", "precision_R_percent", "qk")],
        "text": [("sum", "precision_R_percent", "qk")],
        # CSV column N is exposed as [N (not relevant)] (see LOCAL_NAMES) so it cannot clash with [n];
        # it is left off the view (N = n - R - P) so a problem with the rename cannot break this sheet
        "tooltip": [("sum", "n", "qk"), ("sum", "R", "qk"), ("sum", "P", "qk")],
        "filters": [],
        "sort": {"inst": ("none", "group", "nk"), "using": ("sum", "precision_R_percent", "qk"),
                 "direction": "DESC"},
    },
    {
        "name": "R5c Robustness of a headline",
        "key": "R5c", "ds": "r5_rob", "mark": "Circle",
        "title": "Robustness of <[federated.r5_rob].[none:statistic:nk]> (default: blame-talker clustering, lift 1.69)",
        "caveat": "One statistic at a time (filter). This statistic has 11 rows (observed, megathreads dropped, label "
                  "noise, threshold N); min = 1.28. Null-shuffle and activity checks use other statistics. Hover for the full variant text.",
        "rows": [("none", "check", "nk"), ("none", VARIANT_SHORT, "nk")],
        "cols": [("avg", "value", "qk")],
        "text": [("avg", "value", "qk")],
        "tooltip": [("avg", "lo", "qk"), ("avg", "hi", "qk"), ("attr", "variant", "nk")],
        "filters": [F("statistic", ["lift_blame-talker->blame-talker"], mode="dropdown")],
    },
]
DASHBOARDS = [
    {"name": "1 Where disruption talk lives",
     "title": "1. Where disruption talk lives (R1)",
     "note": "cscareerquestions carries most of the layoff talk: 2.45% of non-bot comments vs 0.20% "
             "(r/technology) and 0.32% (r/programming), Jan-Jun 2025. Its threads of every size carry more layoff talk.",
     "legend": "sub",
     "grid": [("R1a", 0, 0, 60000, 50000), ("R5a", 0, 50000, 60000, 50000), ("R1b", 60000, 0, 40000, 100000)],
     "filters": []},
    {"name": "2 How communities frame it",
     "title": "2. How communities frame it (R2)",
     "note": "Rates of topic markers in employment comments. For the same 152 people the exec-mention gap "
             "disappears, but AI mentions stay higher on r/technology.",
     "legend": "sub",
     "grid": [("R2a", 0, 0, 58000, 100000), ("R2b", 58000, 0, 42000, 100000)],
     "filters": []},
    {"name": "3 Who replies to whom",
     "title": "3. Who replies to whom (R3, R4)",
     "note": "Stories draw sympathy (x2.82); blame-talkers cluster together (x1.69). Colour scales are "
             "centred on lift = 1 (blue above, orange below).",
     "legend": "type",
     "grid": [("R3", 0, 0, 50000, 56000), ("R4a", 50000, 0, 50000, 56000),
              ("R4c", 0, 56000, 100000, 44000)],
     "filters": []},
    {"name": "4 Can we trust the numbers",
     "title": "4. Can we trust the numbers (R5)",
     "note": "Coverage differs by community, so comparisons use Jan-Jun 2025 only. Keyword screens are "
             "provisional (one reader). Blame-talker clustering stays above 1 under label noise, thresholds, megathread removal.",
     "legend": "sub",
     "grid": [("R5a", 0, 0, 45000, 44000), ("R5b", 45000, 0, 55000, 44000), ("R5c", 0, 44000, 100000, 56000)],
     "filters": [("R5c", ("none", "statistic", "nk"), "dropdown")]},
]
STORY = {"name": "Solidarity or Blame (story)",
         "title": "Solidarity or Blame: how Reddit communities discuss disruption in tech employment",
         "points": [
             ("1 Where disruption talk lives", "R1: layoff talk lives in cscareerquestions (2.45% vs 0.20%)"),
             ("2 How communities frame it", "R2: same people, different frames; the AI gap persists"),
             ("3 Who replies to whom", "R3/R4: stories get sympathy, blame-talkers cluster"),
             ("4 Can we trust the numbers", "R5: coverage, precision and robustness caveats"),
         ]}


# ---------------------------------------------------------------- builders
CTX: list = []


class Ctx:
    def __init__(self, directory: str):
        self.directory = directory
        self.schemas = {k: read_schema(os.path.join(EXTRACTS, v[0])) for k, v in DATASOURCES.items()}

    def dtype(self, ds, field):
        for c, t in self.schemas[ds]:
            if local_name(ds, c) == field:
                return t
        for cid, cap, dt, *_ in CALCS.get(ds, []):
            if cid == field:
                return dt
        raise KeyError(f"{ds}: unknown field {field}")


def column_el(parent, ctx: Ctx, ds: str, field: str):
    """Declare a base or calculated column (with its calculation)."""
    for cid, cap, dt, role, typ, formula, fmt in CALCS.get(ds, []):
        if cid == field:
            a = {"caption": cap, "datatype": dt}
            if fmt:
                a["default-format"] = fmt
            a.update({"name": f"[{cid}]", "role": role, "type": typ})
            c = sub(parent, "column", a)
            sub(c, "calculation", {"class": "tableau", "formula": formula})
            return
    dt = ctx.dtype(ds, field)
    role, typ = col_role(field, dt)
    a = {}
    if dt in ("integer", "real") and role == "measure":
        a["aggregation"] = "Sum"
    a["datatype"] = dt
    if field.startswith("rate_"):
        a["default-format"] = "p0.0%"
    a.update({"name": f"[{field}]", "role": role, "type": typ})
    sub(parent, "column", a)


def calc_refs(ds, field):
    import re
    for cid, *_rest in CALCS.get(ds, []):
        if cid == field:
            return re.findall(r"\[([^\]]+)\]", _rest[4])
    return []


def build_datasource(parent, ctx: Ctx, key: str):
    csv, caption, palette_field = DATASOURCES[key]
    stem = csv[:-4]
    ds = sub(parent, "datasource", {"caption": caption, "inline": "true", "name": f"federated.{key}",
                                     "version": "18.1"})
    conn = sub(ds, "connection", {"class": "federated"})
    ncs = sub(conn, "named-connections")
    nc = sub(ncs, "named-connection", {"caption": stem, "name": f"textscan.{key}"})
    sub(nc, "connection", {"class": "textscan", "directory": ctx.directory, "filename": csv,
                           "password": "", "server": ""})
    rel = sub(conn, "relation", {"connection": f"textscan.{key}", "name": csv, "table": f"[{stem}#csv]",
                                 "type": "table"})
    cols = sub(rel, "columns", {"character-set": "UTF-8", "header": "yes", "locale": "en_US", "separator": ","})
    for i, (c, t) in enumerate(ctx.schemas[key]):
        sub(cols, "column", {"datatype": t, "name": c, "ordinal": str(i)})
    if key in LOCAL_NAMES:
        # a field whose name differs from its CSV column needs the explicit map, as in Superstore.twb
        # ([Region (People)] -> [People].[Region]); maps are written for every column, sorted by key
        cm = sub(conn, "cols")
        for c, _t in sorted(ctx.schemas[key], key=lambda x: local_name(key, x[0])):
            sub(cm, "map", {"key": f"[{local_name(key, c)}]", "value": f"[{csv}].[{c}]"})
    mrs = sub(conn, "metadata-records")
    for i, (c, t) in enumerate(ctx.schemas[key]):
        mr = sub(mrs, "metadata-record", {"class": "column"})
        sub(mr, "remote-name", text=c)
        sub(mr, "remote-type", text=REMOTE_TYPE[t])
        sub(mr, "local-name", text=f"[{local_name(key, c)}]")
        sub(mr, "parent-name", text=f"[{csv}]")
        sub(mr, "remote-alias", text=c)
        sub(mr, "ordinal", text=str(i))
        sub(mr, "local-type", text=t)
        sub(mr, "aggregation", text={"string": "Count", "date": "Year"}.get(t, "Sum"))
        if t == "string":
            sub(mr, "scale", text="1")
            sub(mr, "width", text="1073741823")
        sub(mr, "contains-null", text="true")
        if t == "string":
            sub(mr, "collation", {"flag": "0", "name": "LEN_RUS"})
    sub(ds, "aliases", {"enabled": "yes"})
    names = sorted({local_name(key, c) for c, _ in ctx.schemas[key]} | {c[0] for c in CALCS.get(key, [])})
    for n in names:
        # base columns get explicit roles; calcs carry their formula
        column_el(ds, ctx, key, n)
    sub(ds, "layout", {"dim-ordering": "alphabetic", "dim-percentage": "0.5", "measure-ordering": "alphabetic",
                       "measure-percentage": "0.4", "show-structure": "true"})
    if palette_field:
        colors = SUB_COLORS if palette_field == "subreddit" else TYPE_COLORS
        st = sub(ds, "style")
        sr = sub(st, "style-rule", {"element": "mark"})
        enc = sub(sr, "encoding", {"attr": "color", "field": inst("none", palette_field, "nk"), "type": "palette"})
        for val, col in colors.items():
            m = sub(enc, "map", {"to": col.lower()})
            sub(m, "bucket", text=f'"{val}"')


def q(ds, i):
    return f"[federated.{ds}].{inst(*i)}"


def sheet_instances(s):
    out = []
    for k in ("rows", "cols", "text", "tooltip", "lod"):
        out += s.get(k, [])
    for k in ("color", "size"):
        if s.get(k):
            out.append(s[k])
    for f in s.get("filters", []):
        out.append(f["inst"])
    if s.get("sort"):
        out += [s["sort"]["inst"], s["sort"]["using"]]
    seen, uniq = set(), []
    for i in out:
        if i not in seen:
            seen.add(i)
            uniq.append(i)
    return uniq


def title_el(parent, tag, title, caveat=None, size="13", bold=True):
    t = sub(parent, tag)
    ft = sub(t, "formatted-text")
    a = {"bold": "true"} if bold else {}
    a.update({"fontcolor": "#1b1b1b" if bold else "#666666", "fontsize": size})
    sub(ft, "run", a, title)
    if caveat:
        sub(ft, "run", {"fontcolor": "#666666", "fontsize": "9"}, "\n" + caveat)


def build_worksheet(parent, ctx: Ctx, s):
    ds = s["ds"]
    dsn = f"federated.{ds}"
    ws = sub(parent, "worksheet", {"name": s["name"]})
    lo = sub(ws, "layout-options")
    title_el(lo, "title", s["title"], s["caveat"])
    title_el(lo, "caption", s["caveat"], None, size="9", bold=False)
    table = sub(ws, "table")
    view = sub(table, "view")
    dss = sub(view, "datasources")
    sub(dss, "datasource", {"caption": DATASOURCES[ds][1], "name": dsn})
    dep = sub(view, "datasource-dependencies", {"datasource": dsn})
    insts = sheet_instances(s)
    fields = set()
    for d, f, t in insts:
        fields.add(f)
        fields.update(calc_refs(ds, f))
    for f in sorted(fields):
        column_el(dep, ctx, ds, f)
    for d, f, t in sorted(insts, key=lambda x: inst(*x)):
        sub(dep, "column-instance", {"column": f"[{f}]", "derivation": DERIV[d], "name": inst(d, f, t),
                                     "pivot": "key", "type": ITYPE[t]})
    for flt in s.get("filters", []):
        i = flt["inst"]
        fe = sub(view, "filter", {"class": "categorical", "column": q(ds, i)})
        lvl = inst(*i)
        mems = [(f'"{m}"' if isinstance(m, str) else str(m)) for m in flt["members"]]
        ui = {U + "ui-domain": "database", U + "ui-enumeration": "inclusive", U + "ui-marker": "enumerate"}
        if len(mems) == 1:
            a = {"function": "member", "level": lvl, "member": mems[0]}
            a.update(ui)
            sub(fe, "groupfilter", a)
        else:
            a = {"function": "union"}
            a.update(ui)
            g = sub(fe, "groupfilter", a)
            for m in mems:
                sub(g, "groupfilter", {"function": "member", "level": lvl, "member": m})
    if s.get("sort"):
        so = s["sort"]
        sub(view, "sort", {"class": "computed", "column": q(ds, so["inst"]), "direction": so["direction"],
                           "using": q(ds, so["using"])})
    if s.get("filters"):
        sl = sub(view, "slices")
        for flt in s["filters"]:
            sub(sl, "column", text=q(ds, flt["inst"]))
    sub(view, "aggregation", {"value": "true"})
    st = sub(table, "style")
    if s.get("diverging"):
        dv = s["diverging"]
        sr = sub(st, "style-rule", {"element": "mark"})
        sub(sr, "encoding", {"attr": "color", "center": dv["center"], "field": q(ds, dv["field"]),
                             "max": dv["max"], "min": dv["min"], "palette": DIVERGING, "type": "interpolated"})
    sr = sub(st, "style-rule", {"element": "worksheet"})
    sub(sr, "format", {"attr": "display-field-labels", "scope": "cols", "value": "true"})
    panes = sub(table, "panes")
    pane = sub(panes, "pane", {"selection-relaxation-option": "selection-relaxation-allow"})
    pv = sub(pane, "view")
    sub(pv, "breakdown", {"value": "auto"})
    sub(pane, "mark", {"class": s["mark"]})
    enc = sub(pane, "encodings")
    if s.get("color"):
        sub(enc, "color", {"column": q(ds, s["color"])})
    if s.get("size"):
        sub(enc, "size", {"column": q(ds, s["size"])})
    for i in s.get("text", []):
        sub(enc, "text", {"column": q(ds, i)})
    for i in s.get("tooltip", []):
        sub(enc, "tooltip", {"column": q(ds, i)})
    for i in s.get("lod", []):
        sub(enc, "lod", {"column": q(ds, i)})
    pst = sub(pane, "style")
    psr = sub(pst, "style-rule", {"element": "mark"})
    sub(psr, "format", {"attr": "mark-labels-show",
                        "value": "true" if (s.get("text") or s.get("labels")) else "false"})
    sub(psr, "format", {"attr": "mark-labels-cull", "value": "true"})

    def shelf(lst, joiner):
        if not lst:
            return None
        parts = [q(ds, i) for i in lst]
        return parts[0] if len(parts) == 1 else "(" + f" {joiner} ".join(parts) + ")"

    # dimensions nest with '/', several measures sit side by side with '+'
    def expr(lst):
        if not lst:
            return None
        if all(i[2] == "qk" for i in lst) and len(lst) > 1:
            return shelf(lst, "+")
        return shelf(lst, "/")

    r = sub(table, "rows")
    r.text = expr(s.get("rows"))
    c = sub(table, "cols")
    c.text = expr(s.get("cols"))


def legend_runs(ft, kind):
    colors = SUB_COLORS if kind == "sub" else TYPE_COLORS
    sub(ft, "run", {"fontcolor": "#666666", "fontsize": "10"}, "Colours: ")
    for k, col in colors.items():
        sub(ft, "run", {"bold": "true", "fontcolor": col, "fontsize": "10"}, "■ " + k + "   ")
    if kind == "type":
        sub(ft, "run", {"fontcolor": "#666666", "fontsize": "10"},
            "|  heatmaps: blue = lift above 1, orange = below 1")


def build_dashboard(parent, d, by_key, ds_of):
    db = sub(parent, "dashboard", {"name": d["name"]})
    lo = sub(db, "layout-options")
    title_el(lo, "title", d["title"], None, size="16")
    if OPTS["dash_size"] == "fixed":
        sub(db, "size", {"maxheight": "768", "maxwidth": "1366", "minheight": "768", "minwidth": "1366"})
    else:
        # automatic: fills the window when presented directly (1366x768 screen) and shrinks to the
        # Story's content area (about 1366x609) instead of adding scrollbars, as in World Indicators.twb
        sub(db, "size", {"sizing-mode": "automatic"})
    used = [by_key[k] for k, *_ in d["grid"]]
    dsnames = sorted({s["ds"] for s in used})
    dss = sub(db, "datasources")
    for k in dsnames:
        sub(dss, "datasource", {"caption": DATASOURCES[k][1], "name": f"federated.{k}"})
    # filter zones need their field declared, as in Tableau's own PerformanceRecording workbook
    fdeps = {}
    for k, i, _mode in d.get("filters", []):
        fdeps.setdefault(by_key[k]["ds"], []).append(i)
    for dsk in sorted(fdeps):
        dep = sub(db, "datasource-dependencies", {"datasource": f"federated.{dsk}"})
        for i in fdeps[dsk]:
            column_el(dep, CTX[0], dsk, i[1])
        for i in fdeps[dsk]:
            sub(dep, "column-instance", {"column": f"[{i[1]}]", "derivation": DERIV[i[0]], "name": inst(*i),
                                         "pivot": "key", "type": ITYPE[i[2]]})
    zones = sub(db, "zones")
    nid = iter(range(1, 1000))
    root = sub(zones, "zone", {"h": "100000", "id": str(next(nid)), "type": "layout-basic", "w": "100000",
                               "x": "0", "y": "0"})
    sub(root, "zone", {"h": "5500", "id": str(next(nid)), "type": "title", "w": "100000", "x": "0", "y": "0"})
    tz = sub(root, "zone", {"h": "5500", "id": str(next(nid)), "type": "text", "w": "100000", "x": "0",
                            "y": "5500"})
    ft = sub(tz, "formatted-text")
    sub(ft, "run", {"fontcolor": "#333333", "fontsize": "11"}, d["note"])
    lz = sub(root, "zone", {"h": "3500", "id": str(next(nid)), "type": "text", "w": "100000", "x": "0",
                            "y": "11000"})
    legend_runs(sub(lz, "formatted-text"), d["legend"])
    top, avail = 14500, 100000 - 14500
    filt_for = {k: (i, mode) for k, i, mode in d.get("filters", [])}
    for k, x, y, w, h in d["grid"]:
        s = by_key[k]
        Y = top + int(y * avail / 100000)
        H = int(h * avail / 100000)
        if k in filt_for:
            fh = 6000
            i, mode = filt_for[k]
            sub(root, "zone", {"h": str(fh), "id": str(next(nid)), "mode": mode, "name": s["name"],
                               "param": q(s["ds"], i), "show-null-ctrls": "false", "type": "filter",
                               "values": "relevant", "w": str(w), "x": str(x), "y": str(Y)})
            Y, H = Y + fh, H - fh
        sub(root, "zone", {"h": str(H), "id": str(next(nid)), "name": s["name"], "show-title": "true",
                           "w": str(w), "x": str(x), "y": str(Y)})


def build_story(parent, dash_names):
    db = sub(parent, "dashboard", {"name": STORY["name"], "type": "storyboard"})
    lo = sub(db, "layout-options")
    title_el(lo, "title", STORY["title"], None, size="16")
    sub(db, "size", {"maxheight": "768", "maxwidth": "1366", "minheight": "768", "minwidth": "1366"})
    zones = sub(db, "zones")
    z = sub(zones, "zone", {"h": "100000", "id": "2", "type": "layout-basic", "w": "100000", "x": "0", "y": "0"})
    f = sub(z, "zone", {"h": "100000", "id": "1", "param": "vert", "removable": "false", "type": "layout-flow",
                        "w": "100000", "x": "0", "y": "0"})
    sub(f, "zone", {"h": "4453", "id": "3", "type": "title", "w": "100000", "x": "0", "y": "0"})
    sub(f, "zone", {"fixed-size": "125", "h": "16869", "id": "4", "is-fixed": "true", "paired-zone-id": "5",
                    "removable": "false", "type": "flipboard-nav", "w": "100000", "x": "0", "y": "4453"})
    fz = sub(f, "zone", {"h": "78678", "id": "5", "paired-zone-id": "4", "removable": "false",
                         "type": "flipboard", "w": "100000", "x": "0", "y": "21322"})
    fb = sub(fz, "flipboard", {"active-id": "1", "nav-type": "caption", "show-nav-arrows": "true"})
    sps = sub(fb, "story-points")
    n = 0
    for sheet, cap in STORY["points"]:
        if sheet in dash_names:
            n += 1
            sub(sps, "story-point", {"caption": cap, "captured-sheet": sheet, "id": str(n)})


def cards_window(parent, s, maximized=False):
    a = {"class": "worksheet"}
    if maximized:
        a["maximized"] = "true"
    a["name"] = s["name"]
    w = sub(parent, "window", a)
    cards = sub(w, "cards")
    left = sub(sub(cards, "edge", {"name": "left"}), "strip", {"size": "160"})
    for t in ("pages", "filters", "marks"):
        sub(left, "card", {"type": t})
    top = sub(cards, "edge", {"name": "top"})
    for t in ("columns", "rows", "title"):
        sub(sub(top, "strip", {"size": "31"}), "card", {"type": t})
    flt = [f for f in s.get("filters", []) if f.get("mode") == "dropdown"]
    if flt or s.get("color"):
        right = sub(sub(cards, "edge", {"name": "right"}), "strip", {"size": "160"})
        for f in flt:
            sub(right, "card", {"mode": "dropdown", "param": q(s["ds"], f["inst"]), "type": "filter"})
        if s.get("color"):
            sub(right, "card", {"pane-specification-id": "0", "param": q(s["ds"], s["color"]), "type": "color"})


OPTS = {"dash_size": "auto", "zone_attr": "type"}


def to_zone_v2(wb):
    """Newer dialect: zone type-v2= on every zone plus the manifest entry the samples pair with it."""
    for z in wb.iter("zone"):
        if "type" in z.attrib:
            v = z.attrib.pop("type")
            z.set("type-v2", v)
            items = sorted(z.attrib.items())
            z.attrib.clear()
            z.attrib.update(items)
    man = ET.Element("document-format-change-manifest")
    ET.SubElement(man, "SetMembershipControl")
    wb.insert(0, man)


def build(directory: str, only=None, skip=None, story=True, dashboards=True, dash_size="auto",
          zone_attr="type") -> bytes:
    OPTS.update(dash_size=dash_size, zone_attr=zone_attr)
    ctx = Ctx(directory)
    CTX[:] = [ctx]
    sheets = [s for s in SHEETS if (not only or s["key"] in only) and (not skip or s["key"] not in skip)]
    by_key = {s["key"]: s for s in sheets}
    dashes = [d for d in DASHBOARDS if dashboards and all(k in by_key for k, *_ in d["grid"])] \
        if dashboards else []
    wb = ET.Element("workbook", {"locale": "en_US", "source-build": "0.0.0 (0000.0.0.0)",
                                 "source-platform": "mac", "version": "18.1"})
    prefs = sub(wb, "preferences")
    sub(prefs, "preference", {"name": "ui.encoding.shelf.height", "value": "24"})
    sub(prefs, "preference", {"name": "ui.shelf.height", "value": "26"})
    sub(wb, "style-theme", {"name": "smooth"})
    dsx = sub(wb, "datasources")
    for key in sorted({s["ds"] for s in sheets}):
        build_datasource(dsx, ctx, key)
    wss = sub(wb, "worksheets")
    for s in sheets:
        build_worksheet(wss, ctx, s)
    do_story = story and len(dashes) > 0
    if dashes:
        dbs = sub(wb, "dashboards")
        for d in dashes:
            build_dashboard(dbs, d, by_key, None)
        if do_story:
            build_story(dbs, {d["name"] for d in dashes})
    wins = sub(wb, "windows", {"source-height": "30"})
    first = STORY["name"] if do_story else (dashes[0]["name"] if dashes else None)
    for s in sheets:
        cards_window(wins, s, maximized=(first is None and s is sheets[0]))
    for d in dashes:
        a = {"class": "dashboard"}
        if d["name"] == first:
            a["maximized"] = "true"
        a["name"] = d["name"]
        w = sub(wins, "window", a)
        vps = sub(w, "viewpoints")
        for k, *_ in d["grid"]:
            vp = sub(vps, "viewpoint", {"name": by_key[k]["name"]})
            sub(vp, "zoom", {"type": "entire-view"})
        sub(w, "active", {"id": "-1"})
    if do_story:
        w = sub(wins, "window", {"class": "dashboard", "maximized": "true", "name": STORY["name"]})
        sub(w, "viewpoints")
        sub(w, "active", {"id": "-1"})
    if zone_attr == "type-v2":
        to_zone_v2(wb)
    ET.indent(wb, space="  ")
    body = ET.tostring(wb, encoding="unicode")
    return ("<?xml version='1.0' encoding='utf-8' ?>\n\n" + body + "\n").encode("utf-8")


def used_csvs(only=None, skip=None):
    sheets = [s for s in SHEETS if (not only or s["key"] in only) and (not skip or s["key"] not in skip)]
    return sorted({DATASOURCES[s["ds"]][0] for s in sheets})


def write_twbx(path, twb_name, twb_bytes, csvs):
    entries = [(twb_name, twb_bytes)]
    for c in csvs:
        with open(os.path.join(EXTRACTS, c), "rb") as fh:
            entries.append((f"{TWB_DIR_PACKAGED}/{c}", fh.read()))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in entries:   # .twb first, then data sorted
            zi = zipfile.ZipInfo(name, date_time=ZIP_TIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, data)
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(buf.getvalue())
    os.replace(tmp, path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default=HERE)
    ap.add_argument("--name", default=NAME)
    ap.add_argument("--only", default="", help="comma-separated sheet keys, e.g. R1a,R3")
    ap.add_argument("--skip", default="", help="comma-separated sheet keys to drop")
    ap.add_argument("--no-story", action="store_true")
    ap.add_argument("--no-dashboards", action="store_true")
    ap.add_argument("--dash-size", choices=["auto", "fixed"], default="auto",
                    help="auto (default; fits the Story) or fixed 1366x768")
    ap.add_argument("--zone-attr", choices=["type", "type-v2"], default="type",
                    help="zone attribute dialect: type (legacy, default) or type-v2 (+ manifest)")
    a = ap.parse_args(argv)
    only = {x for x in a.only.split(",") if x}
    skip = {x for x in a.skip.split(",") if x}
    known = {s["key"] for s in SHEETS}
    bad = (only | skip) - known
    if bad:
        ap.error(f"unknown sheet keys {sorted(bad)}; known: {sorted(known)}")
    os.makedirs(a.out_dir, exist_ok=True)
    kw = dict(only=only, skip=skip, story=not a.no_story, dashboards=not a.no_dashboards,
              dash_size=a.dash_size, zone_attr=a.zone_attr)
    standalone_dir = os.path.relpath(EXTRACTS, os.path.abspath(a.out_dir)).replace(os.sep, "/")
    twb = build(standalone_dir, **kw)
    twb_path = os.path.join(a.out_dir, a.name + ".twb")
    with open(twb_path + ".tmp", "wb") as fh:
        fh.write(twb)
    os.replace(twb_path + ".tmp", twb_path)
    packaged = build(TWB_DIR_PACKAGED, **kw)
    twbx_path = os.path.join(a.out_dir, a.name + ".twbx")
    write_twbx(twbx_path, a.name + ".twb", packaged, used_csvs(only, skip))
    print(f"wrote {twb_path} ({len(twb):,} bytes, data dir {standalone_dir})")
    print(f"wrote {twbx_path} ({os.path.getsize(twbx_path):,} bytes, {len(used_csvs(only, skip))} CSVs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
