# Exploratory analysis: how these communities talk about tech job disruption

*Working notes, 15 November 2026. Read-only work on `data/processed/reddit.sqlite`, the 200-record reading sample, and the Gephi author export. No existing script, table or label was changed. Every table cited here comes from `scripts/explore_leads.py`, which writes to `outputs/09_leads/`. A full run takes about 2.5 minutes with `.venv-eda/bin/python scripts/explore_leads.py`.*

**Companion notes.**
- `outputs/10_language/LANGUAGE_NOTES.md`: distinctive vocabulary by community, by year, and by upvoted vs downvoted.
- `outputs/11_dynamics/DYNAMICS_NOTES.md`: language change over time, who adopts new words, which styles get upvoted, which sources each community cites, and what further analyses the literature suggests.

**Status of the reading.** All close reading so far was done by Claude: the screen audit, the marker checks, and the blame-target coding. It is recorded in `outputs/09_leads/manual/*_codes.csv` with `coder = claude-provisional`. Treat it as a first pass for a human coder to check, not as results.

**Scope rules used throughout.**
- Comparisons across the three subreddits use comments up to June 2025 only. That is the last month all three have comments.
- Anything later is looked at within r/cscareerquestions (cscq) only.
- cscq has no collected posts, so the comment is the unit there and thread titles are unknown.

**Note on scores.** Scores are snapshots taken at collection time, and big threads collect far more votes than small ones. So instead of raw scores, these notes mostly use a comment's *within-thread score percentile*: 0 means the lowest-scored comment in its thread, 1 the highest. Many comments tie at the minimum score, which pulls the average down to about 0.43, so differences between groups matter more than the absolute level.

---

## 1. First question: what is the keyword screen actually picking up?

Before counting anything we needed to know what the six screens in `scripts/disruption_rules.py` return. We read all 200 records in the reading sample and sorted each into three classes:
- *relevant*: actual employment disruption.
- *adjacent*: job talk that is not disruption, such as résumé tips, interview mechanics or salary chat.
- *not relevant*: unrelated content.

Source: `screen_audit/manual_precision_by_group.csv`.

| Screen group | n | relevant | adjacent | not relevant |
|---|---:|---:|---:|---:|
| layoffs | 40 | 38 | 2 | 0 |
| corporate_restructuring | 20 | 15 | 1 | 4 |
| economic_policy | 20 | 14 | 5 | 1 |
| ai_work_change | 30 | 8 | 12 | 10 |
| hiring_conditions | 40 | 9 | 19 | 12 |
| career_transition | 20 | 3 | 8 | 9 |
| background (no screen match) | 30 | 2 | 4 | 24 |

The layoff screen is clean. The hiring, AI and career screens mostly return job-adjacent chatter or noise. Part of the career-transition noise turned out to be a regex bug: `quit\w*` also matches "quite". Of 14,315 career-transition hits, 5,432 (37.9%) matched only on "quite", and 2,639 records are in the candidate pool for no other reason (`screen_audit/quite_artifact.csv`).

This shaped everything that follows. We built the rest of the analysis around the layoff screen, and any result that depends on the noisier screens is checked by reading a sample.

---

## 2. When people explain layoffs, what gets upvoted?

**What we did.** We took layoff, AI and hiring candidate comments from threads with at least 10 comments. Bots and very short comments were dropped. We then tagged each comment with simple text markers for the kind of explanation it offers:
- AI as an excuse or pretext ("using AI as an excuse", "blame it on AI");
- AI inevitability ("AI will replace…", "adapt or die");
- executive or shareholder blame;
- offshoring or H-1B;
- macroeconomics;
- individual performance.

For each marker we compared the average within-thread percentile of comments with and without it (`lead1_reward/marker_within_thread_percentile.csv`, figure `figures/lead1_marker_percentiles.png`).

**What we saw.**

| Marker | cscq (difference, 95% CI) | r/programming | r/technology |
|---|---|---|---|
| AI as excuse | +0.04 (0.02 to 0.06), n=984 | **+0.16** (0.09 to 0.24), n=55 | +0.09 (0.04 to 0.14), n=183 |
| Executive / shareholder blame | +0.04 (0.02 to 0.05) | +0.08 (0.04 to 0.13) | +0.06 (0.04 to 0.08) |
| AI inevitability | −0.03 (−0.05 to −0.01) | 0.00 (−0.07 to 0.08) | −0.04 (−0.08 to 0.01) |
| Individual performance | 0.00 | +0.03 (CI spans 0) | +0.02 (CI spans 0) |

