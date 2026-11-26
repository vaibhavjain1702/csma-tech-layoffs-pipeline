# Solidarity or Blame: the project in layers

*26 November 2026 (first written 25 November; updated for the final submission). This file organises the whole project as a stack of layers. It starts from the raw data and builds up to the social-media concepts the report is about. Each layer answers one question, uses only what the layers below it established, and has its own validity check. `docs/PROJECT_REFERENCE.md` stays the master reference for team, method and the full file map. The earlier version of this file, organised by result, is in `outputs/archive/PROJECT_REFERENCE_2_by_result.md`.*

**How to read it.** A claim is only as strong as the weakest layer under it. Most open problems sit at layer 0 (what was collected) and layer 3 (labels nobody has checked). Both limit everything built on top of them, which is why validation comes before writing.

---

## The stack at a glance

| Layer | Question | State | Weakest point |
|---|---|---|---|
| **7. Concepts** | What does this say about solidarity, blame, echo chambers and polarisation? | Synthesis written | It inherits every weakness below it. Polarisation cannot be measured |
| **6. Network** | How are people connected, and does their role shape their position? | Done (R4) | The graph has comments only, no posts |
| **5. Interaction** | What kind of reply does each kind of comment get? | Done (R3) | Reply markers unchecked; the agree marker is unreliable |
| **4. Comparison** | How do communities, periods and people differ? | Done (R1, R2, D1–D4) | The cross-poster group is small |
| **3. Slices and labels** | Which comments are about disruption, and what does each one do? | Built; **not human-checked** | **The main bottleneck** |
| **2. Distributions** | What does the data look like before any labels? | Done | Heavy tails |
| **1. Processed data** | Is the data clean and linked? | Done | Missing parent comments |
| **0. Collection** | What was collected, and what is missing? | Done | **No cscq posts; coverage differs by community** |

**Layers vs the report.** The layers are how the analysis is built. R1–R5 are how the report presents it.

| Report result | Layer |
|---|---|
| R1 (where disruption talk lives) | 4 |
| R2 (how communities talk) | 4, including D1 |
| R3 (how replies respond) | 5 |
| R4 (network) | 6 |
| R5 (validity) | The validity check of every layer, gathered in one table |

Visualisation is not a layer of its own: each layer produces its own figures, and the Tableau files are named by result.

---

## Layer 0. Collection: what exists and what doesn't

**Question.** What did we collect, and what did the platform or the archive leave out?

| | |
|---|---|
| Source | Arctic Shift (Vaibhav). **Settings known:** full-subreddit pulls (`posts/search`, `comments/search`, `after`/`before` timestamps, limit 100, sort asc), no keyword filter at collection, 3 of 7 configured subreddits collected, run 23–24 Sep 2026. See `collection/PROVENANCE.md` |
| Size | 115,213 posts and 2,859,037 comments (2.97M records) |
| Coverage | cscq comments Jan 2025 – Sep 2026; r/technology Jan – Jun 2025 (23 of 26 weeks); r/programming Jan – Dec 2025 |
| **Missing** | **No cscq posts at all**, in any month |

- **Concept: platform and archive artefacts.**
  - Because there are no posts, 108,722 cscq replies to posts (40% of human comments) have nothing to point at, and layoff stories told as a post are invisible.
  - Coverage ends on different dates, so a trend can be a coverage effect.
- **What it allows the layers above.** Claims about "the collected corpus" only. Comparisons between communities use the shared window (Jan–Jun 2025); trends over time use cscq only.
- **Validity.** External validity is set here: three subreddits, a 2025 window, comments only.
- **Cause of the gaps.** The comment streams for r/technology (to 2025-06-09) and r/programming (to 2025-12-12) stopped months before the collection date, and no cscq posts were saved. The collector stops silently on API errors, or the run was interrupted; no logs were kept, so we cannot say which. Evidence: `collection/PROVENANCE.md`.
- **Open item: state the limit up front.** The team decided **not to collect more data**, so every claim says "the collected corpus" and the missing cscq posts are named as a limit.
- **Files.** `outputs/01_profile/`, `docs/PROCESS_REPORT.md`, `collection/PROVENANCE.md` (how it was collected and why coverage differs), `collection/` (collector code, config, checkpoints), `collection/verify_raw_timeline.py` (re-checks the timeline from the raw files).

