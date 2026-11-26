# Community dynamics: change over time, adoption, voting style and sources

*Working notes, 15 November 2026. Script: `scripts/explore_dynamics.py`. It is read-only, takes about 100 seconds, and peaks at about 240 MB of memory. Outputs are in `outputs/11_dynamics/`. It reuses the tokenizer and the Fightin' Words method from `scripts/explore_language.py` (see `outputs/10_language/LANGUAGE_NOTES.md`).*

This round asked four questions that published Reddit research has asked of other communities, applied to ours.

| Question | Borrowed from |
|---|---|
| E. How fast does the conversation change, and what is new each month? | Zhang et al. 2017, *Community Identity and User Engagement in a Multi-Community Landscape* (ICWSM): communities differ in how *dynamic* their language is. |
| F. Who brings in new vocabulary: regulars or newcomers? | Danescu-Niculescu-Mizil et al. 2013, *No country for old members* (WWW): users adopt community language early in their "lifecycle" and stop adapting later. |
| G. What style of comment does a community reward? | Goyal et al., *Uncovering the Internet's Hidden Values* (ICWSM; arXiv 2410.13036): highly upvoted content as a window on community values. Also *The Language of Approval* (arXiv 2509.10370). |
| H. What sources do communities cite? | The usual "information ecosystem" analysis of links in posts. |

---

## E. How fast cscq's language changes, and what is new each month

**What we did.**
- For every month we built the word distribution of all cscq comments.
- We measured how different each month is from the one before, using Jensen–Shannon divergence (`E_language_change/cscq_monthly_jsd.csv`, figure `figures/E_cscq_language_change.png`).
- We also listed the words most over-used in each month compared with the previous three months (`cscq_whats_new_each_month.csv`). This works as an automatic event timeline.

**What we saw.** The month-to-month change is mostly flat, at about 0.010 bits. It has clear bumps:
- **Sep–Oct 2025**, the largest: 0.014 then 0.016. September's new words are *h1b, american, fee, americans, workers, trump, union, visa, talent, offshore*.
- **Jan–Feb 2026:** 0.014 then 0.015. February's new words are *ai, claude, agents, code, agent, slop, anthropic, codex*. March adds *models, llm, opus, productivity, output*.
- **Jul 2026 and Sep 2026:** 0.014 and 0.015.

Read as a timeline, the "what's new" list is a compact history of the period:

| Month | New vocabulary (z-score) | What it is |
|---|---|---|
| Apr 2025 | tariffs, recession, insurance | macro fear after the tariff announcements |
| May 2025 | stem, students, phd, degree, h1b, grads, wages | students and credentials |
| Sep 2025 | h1b (42), american, fee, trump, union, visa, offshore | the $100k H-1B fee proclamation |
| Feb–Mar 2026 | claude, agents, slop, anthropic, codex, opus, productivity, output | AI coding agents arrive at work |
| Jun 2026 | palantir, lockheed, union(s), clearance, defense, tokens | defense-tech employers; unions ("Fuck Palantir and ex-Palantir employees.", +380) |
| Jul 2026 | chinese, unions, indians, discrimination, h1b, sponsorship | immigration and discrimination return |
| Aug 2026 | pip, prs, manager, ranking | performance management: PIPs and stack ranking (447 PIP comments in 78 threads) |
| Sep 2026 | pto, unlimited, collar, cooked | working conditions ("Unlimited PTO policies are not favorable…", +395); "white collar" jobs being "cooked" |

AI model names show up as ordinary words: "mythos" in April 2026, "fable" in June 2026 ("What if the person fixing the code is in Manila and using Claude Fable 5…"). The subreddit tracks AI releases the way it used to track interview formats.

**What it might mean.** Most of the time the community talks about the same things. Its vocabulary shifts at a few moments: one policy shock (H-1B), one technology shift (AI agents at work), and then, in 2026, a turn toward *conditions inside the job*: PIPs, ranking, PTO, mandates. That last turn has not been described anywhere else in our notes.

**Limitations.** A single large thread can dominate a month. For example, June 2025's "officer/enlisted" words come from one military-careers thread. The timeline points to *where to look*; it does not identify events by itself.

---

## F. Who adopts the new words: regulars or occasional commenters?

**What we did.**
- We split cscq commenters by how much they post in the corpus: **heavy** (50+ comments, 2,997 people, 458k comments), **regular** (10–49, 12,569 people) and **occasional** (fewer than 10, 86,111 people).
- For eight tracked terms we compared how often each group uses them, month by month (`F_adoption/`, figure `figures/F_adoption_by_author_tier.png`).

