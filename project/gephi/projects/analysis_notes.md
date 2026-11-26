# Gephi analysis notes (final, 26 November 2026)

These are the notes asked for in `gephi/README.md` sections 1 and 7. They cover four networks, all built with **Gephi's own engine**.

## 1. Software, date and how this was run

| | |
|---|---|
| Engine | **Gephi Toolkit 0.11.4**, the library behind Gephi Desktop. Fat jar `gephi/toolkit/lib/gephi-toolkit-0.11.4-all.jar` from Maven Central (`https://repo1.maven.org/maven2/org/gephi/gephi-toolkit/0.11.4/gephi-toolkit-0.11.4-all.jar`). SHA-256 `2a2f8226230965120d9c6037c93a97b685d976366bc959aab33912cf47365afa` matches the published `.sha256`. |
| Desktop app on this Mac | Gephi **0.11.3** (`/Applications/Gephi.app`). The projects were saved by toolkit 0.11.4, which is one patch release newer. See section 7. |
| Java | JDK 23.0.2, run headless (`-Djava.awt.headless=true`). |
| Date run | 26 November 2026 |
| Code | `gephi/toolkit/src/GephiRun.java`, driven by `gephi/toolkit/run.sh MODE [ARGS]` (the script header lists every mode). See "Exact commands" below. |
| Statistics used | Gephi's `Degree`, `WeightedDegree`, `ConnectedComponents` (directed: weak plus strong), `Modularity` (Louvain with the Lambiotte resolution), `PageRank` and the `GiantComponentFilter`. All are the same classes the Desktop app runs. Each HTML report from `getReport()` is in `gephi/stats/*_report.html`, with its charts beside it. |
| Layout | Gephi `ForceAtlas2`, Barnes-Hut (theta 1.2), then a prevent-overlap pass (`adjustSizes`). Starting positions come from `java.util.Random(20261126)` over the nodes sorted by Id. The exact settings for each figure are in `gephi/stats/*_layout_settings.txt`. |
| PNG | Gephi's own PNG exporter needs a screen device: it threw `HeadlessException` in `G2DRenderTargetBuilder`. So each figure is exported from **Gephi Preview as PDF** (and SVG for three of the four networks). `pdf_to_png.py` then turns page 1 into a PNG on white, 3,600–4,000 px wide, with PyMuPDF 1.24.10 in a throwaway venv. Nothing is redrawn: the PNG pixels are Gephi's vector render. |
| Slide versions | `figures/*_slide.png` (3840×2160) paste Gephi's PNG unchanged, scaled to fit, and add a Pillow legend panel and a caption strip (`make_slides.py`). |

**Exact commands (how the submitted files were made)**

Run from `gephi/toolkit/`. `pdf_to_png.py` needs `pymupdf` (`pip install pymupdf==1.24.10` in a throwaway venv); `make_slides.py` needs only Pillow.

1. `./run.sh type`, `./run.sh authors`, `./run.sh r4`, `./run.sh conv`: import, statistics, first layouts, projects and CSVs.
2. `./run.sh relayout_authors 10 1 true 1500 200 4` and `./run.sh relayout_conv 1 8 false 2000 200 4`: the final layouts of the LWCC and conversation figure workspaces (scaling, gravity, strong gravity, iterations, overlap iterations, threads).
3. Fix round (26 Nov, after the independent check): `./run.sh recolor_authors` greys the 58 smaller LWCC groups **without moving any node** (x-extent before and after: −669.99 to 671.49) and gives the full-network workspace a strong-gravity layout; `./run.sh layout_conv_full` lays out the full conversation workspace, which had been saved with every node at (0,0). The 30-component figure workspace was not touched (its x-extent stayed −3,900.7 to 3,619.3).
4. `python -B pdf_to_png.py 4000 ../figures/<name>.pdf`, then `python -B make_slides.py`.
5. `./run.sh verify` re-opens every project (section 6).

`authors` and `conv` now use the final settings by default, so a fresh `./run.sh all` reproduces the same kind of picture. **Do not re-run `authors`, `r4`, `conv` or `all` casually:** they re-run Gephi Modularity and ForceAtlas2, which are not bit-for-bit repeatable (see below), and they overwrite the projects, figures and `stats/` tables that this note quotes. The code changes to those two default paths were compiled but not executed end to end.

**Reproducibility, stated honestly**