## Layer 1. Processed data: clean, pseudonymous, linked

**Question.** Is the text usable, are authors handled ethically, and is the reply structure correct?

| | |
|---|---|
| Text | 94.61% of comment bodies are usable. HTML is decoded, quoted lines are separated so that `own_text` holds only the author's words, and deleted or removed text is marked |
| Authors | Stable pseudonyms (`author_key`) and a bot flag (`likely_bot`) |
| Structure | Reply edges are rebuilt from parent links. Missing parents are kept and marked |
| Database | `data/processed/reddit.sqlite`. Every analysis opens it read-only |

- **Validity.**
  - The bot flag matters: taking bots out of the denominator moves R1 from 2.33% to 2.45%.
  - Author keys are unsalted hashes, so a guessed username can be confirmed. They must never appear in outputs, and all exports use neutral ids.
- **Files.** `outputs/02_preprocessing/`, `outputs/03_tables/`, `docs/METHODOLOGY.md`, `docs/DATA_DICTIONARY.md`.

## Layer 2. Distributions: what the data looks like

**Question.** Before any label is applied, what is the shape of activity?

- **Volume over time** differs by community and has gaps (see layer 0).
- **Author activity is heavy-tailed.** Among cscq authors in Jan–Jun 2025:

  | Authors with | Number | Share of all comments |
  |---|---:|---:|
  | ≥5 comments | 10,922 | 80% |
  | ≥20 comments | 2,683 | 53% |

- **Attention is concentrated.** The top 1% of users receive 17.8% of replies (October Gephi network). 97% of author pairs exchange only one reply. Degree has a long tail (`15_network/fig_degree_ccdf`).
- **Thread sizes are skewed.** A few mega-threads hold many of the comments.
- **Scores are snapshots**, and they favour comments that arrived early.
- **Concept: heavy-tailed distributions.**
- **What it requires of the layers above:**
  - use medians rather than means;
  - compare within activity bands, or match on activity;
  - profile authors only if they have 5 or more comments;
  - run a check without the mega-threads;
  - use score percentiles within a thread and control for early arrival.
- **Files.** `outputs/04_analysis/` (five figures), Tableau `r1_daily_by_community`, `r1_threads`.

## Layer 3. Slices and labels: turning text into variables

**Question.** Which comments are about disruption, and what is each one *doing*?

**Slices**:
- six employment screens (177,808 candidate records);
- the shared window (Jan–Jun 2025);
- cscq only;
- cross-posters (the same author in two communities).

Within cscq Jan–Jun 2025, there are 40,950 employment comments from 14,235 authors.

**Labels** are all rule-based markers, and none has been checked by a person.

| Kind | Labels | What it really measures | Provisional precision |
|---|---|---|---|
| Speech act | `experience` (telling your own story) | What a comment does | 39/40 on layoff comments; about 11/20 overall |
| Topic | `mentions_execs`, `mentions_offshore`, `ai_excuse` | What it talks about, **not whom it blames** | Only 7 of 70 offshoring mentions blame foreign workers |
| Claim | `ai_replaces`, `doom` | A view about the future | `ai_replaces`: only 7 of 30 agree with it |
| Reply function | `sympathy`, `advice`, `agree`, `challenge` | How a reply responds | **Not checked by a person.** `agree` also fires on hostile replies that start with "This…": the stance model reads only 30% of those as agreement, against 82% of other agree hits |
| Screens | layoffs; hiring | Ways to find candidate comments | About 95%; **about 22%, so do not quote hiring figures** |
| Model labels (extra signal) | sentiment (VADER, RoBERTa); zero-shot stance `blames_execs`, `ai_is_excuse`, `blames_offshore`, reply `agrees`/`disagrees`/`sympathy` | Off-the-shelf models, not trained on our data | Read against examples: `blames_execs`, `ai_is_excuse` and reply `agrees` are usable; **`blames_offshore` (recall 0.14) and reply `disagrees` (fires on 62% of replies) are not**. See `17_sentiment_stance/` |

