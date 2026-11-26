# CSMA Project — Complete Guide

## "Solidarity or Blame: Computational Social Media Analysis of Technology Employment Disruption"

**Purpose of this document:** A one-stop, exhaustive reference for understanding the entire project — what it is, what has been done, how it was done, what was achieved, and what a teacher might ask. Read this in ~60 minutes and you will be prepared.

---

## Table of Contents

1. Project Overview and Motivation
2. Research Questions and Hypotheses
3. Data Source and Collection (Your Role — Vaibhav Jain)
4. Corpus Profile — What Was Collected
5. Preprocessing Pipeline
6. Lexical Screening and Broader Employment Screens
7. Headline Results — The Controlled Comparison
8. Exploratory Stance Baseline
9. Network Exports for Gephi
10. Reading Sample and Human Coding Preparation
11. EDA Figures (5 Visualizations)
12. Testing and Validation
13. Team Roles and Contributions
14. Mid-Term Deliverables — Report and Presentation Breakdown
15. What Has Been Achieved (Phase 2 Summary)
16. What Remains After Mid-Term (Phase 3 Plan)
17. Repository and Code Architecture
18. Key Limitations and Caveats
19. Literature Review Summary (15 Studies)
20. Potential Viva Questions and Model Answers (30 Q and A)

---

## 1. Project Overview and Motivation

### What is this project about?

This project examines **how technology employment disruption (layoffs, hiring freezes, AI displacement, restructuring) is discussed, interpreted, and socially negotiated across Reddit communities**. Instead of simply measuring sentiment (positive/negative), the project investigates:

- What experiences people describe (job loss, job search difficulties, career transitions)
- How people **explain** employment changes (blaming AI, corporate greed, the economy)
- Whether communities offer **solidarity** (empathy, advice, support) or **blame** (dismissal, mockery, "you should have upskilled")
- How reply networks and interaction structures differ across communities

### Why Reddit?

Reddit offers publicly accessible, threaded, community-specific discussions where people discuss employment issues with varying degrees of anonymity. Different subreddits have different "cultures":

- **r/cscareerquestions** — A community of current and aspiring software professionals discussing jobs, interviews, career paths. Personal, worker-centric.
- **r/technology** — A general-interest tech news community. Broader, more industry-focused.
- **r/programming** — Focused on software development. More technical discussions.

### The Core Insight

The same event (e.g., Meta layoffs) is discussed very differently in r/cscareerquestions (where someone might say "I just got laid off, what do I do?") versus r/technology (where someone might say "Meta lays off 10,000 — stock rises"). The project quantifies and characterizes this difference.

### What makes this a "Computational Social Media" project?

It combines:
- **Large-scale data collection** from Reddit (~3 million records)
- **Computational text analysis** (lexical screening, keyword matching, NLP baselines)
- **Network analysis** (reply graphs, author interaction networks via Gephi)
- **Qualitative human coding** (planned manual annotation of a 200-record sample)
- **Statistical comparison** (rate ratios, two-proportion tests)

---

## 2. Research Questions and Hypotheses

### Five Research Questions

| # | Research Question |
|---|---|
| RQ1 | What employment experiences and changes do participants describe, and how do these vary across communities? |
| RQ2 | How do participants explain disruption, assign responsibility, and imagine the future of technology work? |
| RQ3 | How do replies provide support, seek clarification, endorse claims, challenge them, or negotiate uncertainty? |
| RQ4 | How are participation and responses structured, and how do particular narratives receive attention or become contested? |
| RQ5 | How do these patterns vary alongside documented employment, AI, economic, and policy developments? |

### Three Testable Hypotheses

| Hypothesis | Statement | Mid-term Status |
|---|---|---|
| **H1** | Employment-disruption language **differs significantly by community context** (e.g., r/cscareerquestions vs r/technology) | Preliminary support — Rate ratios of 5x to 19x across all six facets |
| **H2** | Worker-centred support ("solidarity") and industry-level framing ("blame") **differ by community** | Not yet tested — Requires human coding of the 200-record sample |
| **H3** | Solidarity and blame labels have **different reply patterns** (e.g., solidarity posts get more supportive replies) | Not yet tested — Requires validated stance labels joined to Gephi network data |

**IMPORTANT:** The current study is a **within-Reddit, cross-community pilot**. No X (Twitter) or LinkedIn data has been collected or analyzed.

---

## 3. Data Source and Collection (Your Role — Vaibhav Jain)

### Your Specific Contribution

**Vaibhav Jain** was responsible for **Reddit data collection, raw batches, provenance, and coverage checks**.

### Data Source: Arctic Shift

The data was collected using the **Arctic Shift API** — a community-maintained historical Reddit data archive (since Pushshift was shut down by Reddit). Arctic Shift provides access to historical posts and comments in JSON format.

### How the Collection Pipeline Works

Your local project directory contains the collection pipeline code:

| File | Purpose |
|---|---|
| main.py | Entry point — accepts --mode (smoke/collect/process/qa/full) |
| src/collector.py | ArcticShiftCollector class — fetches data from Arctic Shift API |
| src/processor.py | DataProcessor class — filters by keywords, deduplicates, saves CSVs |
| src/privacy.py | PrivacyAgent class — pseudonymizes author names via SHA-256 hashing |
| src/qa.py | QAAgent class — generates quality assurance reports |
| src/orchestrator.py | ProjectManager class — orchestrates the full pipeline |
| config/collection_config.yaml | Configuration: subreddits, date range, keywords, rate limits |