- **Statistics.** Counts, degrees and components are exact and deterministic. Modularity was run with **Randomize = Off**. Even so, Gephi's Louvain is **not bit-for-bit repeatable** between JVM runs:
  - On the R4 network, three runs gave Q = 0.2723 with 81 classes, then 0.2726 with 84 classes, then 0.2723 with 81 classes.
  - Treat class numbers and the exact group sizes as one run's output. The tables in `stats/` match the saved projects and the figures, because they all come from the same run.
  - The October author network (section 3) was run once for the baseline. Its Q was cross-checked independently, as section 3 describes.
- **Layout.** The type network has fixed coordinates.
  - The author LWCC, R4 and conversation layouts use ForceAtlas2 with 4 threads. Re-running gives a near-identical picture but not identical coordinates. One example is the LWCC x-extent: −666.7 to 678.0 on one run, −670.0 to 671.5 on another.
  - The layout that matches each figure is the one saved in the `.gephi` and the `.gexf`.

---

## 2. Type network: comment kind to reply kind (open task 5)

- **Input:** `outputs/12_replies/gephi/type_nodes.csv` and `type_edges.csv`. These cover cscq, with 91,229 direct replies (excluding self-replies) across 18,817 threads, Jan 2025 – Sep 2026. See `outputs/12_replies/REPLY_NOTES.md`.
- **Graph:** 12 nodes, 32 directed edges.
  - The 12 nodes are 8 comment kinds, including `none`, which is the baseline, and 4 reply kinds. (`REPLY_NOTES.md` says "11-node"; the file has 12 because it includes `none`.)
  - **Edge weight = lift** against unmarked comments. The weight sum is 33.62.
- **Layout:** fixed two columns. Comment kinds sit on the left, in file order from top to bottom; reply kinds sit on the right.
- **Encoding:**
  - Edge thickness = 7 × lift (Preview, no rescaling).
  - Colour by lift band:
    - **lift ≥ 1.2: vermillion #D55E00** (7 edges);
    - 1.0–1.2: mid grey (14);
    - < 1.0: light grey (11).
  - Labels are on, 24 pt bold with a white outline. No arrows; direction is left to right.
- **The 7 strong edges:**
  - experience → sympathy **2.82**;
  - doom → advice 1.38;
  - blames_workers → sympathy 1.29;
  - ai_excuse → agree 1.29;
  - ai_replaces → agree 1.26;
  - mentions_execs → agree 1.26;
  - ai_replaces → challenge 1.23.
- **Files:**
  - `projects/type_network_lift.gephi` (plus `.gexf`);
  - `figures/type_network_lift.{png,svg,pdf}` and `type_network_lift_slide.png`;
  - `stats/type_network_{nodes,edges}.csv` and `stats/type_*_report.html`.

**Caption.** "Comment kind → reply kind in r/cscareerquestions (91,229 direct replies, Jan 2025 – Sep 2026). Edge thickness is proportional to lift against unmarked comments. Vermillion edges have lift ≥ 1.2, mid-grey edges 1.0–1.2, and light-grey edges below 1. Experience (someone's own layoff story) → sympathy reply = 2.82× (5.11% vs 1.82%). Markers are rule-based and not yet human-checked."

**Reading.** Replies to first-person layoff stories carry sympathy far more often than replies to unmarked comments. Comments that blame or invoke AI draw less sympathy and somewhat more challenge. The thick edges into "agree reply" are a marker artefact: the agree rule also fires on hostile replies that start with "This", and the stance model reads blame topics as drawing no extra agreement (`outputs/17_sentiment_stance/`). Do not read them as "blame draws agreement". This is a lead, not a Finding: the `experience` marker's precision is about 11 in 20, and the human check sheet is still open.

---

## 3. October author reply network (README sections 1, 2, 5 and 6)

### Construction and scope

- **Import.** `exports/authors_keyword-comments_direct/nodes.csv` and `edges.csv` were built directly into a Gephi graph as directed and weighted. All original columns are kept, as numbers where they are numeric.
- **Edges.** Each edge runs from the replying user to the parent author. Weight = retained replies; ThreadCount = distinct threads.
- **Exclusions.** The October export left out:
  - unknown and missing-parent authors;
  - self-replies;
  - invalid cross-thread links.

**Checks against the README baseline (all match):**