- **Concept: construct splitting.** A topic is not blame, and emotional support is not informational support.
- **Concept: reliability vs validity.**
  - The markers are perfectly consistent: the same input always gets the same label. That doesn't make them correct, which is what validity means.
  - The agree marker is consistent and wrong.
  - Two human coders give both: agreement between coders (reliability) and precision (validity).
- **This is the bottleneck.** Every number in layers 4–7 counts these labels. Until someone codes the 240-row check sheet (`outputs/12_replies/check_sheet.csv`), nothing can be a Finding. The kit for doing it is ready: `docs/HUMAN_CHECK_GUIDE.md`, the coder files in `annotations/human_check/` and `scripts/score_human_check.py`. The coding itself is not done yet.
- **Files.** `outputs/03_tables/`, `outputs/05_sample/`, `outputs/07_annotations/`, `outputs/09_leads/`, `scripts/explore_leads.py` (`M`), `scripts/explore_replies.py` (`PARENT`, `REPLY`).

## Layer 4. Comparison: communities, periods and people

**Question.** Using the labels, how do communities, time periods and individual authors differ?

| Result | What we found | Label |
|---|---|---|
| **R1. How much, and when** | Layoff talk is 2.45% of cscq comments vs 0.20% in r/technology. Inside threads that mention layoffs it is 4.06% vs 0.49%. 67% vs 21% of large threads contain it. Weekly variability (CV) is 0.21 for cscq, 0.45 for r/technology and 0.76 for r/programming | Supported |
| **R2. How it is framed** | cscq posts own stories (8.9% vs 3.1%) and links to labour statistics (FRED, BLS). r/technology frames layoffs in corporate and political terms and links to news. r/programming talks about the craft | Supported |
| **D1. The same person in two places** | About 150 people post in both communities. Their mentions of executives are about equal in the two (6.6% vs 5.8%), but their AI talk differs by 9.4 points. **Stance (model):** within the same 152 authors, the gaps in *blaming* executives and AI also disappear (every CI includes 0), although r/technology blames more across all authors | Lead |
| **D3. A shock** | After the H-1B announcement (19 Sep 2025), offshoring talk went from 13% to 43% for one week, then fell below its earlier level. The framing didn't change | Supported |
| **AI as an excuse** | Did not grow. AI talk overall doubled, so the excuse share only looked bigger | Supported |
| Spikes | A shared spike in mid-May 2025; cscq's top week is 21 April. **Neither is matched to an event yet** | — |

- **Concept: base rate vs lift.** Always give the absolute rates as well as the ratio.
- **Concept: unit of analysis.** Comment, thread, week or person each give a different claim. The D1 gap disappearing is a composition effect: the communities differ partly because different people post in them.
- **Validity.** Shared-window denominators, bots excluded, checks within threads. **Open:** pick one window (Jan–May or Jan–Jun 2025).
- **Files.** `outputs/08_midterm/`, `outputs/10_language/`, `outputs/11_dynamics/`, `outputs/13_interpretation/`, `outputs/14_directions/`, Tableau `r1_*`, `r2_*`.

## Layer 5. Interaction: comment → reply

**Question.** Does what a comment does predict how people answer it?