Comments that call AI an excuse, or that blame executives, sit higher in their threads in all three communities. Comments about AI inevitability sit slightly lower in cscq, and possibly in r/technology.

**Does arrival time explain it?** Early comments collect votes whatever they say, so we split the comparison by whether a comment arrived in the first 20% of its thread and by whether it replied to the post or to another comment (`lead1_reward/marker_strata.csv`):
- In cscq, the "AI as excuse" advantage is almost all among *early* comments: +0.05 for early replies to the post, +0.13 for early replies to comments, and about 0 for late ones.
- The inevitability penalty shows the same pattern: −0.09 and −0.10 early, about 0 late.
- Executive blame stays positive in three of the four groups.

So the voting effect sits where voting happens. Late comments barely move, whatever they say.

**What reading the matches showed.** These markers are blunt, so we read 30 random matches of each (`manual/ai_pretext_codes.csv`, `manual/ai_inevitable_codes.csv`).
- **AI as excuse.** About half really argue that AI is a cover story (15 of 30, plus 2 partial). The rest use "excuse" in some other sense. Typical real examples:
  > "Rofl nah its this is more to cover their inefficiency (Block did not need 10k employees with what they were doing…) but that sounds bad so they blame it on AI." (cscq, +156)
  >
  > "As somebody that works at Walmart in tech, these layoffs had nothing to do with AI except insofar as AI offers a convenient excuse. On our team, the people with the lowest performance ratings last year were cut." (r/technology, +6)
- **AI inevitability.** The marker is worse. Only 7 of 30 matches actually endorse the idea that AI will replace jobs, and 6 more do so conditionally. Most matches quote the claim in order to knock it down: "The whole 'AI will replace developers' hype was way overblown from the start". The 7 real endorsements sat low in their threads (mean percentile 0.23, against 0.42 for the rest), for example:
  > "Many refuse to see what is inevitable, because it's unpleasant to acknowledge… eventually, it will replace most, if not all, of them." (cscq, −7)

  The numbers are tiny, but they point in the same direction as the table. The table itself mixes endorsements with rebuttals.

Dissent from the "AI is an excuse" line is not always punished. One comment that names the norm and pushes against it was among the top in its thread:
> "People on this sub will say you are just AI-washing and using AI as an excuse not hire people. But the truth is obvious: AI is already impacting how software engineering is done…" (cscq, +43, 97th percentile)

**What it might mean.** All three communities seem to accept that the disruption is real while rejecting the official explanation for it. "Management is using AI as cover" is a comfortable, often-rewarded position. "AI really can do our jobs" is harder to say. One reading is professional identity defence. Another is simple scepticism of corporate PR. Telling these apart needs reading, not counting.

**Still open.**
- Is this a stable norm, or mostly a feature of a few big early threads?
- What do replies to the rare real inevitability claims look like: argument, mockery, or silence?
- In 2026, when cscq talks much more about AI (Section 4), does the "excuse" line weaken?

---

## 3. Do people who were laid off explain it differently from people watching?

**Why we looked.** Earlier counts suggested AI comes up much more in r/programming layoff talk (39% of layoff comments, up to June 2025) than in cscq (11%). One explanation is distance: people affected by a layoff talk about consequences, while onlookers theorise causes. To test that without the community confound, we compared *within cscq*. We matched comments that report the author's own layoff ("I was / got / just got … laid off / let go") with all other cscq layoff comments (`lead2_proximity/first_person_vs_other.csv`).

**What we saw** (cscq, all months; first-person n = 1,938, other layoff comments n = 21,122):

| | First-person | Other layoff comments |
|---|---:|---:|
| Mentions AI at all | 8.8% | 18.1% |
| AI as excuse | 0.4% | 2.0% |
| Executive / shareholder blame | 2.8% | 6.4% |
| Offshoring / H-1B | 4.5% | 7.2% |
| Macroeconomics | 2.7% | 4.9% |
| Consequence words (savings, insurance, COBRA, rent, months unemployed, applications, family…) | **27.6%** | 14.7% |
| Replies per comment | 0.63 | 0.74 |
| Replies with sympathy words | 4.8% | 1.6% |
| Replies with challenge words | 3.2% | 4.3% |