**What we saw.**
- **The AI vocabulary arrives everywhere at once.** Slop, agents, vibe coding and claude rise at the same time and to the same level in all three groups. In 2026 the heavy-to-occasional ratio is about 0.9–1.2. Regulars did not lead the adoption.
  - In 2025, occasional commenters used "agents" and "vibe coding" slightly *more* than regulars (ratios 0.72–0.86). These words came in from outside the community core.
- **"Cope / copium" is the regulars' word.** Heavy users use it 1.35× (2025 H1) to 1.7× (2026 H1) as often as occasional users. It is the community's word for policing views, and the people who use it most are the core.
- **H-1B talk is not driven by newcomers.** In the September 2025 spike all three groups rose together. The share of comments from occasional users that month (20.7%) was normal. The event got the existing community talking; it did not bring in outsiders.

**What it might mean.** Adoption studies of hobby communities (Danescu-Niculescu-Mizil et al.) find that core members carry the community's language. In cscq, *topic* words such as AI tools or H-1B spread through everyone at once, because they come from outside events. *Norm* words such as "cope" are concentrated in the core. That separates two kinds of vocabulary: words about the world, and words about how to talk.

**Limitations.** Activity is counted only inside this corpus (Jan 2025 – Sep 2026). Someone with 8 comments here may be a long-time member who posted elsewhere or before 2025. The occasional share is also inflated at the edges of the window (25.6% in Jan 2025, 26.3% in Sep 2026), because activity outside the window is unseen.

---

## G. What style of comment sits higher in its own thread?

**What we did.**
- We took employment-related comments in threads with at least 10 comments (cscq all months; r/technology and r/programming up to June 2025).
- We regressed each comment's within-thread score percentile on simple style features: first or second person, a question, numbers, profanity, certainty or hedging words, humour markers ("lol"), a link, length, early arrival, and replying to the post rather than to a comment.
- Standard errors are clustered by thread (`G_style_and_votes/ols_within_thread_percentile.csv`, figure `figures/G_style_coefficients.png`). There are 125,552 cscq comments in 12,868 threads.

**What we saw.**
- **Timing outweighs everything else.** Arriving in the first 20% of a thread raises the percentile by **+0.32** in cscq (+0.26 to +0.29 elsewhere). Every style effect below is 10 times smaller. This is the single most important caution for any claim about "what the community rewards".
- With timing held fixed, the same style pattern appears in all three communities:
  - **Rewarded:** profanity (+0.03 to +0.06), numbers or amounts (+0.02), and slightly longer comments (+0.01 per doubling of length).
  - **Penalised:**
    - questions (−0.04 in cscq);
    - hedging, such as "maybe", "I think" or "probably" (−0.01 to −0.03);
    - humour markers such as "lol" (−0.02 to −0.04);
    - addressing the other person as "you" (−0.04 in r/technology, −0.03 in r/programming);
    - links (−0.05 in cscq, −0.07 in r/programming).
  - **First person "I"** is slightly negative in cscq (−0.02). That seems to conflict with the vocabulary result (experience words are upvoted), but "I" also covers opinion phrases like "I think" and "I feel". Concrete details such as *months, yoe, boss*, together with numbers, are what rise. The pronoun on its own does not.

**What it might mean.** What these communities reward is *blunt, concrete and committed* writing: say it directly, swear if you want, give numbers, don't hedge, don't argue with "you". This fits the Goyal et al. finding that upvoted content follows each community's own norms rather than general politeness. In these three subreddits the shared norm leans toward frank and specific.

**Limitations.**
- These are associations, not causes.
- The features are word lists.
- Within-thread percentile still depends on how many votes a thread gets.
- In cscq a "link" is often self-promotion (see H), which partly explains its penalty.

---

## H. What sources do the communities cite?

**What we did.** We extracted domains and linked subreddits from URLs in employment comments, using January–June 2025 for the comparison across communities (`H_sources/`).

**What we saw.** Links are rare: 2.7% of cscq employment comments, 4.0% in r/programming and 3.1% in r/technology. Where they appear, each community has its own kind of evidence:
- **cscq links labour-market data and career tools.** FRED (fred.stlouisfed.org, 191 comments from 124 different people), the New York Fed, BLS, levels.fyi, USCIS and DOL, plus interview-prep and salary tools.
- **r/programming links research and code.** GitHub, SSRN, MIT Sloan, MDPI, JAMA, the Stack Overflow survey, xkcd.
- **r/technology links news.** YouTube, Wikipedia, NYT, Wired, Business Insider, CNBC, Forbes, NPR, the Washington Post, CNN.
- **Links between subreddits are mostly to related career subreddits.** cscq links to r/csmajors, r/engineeringresumes, r/experienceddevs and r/remotejobseekers. r/technology links to r/antiwork and r/military.

