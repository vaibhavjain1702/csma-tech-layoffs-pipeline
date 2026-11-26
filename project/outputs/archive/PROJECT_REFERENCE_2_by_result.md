# Solidarity or Blame: project reference 2 (organised by result)

*25 November 2026. This version is organised around the five results, R1–R5, that the report will present. Data, team, method and the full file map are in `docs/PROJECT_REFERENCE.md`, which stays the master reference. This file covers what each result says, how sure we are, the wording to use, and what still has to be done.*

---

## 1. The story in one paragraph

> When tech work is disrupted, Reddit communities support people who say what happened to them, and argue with people who blame someone. Blame of executives travels with the person, whichever community they post in; how much people talk about AI depends on the community.

The second sentence replaces "who gets blamed is something people bring with them, not something a community produces". The evidence (D1) supports that claim for executives but not for AI talk, so the blanket version overclaims (see R2).

## 2. Where we are

| | |
|---|---|
| **Analysis** | Essentially complete for R1–R4. R5 checks exist but are spread across folders |
| **Validation** | **Not started.** Every label is a keyword marker. Nothing can be called a *Finding* until the human check sheet is coded |
| **Biggest risk** | Results rest on unchecked markers, and one marker (agree) is known to be unreliable |
| **Biggest gap** | The database has **no cscq posts**. People who tell their story as a post are invisible |
| **Recommendation** | Stop adding analyses. Validate, fix the wording, write |

Claim labels follow `docs/INTERPRETATION_ROUTINE.md`: **Lead** (one number), **Supported** (survived the rivals, and an independent measure agrees), **Finding** (three or more measures agree *and* the labels are human-checked). At present nothing is a Finding.

## 3. The five results

### R1. Where disruption talk lives (H1)
| | |
|---|---|
| **Say it** | In cscq, layoffs are part of everyday talk; in r/technology they come up when there is news |
| **Numbers** | 2.45% vs 0.20% of non-bot comments (Jan–Jun 2025). Within threads that mention layoffs at all: 4.06% vs 0.49%. 67% of large cscq threads contain layoff talk, against 21% in r/technology |
| **Shape over time** | Weekly variability (CV): cscq 0.21, r/technology 0.45, r/programming 0.76. Peak week / median week: 1.6, 2.4, 4.7 |
| **Spikes** | Mid-May 2025 is shared: the week of 12 May is r/technology's top week and cscq's second, and r/programming peaks the next week. cscq's top week is 21 April. **Neither is matched to an event yet** |
| **Status** | **Supported** |
| **Caveat** | r/technology covers only 23 of the 26 weeks. The layoffs screen is about 95% precise; the hiring screen is about 22%, so **do not quote the 18.7× hiring figure** |
| **Files** | `outputs/08_midterm/`, `outputs/13_interpretation/`, Tableau `r1_*` |

### R2. How communities talk (H2 + D1)
| | |
|---|---|
| **Say it** | cscq tells personal stories and talks about consequences; r/technology frames things in corporate and political terms; r/programming talks about the craft |
| **Numbers** | Own-story comments 8.9% (cscq) vs 3.1% (r/technology). cscq links to labour statistics (FRED, BLS), r/technology to news sites |
| **Same person, two places (D1)** | About 150 authors post in both (160 in D1, 152 in the Tableau set, which leaves out career-transition-only comments). Their mentions of executives are about equal (6.6% vs 5.8%), so **blame of executives travels with the person**. Their AI talk still differs by 9.4 points, so **AI talk depends on the community** |
| **Status** | **Supported**, then narrowed by D1 |
| **Caveat** | Cross-posters are a special group, so the within-author result may not generalise. "Mentions executives" and "mentions offshoring" are **topic** markers, not stance: only 7 of 70 offshoring mentions blamed foreign workers |
| **Files** | `outputs/10_language/`, `outputs/14_directions/DIRECTIONS_NOTES.md` (D1), Tableau `r2_*` |