| Measure | Gephi | Baseline |
|---|---:|---:|
| Users / directed pairs / summed weight | 14,507 / 15,427 / 15,977 | 14,507 / 15,427 / 15,977 |
| Average Degree (Gephi's directed report; this is the mean in- or out-degree) | 1.0634 | 15,427/14,507 ≈ 1.063 |
| Average Weighted Degree | 1.1013 | 15,977/14,507 ≈ 1.101 |
| Weak components | 2,199 | 2,199 |
| Largest weak component | 9,330 (64.31%) | 9,330 (64.31%) |
| Two-user components | 1,771 | 1,771 |
| Strong components / largest | 12,951 / 1,210 | 12,951 / 1,210 (FINDINGS.md) |
| Pairs with weight > 1 / ThreadCount > 1 | 446 / 18 | 446 / 18 |

- Gephi's `In-Degree` and `Weighted In-Degree` equal the exported `InDegreeRetained` and `InWeightRetained` for every node (checked with pandas).

**Table exports, all with every original column plus Gephi's columns:**

| File | Rows |
|---|---:|
| `stats/nodes_full_metrics.csv` | 14,507 |
| `stats/edges_full.csv` | 15,427 |
| `stats/nodes_largest_component_modularity_r1.csv` | 9,330 |
| `stats/nodes_largest_component_modularity_r050.csv` | 9,330 |
| `stats/nodes_largest_component_modularity_r150.csv` | 9,330 |
| `stats/edges_largest_component.csv` | 12,360 |

### Largest component and modularity

- **Filter.** Topology > Giant Component (`GiantComponentFilter`) leaves **9,330 nodes and 12,360 edges**, with a weight sum of 12,845.
- **Workspace.** That filtered set is stored as its own workspace in the project, so the project opens straight onto it. Connected Components on that workspace gives 1 component.
- **Modularity settings:** Use edge weights = On; **Randomize = Off**. Gephi's Modularity treats the graph as undirected.
- **Run order** follows the README: 0.5, then 1.5, each exported straight away, then the 1.0 baseline last. The baseline is the run that the figure, the colours and the saved project use. In `nodes_largest_component_modularity_r050.csv` and `..._r150.csv`, the column "Modularity Class" holds that file's run.

| Run | Resolution | Q (Gephi "Modularity") | Q with resolution | Groups | Largest group |
|---|---:|---:|---:|---:|---|
| Sensitivity | 0.5 | 0.809 | 0.399 | 113 | 345 (3.70%) |
| **Baseline** | **1.0** | **0.813** | 0.813 | **66** | 361 (3.87%) |
| Sensitivity | 1.5 | 0.810 | 1.230 | 49 | 550 (5.89%) |

**Baseline top-5 groups (shares of the 9,330 users):**

| Group | Users | Share |
|---|---:|---:|
| 6 | 361 | 3.87% |
| 0 | 341 | 3.65% |
| 24 | 270 | 2.89% |
| 16 | 251 | 2.69% |
| 15 | 250 | 2.68% |

- The full ranked list is `stats/authors_lwcc_modularity_r1_group_sizes.csv`. Group numbers have no topic meaning.
- **Within-group replies:** 10,666 of 12,845 retained replies (**83.0%**) link users in the same baseline group.
- **Resolution effect.** In Gephi's convention, a lower resolution gives more and smaller groups (113 at 0.5), and a higher one gives fewer and larger groups (49 at 1.5). Q stays near 0.81 throughout. This tests sensitivity to the setting; it does not validate the groups.
- **Independent check.** networkx weighted modularity (γ = 1, mutual edges summed) on the exported baseline partition gives **Q = 0.8115**, against Gephi's 0.813.
  - The October partition (FINDINGS.md: 55 main-component groups, largest 412) had Q = 0.806 within the main component.
  - The new run gives a similar picture, with slightly finer groups.

### Figure

- **Colour = baseline modularity class.**
  - The 8 largest groups use fixed colour-blind-safe colours: #0072B2, #D55E00, #009E73, #CC79A7, #E69F00, #56B4E9, #882255 and #999933.
  - The other 58 groups (7,161 users, 76.8%) are one grey, #C8C8C8, so only the 8 largest groups are identifiable. (The first render gave them pale pastel hues, which were easy to confuse with the 8 legend colours; they were greyed in the fix round with positions unchanged.)
  - The colours are arbitrary group IDs. The same palette means author types on the R4 type slide, so say this aloud when the slides are shown back to back.
  - The full mapping is in `stats/authors_lwcc_palette.csv`.
- **Size** = Ranking on InWeightRetained, linear, **5–30** (min 0, max 300).
- **Layout:** ForceAtlas2, scaling 10, gravity 1, **strong gravity on**, 4 threads, 1,500 iterations, then prevent overlap (200 iterations).
  - The README's starting point (scaling 100, normal gravity) was tried first. It spread the tree-like component over about 50,000 units, so nodes were invisible at slide size. LinLog was also tried and was no better.
- **Preview:** edges at opacity 45 with mixed colour, no labels, no arrows.
- **Files:**
  - `figures/largest_component_communities.{png,svg,pdf}` and `largest_component_communities_slide.png`;
  - `projects/author_replies.gephi` (plus `author_replies_largest_component.gexf`).

**Caption.** "Largest weak component of the selected layoff-related author reply network (9,330 users, 12,360 directed user pairs). Node size represents retained replies received; colour represents the baseline modularity partition (Gephi Modularity, edge weights on, resolution 1.0, randomize off; 66 groups, Q = 0.813). Layout positions have no geographical or temporal meaning."

### Interpretation, in four parts (descriptive)

1. **Construction and scope.**
   - Edges run from the replying author to the parent author. They come from selected layoff-matching comments in the October export, and the parent comment need not match.
   - Weights count retained replies.
   - Unknown or missing parents, self-replies and invalid cross-thread links were excluded.
   - Keyword selection and uneven community and time coverage both shape which connections are observed.
2. **Connectedness.**
   - The retained reply network has a large weak component holding **64.3% of users** (9,330 of 14,507), alongside **2,198 small disconnected groups**. 1,771 of those groups are single user pairs.
   - Mutual directed reachability is much rarer: the largest strong component has 1,210 users.
3. **Participation.**
   - Attention is concentrated: the top 20 recipients receive 7.32% of retained replies, and the top 20 senders send 4.89% (FINDINGS.md).
   - Repeated replies occur for **446 directed user pairs**. Only **18 pairs recur across multiple threads**, so most connections are one-off.
   - In the figure, one user receives 300 replies from 296 distinct users. That is the large blue node at the bottom.
4. **Structural groups.**
   - At resolution 1.0, Gephi finds 66 groups in the main component (Q = 0.813).
   - The largest group holds only 3.9% of users, and 83% of replies stay within a group.
   - The group count depends on resolution: 113 groups at 0.5 and 49 at 1.5.
   - These are groups of reply connections. They are not topics, narratives or worker identities, and the network alone cannot name them.

Paths are possible structural connections, not demonstrated information flow. Incoming replies measure response attention, not approval. No population or causal claims follow from this.

---

## 4. R4 cscq author-type network (`outputs/15_network/network_profiled.gexf`)

### Input and checks

- **Import.** GEXF through Gephi's importer with DefaultProcessor, directed.
- **Graph:**
  - **10,778 nodes**, which are the profiled authors (at least 5 comments) of the cscq LWCC, Jan–Jun 2025;
  - **91,657 directed edges** with weight sum 115,171;
  - no positions in the input.
- **Types:**

| Type | Authors |
|---|---:|
| story-sharer | 233 |
| blame-talker | 577 |
| helper | 1,770 |
| other | 8,198 |

  Low-activity authors are not in this file.
- **Average Degree** 8.504; **Average Weighted Degree** 10.686.
- **Connected Components:** 49 weak components. The largest has 10,730 authors (99.55%).
  - This is because restricting to profiled authors drops the low-activity authors who connected the remaining 48.
- **PageRank:** directed, p = 0.85, ε = 0.001, edge weights on.
  - Values range from 1.48e-5 to 6.51e-3.
  - Gephi's `pageranks` column is used for node size. The GEXF's own `pagerank` attribute, from networkx, is kept as well.
- **Modularity:** weights on, resolution 1.0, **Randomize Off**.
  - The saved run has **Q = 0.2723 with 81 classes**. A repeat run gave 0.2726 with 84 classes (see section 1).
  - The 8 largest classes hold 704, 658, 648, 580, 577, 559, 528 and 409 authors (6.5% down to 3.8%). The exact list is in `stats/r4_modularity_group_sizes.csv`.
  - How types spread across classes is in `stats/r4_type_by_modularity_class.csv`.
  - **Type mix inside the 8 largest classes stays close to the overall mix.** Overall: story-sharer 2.2%, blame-talker 5.4%, helper 16.4%, other 76.1%. Inside those classes: story-sharer 1.0–3.3%, blame-talker 3.9–7.3%, helper 15.0–19.0%, other 73.5–77.8%. This matches NETWORK_NOTES N4: groups do not line up with types.

### Comparison with the Louvain Q ≈ 0.43 in NETWORK_NOTES.md

That value (59 communities) comes from Louvain on the **whole cscq LWCC: 30,976 authors, including about 20,000 low-activity authors**. Gephi here runs on the **profiled subgraph only**: 10,778 authors and only the ties among them. The two Q values are therefore **not directly comparable**.

Part of the gap is also a convention. Gephi's Modularity works on an undirected view that keeps one weight per mutual pair (A→B and B→A collapse to the larger weight). With mutual weights summed instead, the same Gephi partition scores Q ≈ 0.31 in networkx, and networkx Louvain on this subgraph reaches about 0.33 (the 59 NETWORK_NOTES communities restricted to this subgraph score 0.325). So every estimate agrees on modest structure in the profiled core, well below the 0.43 of the full LWCC. On the October LWCC the convention barely matters (Gephi 0.813 vs networkx 0.8115).

The lower Gephi Q (0.27) fits the profiled authors being the dense, well-mixed core: NETWORK_NOTES N4 finds "one well-mixed block" in the core, where Louvain gets Q = 0.22. Both runs agree on the substantive point: interaction groups exist, but they do not line up with author types.

### Figures

Both figures use the same ForceAtlas2 layout:

- scaling 10, gravity 1, strong gravity on (otherwise the 48 tiny components fly off and the core renders as a dot);
- 4 threads, 1,000 iterations, then prevent overlap (100 iterations);
- edges at opacity 6% with source colour; no labels;
- node size 4 + 36 × sqrt((PageRank − min)/(max − min)). The square root keeps the long tail visible.

The two figures:

- `figures/r4_author_types.{png,pdf}` and `_slide.png`. Colour = type, using the shared palette: story-sharer #0072B2, blame-talker #D55E00, helper #009E73, other #CC79A7.
- `figures/r4_modularity.{png,pdf}` and `_slide.png`. Colour = Gephi Modularity class: the 8 largest in fixed colours, the rest grey #C8C8C8. This is the second workspace in the project.
- There is no SVG for R4: with 91,657 edges the SVG is about 44 MB and slow to export. Use the PDF for vectors.

**Captions.**

- "r/cscareerquestions reply network, Jan–Jun 2025: 10,778 profiled authors (≥ 5 comments) and 91,657 directed pairs. Colour = rule-based author type; size = Gephi PageRank. Typed authors are not at the edge or in separate regions; they sit slightly nearer the centre than other authors, probably because they are more active (N1, N4). ForceAtlas2; positions have no geographic or temporal meaning."
- "Same cscq network and layout as the author-type figure; colour = Gephi Modularity class (weighted, resolution 1.0, randomize off; 81 classes, Q = 0.27 on this profiled subgraph). Groups cut across author types; class numbers have no topic meaning." Slide note: "Colours here are arbitrary group IDs, not author types."

**Where typed authors sit (radial check on the saved layout).** Splitting the R4 layout into five rings by distance from the centre: blame-talkers are 8.7% of the inner ring and 2.6% of the outer; helpers 18.5% vs 9.6%; story-sharers 3.2% vs 1.3%. The outer ring is 86.5% "other". Median radius: blame-talker 857, story-sharer 873, helper 948, other 1,015. So typed authors are mixed in, not on the edge, but sit slightly nearer the centre, which fits N1's activity effect. (Numbers from the independent verifier's check of `r4_cscq_author_types.gexf`.)

