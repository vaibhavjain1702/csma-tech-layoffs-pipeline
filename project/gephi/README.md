# Gephi workflow for the current author reply network

## Status (26 Nov 2026)

**What was produced.** The Gephi work from this guide is done and saved in this folder:

| Where | What |
|---|---|
| `projects/author_replies.gephi` | October author network (14,507 users, 15,427 edges, weight 15,977) and a workspace with its largest weak component (9,330 users, 64.31%), with Gephi's Modularity (resolution 1.0, randomize off, weighted): Q = 0.813, 66 groups |
| `projects/r4_cscq_author_types.gephi` | The R4 author-type network (10,778 profiled authors, 91,657 edges), coloured by author type and by Gephi modularity class (Q = 0.27, 81 classes; not comparable to the Louvain Q = 0.43 in `outputs/15_network/NETWORK_NOTES.md`, which used all 30,976 authors) |
| `projects/type_network_lift.gephi` | The comment-kind → reply-kind "type network": 12 nodes (8 comment kinds incl. none + 4 reply kinds), 32 edges, weight = lift |
| `projects/conversations.gephi` | The conversation network (13,866 nodes, 13,206 edges), plus a workspace with its 30 largest components |
| `projects/*.gexf` | The same networks with positions, colours and sizes, for the author largest component, R4 and the type network (fallback if a `.gephi` will not open) |
| `projects/analysis_notes.md` | Version, date and settings, statistics, captions, a four-part interpretation, and how to open the projects. **Read this first** |
| `figures/` | Gephi Preview exports (PDF, PNG, and SVG except for R4) and a `*_slide.png` version of each (3840 × 2160, with legend and caption). The type-network slide is the one for open task 5 |
| `stats/` | Gephi's statistics as CSV tables, its HTML reports (and their charts), layout settings and run logs |
| `toolkit/` | The code that produced all of it (`run.sh`, `src/GephiRun.java`, `pdf_to_png.py`, `make_slides.py`) |

**How.** The **Gephi Toolkit 0.11.4** (the library behind Gephi Desktop, from Maven Central, checksum verified by `toolkit/run.sh`) was run **headless** with JDK 23. It uses the same statistics, filter and layout classes as Gephi Desktop 0.11.3 (the app on this Mac). No Gephi window was used to make the files. Gephi's PNG exporter needs a screen, so figures were exported from Gephi Preview as PDF and rasterised. The final layouts use strong gravity, not the "scaling 100" suggested further down, because scaling 100 gave blank or dot-like pictures at slide size; the settings are in `stats/*_layout_settings.txt`. Gephi's Modularity and ForceAtlas2 are **not bit-for-bit repeatable**, so do not re-run `authors`, `r4`, `conv` or `all` in `toolkit/run.sh` casually: they overwrite the projects, figures and statistics that the notes quote.

**How to open the files in Gephi Desktop.**
1. Open Gephi 0.11.3, then File > Open, and choose a `.gephi` file in `projects/`.
2. Switch between workspaces with the workspace selector at the bottom (Window > Workspaces). For a demo or screen recording use the figure workspaces: "Largest weak component (9,330 users)", the two R4 workspaces, the type network and "30 largest components (figure)".
3. Go to Preview and press Refresh. Statistics columns are in Data Laboratory.
4. If a project will not open (the files were saved by toolkit 0.11.4, one patch release newer than Desktop 0.11.3, and this has **not been tested in the GUI**), open the `.gexf` beside it with File > Open.

Details, exact commands and the honest list of limits are in [`projects/analysis_notes.md`](projects/analysis_notes.md).

---

## Original guide (written October 2026; the steps below were followed by the work above)

All Gephi-specific material is organized here. Start with the [completed Python findings and four plots](analysis/FINDINGS.md), or follow the app workflow below.

| Folder | Contents |
|---|---|
| `input/` | Your Gephi-calculated [author metrics CSV](input/authors_keyword-comments.csv) |
| `exports/` | Original author and conversation node/edge CSVs and network manifests |
| `analysis/` | Python findings, analyzed metrics, tables, settings, validation, and figures |
| `rankings/` | Four standalone top-20 author tables |
| `projects/` | Saved `.gephi` projects, `.gexf` fallbacks and `analysis_notes.md` (see Status above) |
| `figures/`, `stats/`, `toolkit/` | Figures and slides, Gephi statistics and reports, and the headless Toolkit code (see Status above) |
| `scripts/` | Network export, rankings, and analysis scripts |
| `tests/` | Checks for the Python network-analysis methods |

Run commands from the **csma project root**, since these scripts use shared project paths and helpers. For example:

```bash
python gephi/scripts/analyze_gephi.py
python gephi/scripts/export_author_rankings.py
python -m unittest discover -s gephi/tests -v
```

This is the preliminary network analysis to complete now. Use the existing author export; no new collection, export scope, or coding is required. The qualitative pilot remains aside. The goal is to describe connectedness, attention, repeated interaction, and structural groups. The graph illustrates these results.