### R3. How replies respond (H3, the headline)
| | |
|---|---|
| **Say it** | In cscq, telling your own story draws comfort. Comments about executives, offshoring or AI as an excuse draw debate |
| **Numbers** | Sympathy replies 5.11% for story comments vs 1.82% for unmarked comments (×2.82), with less pushback. Doom draws advice (×1.38) |
| **Rivals checked** | Advice does not rise, so stories are not just requests for help. The effect holds within a length band. CIs are thread-clustered. Votes agree |
| **Status** | **Supported.** Becomes a Finding once the check sheet is coded |
| **Wording to use** | Say "blame draws **debate**", not "agreement". The agree marker fires on hostile replies that start with "This" (e.g. *"This is complete crazy talk"*) |
| **Wording to avoid** | "Communities rally round story-sharers." Most replies to a story are still not sympathetic, so always give the absolute rates next to the lift |
| **Concept** | Emotional vs informational support. Solidarity follows disclosure, not a shared enemy |
| **Files** | `outputs/12_replies/REPLY_NOTES.md`, Tableau `r3_*` |

### R4. The social structure behind R3 (network)
Scope: the cscq author reply graph (replier → parent author), Jan–Jun 2025. The largest connected component has 30,976 authors (97%) and 162,024 replies.

| | Result | Label |
|---|---|---|
| **N1** | **Position follows activity, not role.** We expected central helpers and peripheral story-sharers. Once activity is matched, story-sharers are not on the edge and helpers are not hubs | Supported (no difference); **contradicts the expectation** |
| **N2** | **Sympathy flows to story-sharers**, 1.6–1.9× more often whoever is replying. Helpers write about half of it | Lead |
| **N3** | **Blame-talkers form an argument group.** They reply to each other 1.69× more than chance (z = 27 against a degree-preserving null; z = 8 against a within-thread null at 1.46). Inside the group, challenge rises (7.2% vs 4.5%) and agreement does not | Supported |
| **N4** | Louvain communities (59, Q = 0.43) are **not** sorted by type (NMI ≈ 0.005) | Supported (no difference) |
| **N5** | k-means (k = 4) finds story, executives, AI-as-excuse and "rest" clusters, but **no helper cluster**. Agreement with the rule-based types is weak (ARI 0.14) | Lead |

- **Do not report** the story → story lift of 1.35.
- **Coverage limit.** 108,722 replies to posts (40% of human comments) have no target, because no cscq posts were collected. R4 describes comment-to-comment conversation only. People who post their story as a post are probably the real periphery.
- **Files:** `outputs/15_network/NETWORK_NOTES.md`, `network_profiled.gexf`, Tableau `r4_*`.

### R5. Validity
| Threat | What we did | Still needed |
|---|---|---|
| Labels are keyword markers | Provisional precision on samples | **Code the 240-row check sheet**, two coders, agreement |
| Agree marker is unreliable | Wording changed to "debate" | Add the hostile "This…" replies to the check sheet |
| No cscq posts | Documented; R3 and R4 restricted to comment-to-comment replies | **Decide:** collect the posts, or state the limit up front |
| Activity explains position (R4) | Activity bands and matched pairs | — |
| A few mega-threads | Top 1% of threads dropped; results hold | — |
| Label noise | Simulated false positives and negatives | — |
| Shared threads explain mixing | Within-thread null | — |
| Different windows (Jan–May vs Jan–Jun 2025) | Both reported | **Pick one** for the final report |
| Vote snapshots | Within-thread percentiles; control for early arrival | — |
| Unknown collection settings | Describe "the collected corpus" only | — |

All robustness numbers are collected in Tableau `r5_robustness_long.csv`. **A single R5 table for the report has not been built yet.**

## 4. Course concepts mapped to the results

Use a concept only where it explains something about our data. Each row says where it shows up and what it changes in the claim.

### 4.1 Concepts that fit