**Files:** `projects/r4_cscq_author_types.gephi` (workspaces: types, modularity) plus `r4_cscq_author_types.gexf`; `stats/r4_*`.

---

## 5. Conversation network (stretch)

- **Input:** `exports/conversations_keyword-posts_direct/`.
- **Graph:** 13,866 records (654 posts and 13,212 comments; 6 records not present) and 13,206 reply links, with no missing endpoints.
- **TextPreview is never imported** into Gephi. No text labels are drawn or stored.
- **Communities:**

| Subreddit | Records |
|---|---:|
| technology | 11,578 |
| programming | 2,282 |
| blank | 6 |

  cscq has no posts in the database, so it is absent here.
- **Degree:** Average Degree 0.952. The maximum in-degree is 891 direct replies, to one record.
- **Components:** 660 weak components. The largest has 2,190 records (15.79%); 558 are single records, such as posts with no retained reply.
  - The 30 largest components hold 12,156 records.
- **Figure:** the 30 largest components.
  - ForceAtlas2: scaling 1, gravity 8, 4 threads, 2,000 iterations, then prevent overlap (200 iterations).
  - Colour = subreddit: technology #56B4E9, programming #009E73.
  - Size = 3 + 27 × sqrt(in-degree / max).
  - Edges at opacity 60; no labels.