Inputs: [nodes.csv](exports/authors_keyword-comments_direct/nodes.csv), [edges.csv](exports/authors_keyword-comments_direct/edges.csv), and [network manifest](exports/authors_keyword-comments_direct/manifest.json).

Each node is a pseudonymous user. A directed edge goes from the replying user to the parent author. Weight counts selected observed replies. ThreadCount counts the distinct threads represented by that directed pair. This is an aggregated, static network: FirstReplyUTC and LastReplyUTC are summary attributes, not a sequence of all replies or a configured dynamic timeline.

## 1. Preserve and check the imported network

Save your project under `gephi/projects/author_replies.gephi`. This folder is ready for your results. Record the Gephi version and date in a short `analysis_notes.md` in that folder.

Turn off active filters before the whole-network analysis. Check 14,507 nodes and 15,427 directed edges. The summed edge weights should be 15,977. Keep weights as numbers. Do not reimport edges into the same workspace, which could duplicate them.

## 2. Describe the full network

In Overview > Statistics, run Average Degree, Average Weighted Degree, and Connected Components. Keep Directed selected where offered. Record the statistics and export or capture their reports. Weak connectivity ignores arrow direction when identifying components; strong connectivity requires directed paths in both directions. Gephi adds Component ID for weak components and a separate strongly-connected identifier.

The following baseline was calculated directly from the original CSVs on 5 October 2026; it is not a claim that the user has run these analyses in Gephi.

| Measure | Full-export baseline |
|---|---:|
| Users | 14,507 |
| Directed user pairs | 15,427 |
| Retained replies, summed weights | 15,977 |
| Weak components | 2,199 |
| Largest weak component, users | 9,330 |
| Largest weak component, share of users | 64.31% |
| Two-user components | 1,771 |
| Top 20 recipients' share of retained replies | 7.32% |
| Top 20 senders' share of retained replies | 4.89% |
| Directed pairs with weight greater than one | 446 |
| Directed pairs occurring across multiple threads | 18 |
| Unordered pairs with edges in both directions | 859 |

Average incoming degree is 15,427 / 14,507 = approximately 1.063; average incoming strength is 15,977 / 14,507 = approximately 1.101. Outgoing averages are the same. A total-degree average counts both incoming and outgoing connections, so it may be twice the incoming average. Record which convention the report uses rather than treating a factor-of-two difference as an import error.

Save `nodes_full_metrics.csv` and `edges_full.csv` through Data Laboratory > Export table while all filters are off. Check the exported row counts, excluding the header. Keep all original columns and the new component columns.

## 3. Identify attention and response activity

The four top-20 tables are already generated in [author_rankings](rankings/). Regenerate them from the project root with:

```bash
python gephi/scripts/export_author_rankings.py
```

This reads the original full-network nodes.csv and writes four ranked CSVs, preserving every input column and adding Position and RankingMetric. It needs only Python's standard library. The manifest records the input hash, scope, and ties. Exactly 20 rows are selected by metric descending then node ID ascending; equal metric values are tied even if their displayed positions differ. Use `--top 50` for longer tables. These rankings use the existing retained counts, so running Gephi statistics is not required to produce them.

In Data Laboratory > Nodes, click each column header until the largest values appear first to inspect the same measures in Gephi. Gephi table exports may export more than the displayed/selected rows, so check before naming a file a top-20 table.

| Rank by | Interpretation |
|---|---|
| InWeightRetained | Total retained replies received: attention |
| OutWeightRetained | Total retained replies sent: response activity |
| InDegreeRetained | Number of distinct users replying to the user |
| OutDegreeRetained | Number of distinct users the user replied to |

The generated tables keep Id, Label, and all four measures. Compare whether the same users appear across rankings. For high-attention users, compare incoming weight with incoming degree: many replies from relatively few partners differs from responses from many partners. ScopeCommentCount is a count of selected source comments before edge exclusions, not the user's total Reddit activity.

For concentration, sum InWeightRetained for the top 20 recipients and divide by 15,977; multiply by 100. Do the equivalent for outgoing weight. Describe the percentage without labeling it high or low against an unspecified benchmark.

## 4. Describe repeated exchanges

In Data Laboratory > Edges, sort Weight descending and inspect the top 20 pairs. Next sort ThreadCount descending and inspect all 18 pairs with ThreadCount greater than one. Keep Source, Target, Weight, ThreadCount, FirstReplyUTC, and LastReplyUTC in the results.

Two replies within a single thread are a repeated exchange; replies across multiple threads indicate recurrence across discussions. The endpoints alone do not tell you whether those discussions occur in different subreddits. First and last dates show the observed span, not continuous participation.

To check a reciprocal pair, look for A to B and B to A in the full edge table. Count that as one unordered pair, and keep the two directional weights separately. Mutual response does not establish support, agreement, or a continuous dialogue: the replies may occur in different threads or times.