**A data-quality finding.** Some of the most-linked cscq domains are **promotional accounts the bot filter misses**:
- interviews.chat: 292 comments from **3 accounts**, mean score 1.1.
- prachub.com: 55 comments from **1 account**, mean score −0.4.
- salaryscript.com: 64 comments from 2 accounts.

Genuine citations look different. FRED (124 people) and BLS (110 people) come from many different users, with mean scores of +7.8 and +4.9. The team should consider extending `likely_bot` to accounts that repeatedly post the same commercial domain.

**What it might mean.** The three communities have different *evidence cultures*. cscq argues with statistics about the job market, r/programming with studies, and r/technology with journalism. This fits the roles found in the vocabulary analysis: job seekers, craftspeople and news readers.

---

## Things the literature suggests we could still do

From the papers above and the related work found while searching:

1. **Distinctiveness and dynamicity scores** (Zhang et al. 2017) for all three communities in January–June 2025. That would place them on the paper's map: is cscq a "distinctive, dynamic" community?
2. **Emotion over time** with an emotion model trained on Reddit text, such as GoEmotions (Demszky et al. 2020, built from Reddit comments), or a lexicon such as NRC or VADER. A Reddit-trained model fits our data better than a general lexicon; this needs `transformers` installed, or a lexicon download.
3. **Topic modelling with BERTopic** on layoff comments, then topic share by month. This is common in recent Reddit studies; it needs `bertopic` and `sentence-transformers`.
4. **LLM-assisted labelling with human validation** for explanation and stance (Gilardi et al. 2023; Törnberg 2023). A Princeton project, [ECHO](https://echo.cs.princeton.edu), used this kind of LLM-assisted thematic analysis on Reddit discussions of AI and work at a scale of millions of comments. It needs a team decision on sending text to an API.
5. **Compare with work on layoff talk elsewhere:**
   - Twitter reactions to mass dismissals (Bassanini et al., *Industrial Relations*, DOI 10.1111/irel.12386);
   - a planned SSRC study of Reddit posts by laid-off people, tracking emotion before and after a layoff;
   - a 2026 *Frontiers in Psychology* study of 1,454 Reddit narratives about AI job displacement (themes: shattered trust, eroded identity);
   - "AI-washing" commentary, which reports that AI was named in a small share of actual layoff announcements. That gives an outside benchmark for cscq's "AI is an excuse" norm.

Of these, (1) needs no new packages and fits directly on top of E and A. (2) and (3) are the most common methods in recent student and conference Reddit papers.

## Sources
- Zhang, Hamilton, Danescu-Niculescu-Mizil, Jurafsky, Leskovec (2017), [Community Identity and User Engagement in a Multi-Community Landscape](https://arxiv.org/abs/1705.09665), ICWSM.
- Danescu-Niculescu-Mizil, West, Jurafsky, Leskovec, Potts (2013), [No country for old members](https://www.cs.cornell.edu/~cristian/Linguistic_change.html), WWW.
- Goyal, Lambert, Jain, Chandrasekharan, [Uncovering the Internet's Hidden Values](https://arxiv.org/abs/2410.13036), ICWSM.
- [The Language of Approval](https://arxiv.org/abs/2509.10370) (arXiv preprint, 2025).
- Monroe, Colaresi, Quinn (2008), Fightin' Words, *Political Analysis* 16(4).
- [Don't Downsize This! Social reactions to mass dismissals on Twitter](https://acss-dig.psl.eu/blog/social-reactions-to-mass-dismissals) (Bassanini et al., *Industrial Relations*).
- [SSRC project on Reddit posts by laid-off workers](https://www.ssrc.org/?p=18788).
- [Algorithmic anxiety: Reddit narratives of AI job displacement](https://www.frontiersin.org/articles/10.3389/fpsyg.2026.1745164), *Frontiers in Psychology* (2026).
- [ECHO: Extracting Community Insights for Policymaking](https://echo.cs.princeton.edu) (Princeton).
- [Remotive: What's really lying beneath the layoffs](https://remotive.com/blog/whats-really-lying-beneath-the-layoffs/) ("AI washing" commentary).
- [Reddit pipeline with BERTopic and GoEmotions](https://discuss.huggingface.co/t/looking-for-feedback-on-an-nlp-preprint-analyzing-climate-related-reddit-discourse/179347) (example of the method stack).
