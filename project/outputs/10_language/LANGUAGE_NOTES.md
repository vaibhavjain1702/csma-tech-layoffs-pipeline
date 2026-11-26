# How the communities talk: vocabulary analysis

*Working notes, 15 November 2026.*
- **Script:** `scripts/explore_language.py`. It is read-only, runs in about 4 minutes, and peaks at about 280 MB of memory.
- **Outputs:** all tables and figures cited below are in `outputs/10_language/`.
- **Context snippets:** each comparison has an `examples_in_context.csv` file showing every top word in real sentences, so each word can be checked without reading whole threads.

## What we did and why

Instead of hand-coding comments, we let word frequencies show how the communities differ. There are two analyses.

**1. Distinctive vocabulary.** For two groups of comments, which words does one group use unusually often compared with the other?
- **Method:** "Fightin' Words" (Monroe, Colaresi & Quinn, 2008). It computes a log-odds ratio for each word, smoothed with a prior built from both groups pooled, and divides by its standard error to get a z-score.
- **Why this method:** rare words cannot dominate the ranking, as they do with raw ratios, and common words cannot dominate either, as they do with raw counts.
- **Reading the score:** |z| > 2 is roughly "unlikely to be chance". We treat z as a ranking, not a formal test, because thousands of words are compared.
- **Tokens:** single words and two-word phrases, with stopwords removed.

**2. Vocabulary over time.** We tracked 18 terms the communities themselves use, such as "cooked", "cope", "AI-washing", "vibe coding" and "slop". For each we counted the share of cscq comments containing it, per month, per 10,000 comments. Each pattern was checked against random matches in context, and three were tightened after that check (see Limitations).

**Scope rules, as in the rest of the project:**
- Comparisons between communities use January–June 2025 only.
- Anything later uses cscq only.
- Bots are excluded.
- "Employment comments" means comments matching the layoffs, hiring, AI, restructuring or economic-policy screens. The career-transition screen is left out because of its "quite" bug.

## What we saw

### A. Each community discusses employment in its own vocabulary (Jan–Jun 2025)
Figure: `figures/A_communities_distinctive_terms.png`. Tables: `A_communities/*_vs_rest.csv`.

| r/cscareerquestions | r/programming | r/technology |
|---|---|---|
| job, resume, experience, interview, market, recruiter, offer, swe, yoe, applying, faang, leetcode, months | code, developers, ai, programmers, llms, tools, write, vibe coding, tests, documentation, rust, cursor, article, blog | dei, ai, trump, government, workers, tariffs, white, china, manufacturing, federal, musk, elon, men, women, race, diversity |

The same topic means something different in each place:
- **In cscq**, employment is about *getting through the job search*: résumés, recruiters, offers, years of experience ("yoe").
- **In r/programming**, it is about *the work itself and what AI does to it*: code, tests, documentation, tools.
- **In r/technology**, it becomes *national politics and identity*. "DEI" is the single most distinctive word (17.6 vs 0.6 per 10k tokens), followed by trump, government, tariffs, federal and musk, and also white, men, women and race.

The context file shows r/technology arguing about DEI as a hiring principle, for example: "*My point is that DEI puts irrelevant goals ahead of relevant ones*". Some matches are noise, such as "white" meaning a blank web page. The DEI and federal-workforce angle fits the earlier finding that 13% of r/technology layoff comments mention DOGE, Trump, Musk or federal agencies.

### B. cscq's vocabulary moved from immigration and credentials (2025) to AI tools and AI output (2026)
Figure: `figures/B_cscq_2025_vs_2026.png`. Table: `B_cscq_2025_vs_2026/terms.csv`. This compares Jan–Sep 2025 with Jan–Sep 2026, using a fixed 25% sample of all cscq comments (about 108k and 92k comments).

- **More typical of 2026:**
  - AI tools and vendors: ai, claude, claude code, opus, anthropic, codex, models, agents, agentic.
  - Usage and tokens: tokens, usage, prompt.
  - Code review and output: review, reviewing, output, PRs, manually, faster, workflow.
  - **slop / AI slop**.
- **More typical of 2025:**
  - Immigration and nationality: h1b, american, americans, india, indian, visas, offshoring, outsourcing.
  - Politics: trump, tariffs, dei, tiktok.
  - The credential pipeline: degree, college, cs degree, grads, students, salary, interview.

The 2026 words describe AI as *something you do at work every day*: you review its output, burn tokens, manage agents, and clean up slop. In 2025 cscq was arguing about *who gets the jobs* (immigration, degrees, nationality).

### C. In cscq, upvoted comments tell experiences; downvoted comments argue about immigration and about arguing
Figure: `figures/C_cscq_upvoted_vs_downvoted.png`. Table: `C_cscq_upvoted_vs_downvoted/terms.csv`. This compares comments in the top 10% of their own thread (16,176 comments) with comments scored below zero (5,869), within threads of at least 10 comments.

- **Upvoted:** interviews, yoe, company, resume, laid, years, experience, months, management, boss, manager, started, applying, offer, worked, weeks, friend, felt, graduated. This is the vocabulary of *first-hand experience*, with time, places and people.
- **Downvoted:** h1b, american(s), immigrants, immigration, visa, indians, foreign workers, citizens, country, taxes, biden.
  - Also *meta-argument* words: argument, saying, comment, evidence, prove, racist, delusional, cope, coping.
  - And AI words: ai, chatgpt, agents.

