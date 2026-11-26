# Stop exploring, answer the team's own question

## Context: why you feel confused

We have run three rounds of exploration (`outputs/09_leads`, `10_language`, `11_dynamics`). Each one found something real. None of them was aimed at a question, so the pile keeps growing and nothing feels finished. That is the source of the confusion. More methods (BERTopic, emotion models) would make it worse.

Your team already has the question. The midterm report is titled **"Solidarity or Blame"** and set three hypotheses:

| | Hypothesis | Midterm status |
|---|---|---|
| H1 | Employment talk is more concentrated in r/cscareerquestions than r/technology | Preliminary support |
| H2 | Career discussion has more worker-centred support and experience; technology discussion has more news and industry framing | Not tested |
| H3 | Solidarity and blame comments get different reply and engagement patterns | Not tested |

Two things follow.

**1. Most of what we found already answers H2 and half of H3.** It was just never filed that way.
- H2: cscq's distinctive words are job-search experience (resume, recruiter, yoe, laid off); r/technology's are politics and news (dei, trump, tariffs). cscq links labour data (FRED, BLS); r/technology links news sites.
- H3, engagement half: in cscq, upvoted comments use first-hand experience words; downvoted ones use immigration words and "cope / delusional / prove it". Blame aimed at executives sits slightly above its thread's average (+0.04 to +0.08). H-1B/offshore comments are more often scored below zero (7.0% vs 4.6%). First-person layoff comments get sympathy replies three times as often (4.8% vs 1.6%).
- A possible answer to the title is forming: **solidarity goes to people who report what happened to them; blame is tolerated when it points up at employers and penalised when it points sideways at other workers.** This is provisional and needs the check in step 3.

**2. The untested half of H3 is your own part.** H3 says "reply patterns", and you own the network. The current Gephi graph is who-replied-to-whom among layoff-keyword comments. It carries no labels, and 97% of its user pairs are a single reply, so it cannot say anything about solidarity or blame. What is missing is labels on the reply links: *what kind of comment gets what kind of reply*. That can be computed from the reply table. It needs no thread reading.

Feasibility is checked: 70,592 employment comments in cscq reply to another comment, and the parent's text is in the database for nearly all of them.

## What to do

### Step 1. New script `scripts/explore_replies.py` → `outputs/12_replies/`
Read-only, like the other three. No existing script is changed.

- **Label each comment** with simple rule-based types. A comment can have more than one.
  - first-person experience (laid off, job search)
  - support / advice
  - blame up (executives, greed, shareholders)
  - blame sideways (H-1B, offshoring, immigrants; "skill issue", "lazy")
  - AI as cause / AI as excuse
  - dismissal ("cope", "delusional")
  - none of these
- **Reuse, don't rewrite:** the marker patterns in `scripts/explore_leads.py` (`exec_blame`, `individual_blame`, `offshore_h1b`, `ai_pretext`, first-person layoff, reply sympathy), `TERMS` and `tokens` in `scripts/explore_language.py`, `ols_cluster` in `scripts/explore_dynamics.py`, and the `connect` / `write` / `boot_ci` helpers.
- **Reply table (the H3 result):** for each parent type × reply type, how often it happens compared with how often that reply type appears anywhere. Example of what it would show: "experience comments get support replies 3× more than chance; blame-sideways comments get dismissal replies 2× more".
- **Same people or different people?** Per author, the share of their comments in each type. Do the people who tell experiences also do the blaming, and do the two groups reply to each other?
- **H2 version:** share of each type in the three communities, January–June 2025 only.
- **Gephi files** (in `outputs/12_replies/gephi/`, so `gephi/` is untouched):
  - a small "type → type" network, about 7 nodes, edge thickness = how much more than chance. This is one slide that explains H3.
  - the cscq author reply network with each user's main type as a colour attribute.
- **Check sheet:** 20 random comments per type plus 40 unlabelled, with an empty `human_label` column. The script reports precision and agreement once the column is filled.

### Step 2. One page: `outputs/04_analysis/FINDINGS_BY_HYPOTHESIS.md`
H1, H2, H3. For each: the two or three strongest results, the figure, the caveat, and what not to claim. Everything else we found (monthly timeline, who adopts new words, style and votes) goes in a short "also found" list at the bottom. This page is what you take to your team.

### Step 3. Your part, about an hour
- Fill in the check sheet. These are single comments with a yes/no answer, not threads. If a teammate fills the same sheet, the team gets the agreement number the midterm promised.
- Open the two Gephi files, colour by type, export the pictures.

### Not doing
BERTopic, emotion models, LLM labelling, any further exploration. They can be listed as future work.

## Things I can't see from here
- **Deadline and final-report requirements.** Nothing in the repo states them. Step 1 and 2 are sized to fit in one session either way.
- **Whether your teammates have seen any of this.** Krish's role is stance labels, so step 1 overlaps with his part. Worth telling him before presenting it as the team's result.
- **Every label so far is mine.** The 200-record sample in `outputs/07_annotations` is still fully unreviewed. Step 3 is the smallest honest fix.

## Verification
- Script runs read-only, prints stage timings and peak memory (target under 3 minutes, under 500 MB).
- Row counts reconcile with the checked figure of 70,592 cscq employment replies to comments.
- Each type's hits are spot-checked in a context file before any ratio is interpreted; a pattern that fails is tightened and the change is recorded, as was done in `LANGUAGE_NOTES.md`.
- Gephi CSVs import with the node and edge counts written in `manifest.json`.