### Collection Configuration

- **Subreddits**: technology, cscareerquestions, programming, ExperiencedDevs, antiwork, jobs, careerguidance
- **Date range**: 2025-01-01 to 2026-12-31
- **Keywords**: layoff, layoffs, laid off, job cuts, workforce reduction, downsizing, fired, termination, tech layoffs, AI layoffs, and more
- **Rate limit**: 0.1 second delay between requests, max 5 retries with exponential backoff

### How the Collector Works (Step by Step)

1. **For each subreddit** and each item type (posts and comments):
2. **Load checkpoint** — resume from where the last run stopped (timestamps saved in checkpoints/)
3. **Make paginated API requests** to arctic-shift.photon-reddit.com/api/posts/search and /comments/search
4. **Parameters**: subreddit, after (timestamp), before (end timestamp), limit (100), sort ascending
5. **Handle rate limiting** — exponential backoff on 429 errors, max 5 retries
6. **Save raw JSON** — batches organized by month in data/raw/YYYY-MM/
7. **Update checkpoint** — save the latest timestamp for resume capability

### Privacy Protection

- Author usernames are **hashed with SHA-256** using a configurable salt (CSMA_SALT environment variable)
- Original usernames are replaced with author_hash column
- Raw data files retain originals but are **never committed to Git**

---

## 4. Corpus Profile — What Was Collected

### Total Scale

| Metric | Value |
|---|---|
| **Total records** | **2,974,250** |
| Posts | 115,213 |
| Comments | 2,859,037 |
| JSON batch files | 29,821 |
| Monthly folders | 21 (Jan 2025 to Sep 2026) |
| Raw data size | ~5.74 GiB |
| Duplicate records | **0** |
| JSON parse errors | **0** |
| Comment bodies available | **94.61%** (2,705,044 of 2,859,037) |
| Structural threads | 164,271 |
| Reply edges | 2,859,037 |

### Community-Specific Coverage

| Community | Type | Records | Observation Period |
|---|---|---|---|
| r/cscareerquestions | Comments | 962,337 | Jan 2025 to Sep 2026 |
| r/technology | Comments | 1,657,900 | Jan 2025 to Jun 2025 |
| r/programming | Comments | 238,800 | Jan 2025 to Dec 2025 |
| r/programming | Posts | 38,431 | Jan 2025 to Sep 2026 |
| r/technology | Posts | 76,782 | Jan 2025 to Sep 2026 |

**WARNING: No r/cscareerquestions posts are present** in the collection. Comment coverage ends at different dates for each community. This is critical — you **cannot** compare time trends across communities without accounting for different coverage windows.

### Quality Audit Findings

- 145,840 comment bodies are **removed** (by moderators), 8,152 are **deleted** (by users), 1 is empty
- 65.96% of comments link to a stored submission
- 99.33% of comment-to-comment replies have their parent comment available
- **Zero** posts are missing titles
- Engagement is heavily skewed: median post score = 1, mean = 655.2; median comment score = 1, mean = 13.61

---

## 5. Preprocessing Pipeline

### What Was Done

The analysis-grade pipeline (in the cloned repository) performs:

#### Text Preparation
- **HTML entity decoding** (e.g., &amp; becomes &)
- **Whitespace normalization** (multiple spaces become single space)
- **Preserved**: case, punctuation, negation words, emojis, slang, URLs
- **Quote separation**: Markdown-quoted lines ("> ...") separated into quoted_text; own_text = body minus quotes
- **URL extraction**: Stored in urls_json
- **Word/character counts**: Computed on prepared text

#### Author Pseudonymization
- Known usernames converted to lowercase then to SHA-256-derived 96-bit stable pseudonyms
- Unknown/deleted authors become NULL (never merged into one "deleted user" node)
- likely_bot name-based flag added (not used for automatic exclusion)

#### Conversation Reconstruction
- **Thread roots** identified via link_id (t3_<post-id>)
- **Reply depth** resolved iteratively (handles chains of 1500+ safely)
- **Missing parents** explicitly marked, never invented
- **Cycles** and invalid parent references detected and flagged
- **Reply delay** (child minus parent creation time) computed where possible

### Output Format

| Export | Rows | Format |
|---|---|---|
| posts.csv.gz | 115,213 | Gzip CSV |
| comments.csv.gz | 2,859,037 | Gzip CSV |
| threads.csv | 164,271 | Plain CSV |
| reply_edges.csv.gz | 2,859,037 | Gzip CSV |
| SQLite database | All tables | data/processed/reddit.sqlite |

---

## 6. Lexical Screening and Broader Employment Screens

### Original Layoff Screens

Two keyword screens were used initially:

- **Direct match**: layoff, layoffs, laid off, laying off, lay off — matched **654 posts** and **28,077 comments**
- **Broad match**: adds redundancy, furlough, downsizing, job cuts, workforce reductions — matched **767 posts** and **30,549 comments**

### Broader Employment Disruption Screens (6 Facets)

To go beyond just "layoff" language, **six versioned lexical facets** were implemented in disruption_rules.py:

| Facet | What It Catches | Requires Employment Anchor? | Matching Records |
|---|---|---|---|
| **Layoffs** | layoff, laid off, job cuts, workforce reduction, downsizing, furlough | No | 28,326 |
| **Hiring conditions** | hiring freeze, job search, job market, unemployed, interviews, hiring | Yes | 90,004 |
| **AI/work change** | AI, artificial intelligence, ChatGPT, LLM, automation | Yes | 58,658 |
| **Corporate restructuring** | restructuring, reorganization, merger, acquisition, RTO, offshoring, outsourcing | Yes | 11,396 |
| **Economic/policy** | recession, economy, interest rates, inflation, tariffs, H-1B, labor market | Yes | 18,792 |
| **Career transitions** | career change, reskilling, upskilling, retraining, leaving tech, quitting | Yes | 14,315 |
| **Distinct records matching at least 1** | — | — | **177,808** |

**NOTE:** "Requires Employment Anchor" means the AI/restructuring/economic terms only trigger if the same text field also contains an employment-related word (jobs, hiring, workers, engineers, etc.). This prevents false positives like "AI image generation" being counted as employment-related.

### How Screening Works

Simplified logic from disruption_rules.py:

```
def screen(title, own_text):
    for each field (title, own_text):
        1. Remove URLs
        2. Check for employment anchor (jobs, hiring, workers, etc.)
        3. For each facet:
           - If requires_employment and no anchor: skip
           - Run regex pattern
           - Record matched terms and anchor
    return evidence dictionary
```

Key design decisions:
- URLs and quoted text are **excluded** from screening
- Negation does **not** suppress retrieval ("AI will NOT replace jobs" still matches — it is a candidate for human review)
- Facets **overlap** — one record can match multiple facets
- Matching does not equal relevance — these are retrieval aids, not confirmed labels

---

## 7. Headline Results — The Controlled Comparison

### The Shared Window Approach

Since community coverage ends at different dates, a **fair comparison** uses only the **shared January to May 2025 window** where both r/cscareerquestions and r/technology have complete comment coverage.

### The Core Finding

| Facet | r/cscareerquestions | r/technology | Rate Ratio |
|---|---|---|---|
| **Hiring conditions** | **8.50%** | 0.45% | **18.69x** |
| **Layoffs** | **2.32%** | 0.20% | **11.36x** |
| **Corporate restructuring** | **1.03%** | 0.09% | **11.97x** |
| **Career transitions** | **1.26%** | 0.13% | **10.07x** |
| **AI and work change** | **2.96%** | 0.55% | **5.40x** |
| **Economic or policy** | **1.37%** | 0.25% | **5.58x** |

### What These Numbers Mean

- In the shared window, **r/cscareerquestions** had **256,497** collected comments; **r/technology** had **1,593,759**
- The denominator is **every collected comment** in that community and window (not just employment-related ones)
- **Hiring conditions are discussed 18.69 times more frequently** in r/cscareerquestions than r/technology (8.50% vs 0.45%)
- **Layoff language appears 11.36 times more frequently** in r/cscareerquestions (2.32% vs 0.20%)
- The two-proportion z-test for layoffs gave z approximately 141.42, p < 0.001

### What These Numbers Do NOT Mean

- They are **not** prevalence estimates for technology workers or all of Reddit
- They do **not** measure actual layoffs, hiring freezes, or AI displacement
- Keyword matching does not equal confirmed stance, experience, or relevance
- The statistical test does **not** correct for sampling bias or repeated-author effects

---

## 8. Exploratory Stance Baseline

An **exploratory lexical stance classifier** was applied to the 200-record reading sample to get a rough baseline:

| Category | Count |
|---|---|
| No lexical signal | 118 (59%) |
| Blame-leaning | 35 (17.5%) |
| Solidarity-leaning | 31 (15.5%) |
| Mixed | 16 (8%) |

### By Subreddit

| Subreddit | Blame | Solidarity | Mixed | No Signal |
|---|---|---|---|---|
| r/cscareerquestions | 12 | 9 | 3 | 30 |
| r/programming | 15 | 13 | 9 | 39 |
| r/technology | 8 | 9 | 4 | 49 |

### Method Details
- Used a **solidarity lexicon** (42 terms) and **blame lexicon** (44 terms)
- Rule: solidarity-leaning if at least 1 solidarity term and no blame term; blame-leaning if at least 1 blame term and no solidarity term; mixed if both
- 59% of records had no lexical signal — **human coding is essential**
- This is an **exploratory retrieval aid** that requires human validation

---

## 9. Network Exports for Gephi

Two network graph exports were created for later Gephi visualization:

### Author Reply Network

| Property | Value |
|---|---|
| **What it shows** | Who replies to whom |
| **Nodes** | 14,507 known-author pseudonyms |
| **Edges** | 15,427 directed edges |
| **Direction** | Replying author to Parent author |
| **Weight** | Count of observed replies between the pair |
| **Total retained replies** | 15,977 across 7,312 threads |
| **Scope** | Comments with direct layoff matches |

### Conversation Network

| Property | Value |
|---|---|
| **What it shows** | Comment-to-comment reply chains |
| **Nodes** | 13,866 post/comment IDs (includes 6 missing-record placeholders) |
| **Edges** | 13,206 directed edges |
| **Direction** | Replying comment to Immediate parent |
| **Weight** | 1 per reply |
| **Scope** | Direct-matching stored posts and their collected comments |