| Result | What we found | Label |
|---|---|---|
| **R3. Stories draw comfort** | Sympathy in 5.11% of replies vs 1.82% for unmarked comments (×2.82). Advice does not rise. **Window: all cscq months, Jan 2025 – Sep 2026** (91,229 reply pairs). Jan–Jun 2025 alone gives 4.42% vs 1.93% (×2.29), the same direction | Supported |
| **R3. Doom draws information** | Advice ×1.38 | Supported |
| **R3. Blame topics draw less support, and no extra agreement** | Comments about executives, offshoring or AI as an excuse get less sympathy. The marker showed slightly more "agreement" (×1.0–1.5), but read by the stance model it is flat (×0.92–1.19, every CI overlapping the baseline). Half of all agree-marker hits start with "This", and only 30% of those are read as agreement | Lead: drop "blame draws agreement". Don't claim "debate" either, because the model's disagreement label is unusable |
| **D2. Coming back** | Newcomers who get any reply come back more often (50% vs 39%) | Lead; not causal |
| **Sentiment check (S2)** | Negativity does not explain the story → sympathy effect. Comparing parents of the same sentiment gives ×2.33, against ×2.35 overall (Jan–Jun 2025) | Lead (model signal) |

- **Concept: emotional vs informational support.** The type of support matches the type of need.
- **Concept: base rate vs lift.** Even so, about 95% of replies to stories are not sympathetic.
- **Validity.** CIs are clustered by thread; the effect holds within a length band and within a sentiment band; vote percentiles agree. **The reply markers are unchecked.**
- **Files.** `outputs/12_replies/REPLY_NOTES.md`, `outputs/17_sentiment_stance/SENTIMENT_STANCE_NOTES.md`, Tableau `r3_*`.

## Layer 6. Network: who is connected to whom

**Question.** Moving from comments to people: does an author's role shape their position and the flow of replies?

**Scope.** The cscq author reply graph, with an edge from each replier to the author they replied to, Jan–Jun 2025. The largest connected component has 30,976 authors (97%) and 162,024 replies. Bots and deleted authors are excluded.

| | Result | Label |
|---|---|---|
| **N1** | **Position follows activity, not role.** The expected picture, with helpers at the centre and story-sharers on the edge, is contradicted | Supported (no difference) |
| **N2** | Story-sharers receive 1.6–1.9× more sympathy, whoever is replying | Lead |
| **N3** | Blame-talkers reply to each other 1.69× more than chance (z = 8 against a model that shuffles replies within threads). Inside the group challenge rises (7.2% vs 4.5%) and agreement does not. **Tone (model):** their replies to each other are negative 50% of the time vs 40% between other authors, and the gap holds at equal parent sentiment (7–14 points) | Supported; the tone part is a Lead |
| **N4** | The 59 Louvain communities (Q = 0.43) are not sorted by author type (NMI ≈ 0.005) | Supported (no difference) |
| **N5** | k-means finds clusters for story, executives, AI-as-excuse and the rest, but no helper cluster. It barely matches the rule-based types (ARI 0.14) | Lead |

- **Concept: direct vs shared ties.** A reply is attention, not agreement. The within-thread null separates choosing whom to answer from simply being in the same thread.
- **Concept: null models.** Report the within-thread null, because it is the stricter test. Q has not been compared with a null model, so don't call the community structure strong.
- **Concept: heavy tails.** How active someone is explains where they sit.
- **Validity.**
  - Activity matching.
  - Results hold with the top 1% of threads dropped.
  - Label noise simulated.
  - Results checked at other activity cut-offs (N = 3, 10, 20).
  - **Comments only.**
  - Do **not** report the story → story lift of 1.35.
