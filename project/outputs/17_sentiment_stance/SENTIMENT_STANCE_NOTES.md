# Sentiment and zero-shot stance: an extra signal

*Working notes, 26 November 2026.*

**Scripts.** Both only read the database.
- `scripts/score_text_models.py` runs the models once on the GPU and caches the scores in `data/processed/model_scores.sqlite`, which is git-ignored. It took 41 minutes.
- `scripts/explore_sentiment_stance.py` reads that cache and writes the tables here. It takes about 40 seconds.

**Status.** These are off-the-shelf models that have **not been trained or checked on our data**. We deliberately did not label anything for this. The results are therefore an *extra signal*: **every result here is at most a Lead.** The models ran locally, so no comment text left the machine.

## What was run

**Models.**

| Model | What it does |
|---|---|
| **VADER** | A sentiment word list with social-media rules |
| **RoBERTa sentiment** (`cardiffnlp/twitter-roberta-base-sentiment-latest`) | Negative / neutral / positive, trained on tweets |
| **DeBERTa zero-shot** (`MoritzLaurer/deberta-v3-base-zeroshot-v2.0`) | For a text and a written statement ("The author blames company executives…"), gives the probability that the text implies the statement |

**Where.** Everything is Jan–Jun 2025, human comments only:
- **sentiment:** every cscq comment (274,850), plus employment comments in r/technology and r/programming (300,946 texts in total);
- **blame stance:** employment comments in all three communities (67,122);
- **reply stance:** cscq replies paired with their parent comment (162,722; this is the R4 edge set).

**Fixed in advance.**
- The statements the model was asked about, which are listed in the script and in the cache's `meta` table.
- The cut-off: a model label counts as positive when its probability is above 0.5. This was never tuned.
- The author types come from rebuilding R4 exactly: the same 30,976 authors and the same type counts.

## Which model labels can be used

I judged this from reading examples in `examples.txt` and from agreement with the codes in `09_leads/manual/`. Those codes are also provisional: I made them, and no person has checked them yet.

| Model label | Verdict | Evidence |
|---|---|---|
| Sentiment (both tools) | Usable, but describes tone only | The two tools agree only moderately (r = 0.44). RoBERTa calls 26% of comments negative where VADER does not |
| `blames_execs` | **Usable** | Hits read as real blame. It also catches blame aimed at "management" and "leadership", which the topic marker misses |
| `ai_is_excuse` | **Usable** | Against the provisional codes: precision 0.90, recall 0.60 |
| `blames_offshore` | **Not usable** | Against the provisional codes: recall 0.14. It also labels the pushback "they want you to blame immigrants" as blame |
| `own_job_loss` | Usable on story-marker hits only | 0.97 against the codes, but only about 3 of 12 of its extra finds were the author's own job loss |
| Reply `agrees` | **Usable** | 82% on agree-marker replies that don't start with "This"; the examples read as agreement |
| Reply `disagrees` | **Not usable** | It fires on 62% of all replies, and the examples are mostly neutral continuations or advice |
| Reply `sympathy` | Usable, as a broader reading than the marker | It is stricter than the marker on some replies (11% of marker hits) and broader on others |

The blame stance model is **conservative**. Only 8% of comments that mention executives are read as blaming them, so blame-stance rates are low by construction. **Compare them between groups, not as absolute levels.**

## Results

### S1. Sentiment cannot tell a story from blame (layer 7)
1. **Say it.** In cscq, RoBERTa reads 55% of own-story comments as negative, the same as comments mentioning executives (55%) or offshoring (55%). One statistic sums it up: how often a random story comment is more negative than a random blame-topic comment. For RoBERTa that is 0.50 and for VADER 0.52, where 0.5 means pure chance.
2. **Expected.** Yes. This is the reason the project does not use sentiment as its main measure.
3. **Rival.** cscq is simply less negative overall: 45% negative vs 62% in r/technology. Within r/technology the story vs blame comparison is 0.63 for RoBERTa, where stories read as somewhat more negative, and 0.50 for VADER. So even at best, sentiment separates the two only weakly.
4. **Concept.** Construct splitting: tone is not stance. **A sentiment score would merge solidarity and blame into one "negative" pile.**

### S2. Negativity does not explain the sympathy story comments get (R3 rival)
1. **Say it.**
   - With the sympathy marker, story comments get 2.35× the sympathy of unmarked comments. Comparing only parents of the same sentiment (negative with negative, and so on), the lift is 2.33×: unchanged.
   - Story parents are hardly more negative than unmarked ones (53% vs 48%).
   - The model's broader sympathy reading gives a larger lift: 16.1% vs 2.3% of replies, ×6.9, and ×6.7 within the same sentiment.
2. **Expected.** We were worried that negativity, not telling your story, drives sympathy. **That rival is ruled out.**
3. **Check.** Inside the negative band alone it is 5.5% vs 1.6% with the marker, and 20.6% vs 2.8% with the model.
4. **Caveat.** This window has only 416 replies to story comments, so the CIs are wide (marker 2.7–6.8%). The headline R3 figure (×2.82) covers all cscq months.
5. **Concept.** Emotional support follows disclosure, not tone. **This strengthens R3.**

### S3. Blame-talkers are more negative with each other (R4 N3, the "affective" part)
1. **Say it.**
   - Replies from one blame-talker to another are negative 50.1% of the time (CI 47.4–52.8), against 39.7% between other typed authors.
   - The model reads them as agreement 22% of the time vs 20%: not much more.