### Key Caveats for Networks
- **Exclusions**: Unknown authors, absent parent content, cross-thread links, and self-replies are excluded from the author network
- 12,032 of 28,077 selected comments have absent parent content
- These graphs show **response structure**, NOT friendship, agreement, support, influence, or diffusion
- Gephi visualization and interpretation have **NOT been performed yet** (Phase 3 work)
- **Zero dangling endpoints** — all graph exports passed validation

---

## 10. Reading Sample and Human Coding Preparation

### The 200-Record Employment Sample

A stratified reading sample was created for human annotation:

| Sampling Group | Selected Records |
|---|---|
| Layoffs | 40 |
| Hiring conditions | 40 |
| AI/work change | 30 |
| Corporate restructuring | 20 |
| Economic/policy | 20 |
| Career transitions | 20 |
| Non-matching background | 30 |
| **Total** | **200** |

### Sample Properties
- 95 posts + 105 comments
- 76 from r/programming, 70 from r/technology, 54 from r/cscareerquestions
- Balanced by community x UTC quarter x record kind x score band
- At most 1 record per thread within each group
- Deterministic selection (reproducible)

### Coding Framework (What Human Coders Would Label)

| CSV Field | What It Captures |
|---|---|
| relevance | relevant / irrelevant / uncertain |
| document_type | First-person account, secondhand report, news discussion, question, etc. |
| experiences | Job loss, job search, hiring/interview, career transition, etc. |
| explanations | AI, corporate strategy, economic conditions, policy — and whether asserted, tentative, or rejected |
| future_expectations | Recovery, continued difficulty, displacement, opportunity, uncertainty |
| themes | Broader recurring issues (developed through reading) |
| emotions | Concern, anger, hope, resignation, mixed |
| response_function | Advice, empathy, resource sharing, endorsement, challenge, dismissal |
| notes | Evidence, ambiguity, context |

**IMPORTANT: Status: 0 of 200 records have been coded.** Human coding is Phase 3 work.

---

## 11. EDA Figures (5 Visualizations)

Five static descriptive figures were generated using Matplotlib:

| # | Figure | What It Shows |
|---|---|---|
| 1 | Monthly Coverage by Community and Record Type | Community-specific collection cutoffs; r/technology comments end June 2025, r/programming December 2025 |
| 2 | Body-Text Availability | 94.61% comment bodies available; removed/deleted rates; empty link-post bodies need title-aware interpretation |
| 3 | Direct Layoff-Match Shares | Explicit layoff language is concentrated in r/cscareerquestions comments (~2.5%) vs very low in r/technology (~0.2%) |
| 4 | Broader Candidate Counts by Facet | Hiring conditions dominate (90K records); facets overlap significantly |
| 5 | Saved-Score Distribution | Heavily skewed — median=1, large outlier means; engagement distributions matter for sampling |

Each figure is exported as PNG (high-res) and SVG (vector), with supplementary source CSVs and interpretation notes.

---

## 12. Testing and Validation

### 15 Unit Tests — All Passed

The test file test_research.py covers:

| Test Category | What It Checks |
|---|---|
| DisruptionScreenTests | General AI does not trigger without employment anchor; anchors do not cross field boundaries; quoted/URL-only terms do not trigger; sparse build retains IDs and rolls back incomplete builds |
| PreparationTests | Negation and quote attribution preserved; removed content does not become a document; unknown authors never merge |
| ConversationTests | Depth resolves without submission content; missing parents do not invent depth; cycles detected; chains of 1500+ do not hit recursion limit |
| AnalysisTests | Frequency quantiles interpolate correctly; codes count once per record; new coding dimensions stay separate |
| GraphTests | Author graph preserves direction, weight, and exclusions; zero dangling endpoints |

### Full Output Validation

All major exports validated:
- posts.csv.gz: 115,213 rows, fully parsed
- comments.csv.gz: 2,859,037 rows, fully parsed
- threads.csv: 164,271 rows, fully parsed
- reply_edges.csv.gz: 2,859,037 rows, fully parsed
- disruption_candidates.csv.gz: 177,808 rows, fully parsed
- preprocessing_audit: passed
- gephi/authors: 14,507 unique nodes, 15,427 unique edges, 0 dangling endpoints
- gephi/conversations: 13,866 unique nodes, 13,206 unique edges, 0 dangling endpoints

---

## 13. Team Roles and Contributions

| Member | Role and Work Completed |
|---|---|
| **Vanshit Ahuja** | Archive QA, research design, controlled comparison, hypotheses, statistical interpretation, literature review (15 studies, 617 words), report and PPT revision, privacy checks, testing, repository cleanup, and public release |
| **Vaibhav Jain** (You) | Reddit data collection (Arctic Shift API pipeline), raw batches, provenance tracking, and coverage checks |
| **Dividh Vijay** | All Gephi and network work — node/edge exports, direction, weights, scope, and validation |
| **Tanya** | Data cleaning, thread linkage, quality checks, descriptive analysis, community comparison, and figures |
| **Krish** | Lexical and stance baselines, reading sample, coding framework, and NLP evaluation plan |

---

## 14. Mid-Term Deliverables — Report and Presentation Breakdown

### Deliverable Files

