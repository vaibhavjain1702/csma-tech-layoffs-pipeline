# Tableau workbook: Solidarity or Blame

*Built 26 November 2026 by `tableau/build_workbook.py` from the extracts in `outputs/16_tableau/`. The generator writes the XML directly and never opens Tableau. Expected numbers for checking the views are in `EXPECTED_VALUES.md`.*

**Status:** the structural checks pass, and the workbook was opened and checked in Tableau Desktop 2026.3 (free edition) on 26 Nov 2026, 22:29-22:45 IST. It loads without errors and all four story points render with the expected numbers (R1 2.45% / 0.20% / 0.32%, R3 x2.82, R4a 1.69). Fixes after that check: R2a redrawn as one column per community (it was 36 cramped rows); R4b moved out of dashboard 3 (it stays a worksheet); dashboard 4 titles shortened; colour keys changed to the colours Tableau actually draws (below). Dashboards 1-2 were re-checked in the app after the fixes; dashboards 3-4 after their layout change were checked structurally only.

## Files

| File | What it is |
|---|---|
| `CSMA_Solidarity_or_Blame.twbx` | **Open this one.** A packaged workbook: the `.twb` at the zip root, plus the 10 CSVs it uses under `Data/16_tableau/`. It uses only relative paths, so it should open on any machine. |
| `CSMA_Solidarity_or_Blame.twb` | The same workbook unpackaged. It reads the CSVs through the relative path `../outputs/16_tableau/`. Tableau normally stores absolute paths for text files, so it is not certain that it resolves this one; if it asks for the data, use Data Source > Edit Connection and point it at `outputs/16_tableau/`. Use the `.twbx` for presenting and submitting. |
| `build_workbook.py` | A deterministic generator: the same CSVs always give byte-identical files. |
| `validate_twb.py` | Runs the structural checks and writes `EXPECTED_VALUES.md`. |
| `EXPECTED_VALUES.md` | The numbers each view should show, computed with pandas using the same filters. |

## How to open it

1. Double-click `CSMA_Solidarity_or_Blame.twbx`. Tableau Desktop 2026.3 is installed on this Mac.
2. The workbook is set to open on the **Story**, which steps through the four dashboards. The worksheet tabs hold the single views.
3. If Tableau asks to upgrade the workbook format, accept. Then save with File > Save, which keeps the `.twbx` format.

## Contents, sheet by sheet

Tableau 2026.3 ignored the custom palette written into the data sources, so the views use Tableau's default palette, assigned alphabetically per field, and the dashboards' colour keys name those colours (so they differ from the Gephi figures).
- **Communities:** cscareerquestions blue #4e79a7, programming orange #f28e2b, technology red #e15759. R2b has only two communities, so there technology is orange; its rows are labelled.
- **Author types (network map R4c):** blame-talker blue, helper orange, other red, story-sharer teal.
- **Heatmaps:** a diverging orange-blue scale centred on lift = 1. Blue means more than expected, orange means less.