- **Files:** `figures/conversation_largest_components.{png,svg,pdf}` and `_slide.png`; `projects/conversations.gephi`, with 2 workspaces (full network, and the 30-component figure).

- **Full-network workspace:** laid out in the fix round with the same ForceAtlas2 settings (`stats/conv_full_layout_settings.txt`); no figure is exported from it.

**Caption.** "Keyword-selected post/comment conversation network (13,866 records, 13,206 reply links); the 30 largest weak components. Node size = replies received. Each connected cluster is one thread (one post and its reply tree); each star is a heavily answered post or comment. No text is shown." Each of the 30 components holds exactly one post; several stars can belong to one thread.

---

## 6. Re-open check

`run.sh verify` re-opens every saved project with the toolkit, in a fresh JVM. The log is `stats/run_verify.log`.

The log now also prints the modularity class count and the x-extent and number of nodes at (0,0) per workspace (re-run after the fix round: every workspace has 0 nodes at (0,0)).

| Project | Workspace | Nodes | Edges | Weight sum | Modularity classes | x-extent |
|---|---|---:|---:|---:|---:|---|
| `author_replies.gephi` | Full network | 14,507 | 15,427 | 15,977 | – | −741.7 to 747.0 |
| `author_replies.gephi` | Largest weak component | 9,330 | 12,360 | 12,845 | 66 | −670.0 to 671.5 |
| `type_network_lift.gephi` | Comment kind to reply kind | 12 | 32 | 33.62 | – | −520 to 520 |
| `conversations.gephi` | Conversation network | 13,866 | 13,206 | 13,206 | – | −7,398.9 to 5,343.7 |
| `conversations.gephi` | 30 largest components | 12,156 | 12,126 | 12,126 | – | −3,900.7 to 3,619.3 |
| `r4_cscq_author_types.gephi` | R4 author types (colour = type) | 10,778 | 91,657 | 115,171 | 81 | −1,408.5 to 1,417.8 |
| `r4_cscq_author_types.gephi` | R4 Gephi modularity (8 largest coloured) | 10,778 | 91,657 | 115,171 | 81 | −1,408.5 to 1,417.8 |