| File | Purpose |
|---|---|
| CSMA_Midterm_Report_Solidarity_or_Blame.pdf | Hard copy for submission |
| CSMA_Midterm_Report_Solidarity_or_Blame.docx | Editable version for revisions |
| CSMA_Midterm_Presentation_Solidarity_or_Blame.pptx | 15-minute presentation deck |

### Report Contents

The report includes:
- **617-word comparative literature review** covering **15 studies**
- Each paper's data source, method, result, limitation, and use in this project
- Research questions and hypotheses
- Methodology and pipeline description
- Controlled comparison results (shared-window rate ratios)
- Exploratory stance baseline
- Network export descriptions
- Privacy and ethical considerations
- Limitations and future work

### Presentation Breakdown (15 Slides)

| Slide # | Content | Speaker |
|---|---|---|
| 1 | Title slide | Vanshit |
| 2 | Research question, hypotheses, research gap | Vanshit |
| 3 to 6 | **Literature review** (15 studies across 4 slides) | Krish |
| 7 | NLP method choices and stance baseline | Krish |
| 8 to 9 | **Methodology and validation plan** | Tanya |
| 10 | Data collection, provenance, corpus coverage | **Vaibhav (You)** |
| 11 | Preprocessing and controlled comparison | Tanya |
| 12 | Gephi exports, graph definitions, network limits | Dividh |
| 13 | Key figures and results | Tanya |
| 14 | Contributions, next phase | Vanshit |
| 15 | Questions | Vanshit |

### Your Speaking Part (Slide 10)

You should be prepared to explain:
- **What Arctic Shift is** and why it was used (historical Reddit data access)
- **How many records were collected** (~3 million)
- **Which subreddits** (r/cscareerquestions, r/technology, r/programming)
- **The date range** (Jan 2025 to Sep 2026)
- **Coverage differences** (technology comments end June 2025, no cscareerquestions posts)
- **Quality metrics** (0 duplicates, 94.61% comment bodies available)
- **Provenance** (checkpoints, monthly folders, batch files)

---

## 15. What Has Been Achieved (Phase 2 Summary)

### Completed Work

| Component | Status |
|---|---|
| Corpus profiling and quality audit | COMPLETE |
| Text preparation and conversation reconstruction | COMPLETE |
| Structured dataset and CSV exports | COMPLETE |
| Descriptive analysis (monthly, engagement, vocabulary, threads) | COMPLETE |
| 5 static EDA plots | COMPLETE |
| 6 broader lexical screens (177,808 candidates) | COMPLETE |
| Controlled shared-window comparison (Jan-May 2025) | COMPLETE |
| Exploratory stance baseline on 200-record sample | COMPLETE |
| Reading sample and coding materials prepared | COMPLETE |
| Gephi network exports and validation | COMPLETE |
| 15 unit tests — all passed | COMPLETE |
| Full output validation | COMPLETE |
| Mid-term report, deck, and handoff | COMPLETE |
| Public GitHub repository | COMPLETE |

### Key Achievement: H1 Preliminary Support

The central Phase 2 achievement is **preliminary support for H1**: Employment-disruption language is **significantly more concentrated** in the worker-centric community (r/cscareerquestions) than in the general tech-news community (r/technology), with rate ratios ranging from 5.4x to 18.7x across all six disruption facets.

---

## 16. What Remains After Mid-Term (Phase 3 Plan)

| Task | Description |
|---|---|
| **1. Human coding** | Code the 200-record reading sample + independently coded overlapping subset for inter-coder agreement |
| **2. NLP evaluation** | Evaluate VADER sentiment and a transformer-based stance classifier against human-coded labels |
| **3. Topic modelling** | Run topic models (e.g., LDA/BERTopic) on employment-related comments |
| **4. Gephi interpretation** | Visualize and interpret the network graphs; compute graph metrics (centrality, clustering, communities) |
| **5. Label-network join** | Join validated stance labels to network edges to study how solidarity vs blame propagate in reply chains |
| **6. External triangulation** | Assemble sourced external events (layoff announcements), labor indicators (unemployment rates), and worker surveys |
| **7. Test H2 and H3** | Use validated labels to test whether solidarity/blame differ by community (H2) and whether they have different reply structures (H3) |

---

## 17. Repository and Code Architecture

### Local Data Collection Pipeline (Your Code)

```
Project/
  main.py                          Entry point (--mode smoke|collect|process|qa|full)
  config/collection_config.yaml    Subreddits, keywords, date range, API settings
  src/
    collector.py                   ArcticShiftCollector — API fetching with checkpoints
    processor.py                   DataProcessor — keyword filtering, deduplication
    privacy.py                     PrivacyAgent — SHA-256 author pseudonymization
    qa.py                          QAAgent — quality assurance report generation
    orchestrator.py                ProjectManager — pipeline orchestration
    utils.py                       Config loading, logging setup, project root
  data/raw/YYYY-MM/                Raw JSON batches (not in Git)
  data/processed/                  Processed CSVs (not in Git)
  checkpoints/                     Resume state for collection
  reports/                         QA reports
  Documents/                       Report PDF and PPT copies
```

### Analysis Repository (GitHub Clone)