The pattern holds for cscq before June 2025 alone, and in r/technology, although r/programming has only 12 first-person comments.

**What reading showed.** We read 40 random first-person accounts with their first replies (`manual/first_person_layoff_codes.csv`).
- 39 are real first-person accounts.
- Only **3 of 40 give any cause**: office politics, budget cuts, nepotism ("Why my team got laid off, guess whose nephew didn't?").
- The rest are about what happened next: job hunting, gaps on the résumé, savings, unemployment benefits, stock options lost.
  > "I'm in this boat, I've been laid off for probably three years now… Thinking of doing retail if things don't turn around for me, been living with friends and family and burning through my savings for too long at this point" (+57)
  >
  > "I got laid off 1 day after my child was born. They called me IN the hospital." (+26)
- Replies are mostly practical questions ("Do you mind if I ask you how you navigated the question for employment gap?") or matching stories:
  > "Feel this so much. Cashed in my 401k to avoid going homeless… Moved back in with mom" (reply to the +57 comment above)
  >
  > "sorry bro, pouring one out for you. I've survived 3 rounds so far but it's got me sweating"

**What it might mean.** Explaining layoffs with AI looks mostly like an onlooker's frame. People inside a layoff talk about logistics and survival, and the community answers them with advice and shared experience more than argument. That fits the idea of cscq as a peer support and advice space sitting alongside a debating space.

**Limitations.**
- The first-person pattern has high precision but surely misses many accounts.
- Proximity is *self-presented* and cannot be verified.
- The sympathy and challenge word lists are crude and have low absolute rates.
- First-person accounts do not get *more* replies, so "the community rallies round" would overstate it.

---

## 4. How AI talk in cscq changed between 2025 and 2026

**What we did.** cscq is the only community with comments through September 2026. We counted AI-screen comments per 1,000 cscq comments each month and split them into rough themes (`lead3_ai_shift/cscq_monthly_ai_themes.csv`, figure `figures/lead3_cscq_ai_themes.png`).

**What we saw.**
- AI candidates went from about 28 per 1,000 comments (January–April 2025) to **70 per 1,000 in March 2026**, and stayed at 50–64 through September 2026.
- **Naming specific tools** (Cursor, Copilot, Claude, agents, vibe coding) rose the most: about 1.5 per 1,000 in early 2025 to about 10 in March 2026.
- **Replacement and layoff talk** also rose in 2026, peaking at 17 per 1,000. It did not fade away.
- **AI in hiring and interviews** rose slowly, from about 4–5 to 7–9.
- **Mandate and usage-tracking talk** stays small, but rose from about 0.2 to about 1 per 1,000.

One detail stands out. AI talk *fell* in September 2025, from 40 to 26 per 1,000, the same month H-1B talk exploded (Section 5). Attention may have shifted between topics, but we have not tested that.

**First-hand mandate accounts.** We used a narrow pattern to find comments describing the author's own company pushing AI use ("my company … forcing … AI"). It finds only 9 such comments in all of 2025, then 35 in January–June 2026 (`lead3_ai_shift/cscq_mandate_quantified_by_half.csv`). Of 40 we read, 31 are real first-hand workplace accounts (`manual/first_person_mandate_codes.csv`). What people describe:
- **Being measured:**
  > "My company had a 'refounding moment' and now I'm expected to use a certain number of tokens per month MINIMUM, merge a certain number of PRs, etc. my job went from fun architectural problems to 'how many Claude conversations can you juggle at once before going insane.'" (2026-08)
  >
  > "My company is pushing AI so heavily that your Performance Review literally depends on how much you use AI and how much you output. I fear those who try to push back or don't comply will ultimately end up getting laid off" (2026-04)
- **Clean-up work:** "my company kinda is forcing all the developers to use AI generated code… those PRs are garbage… I have to spend so much more time going through them" (2025-06).
- **Silence:** "At my company it is unsafe to give negative feedback on the AI mandates, so we shut up and comply to keep our paychecks flowing." (+116, 2026-06)
- **A minority who like it:** "Our company has seen insane productivity gains in the last 6 months since we mandated all devs had to use Claude." (2026-06)

