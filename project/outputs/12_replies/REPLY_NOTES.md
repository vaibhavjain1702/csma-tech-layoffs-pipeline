# What kind of comment gets what kind of reply? (H3, reply half)

*Working notes, 19 November 2026. Script: `scripts/explore_replies.py` (read-only, about 40 s, 655 MB).*

> **Correction, 26 November 2026.** The summary bullet "Talk about executives gets agreement" (under "Expected before running", and result 2 below, "slightly more agreement") is **superseded**. Blame topics (executives, offshoring, AI as an excuse) draw **less support and no extra agreement**. The "agree" reply marker over-fires on replies that start with "This", including hostile ones, so the small excess of "agreement" in the table was an artefact of the marker. Read by the zero-shot stance model, the agreement under blame topics is flat (×0.92–1.19, every confidence interval overlaps the baseline); see `outputs/17_sentiment_stance/SENTIMENT_STANCE_NOTES.md`. The original wording is kept below, marked, so the change is visible. The numbers in the table are unchanged. The sympathy result (own story, ×2.8) is not affected.

## Question and expectation

**Question.** In r/cscareerquestions, does the kind of employment comment someone writes change how other people reply to it?

**Expected before running** (based on outputs 09–11):
- Telling your own layoff story gets sympathy.
- Talk about offshoring or blaming workers gets pushback.
- ~~Talk about executives gets agreement.~~ **Superseded (26 Nov correction above): blame topics draw less support and no extra agreement.**

## Data

- **Window:** all cscq months, **Jan 2025 – Sep 2026**. This is not the Jan–Jun 2025 shared window. Restricted to Jan–Jun 2025 the sympathy result is 4.42% vs 1.93% (×2.29), the same direction as the all-months 5.11% vs 1.82% (×2.82).
- **Comments being replied to:** 134,749 cscq employment comments (bots and authors marked unknown are excluded).
- **Replies:** 91,229 direct replies, excluding self-replies, across 18,817 threads.
- **Baseline:** replies to employment comments that match none of the markers (111,498 comments).
- **Lift:** the share of a reply type under one kind of comment, divided by its share under the baseline.
- **Confidence intervals** resample whole threads, because replies in one thread are not independent.
- **Length check:** the `lift_30_150_words` column repeats each comparison using only comments of 30–150 words.

## Label check before interpreting (this changed the labels)

- The first version had a `blame_sideways` label. About 95% of its matches were mentions of offshoring, H-1B or visas, of any stance. That includes job seekers talking about their own visa. It was split into:
  - `mentions_offshore`, a topic label;
  - `blames_workers` ("skill issue", "lazy", "low performers"), which is noisy.
- `mentions_execs` is a topic label too. Naming a CEO is not the same as blaming one.
- **Only `experience` describes something the writer does** (tells their own story). The others describe what a comment talks about.
- `experience` precision: about 11 of 20 sampled comments really are first-person layoff accounts. The misses are hypotheticals ("if I was worried I'd be laid off") and denials ("I was never laid off"). Noise pulls a lift toward 1, so the true sympathy effect is probably larger than measured.

## Results (`reply_table.csv`, `parent_summary.csv`)

| Kind of comment | n | Sympathy reply | Advice | Agreement | Pushback |
|---|---:|---:|---:|---:|---:|
| baseline (no marker) | 111,498 | 1.8% | 5.8% | 6.9% | 4.9% |
| own layoff story | 2,045 | **5.1% (×2.8)** | ×1.0 | ×1.1 | **×0.6** |
| mentions executives | 4,300 | ×0.8 | **×0.6** | ×1.3 | ×1.2 |
| mentions offshoring/H-1B | 13,466 | ×0.8 | **×0.6** | ×1.05 | ×1.07 |
| "AI is the excuse" | 1,071 | ×0.8 | ×0.6 | ×1.3 | ×1.1 |
| "AI will replace you" | 1,104 | ×0.7 | ×0.8 | ×1.3 | ×1.2 |
| market doom ("cooked") | 1,743 | ×0.9 | **×1.4** | ×1.1 | ×1.1 |

1. **Experience is the only kind of comment that clearly changes the reply.**
   - Sympathy replies are 2.8× baseline (95% CI 3.9–6.4% vs 1.8%).
   - Pushback is lower, at 0.6×.
   - Both effects hold in the length check (×2.7 and ×0.7).
   - Typical exchange: "*Can confirm, I got laid off 1 week before my daughter was born…*" → "*Sorry to hear. That's terrible.*"
2. **The direction of blame barely matters.** Comments about executives, offshoring and "AI as excuse" all look alike:
   - slightly more agreement (×1.05–1.3) *(superseded: this is the "This…" marker artefact; see the 26 Nov correction)*;
   - less sympathy and much less advice (×0.6).
   - These comments switch the thread from helping someone to debating, whoever is being blamed. *(Superseded in part: less support holds, but "agreement" and "debate" are not supported. The stance model's disagreement label is unusable, so do not claim debate either.)*
3. **Doom gets advice.** Comments saying the market is "cooked" get 1.4× more advice replies, often "here is what I'd do". Some of those replies push back ("*Don't listen to this fool…*"), so this label mixes advice with rebuttal.
4. **Offshoring talk draws attention and penalties.** 48.7% of these comments get at least one reply (baseline 42%), and 6.8% are scored below zero (baseline 4.2%). Experience comments get the fewest replies (38.8%) but are the least often scored below zero (1.5%).
5. **Lead to check: arguing with exec-talk gets punished** (`reply_scores.csv`).
   - Pushback replies under comments about executives are scored below zero 14% of the time, against 6.5% for other replies to the same comments (n = 192).
   - The "AI is the excuse" comments show the same pattern (17% vs 8%, n = 52).
   - Both counts are small.

**Revised answer to the title.** On cscq, solidarity comes from what a comment *does*, not whom it blames:
- A personal account gets sympathy and less pushback.
- Explanations of any direction get less care. *(Original wording: "get debate: agreement and argument, not care". The "agreement" part is superseded by the 26 Nov correction.)*

## Same people? (`author_roles.csv`, `author_role_replies.csv`)

Among authors with at least 5 employment comments:
- 2,392 mention offshoring but never share a layoff of their own;
- 306 share a layoff but never mention offshoring;
- 352 do both.

The offshoring group mostly replies to itself: 9,910 replies, the largest cell in the table. The two groups are largely different people.

## Files

| File | What it holds |
|---|---|
| `reply_table.csv` | full table with CIs and the length check |
| `parent_summary.csv` | reply rate, length and score for each kind of comment |
| `reply_scores.csv` | scores of the replies themselves |
| `examples_pairs.csv` | 4 real comment → reply pairs per cell, for the qualitative write-up |
| `check_sheet.csv` | 240 rows (160 comments + 80 replies, 20 per label) with an empty yes/no column, giving label precision and team agreement |
| `gephi/type_nodes.csv`, `gephi/type_edges.csv` | 12-node (8 comment kinds incl. none + 4 reply kinds) "comment kind → reply kind" network, weight = lift |

## Limits

- All labels are keyword rules and have not been validated yet; the check sheet is the fix.
- The results are associations within cscq only, with no causal claim.
- Reply types are coarse: "this" counts as agreement, and "wrong" counts as pushback even inside a sympathetic reply.