```
csma-tech-employment-disruption/
  scripts/                         18 Python scripts
    run_pipeline.py                Full pipeline orchestrator
    profile_data.py                Corpus profiling and audit
    preprocess_data.py             Text prep, threading, SQLite build
    screen_disruption.py           6-facet lexical screening
    disruption_rules.py            Screen rule definitions (regexes)
    export_tables.py               CSV export
    summarize_data.py              Descriptive statistics
    preliminary_analysis.py        Monthly/engagement/vocabulary analysis
    plot_eda.py                    5 EDA visualizations
    sample_data.py                 Reading sample generation
    export_reading_packet.py       Context packet export
    export_gephi.py                Network graph exports
    summarize_annotations.py       Human coding progress counter
    validate_outputs.py            Output validation
  tests/test_research.py           15 unit tests
  docs/                            6 documentation files + 2 SQL files
  outputs/                         All generated outputs (no raw data)
  deliverables/                    Report PDF, DOCX, PPT, handoff
  README.md                        Project overview
```

---

## 18. Key Limitations and Caveats

These are crucial to understand because a teacher will likely ask about them:

| Limitation | Explanation |
|---|---|
| **Not representative** | The corpus is not a census of Reddit or technology workers. Collection completeness is unverified. |
| **Unknown collection parameters** | Exact API queries, pagination settings, and cutoff reasons for the data collection are unknown. |
| **Keyword matching is not relevance** | A record matching "layoff" might be discussing a sports context. Human validation is needed. |
| **Uneven coverage** | r/technology comments end June 2025; r/cscareerquestions has no posts. Time trends must use community-specific windows. |
| **No stance validation** | The lexical stance baseline has 59% "no signal." Real stance requires human coding. |
| **Reply is not agreement** | A reply to a "blame" comment does not mean the replier agrees. Network structure is not social endorsement. |
| **No cross-platform data** | Originally planned to include X and LinkedIn — this has not happened. |
| **Pseudonymization is not anonymity** | SHA-256 hashing reduces re-identification risk but does not guarantee anonymity. |
| **Engagement scores are snapshots** | Reddit scores change over time; these are point-in-time captures. |
| **No causal claims** | Correlation between community type and language concentration does not equal causation. |

---

## 19. Literature Review Summary (15 Studies)

The report includes a **617-word comparative literature review** covering **15 studies**. Here is a summary of what kinds of studies were covered:

| Theme | Studies Cover... |
|---|---|
| **Layoff discourse on social media** | How layoffs are discussed on Twitter/X, Reddit, and Glassdoor; sentiment analysis of layoff announcements |
| **Community-specific behavior** | How different online communities frame the same events differently |
| **Solidarity vs. blame framing** | Research on support networks vs. blame attribution in employment crises |
| **AI and automation anxiety** | Studies on how workers perceive AI-driven job displacement |
| **Network analysis of discussions** | Using graph-based methods to understand information diffusion in online communities |
| **Computational text analysis** | NLP methods (VADER, BERT, topic modeling) applied to social media employment discourse |
| **Reddit as a research platform** | Methodological considerations for using Reddit data in social science research |

Each paper was documented with: data source, method, key result, limitation, and how it informs this project.

---

## 20. Potential Viva Questions and Model Answers (30 Q and A)

### Category 1: Project Understanding

**Q1: What is the title and core objective of your project?**

A: "Solidarity or Blame: Computational Social Media Analysis of Technology Employment Disruption." The core objective is to examine how technology employment disruption — including layoffs, hiring freezes, AI displacement, and restructuring — is discussed, interpreted, and socially negotiated across different Reddit communities. We compare how worker-centric communities (r/cscareerquestions) and general tech-news communities (r/technology) differ in their discourse patterns.

---

**Q2: Why did you choose Reddit over other social media platforms?**

A: Reddit was chosen for three reasons: (1) It provides publicly accessible data through archives like Arctic Shift; (2) It has clearly defined community boundaries (subreddits) that allow cross-community comparison; (3) Its threaded conversation structure enables analysis of reply chains and interaction networks. We originally planned to include X (Twitter) and LinkedIn, but comparable data has not yet been collected from those platforms.

---

**Q3: What is the difference between "solidarity" and "blame" in your project context?**

A: "Solidarity" refers to supportive, empathetic responses — offering advice, sharing resources, expressing understanding toward affected workers. "Blame" refers to attributing responsibility — to workers themselves ("you should have upskilled"), to companies ("corporate greed"), to AI, or to government policies. We hypothesize these two framings differ systematically across communities.

---

**Q4: What are your three hypotheses?**

A: H1: Employment-disruption language differs significantly by community context. H2: Worker-centred support (solidarity) and industry-level framing (blame) differ by community. H3: Solidarity and blame labels produce different reply patterns in conversation networks. Currently, only H1 has preliminary support from Phase 2.

---

### Category 2: Data Collection and Methodology

**Q5: What is Arctic Shift and why did you use it?**

A: Arctic Shift is a community-maintained historical Reddit data archive that provides API access to past Reddit posts and comments in JSON format. We used it because Reddit's official API severely limits historical data access, while Arctic Shift allows bulk retrieval of posts and comments across specific subreddits and date ranges.

---

**Q6: How much data did you collect?**

A: We collected 2,974,250 total records — 115,213 posts and 2,859,037 comments — from three subreddits (r/cscareerquestions, r/technology, r/programming) spanning January 2025 to September 2026. The raw data is approximately 5.74 GiB across 29,821 JSON batch files.

---