- **Files.** `outputs/15_network/NETWORK_NOTES.md`, `network_profiled.gexf`, `gephi/`, Tableau `r4_*`.
- **Gephi projects and figures (26 Nov).** `gephi/projects/` holds four saved projects (`author_replies.gephi`, `r4_cscq_author_types.gephi`, `type_network_lift.gephi`, `conversations.gephi`), `.gexf` fallbacks and `analysis_notes.md`; `gephi/figures/` holds the figures and `*_slide.png` versions; `gephi/stats/` holds Gephi's statistics tables and reports. They were built headless with the Gephi Toolkit 0.11.4. Gephi's modularity on the 10,778 profiled authors is Q = 0.27, which is **not comparable** to the Louvain Q = 0.43 above: that was run on all 30,976 authors of the largest component.

## Layer 7. Concepts: what it all means

**Question.** What do layers 4–6 together say about the social phenomena in the title?

| Concept | Definition in our data | Evidence (layer) | Verdict | What would strengthen it |
|---|---|---|---|---|
| **Solidarity** | Sympathy replies to people who tell their own story | R3 ×2.82 (5); N2 (6); D2 (5) | **Supported.** It follows disclosure, not a shared enemy | Checked reply labels; absolute rates next to the lift |
| **Sentiment is not stance** | How well tone separates story comments from blame comments | A score of 0.50 in cscq, where 0.5 is chance (17) | **Supported.** Sentiment would merge solidarity and blame | — |
| **Type of support** | Emotional support (sympathy) vs informational support (advice) | Stories draw sympathy; doom draws advice (5) | **Supported.** The support matches the need | — |
| **Blame** | *Topic* mentions of executives, offshoring, AI as an excuse; plus a zero-shot stance reading | R2 (4); R3 (5); N3 (6); stance model (17) | **Mostly topic.** The stance model reads only 8% of executive mentions as blame. Blame of executives and of AI is usable as a model signal; blame of offshoring is not | Stance labels checked by people (Krish) |
| **Affective (antagonistic) echo chamber** | People cluster together more than a null model predicts, and challenge rather than agree inside the cluster | N3: lift 1.69, z = 8; challenge up, agreement flat; more negative tone inside the group at equal parent sentiment (6, 17) | **Consistent with one**: an argument group with a hostile tone | Show that the people arguing hold opposing stances |
| **Polarisation** | Would need stance groups and a measure of how much they interact across groups | Tried with the stance model: only 9–40 replies per target, and no usable disagreement label (17) | **Not measurable now** | Stance labels checked by people, plus a measure of cross-group interaction. Don't claim it |
| **Selection vs influence** | Whether the same person frames things differently in different communities | D1: executives framing the same; AI talk differs (4). Stance: within the same 152 authors, gaps in blaming executives and in blaming AI also disappear (17) | **Lead.** Blame is brought in by people; AI *talk* is shaped by the community | A larger cross-poster set |
| **Participation inequality** | How concentrated activity and attention are | Heavy tails (2); N1 (6) | **Supported.** The network is a crowd, not a set of roles | — |
| **Issue-attention cycle** | Steady vs bursty talk, and shocks that fade | Weekly variability; D3 (4) | **Supported.** Disruption is a standing condition in cscq and news elsewhere | Match the spikes to events |
| **Framing / evidence cultures** | What kind of evidence each community uses | Stories and labour statistics vs news vs craft (4) | **Supported** | — |

Selection vs influence, participation inequality, the issue-attention cycle and framing are standard social-media concepts that are **not on the course list**. Check them against the course readings before using them.

**The argument in three claims.**
1. **Disruption is a standing condition for those affected and news for everyone else.** (Issue-attention cycle; evidence cultures.)
2. **Communities answer disclosure with support, and give blame less support and no extra agreement. The people who keep raising blame argue among themselves in a more hostile tone.** (Solidarity; type of support; affective echo chamber.) Sentiment alone could not show this, because stories and blame sound equally negative.
3. **Who blames whom is mostly brought in by people; what gets talked about is shaped by the community. The network is organised by how much people take part, not by their roles.** (Selection vs influence; participation inequality.)

