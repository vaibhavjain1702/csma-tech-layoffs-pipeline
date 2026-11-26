# Tableau extracts: guide

*25 November 2026. Made by `scripts/export_tableau.py`, which only reads the database. Rerun it after `scripts/explore_network.py`.*

**Workbook.** These extracts are the data behind the finished Tableau workbook in [`../../tableau/`](../../tableau/README.md) (`CSMA_Solidarity_or_Blame.twbx`: 11 sheets, 4 dashboards and a story). Open the `.twbx` for the finished views, or build your own sheets from the CSVs below. The workbook uses 10 of the 15 extracts; the numbers each view should show are in `tableau/EXPECTED_VALUES.md`.

**Privacy.** These files contain no comment text, no usernames, no Reddit ids and no author hashes. Authors (`p…`) and threads (`t…`) have neutral ids that cannot be traced back. R4 files use the network ids (`a…` for profiled authors, `n…` for the rest), which are a separate scheme: **R4 authors cannot be joined to R2/R3 authors.**

**Window.** Every file covering more than Jan–Jun 2025 has an `in_shared_window` flag (1 = Jan–Jun 2025). Filter on it for any comparison between communities. Collection coverage differs by community:
- r/technology runs only to Jun 2025;
- r/programming runs to Dec 2025;
- cscq runs to Sep 2026;
- **cscq has no posts at all**.

**Labels.** All flags are keyword markers that **no human has checked yet**. Mentions of executives or offshoring are **topic** markers, not stance. The "agree" reply marker also fires on hostile replies that start with "This".

## Files by result

| File | One row = | Rows | Use for |
|---|---|---:|---|
| `r1_daily_by_community.csv` | day × community × kind (posts/comments) | 2,400 | **R1** weekly and daily volume and layoff share; **R5** coverage gaps, bot and deleted shares |
| `r1_threads.csv` | thread | 75,422 | **R1** layoff talk spread across many threads (ambient) or concentrated in a few (event-driven) |
| `r2_employment_comments.csv` | employment-screened comment (all 3 communities, all months) | 173,240 | **R2** framing by community, **R3** parent side, vote/arrival checks (R5) |
| `r2_marker_rates_long.csv` | community × month × base × marker | 1,521 | **R2** quick rate charts (already aggregated) |
| `r2_cross_posters_same_author.csv` | author × community (authors in both cscq and r/technology, Jan–Jun 2025) | 304 (152 authors) | **R2 / D1** same person, two communities |
| `r3_reply_pairs.csv` | human reply to a cscq employment comment (all cscq months) | 91,229 | **R3** what kind of comment gets what kind of reply |
| `r3_reply_type_lift.csv` | comment type × reply type | 32 | **R3** headline lift heatmap |
| `r4_authors.csv` | author in the cscq reply network (Jan–Jun 2025, largest connected component) | 30,976 | **R4** position by type, activity bands |
| `r4_type_flows.csv` | replier type × parent-author type × reply function | 125 | **R4** who replies to whom, and how |
| `r4_centrality_by_type.csv` | type × centrality measure (median, CI) | 68 | **R4** dot-and-whisker chart |
| `r4_communities.csv` | Louvain community (≥50 authors) | 59 | **R4** type mix per community |
| `r4_network_core_nodes.csv` / `r4_network_core_edges_path.csv` | node with x, y / edge end (2 rows per edge) | 1,500 / 39,932 | **R4** drawing the network in Tableau |
| `r5_robustness_long.csv` | one check result | 886 | **R5** every rival check in one table |
| `r5_marker_precision.csv` | screen group | 7 | **R5** provisional precision of the screens |

## Key fields

- **Comment flags** (`r2_employment_comments`), each 0/1. A comment can have several:
  - `own_layoff_story`, `mentions_execs`, `mentions_offshore_visa`, `ethnic_reference`, `blames_workers`;
  - `ai_is_excuse`, `ai_will_replace`, `mentions_ai`;
  - `macro_economy`, `overhiring`, `consequences`, `doom`;
  - `any_blame_topic` = execs, offshore or AI-as-excuse.