| Sheet | Question it answers | Data source | Build |
|---|---|---|---|
| **R1a** Weekly layoff share | Is layoff talk concentrated in one community, and is that steady or spiky? | `r1_daily_by_community` | Line chart. `week_start` (exact date) against *Layoff share (non-bot)*, coloured by subreddit. Filters: kind = comments, in_shared_window = 1. |
| **R1b** Threads with layoff talk | Is layoff talk spread across threads of every size? | `r1_threads` | Bars of *Share of threads with layoff talk* by *Thread size* × subreddit. Filter: in_shared_window = 1. |
| **R2a** Marker rates by community | How does each community frame employment talk (execs, offshoring, AI, economy, doom…)? | `r2_marker_rates_long` | Bars of *Marker rate* by marker × subreddit. Filters: base = employment_core (dropdown), in_shared_window = 1. |
| **R2b** Same authors two communities | Is the framing gap about the people or about the place? | `r2_cross_posters_same_author` | Two bar panes side by side: AVG(rate_mentions_execs) and AVG(rate_mentions_ai), by subreddit, for 152 cross-posters. Each bar is labelled with its own value only (mark labels, no text encoding). |
| **R3** Reply-type lift | What kind of comment gets what kind of reply? | `r3_reply_type_lift` | Heatmap of parent_type × reply_type. Colour and label show lift_vs_none, centred on 1. |
| **R4a** Who replies to whom | Do author types reply to their own kind more than chance predicts? | `r4_type_flows` | Heatmap of replier_type × parent_author_type. Colour and label show lift_vs_random_mixing, centred on 1. Filter: reply_function = all (dropdown; it can be switched to sympathy, advice, agree or challenge). |
| **R4b** Centrality by author type | Which author types sit in central network positions? | `r4_centrality_by_type` | Circle at the median per type, with the label "median (95% CI lo to hi)". Filters: measure = pagerank (dropdown, single value), type = the 5 types (the "minus other" rows are hidden). The title shows the chosen measure. The CI is a label, not a drawn whisker (a whisker needs a dual axis). |
| **R4c** Network position map | What does the network core look like? | `r4_network_core_nodes` | Scatter of x/y for 1,500 core nodes. Colour = type, size = *Size (sqrt pagerank)* so the top node (pagerank 158, ~29x the median) does not cover its neighbours; raw pagerank is in the tooltip. No edges are drawn. |
| **R5a** Coverage over time | Where does collection coverage differ between communities? | `r1_daily_by_community` | Weekly SUM(records) by subreddit (sum of daily counts per week). Filter: kind = comments. All months are shown. |
| **R5b** Marker precision | How far can we trust each keyword screen? | `r5_marker_precision` | Bars of precision_R_percent by screen, sorted in descending order. The CSV has columns `n` (sampled) and `N` (read as not relevant); `N` is exposed as the field **N (not relevant)** (with a `<cols>` map, as Superstore does for renamed fields) so the two names cannot clash. It is not used on the sheet (N = n − R − P). The CSV itself is unchanged. |
| **R5c** Robustness of a headline | Does the blame-talker clustering (lift 1.69) survive label noise, other activity thresholds and dropping megathreads? It does: the minimum is 1.28. For this statistic, the null-shuffle and activity-matched checks report other statistics. | `r5_robustness_long` | Circle at AVG(value) by check × *Variant (short)*. lo, hi and the full variant text (ATTR) are in the tooltip. Filter: statistic = lift_blame-talker->blame-talker (dropdown); the title shows the chosen statistic, and the "1.69 / min 1.28" wording applies to the default only. |

Each sheet has a takeaway title, with the caveat in grey on the line below it and repeated as the sheet caption.