This matches what reading the samples suggested earlier, now across all 22k comments:
- The community rewards people who *report what happened to them*.
- It penalises comments that *argue about immigration* in either direction, and comments that *argue about the argument* ("cope", "delusional", "prove it").

AI words lean slightly toward downvoted comments: "ai" appears at 110 per 10k tokens in downvoted comments vs 93 in upvoted ones. That fits the earlier observation that confident AI claims tend to sink.

### D. Community vocabulary over time (cscq, Jan 2025 – Sep 2026)
Figure: `figures/D_cscq_vocabulary_over_time.png`. Tables: `D_vocabulary_over_time/`.

Change from Jan–Jun 2025 to Jan–Jun 2026, in comments per 10,000:

| Term | 2025 H1 | 2026 H1 | Change |
|---|---:|---:|---:|
| slop | 10 | 91 | ×8.7 |
| agents / agentic | 21 | 115 | ×5.5 |
| vibe coding | 21 | 81 | ×3.9 |
| named AI tools | 102 | 281 | ×2.8 |
| AI-washing / AI as excuse | 4 | 10 | ×2.5 |
| cope / copium | 23 | 43 | ×1.9 |
| overhiring | 9 | 16 | ×1.9 |
| "cooked" | 24 | 37 | ×1.6 |
| doom / doomer | 35 | 53 | ×1.5 |
| layoff / laid off | 230 | 252 | ×1.1 |
| new grad / entry level / junior | 358 | 343 | ×1.0 |
| offshoring / outsourcing | 141 | 104 | ×0.7 |
| ZIRP / interest rates / §174 | 29 | 19 | ×0.7 |
| H-1B | 91 | 50 | ×0.6 |

The monthly charts show the shape of each change:
- **Slow, lasting shifts:**
  - "slop" and "agents" both took off in early 2026. Agents went from about 40 to 130 per 10k between December 2025 and March 2026 and stayed there.
  - "Vibe coding" peaked in March 2026 and has been fading since.
- **Shock and decay:** H-1B jumped to about 470 per 10k in September 2025 and fell back within a month. Offshoring peaked the same month. Both settled lower than before.
- **Rising mood words:** "cope", "doom" and "cooked" all trend up into 2026.
  - "Cooked" jumped in September 2026, mostly in one thread about whether *non-software* workers are now "cooked". The top comment, at +1,479: "*from conversations with friends and family in non software fields, they are cooked but they don't know it*". The community starts applying its own despair word to other professions.
- **Explanations changed.** Macro explanations (ZIRP, interest rates, §174) and immigration explanations declined. "AI as excuse" more than doubled.
  - Its March 2026 peak was spread across 47 threads, not one, so it reads as a general reaction to that month's layoffs:
    > "They can't grow. So they're cutting. AI is the excuse." (+252)
- **Steady through everything:** talk of layoffs and of juniors/new grads barely changed. That is the background the vocabulary shifts happen against.
- **Unions** are discussed steadily, with one spike in July 2026. The spike came from two threads on Microsoft layoffs:
  > "A concrete recent example is that none of the unionized workers at Microsoft were affected in this latest round of layoffs" (+77)
  >
  > "The solution would be unions but we are too cool for that, so let's grind leetcode" (+603)

**Snapshot across communities (Jan–Jun 2025, per 10k comments;** `communities_jan_jun_2025_per_10k.csv`**):**
- cscq uses the market-mood words far more than the others: "cooked" 24 vs 5 and 8; "ghosted" 10 vs under 1.
- Offshoring and H-1B are almost entirely cscq topics: H-1B is 91 in cscq, 5 in r/programming and 9 in r/technology.
- "Vibe coding" and "slop" belong to r/programming in early 2025: 66 and 47 per 10k there.
- cscq picks these words up about a year later, at which point AI becomes a workplace topic for people in the job market and not only for programmers who follow tooling.

## What this adds to the overall story

1. **Each community has its own role.** cscq is where people go through the job search together. r/programming argues about the craft. r/technology turns employment into national politics.
2. **The community rewards experience over argument.** The voting pattern holds up at scale. Personal accounts rise; immigration arguments and meta-argument sink.
3. **AI changed from a debate into a working condition.** In cscq, 2026 vocabulary is about reviewing AI output, tokens, agents and slop. Explaining layoffs as "AI as an excuse" grows at the same time. The two may be related: people who deal with AI's limits every day are less convinced it is the reason they are being laid off.
4. **Events and drift look different.** The H-1B fee was a short shock. AI-at-work vocabulary built up over months and stayed.

## Limitations

- **Counting words is not understanding meaning.** "AI" appears in both praise and mockery, and "cope" partly means "cope with". The context files exist so each top word can be checked before being interpreted.
- **Term patterns were checked and three were changed:**
  - "AI as excuse" now requires "AI" near excuse, scapegoat or pretext, because generic "excuse" was mostly unrelated.
  - "Career change" dropped "nursing" and "electrician", which mostly appeared as examples rather than as moves out of tech.
  - "Union" excludes Soviet, European and credit union.
  - "Agents" still includes some recruiting agents.
- **cscq volume ranges from 35k to 60k comments a month,** under collection rules we don't know, so rates per 10k comments are used throughout.
- **Comparison B uses a 25% sample** of comments to keep memory low. It is a fixed sample (`created_utc % 4 = 0`), so reruns give the same numbers.
- **"Upvoted" and "downvoted" are snapshot scores.** The within-thread top 10% controls for thread size but not for arrival time.
- **Text is from pseudonymised public comments.** Paraphrase quotes before publishing.