**Q7: What keywords did you use for collection?**

A: The initial collection used layoff-related keywords: layoff, layoffs, laid off, job cuts, workforce reduction, downsizing, fired, termination, tech layoffs, AI layoffs, etc. For analysis, we later broadened to six facets: layoffs, hiring conditions, AI/work change, corporate restructuring, economic/policy, and career transitions.

---

**Q8: How did you handle the different coverage periods across communities?**

A: We identified the issue: r/technology comments end June 2025, r/programming ends December 2025, while r/cscareerquestions extends to September 2026. To make a fair comparison, we used only the **shared January to May 2025 window** where both communities have complete coverage. All comparisons explicitly state which window is being used.

---

**Q9: How did you ensure data quality?**

A: We verified: zero duplicate (kind,id) records, zero JSON parse errors, zero folder/creation-month mismatches. We audited text availability (94.61% comment bodies available), parent-child linkage (99.33% comment parents available), and ran 15 unit tests covering text preparation, conversation reconstruction, graph construction, and screening logic. A full output validator checks all CSV exports and Gephi files.

---

**Q10: How did you handle privacy and ethics?**

A: We pseudonymized all author usernames using SHA-256 hashing with a configurable salt. Original usernames are never committed to Git. The raw data, full processed tables, and user-level network files are excluded from the public repository. We explicitly note that pseudonymization reduces but does not eliminate re-identification risk, and that subreddit membership cannot determine someone's occupation or employment status.

---

### Category 3: Analysis and Results

**Q11: What is your headline result?**

A: In the shared January to May 2025 window, hiring-condition language appeared in 8.50% of r/cscareerquestions comments versus 0.45% of r/technology comments — an 18.69x rate ratio. Layoff language was 2.32% versus 0.20%, an 11.36x ratio. All six employment-disruption facets showed 5x to 19x higher concentration in the worker-centric community.

---

**Q12: What statistical test did you use and what did it show?**

A: We used a **two-proportion z-test** comparing the layoff-language rate in r/cscareerquestions (2.32%) versus r/technology (0.20%). The z-statistic was approximately 141.42, with p < 0.001. However, this test assumes independence between observations, which may not hold (repeated authors, threaded conversations). It provides descriptive support for the magnitude of the difference, not a definitive causal conclusion.

---

**Q13: What does the 18.69x rate ratio mean in practical terms?**

A: It means that for every 1,000 collected comments in the shared window, approximately 85 in r/cscareerquestions contain hiring-condition language versus about 4.5 in r/technology. The worker-centric community discusses hiring conditions nearly 19 times more intensely than the general tech-news community. This supports H1 — community context shapes discourse.

---

**Q14: What are the six lexical facets and why did you choose them?**

A: Layoffs, hiring conditions, AI/work change, corporate restructuring, economic/policy, and career transitions. These were chosen because the project brief defines employment disruption as a **broader process** — not just layoffs. The facets capture different dimensions of how technology employment is changing. Each facet uses carefully designed regex patterns with employment anchors to reduce false positives.

---

**Q15: What is an "employment anchor" in your screening methodology?**

A: Some facets (like AI/work change) would generate massive false positives if used alone — "AI" appears in millions of comments about technology generally. An employment anchor requires that the same text field also contains a word like "jobs," "hiring," "workers," "engineers," etc. This ensures we only capture AI discussions that are connected to employment. The layoff facet does NOT require an anchor because terms like "laid off" are inherently employment-related.

---

### Category 4: Networks and Gephi

**Q16: What networks did you build for Gephi and what do they show?**

A: Two networks: (1) An **author reply network** (14,507 nodes, 15,427 edges) showing who replies to whom, weighted by reply count; (2) A **conversation network** (13,866 nodes, 13,206 edges) showing comment-to-comment reply chains. Both are directed graphs scoped to layoff-matching content.

---

**Q17: Can you infer that someone agrees with a post just because they replied?**

A: No. A reply to a "blame" comment could be challenging it, agreeing, asking for clarification, or making an unrelated point. Reply structure shows **interaction patterns**, not endorsement or stance. This is why we need validated stance labels (from human coding) joined to the network edges before we can study how solidarity and blame propagate.

---

**Q18: Why do you have zero dangling endpoints in your graphs?**

A: We validated every exported graph to ensure all edge endpoints exist as nodes. Unknown authors, absent parent content, cross-thread links, and self-replies are explicitly excluded during construction. This means the graphs are structurally valid and can be directly imported into Gephi without data integrity issues.

---

### Category 5: Limitations and Future Work

**Q19: What is the biggest limitation of your current results?**

A: The biggest limitation is that **keyword matching is not validated relevance**. A comment matching "layoff" might be about a completely different context. Until we complete human coding of the 200-record sample and achieve inter-coder agreement, our rates are retrieval frequencies, not confirmed discourse patterns. This is why we call the current work a "preliminary" result.

---

**Q20: Why have you not tested H2 and H3 yet?**

A: H2 (solidarity vs. blame framing by community) requires confirmed stance labels, which need human coding. H3 (different reply patterns for solidarity vs. blame) additionally requires joining those labels to network edges. Both depend on completing the 200-record annotation, achieving inter-coder agreement, and potentially training/evaluating automated classifiers. This is Phase 3 work.

---

**Q21: What would you do differently if you started over?**