| Concept | Where it shows up | What it changes in the claim |
|---|---|---|
| **1. Construct splitting** | **Topic vs blame.** Mentioning executives or offshoring is not blaming them: only 7 of 70 offshoring mentions blamed foreign workers, and the earlier "blame sideways" label was about 95% plain mentions. "AI will replace…" also catches people rejecting the idea (only 7 of 30 agree with it). **Emotional vs informational support.** Story comments raise sympathy (×2.82) but not advice; doom raises advice (×1.38) | Call the markers *topic* labels in R2–R4. R3's headline is a split: disclosure draws emotional support, doom draws informational support. This split is the rival check that shows stories are not just requests for help |
| **2. Unit of analysis** | **Comment:** a comment's type predicts its reply (R3). **Author:** an author's type does not predict their network position once activity is matched (R4, N1). **Thread and week:** the same layoff talk looks ambient in cscq (67% of large threads, weekly CV 0.21) and bursty in r/technology (CV 0.45) (R1). **Community vs person:** the executives gap between communities disappears within the same authors (D1) | State the unit in every claim. Comment-level sympathy and author-level centrality are separate claims, so they don't contradict each other. A comment's role matters to how it is answered; an author's role does not set their position. D1 is a composition effect: the community difference comes from *who* posts there |
| **3. Base rate vs lift** | Sympathy goes from 1.82% to 5.11% (×2.82), but about 95% of replies to stories are still not sympathetic. Layoff share is 2.45% vs 0.20%. "AI as an excuse grew" was a denominator effect, because AI talk overall doubled. Taking bots out of the denominator moves R1 from 2.33% to 2.45% | Always give the absolute rates beside the lift. Name the denominator: non-bot comments, employment-screened comments, or replies to comments |
| **4. Platform artefacts** | No cscq posts in the archive, so 40% of reply links have no target. Each community's coverage ends on a different date. r/technology covers 23 of 26 weeks. The search settings are unknown. Scores are snapshots that favour early arrivals. There are deleted authors and bots | These are R5's coverage threats. R3 and R4 describe **comment-to-comment** conversation only. Make claims about "the collected corpus", not about Reddit |
| **6. Heavy-tailed distributions** | The top 1% of users get 17.8% of replies, and 97% of author pairs exchange only one reply. The degree distribution has a long tail (`fig_degree_ccdf`). N1 is a heavy-tail result: activity, not role, predicts position | Centrality by type uses **medians with bootstrap CIs**. Authors are profiled only from 5 comments upward, because with fewer a single comment sets their rate to 0 or 100%. Comparisons are within activity bands |
| **7. Direct vs shared ties** | The reply graph is **direct** ties: someone chose to answer someone. The author–thread projection is **shared** ties: two people were in the same place. The within-thread null tests whether blame-talkers reply to each other more than sharing threads explains (lift 1.69 observed vs 1.46 expected; z = 8). **A tie means attention, not agreement:** blame-talkers' ties to each other carry challenge | Present N3 against the within-thread null, not only the degree null. Never read the reply network as a network of allies |
| **8. Null models** | Lift is measured against random mixing. A degree-preserving null gives z = 27 and a within-thread null gives z = 8 for blame-talker → blame-talker. Under the degree null, mean assortativity is about 0 | The within-thread null is the stricter test and the one to report. Louvain modularity (Q = 0.43) has **not** been compared with a null, so don't call it strong structure |
| **9. Affective (antagonistic) echo chamber** | N3: blame-talkers cluster together (lift 1.69), and inside the group challenge rises (7.2% vs 4.5% overall) while agreement does not | N3 is *consistent with* clustering in order to argue. But blame-talker is a topic type, not a stance, so we can't show that the people arguing hold **opposing** positions. Call it "an argument group, consistent with an antagonistic echo chamber". Stance-coded labels (Krish) would be needed to go further |
| **10a. Reliability vs validity** | The regex markers are perfectly **reliable**: the same input always gives the same output, and two runs give identical results. That says nothing about **validity**. The agree marker is reliable and invalid: it consistently tags hostile "This…" replies as agreement | Being reproducible is not being reliable as a human label. Two coders on the check sheet give *reliability* (agreement, such as Cohen's κ) and *validity* (precision against human judgement). Both are still missing |
| **10b. Internal vs external validity** | **Internal** (confounds within the data), all checked: comment length, author activity, mega-threads, thread clustering, early arrival, label noise, shared threads. **External** (where the results stop generalising): R3 and R4 are cscq only; Jan–Jun 2025 only; comments only; cross-posters are a special group; Reddit only; the corpus is not a representative sample | R5 should have two parts. The internal half is strong; the external half sets the scope of every claim |

### 4.2 One concept per result, for the report

| Result | Lead concept | Supporting concept |
|---|---|---|
| R1 | Unit of analysis: ambient vs event-driven at the thread and week level | Platform artefacts: coverage |
| R2 | Construct splitting: topic vs blame | Unit of analysis: community vs person (D1) |
| R3 | Construct splitting: emotional vs informational support | Base rate vs lift |
| R4 | Affective echo chamber (N3), with null models | Heavy tails: activity explains position (N1); direct vs shared ties |
| R5 | Reliability vs validity; internal vs external validity | Platform artefacts |

The concept list skips number 5, so this map does too.

## 5. From scattered results to higher-level concepts

Section 4 uses the course concepts to keep each number honest. This section goes one level up. It groups results that look scattered under the social-media concept they share, and states the claim that concept lets us make.

Each row is a ladder: **results → pattern → concept → higher-level claim → limit**. Concepts marked † are **not on the course list**. They are standard ideas from the social-media literature; check them against the course readings before using them, and drop any that the course doesn't cover.

### 5.1 The ladders

| Theme | Results it brings together | Pattern | Concept | Higher-level claim | Limit |
|---|---|---|---|---|---|
| **A. Two rhythms of attention** | R1: 2.45% vs 0.20%; 67% vs 21% of large threads; weekly CV 0.21 vs 0.45 and 0.76. D3: the H-1B spike went from 13% to 43% for one week, then fell below the earlier level | cscq talks about layoffs steadily; r/technology and r/programming talk in bursts; even inside cscq, a shock fades fast without changing the framing | Unit of analysis (2); **issue-attention cycle**† (attention to an issue rises with news and decays) | For people affected, disruption is a **standing condition**; for onlookers, it is **news**. Shocks move attention, not interpretation | Spikes are not yet matched to events; coverage differs by community (4) |
| **B. Evidence cultures** | R2: own stories 8.9% vs 3.1%; cscq links FRED and BLS, r/technology links news; r/programming talks craft | Each community uses a different kind of evidence to make sense of the same events | Construct splitting (1); **framing**† (what a frame selects and makes salient) | Communities don't just discuss disruption at different rates; they **know it differently**: through lived experience and labour statistics, through corporate and political news, or through the craft | Marker-based; topic, not stance |
| **C. Support follows disclosure** | R3: stories ×2.82 sympathy, advice flat; doom ×1.38 advice. R4 N2: sympathy reaches story-sharers whoever replies. D2: newcomers who get a reply come back more (50% vs 39%) | Saying what happened to you draws comfort; voicing worry about the market draws information; any reply is linked to coming back | Construct splitting (1): **emotional vs informational support**; **self-disclosure eliciting support**†; **newcomer retention**† | Solidarity on Reddit is **triggered by disclosure, not by a shared enemy**, and the community matches the type of support to the type of need | Absolute rates are low (5.1%) (3); D2 is a lead and sympathy alone is too rare to test |
| **D. Blame mobilises argument** | R3: blame topics draw debate and less support. R4 N3: blame-talkers reply to each other 1.69× (z = 8 within threads), and challenge rises while agreement does not. Agree marker inflated | Blame doesn't gather allies; it gathers opponents, and the same people keep meeting to argue | Direct ties ≠ agreement (7); null models (8); **affective echo chamber** (9) | Blame produces **contention, not cohesion**: an argument group, consistent with an antagonistic echo chamber | Blame-talker is a topic type, so we can't show opposing stances |
| **E. People bring their frames** | D1: the same authors mention executives about equally in both communities (6.6% vs 5.8%), but their AI talk still differs by 9.4 points. D4: story-sharers and blamers are different people with the same tenure | The executives framing moves with the person; AI talk changes with the community | Unit of analysis (2), community vs person; **selection vs influence**† (do groups attract people who are already alike, or make them alike?) | Blame of executives is **selected in**: people arrive with it. AI talk is **shaped in**: it follows community norms. Communities differ partly because of who joins them | Cross-posters are a special group, about 150 people (10b) |
| **F. Structure is participation, not roles** | R4 N1: position follows activity; N4: communities are not sorted by type (NMI ≈ 0.005); N5: no helper cluster. Oct Gephi: the top 1% get 17.8% of replies, and 97% of pairs reply once | A small active core dominates; position comes from how much you post, not what role you play; communities form around conversations, not around roles | Heavy tails (6); **participation inequality**† (a few people produce most of the content) | The network is a **crowd, not a set of roles**. What people say shapes the reply they get (C, D), but it does not give them a place in the structure | Comment-only network (no posts) (4) |
| **G. What the trace can't show** | No cscq posts (40% of replies have no target); coverage ends on different dates; unknown search settings; vote snapshots; the agree marker | Some of the most important acts, such as posting your own story as a thread, left no trace in our data | Platform artefacts (4); reliability vs validity (10a); external validity (10b) | Our results describe **conversation in comments**, not the whole community, and what a marker counts is not always what it names | — |

### 5.2 The higher-level argument

The ladders above combine into three claims, each resting on more than one result.

1. **Disruption is a standing condition for those affected and news for everyone else** (A, B). The same events are discussed with different rhythms and different evidence.
2. **Reddit communities answer disclosure with support and blame with argument** (C, D). Solidarity is triggered by people telling their own story, not by agreeing on whom to blame. Blame brings people together to disagree.
3. **Who blames whom is mostly brought in, while what gets talked about is shaped locally** (E, F). Blame of executives travels with the person. AI talk follows the community. The network is organised by participation, not by roles.

G is the scope for all three: each claim is about the collected comments, and none is a Finding until the labels are human-checked.

### 5.3 What we are not claiming

- **Not "Reddit is a support community":** most replies to stories are not sympathetic (5.1%).
- **Not polarisation by stance:** we measure topics, not positions.
- **Not cause and effect:** for example, D2 links getting a reply to coming back; it does not show that the reply caused it.
- **Not generalisation beyond the three subreddits, Jan–Jun 2025, comments only.**

## 6. What to do next, in order

| # | Task | Why | Blocks |
|---|---|---|---|
| 1 | **Code the check sheet** (`outputs/12_replies/check_sheet.csv`, 240 rows) with a second coder, ideally Krish, and include the hostile "This…" replies | Without it nothing becomes a Finding | R3 and every label claim |
| 2 | **Decide about the cscq posts**: collect them (Vaibhav, Arctic Shift), or write the limit into R5 | It would strengthen R3 and R4 more than any new analysis | R4 interpretation |
| 3 | Show Krish the R3 and R4 results | He owns the stance labels | Team alignment |
| 4 | Rewrite claims: "debate" not "agreement"; the executives vs AI split; absolute rates beside the lift | Avoids overclaiming | Report draft |
| 5 | Pick one shared window | Consistent numbers | All comparisons |
| 6 | Build one R5 table from `r5_robustness_long.csv` | One place for validity | Report |
| 7 | Match the 21 April and mid-May 2025 spikes, and the mid-December offshoring spike, to events | Explains R1 bursts | R1 |
| 8 | Draft the report from `NETWORK_NOTES.md`, `REPLY_NOTES.md` and this file | — | — |
| 9 | Record the final deadline and report requirements | Planning | — |

**Not to do now:** new analyses, new markers, topic models, or transformer stance models, unless one of R1–R5 needs them.

## 7. Before committing or sharing

- Keep `outputs/15_network/examples.txt` out of any public repo: it contains verbatim comments.
- `network_profiled.gexf` (15 MB) and `outputs/16_tableau/` (42 MB) are large but under GitHub's limits.
- Author keys in the database are unsalted hashes, so a guessed username can be confirmed. They must never appear in outputs. The R4 and Tableau files use neutral ids (`a…`/`n…` and `p…`/`t…`), and these two schemes cannot be joined.
- Nothing from this session has been committed.

## 8. Where to look

| Need | File |
|---|---|
| Master reference (data, team, method, full file map) | `docs/PROJECT_REFERENCE.md` |
| How to interpret a number | `docs/INTERPRETATION_ROUTINE.md` |
| R1–R3 by hypothesis | `outputs/04_analysis/FINDINGS_BY_HYPOTHESIS.md` |
| R3 details | `outputs/12_replies/REPLY_NOTES.md` |
| D1–D4 | `outputs/14_directions/DIRECTIONS_NOTES.md` |
| R4 | `outputs/15_network/NETWORK_NOTES.md` |
| Tableau files for R1–R5 | `outputs/16_tableau/TABLEAU_GUIDE.md` |