- **Other comment fields:**
  - `facet_*` are the six employment screens;
  - `employment_core` = any of the five screens used in H3 (all except `career_transition`, which has the "quite" artefact);
  - `score_pct_in_thread` and `arrival_pct_in_thread` are 0–1 ranks within the thread; `early_arrival` = first 20% of the thread;
  - `human_replies_received`.
- **Reply flags** (`r3_reply_pairs`): `reply_sympathy`, `reply_advice`, `reply_agree`, `reply_challenge`.
  - Parent flags `parent_experience` … `parent_doom` are multi-label.
  - `parent_type_primary` is the first type that matches, for a quick colour, in this order: experience, execs, offshore, workers, ai_excuse, ai_replaces, doom.
- **R4 types:** story-sharer, blame-talker, helper and other cover authors with ≥5 comments; low-activity is <5. Thresholds are in `15_network/NETWORK_NOTES.md`.

## Calculated fields to create in Tableau

```
// R1 layoff share; reproduces the reported 2.45% (cscq) vs 0.20% (r/technology): non-bot denominator
SUM([facet_layoffs]) / (SUM([records]) - SUM([bot_records]))

// R3 sympathy rate for any slice of reply pairs
AVG([reply_sympathy])

// R3 lift against unmarked comments (baseline 1.82% for sympathy)
AVG([reply_sympathy]) / 0.0182

// R4 replies received per reply given
SUM([replies_received]) / SUM([replies_given])
```

## Suggested views (one per result)

1. **R1.**
   - Line chart of the weekly layoff share by `subreddit` (`week_start`, filtered to the shared window). cscq is high and flat, the other two are low and spiky. There is a shared spike in mid-May 2025: the week of 12 May is the top week for r/technology and second for cscq, and r/programming peaks the next week. cscq's top week is 21 April. Neither date has been matched to an event yet.
   - Second view: from `r1_threads`, share of threads with layoff talk by `size_band` × `subreddit`.
2. **R2.**
   - Bar chart from `r2_marker_rates_long`: base = `employment_core` (or `layoff_comments`), shared window, marker on rows, community as colour.
   - Then a slope chart from `r2_cross_posters`: the same author's `rate_mentions_execs` in each community. Within each author the gap disappears; `rate_mentions_ai` keeps its gap.
3. **R3.**
   - Heatmap from `r3_reply_type_lift`: parent type × reply type, coloured by `lift_vs_none` on a diverging scale centred on 1.
   - Check: filter `r3_reply_pairs` by `parent_words_band` and confirm the experience → sympathy lift survives.
4. **R4.**
   - Heatmap from `r4_type_flows`:
     - `reply_function = all`, coloured by `lift_vs_random_mixing`;
     - then `sympathy` / `challenge` coloured by `share_lift` (compare along a row).
   - Box plot from `r4_authors`: `pagerank` by `type`, then split by `activity_band`. The type differences shrink once activity is held equal; that is the N1 result.
   - Network map:
     - use `r4_network_core_edges_path` as a line mark with `path_order` on Path and x/y as dimensions;
     - add `r4_network_core_nodes` as a dual-axis circle coloured by `type`.
5. **R5.**
   - Filter `r5_robustness_long` to one `statistic`, such as `lift_blame-talker->blame-talker`, and plot `value` by `check` / `variant` to see how much it moves.
   - Coverage: `r1_daily_by_community` as `records` by date, coloured by community. Gaps and the different end dates are visible.

## Pitfalls
- **Rates must be computed from sums.** Use the formulas above; never average rates that were already aggregated.
- **Flags overlap.** A comment can count in several types, so percentages across types do not add up to 100%.
- **Reply pairs and the comment table overlap.** `r3_reply_pairs` covers all cscq months, whereas R4 covers only Jan–Jun 2025. Filter `in_shared_window` to compare them.
- **Scores are snapshots.** Use `score_pct_in_thread` and control for `early_arrival`.
- **Cross-poster count.** 152 authors here vs 160 in D1. D1 also counted `career_transition`-only comments.