2. **Rival: their parents are just more negative.** Within each band of parent sentiment, the gap stays at 7–14 points:

   | Parent sentiment | Blame → blame | Other → other |
   |---|---:|---:|
   | Negative | 54.2% | 47.2% |
   | Neutral | 45.0% | 34.1% |
   | Positive | 46.7% (only 107 replies) | 32.5% |

3. **Rival: blame-talkers are negative with everyone.** Partly true. Their replies to other types are negative 45.5% of the time and other types' replies to them 43.7%; both are above 39.7% but below 50.1%. So the most negative cell is inside the group.
4. **Not done.** There is no within-thread null for tone. The structural result (lift 1.69, z = 8) is in N3.
5. **Concept.** This adds a **tone** signal to N3. **The group's exchanges are more negative and no more agreeing: consistent with an affective (antagonistic) echo chamber.** It is still not stance-based, because the types are built from topics.

### T1. Topic markers vs stance (layer 3)
- **Topic is not blame, again.**
  - 7.9% of comments that mention executives are read as blaming them.
  - 5.3% of offshoring mentions are read as blaming offshoring, but that model label is not usable.
  - 29.6% of AI-excuse marker hits are read as saying AI is an excuse.
- **The markers miss some blame.**
  - 60% of the model's "blames executives" comments contain no executives marker. They blame "management", "leadership" or "the billionaire class".
  - For AI as an excuse, the figure is 82%. But the model fires on only 1.4% of all comments, so in absolute terms this is small.
- **Recall of the story marker: no conclusion.** The model's extra finds are mostly *other people's* layoffs, so it can't show how many stories the marker misses. That still needs the human check sheet.

### T2. Blame stance by community, and within the same authors (R2, D1)
- **Across all authors**, r/technology blames more than cscq.

  | Model label | cscq | r/technology |
  |---|---:|---:|
  | Blames executives | 0.7% | 1.6% |
  | Blames AI | 0.9% | 3.8% |
  | AI is an excuse | 0.85% | 2.2% |

- **Within the same 152 authors.** These have at least 2 employment comments in each community: D1's rule, giving 152 rather than D1's 160 because career-transition comments are excluded here.
  - The gaps shrink, and every CI includes zero: executives 1.1% vs 1.9%, AI 1.7% vs 2.4%, AI as an excuse 2.6% vs 2.8%.
  - The one CI that excludes zero is offshoring (0.4% vs 2.1%), and that model label is not usable.
- **This fits D1 and sharpens it.** D1 found that the gap in *talk about* executives disappears within the same people, while the gap in *talk about* AI remains. With stance, the gap in *blaming* AI also disappears within the same people.
- **Concept.** Blame travels with the person (selection). How much AI is *discussed* depends on the community.
- **Caveat.** The rates are tiny and the model is conservative. The cross-posters are a special group, and they blame more than average in cscq too (1.1% vs 0.7%).

### T3. Reply stance (R3 and the agree marker)
- **The agree marker is half wrong.**
  - Agree-marker replies that start with "This" are read as agreement only 30% of the time.
  - The other agree-marker replies are read as agreement 82% of the time.
  - About half of all agree-marker hits start with "This" (4,597 of 9,219).
- **"Blame draws agreement" does not survive.**
  - With the marker, blame-topic parents get 1.0–1.5× the agreement of unmarked comments.
  - With the model, the lift is **0.92–1.19, and every CI overlaps the baseline** (22.5%).
  - Blame topics get **less sympathy** (×0.5–0.6) and **no extra agreement**. Story comments get *less* agreement (×0.81) and much more sympathy.
- **Polarisation check: not enough data.** We asked whether repliers who blame the same target disagree less. There are only 9–40 cases per target, and the disagreement label is not usable anyway. **Polarisation stays unmeasurable.**

## What this changes in the project

| Where | Change |
|---|---|
| R3 | **Stronger:** the story → sympathy effect survives sentiment control (S2). **Wording:** drop "blame draws agreement". Say blame topics draw *less support and no extra agreement* (T3). "Debate" is also not shown by the model, because its disagreement label is unusable |
| R4 N3 | **Adds tone:** blame-talker exchanges are more negative even at equal parent sentiment (S3) |
| R2 / D1 | **Sharpens it:** blame *stance* travels with the person; AI *talk* is shaped by the community (T2) |
| Layer 3 | The agree marker is confirmed half wrong. The executives marker misses blame phrased as "management" or "leadership" |
| Layer 7 | "Sentiment is not stance" now has a number: a story-vs-blame score of 0.50 (S1). Polarisation is still not measurable |

## Limits
- **No model was checked by a person on our data.** The verdicts on which labels are usable come from my reading of examples and from codes I made myself.
- **The thresholds are fixed, not calibrated.** The models were not trained on Reddit employment talk; the sentiment model was trained on tweets.
- **Only Jan–Jun 2025**, so R3's numbers here (×2.35) are smaller samples than the headline figure, which uses all months.
- **The new packages are not in the pinned project requirements.** torch 2.15 (CUDA), transformers 5.24, vaderSentiment and sentencepiece were added to `.venv-eda`.
- **Model downloads need `HF_HUB_OFFLINE=1`.** On this network Hugging Face's online update checks fail with SSL errors, so set that variable once the models are cached.

## Summary for the report
A sentiment score cannot separate people telling their own layoff story from people blaming someone: both are equally negative. Stories still draw several times more sympathy than other comments, even compared with comments of the same tone, so solidarity follows disclosure rather than negativity. A zero-shot stance model finds no extra agreement for blame. Replies between blame-talkers are more negative than other replies at equal parent tone, and blame of AI, like blame of executives, stays the same when the same people post in different communities. These are model readings that no person has checked on our data, so they are Leads.