**What it might mean.** In 2026, a layer of talk about AI *as a condition of work* was added on top of the "will AI take jobs" debate, without replacing it. That covers mandates, metrics, review load and fear of speaking up. Our earlier notes called this a shift from threat to discipline. The monthly data say "added on top" is more accurate.

**Limitations.**
- Tool names are new vocabulary, so part of the rise in tool talk just reflects new words existing.
- cscq volume swings from 35k to 60k comments a month, under unknown collection rules.
- The mandate pattern is narrow (52 comments in total), so it is a lower bound, too small for trends within the data.

---

## 5. Offshoring and H-1B: where the community draws lines

**What we did.**
- Compared how offshore/H-1B comments rank against all cscq candidates (`lead4_offshore/cscq_polarisation.csv`).
- Counted H-1B mentions per day from August to October 2025, around the 19 September $100k fee proclamation (`lead4_offshore/cscq_daily_h1b.csv`, `figures/lead4_daily_h1b.png`), and checked which threads drove each spike (`lead4_offshore/cscq_h1b_spike_days.csv`).
- Read a sample of 70: 35 from the top 10% of their threads and 35 from the bottom or below zero. For each we noted who was being blamed (`manual/offshore_blame_target_codes.csv`).

**What we saw in the counts.** Offshore/H-1B comments are not over-represented among the top-ranked: 12.9% reach their thread's top decile, the same as the baseline. They are more often voted below zero: 7.0% against 4.6% for all candidates, and 6.8% for comments naming Indian or Chinese people. An earlier count had suggested polarisation at both ends. With visibility controlled, the clearer signal is that more of these comments get net downvotes.

**What we saw in the timeline.** H-1B talk in cscq usually sits at 1–4 mentions per 1,000 comments.
- Before the proclamation, the spikes come from **single threads**: 49–100% of a spike day's mentions sit in one thread. They are debates, often with corrections at the top:
  > "There is so much misinformation on this sub. There is a difference between perm and h1b." (+69)
  >
  > "across the industry only ~5% of software engineers in the US are on H1B." (+78)
- On **20 September** the topic spread across the subreddit: 577 mentions (104 per 1,000) over 31 threads. The top comment on the 19th welcomed the fee with a reservation:
  > "I think $100k is a bit high, but I think it aligns with the goal of the H1B program. It's intented to be a way to fill gaps in skills…" (+830)
- Within about four days the rate was back to normal, apart from one more single-thread spike on 28 September.

**What we saw in the reading.**

| Who is blamed | Top of thread (35) | Bottom / negative (35) |
|---|---:|---:|
| Employers or the visa system | 16 | 5 |
| Foreign workers themselves | 4 | 3 |
| Ethnicised leadership or stereotypes | 3 | 4 |
| Pushback against blaming immigrants | 3 | 6 |
| Off-topic or incidental mention | 9 | 17 |

- Upvoted offshore comments mostly make **the employer or the system** the actor, and present visa workers as exploitable rather than as the problem:
  > "you can more easily abuse H1B workers because they are dependent on the company for status…" (+176)
  >
  > "There exist H1B workers that are paid well. This does not mean that H1B isn't also used to depress pay." (+25)
  >
  > "It's outsourcing. The model has changed. It's now a jobs transfer model…" (+178)
- But "my company hired an Indian CTO, then moved jobs to India" stories are also upvoted (+117, +21). Anti-racist pushback can be upvoted too ("Lmao the blatant racism here…", +20).
- Of the 9 comments in the sample with net-negative scores, 4 push back against blaming immigrants ("distilling it to just an h1b issue is choosing to divide it upon lines that are racially motivated", −2). Others are stereotypes (a caste anecdote, −11) or hard-line nationalism ("If Trump was a *nationalist* president, he would terminate all H1B visas immediately", −1).

**What it might mean.** The line the community draws seems to be about *who* is blamed, not the topic. Criticising employers and the visa system is the accepted position. Blaming workers as people gets mixed reactions. So does defending the current system or calling the thread racist. Ethnicised stories about leadership sit in a grey zone: sometimes upvoted, sometimes not. This is boundary work, and it needs careful coding.

**Limitations.**
- n = 70 with one coder (Claude).
- "Bottom" mostly means *low-visibility*, a score of 1 in a big thread, rather than rejected. Only the net-negative cases are clear rejections.
- Removed comments are not visible to us. Moderator removal would hide the most extreme content.

