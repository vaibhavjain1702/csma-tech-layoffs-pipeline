# Solidarity or Blame: how Reddit communities discuss disruption in technology employment
*CSE3729 Computational Social Media Analysis, BMU, Semester 7. Final insights, 27 November 2026.*

## Answer in one sentence

In r/cscareerquestions, solidarity follows disclosure, not a shared enemy: people who tell what happened to them get sympathy, while blame topics draw less support and no extra agreement, and who gets blamed comes with the person rather than the community.

## Three core claims

**1. Layoff talk is concentrated in the career community (H1, Supported).**
- Share of non-bot comments that mention layoffs, Jan-Jun 2025: **2.45%** in r/cscareerquestions (cscq), **0.20%** in r/technology, **0.32%** in r/programming.
- Inside threads that mention layoffs: 4.06% vs 0.49% (cscq vs r/technology). 67% of large cscq threads contain layoff talk, against 21% in r/technology.
- Weekly variability (CV) is 0.21 / 0.45 / 0.76 (cscq / r/technology / r/programming): layoffs are ambient in cscq and event-driven in r/technology.
- The midterm comparison (Jan-May 2025) gave 2.32% vs 0.20%, 11.36x.
- The hiring screen's ratio is unreliable (precision about 22%) and is not quoted.

**2. The communities frame disruption differently, and part of the gap follows the person (H2, Supported, then narrowed).**
- Own layoff stories: **8.9%** (cscq) vs **3.1%** (r/technology). cscq links labour statistics (FRED, BLS); r/technology links news; r/programming talks craft.
- D1: for the same ~152-160 authors who write in both communities, executive mentions are 6.6% vs 5.8% (the gap disappears), while AI talk still differs by +9.4 points. Who gets blamed comes with the person; topics are shaped by the community.

**3. Sympathy follows disclosure, not blame (H3, Supported).**
- Replies to personal layoff stories contain sympathy in **5.11%** of cases vs **1.82%** for unmarked comments (x2.82). This covers all cscq months, Jan 2025 - Sep 2026: 91,229 reply pairs on 134,749 employment comments. Jan-Jun 2025 alone gives 4.42% vs 1.93% (x2.29).
- Advice does not rise for stories; doom draws advice (x1.38). Blame topics (executives, offshoring, AI-as-excuse) draw less sympathy (x0.77-0.81) and no extra agreement (stance model x0.92-1.19). The effect holds within a length band and with thread-clustered confidence intervals.
- Network view (cscq reply graph, Jan-Jun 2025; largest connected component 30,976 authors, 162,024 replies): blame-talkers reply to each other 1.69x more than chance (z = 8, within-thread null) with more challenge (7.2% vs 4.5%) but not more agreement, consistent with an antagonistic echo chamber. Position follows activity, not role; the top 1% of users receive 17.8% of replies.

**Other results.**
- Newcomers who get any reply come back more often, 50% vs 39% (a lead, not causal).
- After the H-1B announcement (19 Sep 2025), offshoring talk rose from about 13% to 43% for one week, then fell below its earlier level: a shock, not a shift.
- "AI as an excuse" did not grow; that was a denominator effect. Sentiment is not stance: sentiment separates story comments from blame comments only at 0.50, which is chance.

## What we can claim

- Describe, for three subreddits and comments only, how often and how employment disruption is discussed and how replies respond, in the collected corpus (2,974,250 records; 115,213 posts, 2,859,037 comments).
- State that the results are Supported by the keyword-rule labels and are robust to the bot denominator, shared window, thread clustering, length bands, label-noise simulation, activity thresholds and megathread removal.
- Compare communities only in the shared window (Jan-Jun 2025); describe time trends in cscq only.

## What we cannot claim

- No causal claims and no population claims: three subreddits, comments only, Jan 2025 - Sep 2026. Not representative of technology workers; not cross-platform.
- Coverage is uneven (cscq to 23 Sep 2026 with 0 posts; r/technology comments to 9 Jun 2025; r/programming to 12 Dec 2025). This is a collection-run artefact (see collection/PROVENANCE.md), so prevalence and complete coverage cannot be claimed.
- We do not claim that blame topics draw agreement: the agree marker over-fires on replies that start with "This". We claim only less support and no extra agreement.
- Polarisation is not measurable now. Topic is not stance; the AI/work, hiring and career-transition screens are weak (see below).

## Validity status

- **The human label check has not been completed.** The labels are keyword rules, and their precision is provisional (one reader). A human check with two independent coders is prepared (docs/HUMAN_CHECK_GUIDE.md, 240 rows) but pending. Until it is done, results are "Supported", not "Findings", and no inter-coder agreement is reported.
- Provisional precision (one reader): layoffs screen 95%; restructuring 75%; economic policy 70%; AI/work 26.7%; hiring 22.5%; career transition 15%. Experience marker 39/40 on layoff comments (about 11/20 overall); ai_replaces only 7/30 endorse; offshore only 7/70 blame foreign workers; the agree marker over-fires.

## Next steps

1. Run the human check (240 rows, two coders working alone), then score it with scripts/score_human_check.py. Only then upgrade labels from "Supported" to "Findings" or revise them.
2. Join validated stance labels to the reply networks to test the reply-structure part of H3 with human labels.
3. Replace or retire the weak screens (hiring, AI/work, career transition); date the second offshoring spike (mid-Dec 2025).
4. Add topic modelling and external labour indicators only if a hypothesis needs them. The team decided not to collect more data.