## 7. How to open the projects in Gephi Desktop

1. Open Gephi 0.11.3, then File > Open, and choose a file in `gephi/projects/`.
2. Switch workspaces from the workspace selector at the bottom of the window (or Window > Workspaces).
   - `author_replies.gephi` has "Full network (14,507 users)" and "Largest weak component (9,330 users)".
   - `r4_cscq_author_types.gephi` has "R4 author types (colour = type)" and "R4 Gephi modularity (8 largest coloured)".
   - `conversations.gephi` has the full network and the 30-component figure workspace.
   - **For a demo or screen recording**, open the figure workspaces: "Largest weak component (9,330 users)", either R4 workspace, the type network, and "30 largest components (figure)". These match the slides. The two full-network workspaces are laid out (author: strong gravity, scaling 10; conversation: gravity 8, scaling 1) and coloured, but were never rendered as figures; the author one shows users outside the largest component in light grey #E2E2E2.
3. The node colours, sizes and positions are stored in the project. Go to the **Preview** tab and press **Refresh**. If Preview defaults reset, set:
   - edge opacity: about 6 for R4, 45 for the author network, 60 for the conversation network;
   - Show labels: off, except for the type network.
4. Statistics columns (Degree, Component ID, Modularity Class and PageRank) are in Data Laboratory.

**If a project will not open.** The files were saved by toolkit 0.11.4, and Desktop is 0.11.3; this has **not been tested in the GUI**. Instead, use File > Open on the `.gexf` beside each project:

- `author_replies_largest_component.gexf`
- `r4_cscq_author_types.gexf` (types workspace)
- `type_network_lift.gexf`

These carry positions, colours, sizes and every attribute column.