---

## 6. What the author network shows, and what it doesn't

**What we did.**
- Re-ran the Gephi author reply graph (`gephi/exports/authors_keyword-comments_direct`) under simple thresholds (`lead5_network/threshold_robustness.csv`).
- Checked what the top in-degree and betweenness accounts are (`top_in_degree_what_they_are.csv`, `betweenness_vs_threads.csv`).
- Profiled the top 10 betweenness accounts against a fixed ~5% sample of all cscq comments (`brokers_profile.csv`).

**What we saw.**

| Version | Users | Edges | Largest component |
|---|---:|---:|---:|
| Full export | 14,507 | 15,427 | 64.3% |
| Both endpoints degree ≥ 2 | 4,721 | 7,676 | 91.8% |
| Both endpoints degree ≥ 5 | 1,013 | 2,153 | 98.2% |
| Only repeated ties (weight ≥ 2) | 674 | 446 | **4.3%** (29 users) |
| Only reciprocated ties | 1,347 | 1,718 | **9.0%** (121 users) |

- **Repeated relationships are rare.** Keep only ties that happen twice, or that run in both directions, and the network falls apart.
- **The top in-degree accounts are r/technology news posters.** The #1 account received 300 replies, all of them to its posts, and has 1,838 posts but only 14 comments.
- **Betweenness mostly measures how many threads someone takes part in.** Among users with any betweenness, its correlation with the number of distinct threads is 0.57 (Spearman). The top 20 by betweenness appear in a median of 29.5 threads, against a median of 1 for everyone else.
- **The top-10 betweenness accounts are long-running cscq regulars.** Most were active 19–21 months, with 573–5,525 comments each.
- **Are the regulars especially "realist" ("the market really is bad")?** The text check gives a weak answer:
  - The realism wording is above the 0.46% baseline for 8 of 10, but never above 2.5%.
  - Talk about AI splits evenly: 5 of 10 are below the 11.0% baseline (as low as 2%), and 5 above (up to 22%).
  - Offshore talk is above the 2.5% baseline for 5 of 10.
  - So the regulars do not share one profile. Any "realist" persona has to be found by reading them, not inferred from position in the graph.

**What it might mean.** The graph is mostly thread structure plus a few heavy posters, not communities or alliances. Its practical value is as a list of regulars who can be followed over 20 months by reading their comments in order. The difference between in-degree and betweenness reflects posting versus commenting, not influence. Any network write-up should say this.

---

## 7. Other things noticed along the way (not yet followed up)

- **r/technology discusses employment through politics.** 13.4% of its layoff comments mention DOGE, Trump, Musk or federal agencies, against about 4% elsewhere. Its top hiring-matched comment, at +9,363, is a timeline of FAA firings.
- **Gallows humour is a highly rewarded register in cscq layoff threads.** "Layoffs will continue until morale improves." (+2,818)
- **Survivors of layoffs describe heavier workloads.** "…that 100% of work includes what historically would be done by more than 1 person because of constant layoffs." (+1,230). The current coding guide has no category for this.
- **cscq layoff peaks are tied to claimed events.** One example is the Oracle "set to layoff 20%… to build AI data centers" comment (+865, March 2026). Claims like this need checking against a dated event register before they are treated as events.

---

## 8. Questions this leaves us with

1. **Explanations and reward.** Which layoff explanations does each community reward or reject? Is "AI is an excuse" a norm that is stable over time, or one that 2026 erodes?
   - Unit: comments making a causal claim about layoffs.
   - Approach: compare within-thread rank and the stance of replies.
2. **Proximity.** Does explanation follow distance from the event? Coding proximity (self / close other / onlooker / news reaction) against explanation frame, within cscq, would test Section 3 properly.
3. **AI as a condition of work.** How did cscq's AI talk change from 2025 to 2026? What repertoires appear in response to mandates: compliance, malicious compliance, silence, exit?
   - Approach: fixed sample per quarter, coded by hand, aligned with a dated register of company AI mandates.
4. **Boundaries in offshore talk.** Where does the community draw the line between criticising the system and blaming people? Who gets pushed back on, and how?

Each question has the same main validity threat: scores are snapshots that depend on visibility. Use within-thread rank and arrival time, and do not compare raw scores across communities of different sizes.