A: (1) Document collection parameters more thoroughly (exact API queries, pagination settings); (2) Ensure consistent community coverage periods from the start; (3) Consider including r/cscareerquestions posts (currently missing); (4) Plan the cross-platform component (X, LinkedIn) earlier with concrete data access plans; (5) Begin human coding earlier in parallel with pipeline development.

---

**Q22: How will you evaluate VADER and the transformer classifier?**

A: We will use the human-coded 200-record sample as ground truth. VADER provides a polarity-based sentiment score, while a transformer (e.g., fine-tuned BERT or RoBERTa) can classify stance. We will compute precision, recall, F1-score, and confusion matrices against human labels. If the lexical stance baseline has 59% "no signal," we expect the transformer to substantially outperform VADER.

---

### Category 6: Technical Understanding

**Q23: Why Python's standard library instead of pandas/scikit-learn for the analysis pipeline?**

A: The core pipeline uses Python 3.10+ standard library (csv, json, sqlite3, re) for maximum reproducibility — no dependency version conflicts. This ensures anyone can run the pipeline on any machine with Python installed. Pandas is only needed for the collection pipeline, and Matplotlib is isolated in a separate virtual environment just for EDA plots.

---

**Q24: How does your conversation reconstruction handle cycles and missing parents?**

A: The algorithm uses iterative depth resolution (not recursion) to safely handle chains of 1500+ comments. Cycles (comment A replies to B, B replies to A) are detected and flagged with depth_status='cycle'. Missing intermediate parents result in depth_status='missing_parent'. Invalid parent references get depth_status='invalid_parent'. No depth is ever invented — only explicitly resolvable depths are assigned.

---

**Q25: What is the SQLite database used for?**

A: data/processed/reddit.sqlite is the working database containing all records, features, threads, reply edges, disruption screens, and reading samples. It enables efficient SQL joins, filtering, and contextual reading without repeatedly parsing 5.74 GiB of raw JSON. The flat CSV exports are derived from this database for analysis outside SQLite.

---

### Category 7: Conceptual and Theoretical

**Q26: How does your project relate to computational social science?**

A: It combines computational methods (large-scale data collection, lexical screening, network analysis, NLP) with social science questions (how communities construct meaning around employment disruption, whether framing differs by context). We are not just measuring sentiment — we are examining how people explain, negotiate, and respond to employment change collectively.

---

**Q27: What is the difference between descriptive rates and prevalence estimates?**

A: Our rates describe the **collected corpus** — the percentage of downloaded comments matching specific patterns. A prevalence estimate would require a representative sample of a defined population (e.g., all technology workers, all Reddit users). We cannot make prevalence claims because our collection is keyword-targeted, community-limited, and of unknown completeness.

---

**Q28: Why can you not claim this study represents all technology workers?**

A: Because: (1) Reddit users are not a representative sample of technology workers; (2) Not all technology workers use these subreddits; (3) Our collection is keyword-targeted, biasing toward certain discussions; (4) We cannot verify participants' actual occupation, location, or employment status from their posts; (5) Community-specific norms influence who posts and what they say.

---

**Q29: What would "external triangulation" add to your study?**

A: Triangulation means comparing our discourse patterns with independently documented events (e.g., confirmed layoff announcements from WARN Act filings, BLS unemployment data, AI development milestones). If we see a spike in layoff language in February 2025 and there was a major layoff announcement that month, that provides interpretive context. But temporal coincidence alone does not prove the discussion was caused by that event.

---

**Q30: If you found that r/cscareerquestions has more blame language, what would that mean?**

A: It would mean that within the collected corpus, worker-centric communities express more blame attribution (toward companies, AI, policies, or fellow workers). But we would need to distinguish: blame toward whom? By whom? In response to what? A "blame" comment might be "company X is evil" (blame toward corporation) or "you should have learned Python" (blame toward the worker). The human coding scheme distinguishes these — which is why automated classification alone is insufficient.

---

## Quick Reference Card

| Item | Key Number/Fact |
|---|---|
| **Project title** | Solidarity or Blame |
| **Total records** | 2,974,250 |
| **Posts** | 115,213 |
| **Comments** | 2,859,037 |
| **Subreddits** | r/cscareerquestions, r/technology, r/programming |
| **Date range** | January 2025 to September 2026 |
| **Data source** | Arctic Shift API |
| **Comment body availability** | 94.61% |
| **Broader screen matches** | 177,808 records |
| **Highest rate ratio** | Hiring conditions: 18.69x |
| **Layoff rate ratio** | 11.36x |
| **Shared comparison window** | January to May 2025 |
| **Reading sample size** | 200 records |
| **Author network nodes** | 14,507 |
| **Unit tests** | 15 — all passed |
| **Literature review** | 15 studies, 617 words |
| **H1 status** | Preliminary support |
| **H2 status** | Not yet tested |
| **H3 status** | Not yet tested |
| **Your role** | Data collection, raw batches, provenance |

---

**TIP FOR PRESENTATION (Slide 10):** Focus on the numbers — 3M records, 3 subreddits, 94.61% body availability, zero duplicates, checkpointed collection via Arctic Shift API with rate limiting and exponential backoff. Mention the coverage gap issue and how the shared-window approach solves it.

---

*Document generated from analysis of the full project repository, local pipeline code, all documentation, output files, and deliverables.*