## 5. Explore structural groups in the main component

Save the full-network tables first. In Overview > Filters, expand Topology and drag Giant Component to Queries, then click Filter. Check that 9,330 nodes remain. If the count differs, clear other filters and verify that you have selected the largest weak component. Do not apply a minimum-degree or minimum-weight filter at this stage.

Run Statistics > Modularity on this filtered view. Use edge weights and resolution 1.0. Record the Randomize option, modularity score, community count, and the visible node/edge counts. Gephi's standard Modularity implementation uses an undirected view, even when the imported network is directed. Thus these are groups based on reply connections; directional roles still come from incoming/outgoing measures.

Export `nodes_largest_component_modularity_r1.csv` immediately after this run; verify it contains 9,330 records. Include Modularity Class. If an export offers visible/all graph options, choose visible for this file. Count users per class in a spreadsheet and describe the five largest groups, including each group's share of the 9,330 users.

As a small sensitivity check, optionally repeat at resolutions 0.5 and 1.5 and export each result separately before the next run overwrites Modularity Class. Record how group counts and largest-group sizes change. Class numbers cannot be compared directly across runs. These settings test dependence on resolution; they do not validate the groups or establish stable community membership.

For your baseline figure, rerun resolution 1.0 with the recorded options and export the matching node table again so the colors and final saved labels refer to the same run. Group membership can vary if randomization is enabled. Describe groups as structural groups; do not name them after topics or worker identities using network data alone.

## 6. Make one supporting figure

On the largest-component view, color nodes through Appearance > Nodes > Color > Partition > Modularity Class. Size through Ranking > InWeightRetained, initially 5 to 30. These retained columns refer to the original full network; for a complete weak component, its members have no edges to other components, so those values remain applicable. Additional filters would change that relationship.

Use ForceAtlas 2, with scaling 100 as a starting point and Prevent Overlap enabled. Stop when the layout settles. Keep labels hidden and adjust zoom to inspect groups. In Preview, use modest edge opacity, Refresh, and export an SVG or high-resolution PNG. Name it `largest_component_communities.png` or `.svg`.

Caption: "Largest weak component of the selected layoff-related author reply network (9,330 users). Node size represents retained replies received; color represents the baseline modularity partition. Layout positions have no geographical or temporal meaning." Add the visible edge count and modularity settings from your run.

## 7. Write the preliminary interpretation

Write a short account in `analysis_notes.md` with four parts:

1. Construction and scope: selected layoff-matching comments, replying-author to parent-author edges, weights, date of export, unknown/missing-parent exclusions.
2. Connectedness: full-network component count, main-component share, and small components.
3. Participation: attention/activity concentration, overlap between rankings, repeated pairs and cross-thread recurrence.
4. Structural groups: main-component modularity settings, group sizes, optional sensitivity results, and figure.

A supported starting statement is: "The retained reply network includes a large weak component containing 64.3% of users alongside many small disconnected groups. Repeated replies occur for 446 directed user pairs; only 18 pairs recur across multiple threads in this export."

Interpretation remains descriptive. Keyword selection, missing parent records, and uneven community/time coverage affect observed connectivity. User pairs aggregate over threads and time. Paths are possible structural connections, not demonstrated information diffusion. Incoming replies measure response attention, not approval or influence. Network partitions cannot establish competing narratives without content analysis. No population or causal claims follow from this stage.

## Completion checklist

- Saved Gephi project and recorded software version/settings.
- Full-network metrics and node/edge exports with verified counts.
- Attention/activity rankings and repeated-interaction tables.
- Largest-component partition export and group-size summary.
- One figure whose caption specifies the subset and visual encodings.
- Short interpretation with construction limits and scope.

This is sufficient for a preliminary structural network analysis of the current export. Narrative coding, event comparisons, and diffusion analysis remain later research tasks.

## Documentation checked

- [Gephi quickstart](https://gephi.org/quickstart/): appearance, layouts, statistics, filters, table inspection, previews, and saving.
- [CSV import manual](https://docs.gephi.org/desktop/User_Manual/Import/CSV_Format/): importing nodes/edges and preserving data types.
- [Connected Components implementation](https://github.com/gephi/gephi/blob/master/modules/StatisticsPlugin/src/main/java/org/gephi/statistics/plugin/ConnectedComponents.java): weak and strong components and their attributes.
- [Modularity implementation](https://github.com/gephi/gephi/blob/master/modules/StatisticsPlugin/src/main/java/org/gephi/statistics/plugin/Modularity.java): undirected view and weighted/resolution options.
- [Giant Component filter API](https://javadoc.io/static/org.gephi/gephi-toolkit/0.10.1/org/gephi/filters/plugin/graph/GiantComponentBuilder.html).

Menu wording can vary between Gephi versions. The local CSV baseline is independent of interface wording.