---

## 9. What we suggest doing next, in order

1. **Human-code 60 records** (10 per screen group) with the codebook below, using two coders, then compare. This checks the codebook and replaces Claude's provisional audit.
2. **Have a human re-code the five Claude-coded samples** in `outputs/09_leads/manual/`. This is about 220 comments and gives the marker precision we would report.
3. **Read whole threads** where the arguments in Sections 2 and 5 happen: the 20 September 2025 cscq threads, the single-thread H-1B debates in August, and the May 2025 r/technology thread "lost his $150K job to AI… rejected from 800 jobs" (633 candidate comments). Write a short memo per thread on how blame is argued.
4. **Read the top-10 betweenness regulars in time order**, to see whether a "realist" persona exists and whether it shifts.
5. **Fix or document the "quite" bug** before any career-transition count is reported. Treat it as a documented rule change, not a silent edit.
6. **Build a small event register:** the H-1B proclamation, named layoffs, and company AI mandates in 2025–26.

---

## Appendix: starter codebook (for `annotations/reading_labels_employment.csv`)

This refines `docs/CODING_STARTER.md` using what the reading above turned up. Separate multiple codes with semicolons. Code what the *author* says, not what the screen matched, and put the evidence span in `notes`.

- **`relevance`**
  - `relevant`: tech employment disruption.
  - `adjacent`: job talk that is not disruption, such as résumés, interviews or salary. This value is new; without it about 28% of hits get forced into yes or no.
  - `irrelevant`: no employment content, including screen false positives such as "quite".
  - `uncertain`.
- **`document_type`**: `first_person`, `close_other`, `news_share`, `news_reaction`, `advice_request`, `advice_given`, `opinion_argument`, `joke_meme`, `other`.
- **`experiences`** (only if actually described): `laid_off`, `survived_layoff`, `workload_increase`, `job_search_struggle`, `offer_success`, `ai_mandate_at_work`, `rto_or_offshore_at_work`, `career_exit_or_switch`, `immigration_status_risk`.
- **`explanations`**: add the suffix `_asserted`, `_tentative` or `_rejected`. Section 2 showed why rejection has to be coded: most "AI will replace" text is quoted in order to reject it.
  - `ai_capability`, `ai_pretext`, `ai_capex`, `exec_greed_shareholders`, `overhiring_correction`, `macro_rates`, `offshoring`, `immigration_h1b`, `oversupply_of_grads`, `individual_performance`, `govt_policy_politics`, `other`.
- **`blame_target`** (for offshore/immigration talk): `employer_or_system`, `foreign_workers`, `ethnic_group_or_leadership`, `pushback_on_blame`.
- **`future_expectations`**: `recovery`, `prolonged_downturn`, `ai_displacement`, `ai_overhyped_will_backfire`, `deskilling_quality_decline`, `leave_field`, `uncertain_mixed`.
- **`themes`** (emergent): `ai_as_excuse`, `market_denial_vs_realism`, `survivor_intensification`, `ai_mandate_metrics`, `ai_mandate_silence`, `economic_nationalism`, `ethnic_blame`, `junior_pipeline_collapse`, `gallows_humor`, `collective_action_union`, `political_federal_workforce`.
- **`emotions`** (only with textual evidence; name the target in `notes`): `anger`, `fear_anxiety`, `despair_resignation`, `cynicism`, `hope`, `relief`, `schadenfreude`, `mixed`.
- **`response_function`** (relative to the parent): `empathy_support`, `practical_advice`, `shared_experience`, `information_resource`, `endorse_amplify`, `challenge_counterargue`, `correct_fact`, `dismiss_mock`, `blame_victim`, `police_optimism`, `police_doom`, `humor`, `none_toplevel`.

**Decision rules.**
1. Mark relevance first. If `irrelevant`, stop.
2. Quoted text (`>`) belongs to the parent, not the author.
3. Sarcasm: code the intended meaning and add `sarcasm` to `notes`.
4. An explanation counts only if the author links a cause to employment outcomes.

*Ethics note.* Quotes here are verbatim from pseudonymised records, for internal team use only. Before anything is published, paraphrase quotes or check that they cannot be searched back to an account. This matters most for first-person layoff, health or family, and visa-status disclosures.