**What we are not claiming.**
- That Reddit is a support community: most replies to stories are not sympathetic.
- Polarisation by stance.
- Cause and effect.
- Anything beyond three subreddits, Jan–Jun 2025, comments only.

---

## Next steps, by layer (lowest first)

| Layer | Task | What it unblocks |
|---|---|---|
| 0 | ~~Decide about the cscq posts~~ **Done:** the team will not collect more data; the limit is stated up front (see layer 0 and `collection/PROVENANCE.md`) | Coverage for layers 5–6 |
| 3 | **Code the 240-row check sheet** with a second coder, ideally Krish, and include the hostile "This…" replies. The kit is **ready** (`docs/HUMAN_CHECK_GUIDE.md`, `annotations/human_check/`, `scripts/score_human_check.py`); the coding is **not done** | Every Finding |
| 3 | Show Krish the R3 and R4 results | Stance labels, needed for blame and polarisation |
| 4 | Pick one shared window. Match the 21 April, mid-May and mid-December spikes to events | Consistent R1 numbers, and an explanation for the spikes |
| 5–7 | Fix the wording: blame topics draw *less support and no extra agreement* (not "agreement", not "debate"); the executives vs AI split; absolute rates next to every lift. **Done in the reference docs and in `REPLY_NOTES.md` on 26 Nov; the report is written by others** | Report draft |
| All | Build one validity table with a row per layer, from `16_tableau/r5_robustness_long.csv`. The Tableau workbook has the R5 sheets (coverage, marker precision, robustness) | R5 |
| 6 | ~~Gephi projects and figures~~ **Done 26 Nov** (`gephi/projects/`, `gephi/figures/`). Tableau workbook **built** (`tableau/`); opening it in Tableau Desktop is still to be confirmed | Final presentation |
| — | Write the report in order: layers 0–3 as data and method, 4–6 as results, 7 as discussion | — |

**Not now:** new analyses, markers or models, unless a layer above needs them.

## Before committing or sharing

- Keep `outputs/15_network/examples.txt` and `outputs/17_sentiment_stance/examples.txt` private: they contain verbatim comments. Both are git-ignored.
- Model scores are cached in `data/processed/model_scores.sqlite`, which is git-ignored and keyed by Reddit id.
- Author keys must never appear in outputs. The R4 ids (`a…`/`n…`) and the Tableau ids (`p…`/`t…`) are separate schemes that cannot be joined.
- Large files: `network_profiled.gexf` is 15 MB; `outputs/16_tableau/` is 42 MB. The Gephi toolkit jar is 88 MB and `gephi/figures/` is about 100 MB.
- The public GitHub repo `lazinWolf/csma-layoff-sentiment` reflects the state of **26 Nov 03:15** (including the sentiment and stance work, commit `810dc19`). It does **not** include the additions made later on 26 Nov: the Gephi projects and figures, the Tableau workbook, `collection/`, `requirements.txt`, the human-check kit and the doc updates.

## Output folders by layer

| Layer | Folders |
|---|---|
| 0 | `01_profile/` |
| 1 | `02_preprocessing/`, `03_tables/` |
| 2 | `04_analysis/` (figures) |
| 3 | `05_sample/`, `07_annotations/`, `09_leads/` (the check sheet is in `12_replies/`) |
| 4 | `08_midterm/`, `10_language/`, `11_dynamics/`, `13_interpretation/`, `14_directions/` |
| 5 | `12_replies/` |
| 6 | `15_network/` (and `gephi/` at the project root, including `gephi/projects/`, `gephi/figures/`, `gephi/stats/`) |
| 3, 5–7 (model signal) | `17_sentiment_stance/` |
| 7 | This file |
| All | `16_tableau/` (named by result, R1–R5); the workbook built from it is in `tableau/` at the project root |
| 0 | `collection/` at the project root (collector code, provenance) |
| — | `archive/` (superseded, including `FINDINGS_BY_HYPOTHESIS.md`) |