**Dashboards** (size: automatic, so they fill a 1366 × 768 screen when shown directly and shrink to the Story's content area, about 1366 × 609, without scrollbars; `--dash-size fixed` gives fixed 1366 × 768). Each has a one-line takeaway and a colour key.
1. **Where disruption talk lives:** R1a, R5a, R1b.
2. **How communities frame it:** R2a, R2b.
3. **Who replies to whom:** R3, R4a, R4c (R4b stays a separate worksheet).
4. **Can we trust the numbers:** R5a and R5b on top, R5c full width below (with a statistic dropdown).

**Presenter note:** the R5c title (and R4b's, when shown as a sheet) names the selected statistic/measure, but their headline numbers are for the default selection (pagerank; blame-talker → blame-talker lift). Leave the dropdowns at the default during the talk.

**Story:** *Solidarity or Blame (story)*, 1366 × 768, chains dashboards 1 to 4, one story point each. It follows the Data Narratives lecture.

## Data sources and calculated fields

There are ten CSV (text-file) connections, one per extract used. None of them are blended or joined. The extracts `r2_employment_comments`, `r3_reply_pairs`, `r4_authors`, `r4_communities` and `r4_network_core_edges_path` are **not** used by these views, so they are not packaged. They remain in `outputs/16_tableau/` for ad-hoc analysis.

| Calculated field | Data source | Formula |
|---|---|---|
| Layoff share (non-bot) | r1_daily_by_community | `SUM([facet_layoffs]) / (SUM([records]) - SUM([bot_records]))` |
| Thread size | r1_threads | `CASE [size_band] WHEN "1-9" THEN "1) 1-9 comments" … WHEN "1000+" THEN "5) 1000+" END`. The prefixes make the bands sort in size order. |
| Share of threads with layoff talk | r1_threads | `AVG([has_layoff_talk])` |
| Marker rate | r2_marker_rates_long | `SUM([hits]) / SUM([base_comments])` |
| Median (95% CI) | r4_centrality_by_type | `STR(ROUND(SUM([median]),3)) + " (" + … + ")"`, used as a label |
| Size (sqrt pagerank) | r4_network_core_nodes | `SQRT(SUM([pagerank]))`, used for circle size in R4c |
| Variant (short) | r5_robustness_long | `CASE [variant] WHEN "drop 10% of hits + …" THEN "noise: drop 10%" … ELSE [variant] END`, short row labels for R5c |

`TABLEAU_GUIDE.md` also suggests `AVG([reply_sympathy])`, `AVG([reply_sympathy]) / 0.0182` and `SUM([replies_received]) / SUM([replies_given])`. Those need `r3_reply_pairs` and `r4_authors`, which these views do not use. R3 uses the precomputed `lift_vs_none` column instead, which gives the same ×2.816. The guide's formulas apply only for ad-hoc analysis on the unpackaged extracts.

## How to regenerate

```
cd "<project>/Archive"
PYTHONDONTWRITEBYTECODE=1 python3 -B tableau/build_workbook.py     # writes .twb and .twbx
PYTHONDONTWRITEBYTECODE=1 python3 -B tableau/validate_twb.py       # checks + EXPECTED_VALUES.md; exit 1 on failure
```

The build needs only Python 3 and pandas. If `scripts/export_tableau.py` changes the extracts, rerun both commands.

**If Tableau will not open the file**, first try building without the Story (`--no-story`). The Story is the least-tested construct. If that still fails, the generator can leave further parts out so the problem can be bisected:
- `--no-story`
- `--no-dashboards`
- `--only R1a,R3`
- `--skip R4b`
- `--out-dir DIR --name NAME`, to write the variant somewhere else.
- `--zone-attr type-v2`: writes every zone with the newer `type-v2=` attribute plus the `<document-format-change-manifest><SetMembershipControl/></document-format-change-manifest>` that Tableau's newer samples pair with it. Try this if the Story's `type='flipboard'` zones are rejected; it changes all zones, never a mix.
- `--dash-size fixed`: fixed 1366 × 768 dashboards (they will scroll inside the Story).

For example, `python3 -B tableau/build_workbook.py --out-dir /tmp/t --name test --only R3` builds a workbook with the R3 sheet only.

**Format.** The XML follows the workbook format that Tableau itself ships in `install/Performance/PerformanceRecording_new.twb`: version 18.1, a plain `<relation>`, and `type=` on zones. The CSV connection attributes follow the Superstore sample; the Story structure follows World Indicators. The Story's `type='flipboard'`/`'flipboard-nav'` zones are the least-proven part: the shipped samples write them only as `type-v2=`. Tableau upgrades the format silently the first time the workbook is saved, and running `build_workbook.py` again overwrites any edits made in the GUI.

**Pre-built fallbacks** (session scratchpad, lost on reboot; rebuild with the flags above if gone): `variant_no_story.twbx`, `variant_type_v2.twbx`, `variant_fixed_dash.twbx`, `variant_sheets_only.twbx` and `only_<sheet>.twbx` were built into the build session's temporary folder. If they are gone, rebuild them with the flags above into any folder outside the project. Try `--no-story` first, then `--zone-attr type-v2`.

## Caveats (from `outputs/16_tableau/TABLEAU_GUIDE.md`)

- **Compare communities only in Jan–Jun 2025** (`in_shared_window = 1`), because coverage differs:
  - r/technology comments end on 2025-06-09;
  - r/programming comments end on 2025-12-12;
  - cscq comments run to 2026-09-23;
  - **cscq has no posts**.
- **No human has checked the labels yet.** All flags are keyword markers. Mentions of executives or offshoring are *topic* markers, not stance. The "agree" reply marker also fires on hostile replies that start with "This". The R5b precision figures are provisional, from one reader.
- **Rates must come from sums.** The calculated fields do this; never average rates that were already aggregated. The one exception is R2b, which averages per-author rates on purpose (the same-author design of D1).
- **Flags overlap.** A comment can carry several markers, so shares across types do not add up to 100%. In R3 the parent types overlap too.
- **R3 covers all cscq months** (91,229 reply pairs, Jan 2025 – Sep 2026; experience → sympathy ×2.82). Jan–Jun 2025 alone gives ×2.29. R4 covers Jan–Jun 2025 only.
- **The R4 ids (`a…`/`n…`) cannot be joined to the R2/R3 ids (`p…`).**
- **Cross-posters:** 152 here vs 160 in D1, because D1 also counted comments that matched only `career_transition`.
- **Scores are snapshots.** Control for arrival time (`early_arrival`) when looking at votes.
