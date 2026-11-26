# Human label check: guide for coders

*CSE3729 Computational Social Media Analysis (BMU). "Solidarity or Blame: how Reddit communities discuss disruption in technology employment". Written 26 Nov 2026 for the 27 Nov presentation.*

## 1. What the task is, and why it matters

Every comment and reply type in our results is a keyword rule (a regex). The comment rules are in `scripts/explore_leads.py` (dict `M`), and `scripts/explore_replies.py` maps them to labels (dicts `PARENT` and `REPLY`). A rule always gives the same answer for the same text, so it is perfectly *consistent*. That does not make it *correct*.

This check measures two things.

1. **Precision of each rule.** Of the 20 comments a rule flagged, how many really are what the label says? Precision = yes / (yes + no), with a 95% confidence interval.
2. **Agreement between two independent coders** (percent agreement and Cohen's kappa). This shows that the yes/no judgement itself is reliable, not one person's opinion.

Together they answer the question every audience asks: **"can you trust the number?"** Under `docs/INTERPRETATION_ROUTINE.md`, nothing can be called a **Finding** until a human has checked the labels. Every precision figure so far is "Claude-provisional". This check replaces them.

**What is being checked.** `outputs/12_replies/check_sheet.csv` holds 240 rows, in fixed blocks of 20 per label. The rows were drawn at random (seed 20261119) from r/cscareerquestions employment comments, and from the direct replies to them, by `scripts/explore_replies.py`, step 8.

| rows | unit | label | rows | unit | label |
|---|---|---|---|---|---|
| 1–20 | comment | `experience` | 121–140 | comment | `doom` |
| 21–40 | comment | `mentions_execs` | 141–160 | comment | `none` |
| 41–60 | comment | `mentions_offshore` | 161–180 | reply | `sympathy` |
| 61–80 | comment | `blames_workers` | 181–200 | reply | `advice` |
| 81–100 | comment | `ai_excuse` | 201–220 | reply | `agree` |
| 101–120 | comment | `ai_replaces` | 221–240 | reply | `challenge` |

## 2. Who does what

**Recommended: 2 coders.** Coders A and B each code **all 240 rows** on their own. That takes about 60–90 minutes each, or 15–20 seconds a row; replies are short.

**Alternative: 4 coders.** Every row is coded by exactly 2 people, and each label stays within one pair, so every label gets its own kappa.

| Coder | File | Rows to code | Labels |
|---|---|---|---|
| A | `annotations/human_check/check_sheet_coder_A.xlsx` | **1–120** | experience, mentions_execs, mentions_offshore, blames_workers, ai_excuse, ai_replaces |
| B | `annotations/human_check/check_sheet_coder_B.xlsx` | **1–120** | the same |
| C | `annotations/human_check/check_sheet_coder_C.xlsx` | **121–240** | doom, none, sympathy, advice, agree, challenge |
| D | `annotations/human_check/check_sheet_coder_D.xlsx` | **121–240** | the same |

In the 4-coder split, leave the other half blank. A blank cell means "not coded", and the scorer handles it.
- Rows 1–120 are longer comments and include the optional `blamed_target` column, so they take A and B longer: about 40–50 minutes, against 30–40 for C and D.
- If A and B are short of time, they can skip `blamed_target`.

**Files.**
- Each coder has an Excel workbook with two sheets:
  - `Instructions`: a short version of section 5;
  - `Coding`: one row per text, with dropdowns.
- Each workbook has a CSV twin, `check_sheet_coder_X.csv`, with the same columns, for anyone without Excel. Fill **either** the xlsx **or** the csv, not both. The scorer uses whichever one is filled; if both are, it uses the xlsx and warns.
- Google Sheets or LibreOffice: upload or open the xlsx and fill it there. Then download it back as `.xlsx` under the **same file name**, or as `.csv` under the CSV twin's name.

**Columns in `Coding`.** Fill only the three columns marked "fill".

| column | what it is |
|---|---|
| `row_id` | 1–240. Stable; it follows the order of `check_sheet.csv` |
| `unit` | `comment` or `reply` |
| `machine_label` | the label the rule gave this text |
| `label_meaning` | the one-line yes/no rule for that label |
| `text` | the text, with what the rule matched (see below) |
| `label_correct` | **fill**: `yes`, `no` or `unsure` |
| `blamed_target` | **fill**, only on the 4 blame-topic labels (yellow cells): `yes` or `no`. Grey cells are pre-filled `na`; leave them |
| `notes` | **fill when useful**: a short reason, especially for `no`, `unsure` and `none`=`no` |
| `id` | the Reddit comment id |

**How the `text` cell differs from `check_sheet.csv`.** The original text is cut at 500 characters for comments and 400 for replies. To help you judge, two things were added at the end of the cell:
- **`[rule fired on: «…»]`** shows the exact words the rule matched, so you know what to look at.
- **`[TEXT CUT AT … CHARACTERS. The rule fired further on …] …excerpt…`** appears on the **42 rows** where the matched words were in the hidden part of the comment: rows 3, 11, 31, 33, 35, 36, 59, 61, 66, 72, 74, 76, 80, 84, 87, 95, 96, 99, 100, 104–107, 110, 116, 118, 119, 123, 133, 135, 165–168, 177, 181–184, 193, 236, 239. The excerpt is about 220 characters either side of the match, taken from the full comment in the database (read-only).

Before building the files, each of the 240 full texts was re-run through the real rules:
- every row reproduces its label;
- none of the 20 `none` rows matches any of the seven comment rules.

## 3. Independence

1. **Code alone.** Do not discuss rows, compare answers, or look at another coder's file until **every** coder has finished. Agreement only means something if the judgements are independent.
2. Read sections 4 and 5 first. Questions about a *rule* (not a specific row) go to the whole team, and the answer is added to this guide for everyone.
3. Then run the scorer (section 7). It lists the rows where the coders disagree.
4. **Adjudicate together.**
   - Discuss each listed row and agree one final answer.
   - Write the final answers to `annotations/human_check/adjudicated.csv`, with columns `row_id,final_label_correct` and optionally `final_blamed_target`. Include only the rows you decided.
   - Rerun the scorer.
   - **Never change your own coding file after you have seen the other coder's answers.** Kappa must be computed from the independent answers, and adjudication goes only in `adjudicated.csv`.

## 4. The one question per row

> **Does the machine label correctly describe this text, under that label's rule in section 5?**

- **Judge only the label in `machine_label`.** A comment can deserve other labels too; ignore them. The rule fired anyway, so you are checking whether that firing was right.
- **`yes`**: the text really is what the label says, under the rule.
- **`no`**: the rule fired by mistake (a false positive).
- **`unsure`**: use it only when the text truly does not let you decide. For example:
  - the relevant part is cut off and the excerpt does not settle it;
  - sarcasm you cannot read;
  - a reply whose meaning depends entirely on the parent comment you cannot see.

  Write the reason in `notes`. Aim for fewer than 1 row in 10. `unsure` is **not** for hard calls: apply the rule and choose. Unsure rows are left out of precision and counted separately, so overusing it shrinks n and widens the intervals.
- **Judge the author's own words.** Quoted lines starting with `>` were already removed, but inline quotes remain.

**Three families of labels.** This is the key to answering consistently.

| Family | Labels | `yes` when | Quoting, negation, hypotheticals, sarcasm |
|---|---|---|---|
| **Act / claim** | `experience`, `ai_replaces`, `doom`, and the 4 reply labels | the author actually **does or asserts** it | → **no** |
| **Topic** | `mentions_execs`, `mentions_offshore`, `ai_excuse`, `blames_workers` | the matched word is used **in its intended employment sense**, whatever the stance | → still **yes**: stance goes in `blamed_target` |
| **Baseline** | `none` | the text contains **none** of the seven comment types | — |

Topic is not stance. "It's not the CEOs' fault" is about executives, so `mentions_execs` = yes and `blamed_target` = no.

## 5. YES/NO rules for all 12 labels

Each rule lists:
- what the regex matches;
- **YES** and **NO**, where NO covers the false positives the regex is known or likely to catch;
- the "fired on" tally from the 20 sampled rows, which shows where the risk is.

### Comment labels

#### `experience` (rows 1–20). Act: telling your own job-loss story
- **Regex.** One of "I was / I got / I've been / I have been / I'm being / I am being / I just got / we were / we got / my (whole) team was/got", followed within 30 characters (no `.`, `!` or `?` in between) by "laid off / let go / RIF'd / riffed / cut". Also "laid me off", "let me go", and "since I/my (was/got) laid off/layoff".
- **Fired on (20 rows):**
  - "I got laid off" 8, "I was laid off" 6, and 1 each of "since I was laid off", "I just got laid off", "I've been laid off" and "my team was let go";
  - also **"I was never laid off"** 1 and **"I was worried I was close to being laid off"** 1.
- **YES.** The author says a layoff or job loss **actually happened** to them or to their own team. All of these count:
  - an old layoff;
  - a single passing line inside a question or advice request ("I got laid off in May, which certs should I get?");
  - being let go or fired for performance;
  - being formally told that their layoff is coming.
- **NO.**
  - Hypothetical: "if I got laid off tomorrow".
  - Feared or "almost": "I was worried I'd be let go", "I was close to being laid off".
  - Denied: "I was never laid off".
  - A pay, hours or budget cut: "I got a pay cut", "we were told budgets would be cut".
  - "let me go ahead and…", or "cut" in another sense.
  - Someone else's layoff.
  - The author did the laying off: "I was the one who laid off people".
  - A joke.

#### `mentions_execs` (rows 21–40). Topic: company leadership and capital
- **Regex.** greed, greedy (any "greed…"), shareholder(s), stock price, stock buyback(s), buyback(s), executive(s), execs, C-suite, CEO(s), Wall Street, investor(s).
- **Fired on:** CEO/CEOs 7, C-suite 3, executive 2, execs 2, investor(s) 2, shareholder(s) 2, Wall Street 1, greedy 1.
- **YES.** The word really refers to company leadership or capital (executives, CEOs, C-suite, shareholders, investors, Wall Street, stock price or buybacks) or to corporate greed. **Stance does not matter.** All of these are yes:
  - neutral: "my CEO announced RTO";
  - defending: "execs had no choice";
  - quoting: "the CEO said AI…";
  - denying blame: "it's not the CEOs' fault".
- **NO.** The word has another meaning:
  - "executive order" (common around the Sept 2025 H-1B proclamation), "executive function", "executive summary";
  - "greedy algorithm", or "greedy" aimed at workers, landlords or recruiters rather than companies or capital;
  - "investor" or "stock price" about the **author's own personal investing** ("I'm an investor in index funds").

#### `mentions_offshore` (rows 41–60). Topic: offshoring, outsourcing, H-1B, visas
- **Regex.** offshor… (offshore, offshoring, offshored), outsourc… (outsource, outsourcing, outsourced), H1B / H-1B / H1-B (and plurals), visa(s).
- **Fired on:** offshoring/offshore/offshores 10, H1B(s) 6, outsource/outsourced/outsourcing 4.
- **YES.** The text really talks about offshoring or outsourcing **jobs**, the H-1B programme, or work visas and immigration for jobs. Stance does not matter. **The author's own visa situation counts** ("I'm on OPT and need sponsorship"). That is the topic, even with no blame.
- **NO.**
  - Visa the company ("I interviewed at Visa").
  - A tourist or travel visa unrelated to work.
  - "Outsourcing" to AI or tools ("they outsourced it to AI", "outsourcing your thinking to ChatGPT").
  - Outsourcing of non-job tasks.

#### `blames_workers` (rows 61–80). Topic: workers' skill, effort or performance
- **Regex.** low performer(s), skill issue, not good enough, unqualified, lazy, deadweight, underperform… (underperformer, underperforming, underperformed), git gud.
- **Fired on:** **lazy 9**, low performers 4, unqualified 3, not good enough 2, skill issue 1, underperformed 1.
- **Read this first.** The label's *name* says "blames", but this column measures the **topic**: does the text talk about workers' or job seekers' skill, effort or performance? Actual blame is the optional `blamed_target` question. Because of that, this column will overstate what the name claims; say so whenever you report it.
- **YES.** The trigger describes the skill, effort, performance or qualifications of workers or job seekers. All of these count:
  - blaming: "only the low performers got cut";
  - reporting management's label: "they called us low performers";
  - rejecting the blame: "it's not a skill issue, the market is broken";
  - self-talk: "I feel like I'm not good enough".
- **NO.**
  - Code, tools or products: "lazy loading", "lazy evaluation", "this IDE is lazy".
  - AI: "AI is not good enough to replace us".
  - Pay or offers: "the pay is not good enough".
  - Stocks: "the stock underperformed".
  - "unqualified success".
  - Aimed at employers, recruiters, managers or executives: "lazy recruiters", "an unqualified CEO". That is not blaming *workers*.

#### `ai_excuse` (rows 81–100). Topic: AI as an excuse or cover for cuts
- **Regex.** Two groups.
  - **(a) No mention of AI is needed:** excuse, scapegoat…, pretext, smokescreen, "cover story", "cover for", "AI washing".
  - **(b) Must mention AI:** "blame(d) (it) on (the) AI"; "not / isn't / wasn't / aren't / weren't (really) because of / due to / about / caused by / replaced by AI"; "using AI as an excuse/cover/reason/justification"; "AI is (just) the/an excuse/cover".
- **Fired on:** **bare "excuse" 13**, scapegoating 2, AI washing 2, pretext 1, "using AI as an excuse" 1, "cover for" 1.
- **YES.** The text deals with AI being an excuse, cover or pretext for layoffs or hiring cuts, or it disputes whether AI is really the cause of job cuts ("these layoffs aren't really because of AI"). **Stance does not matter**: "people say AI is just the excuse, but it really is replacing us" is still yes.
- **NO.** "excuse", "cover for", "scapegoat" and the like used **without AI being the thing in question**:
  - "excuse me", "there's no excuse for this", "I'll cover for you";
  - "H-1Bs are a scapegoat";
  - "they used the economy as an excuse" (no AI);
  - "AI is no excuse for bad code" (not about job cuts);
  - "this thread is not about AI".

#### `ai_replaces` (rows 101–120). Claim: AI will replace jobs
- **Regex.**
  - "AI / LLM(s) / **it** / agent(s)" + "will / is going to / are going to / gonna" + (soon) + "replace / take / eliminate / automate / wipe out / make … obsolete";
  - "jobs will be/are gone/obsolete/dead";
  - "adapt or die / adapt or get left";
  - "get/be/being left behind";
  - "you'll/you will be replaced";
  - "replaced by someone/people who/using".
- **Fired on:** **"it will take" 7**, "AI will replace" 5, "AI will take" 2, "AI is going to take/wipe out" 2, "it will replace" 1, "get/be left behind" 2, "jobs will be gone" 1.
- **What does and doesn't fire.** Literal "AI will **not** replace" does *not* fire, because "not" breaks the phrase. The rejections it catches come wrapped around the phrase:
  - "I don't think AI will replace us";
  - "Do you think AI will replace us?";
  - "CEOs claim AI will replace devs, which is nonsense".

  Earlier provisional reading: only 7 of 30 such hits endorse the claim.
- **YES.** The **author themselves asserts** that AI, automation or LLMs will replace, eliminate or take jobs or workers. All of these count:
  - only some jobs: "AI will replace most junior roles";
  - hedged but asserted: "AI will probably take a lot of these jobs";
  - workers who don't adapt to AI being left behind or replaced: "you'll be replaced by someone using AI".
- **NO.**
  - **"it will take [time / years / a while]"** where "it" is not AI (check what "it" refers to).
  - Doubt or denial: "I don't think AI will replace…".
  - A question.
  - Someone else's view reported or quoted without the author endorsing it.
  - A joke or sarcasm.
  - "left behind" not about AI and work.
  - "jobs are gone" because of offshoring or the economy, not AI.

#### `doom` (rows 121–140). Claim: the job market is bad
- **Regex.** "market is (really) bad / terrible / brutal / awful / cooked / rough / trash", "it (really) is that bad", "not lying", "in denial", "denial", "stop coping / stop pretending", "cooked", "bloodbath", "tech depression".
- **Fired on:** **cooked 6**, "market is bad / really bad" 5, "market is brutal" 3, "market is terrible" 2, "in denial" 2, **"denial" 1**, "market is rough" 1.
- **YES.** The author asserts that the **tech job market or job prospects are bad**. This covers mild wording ("the market is rough right now, but…") up to "we're cooked", "bloodbath" or "tech depression". It also covers:
  - the author's **own** prospects: "I'm cooked, 8 months unemployed";
  - "people are in denial about how bad it is".
- **NO.**
  - Cooking food.
  - "I'm cooked" about an exam or a game.
  - The housing or stock market.
  - "denial" of a claim, visa, insurance or service.
  - "in denial" or "not lying" about something unrelated.
  - Disputing doom ("people say the market is bad, but I got 3 offers").
  - Quoting doom in order to reject it.

#### `none` (rows 141–160). Baseline purity
- **Rule.** These comments matched **none** of the seven comment rules anywhere in the full text (re-checked). They are the baseline that every "lift" is compared against.
- **YES.** The text really contains **none** of the seven types, in **any wording**:
  1. the author's own job loss;
  2. executives, upper management, shareholders, investors or corporate greed;
  3. offshoring, outsourcing jobs, H-1B or work visas;
  4. workers or job seekers **described as** lazy, unskilled, unqualified, low performers or not good enough. Ordinary talk about skills, experience, studying or learning a language does **not** count;
  5. AI as an excuse or cover for cuts, or whether AI is really the cause;
  6. a claim that AI will replace jobs;
  7. a claim that the job market is bad.
- **NO.** At least one type is present in words the rules missed. Write which one in `notes`. Examples:
  - "I was fired in March", "got laid off last month" (no "I was / I got");
  - "upper management", "leadership", "the owners". A direct line manager, or a bare "the company", does **not** count;
  - "the job market is horrible";
  - "companies are moving jobs to India".
- Judge only the text shown. If the comment is cut off, do not guess what the rest says.

### Reply labels

**Replies come without the comment they answer.** Judge from the reply's own words. Use `unsure` only when the reply means nothing without its parent.

#### `sympathy` (rows 161–180). Emotional support
- **Regex.** sorry, good luck, best of luck, hang in, rooting for, feel for you, that sucks, you got this, wishing you, congrat…, glad you, hugs.
- **Fired on:** **sorry 12**, good luck 5, best of luck 1, glad you 1, that sucks 1.
- **YES.** The reply offers genuine emotional support to the person: sympathy, comfort, encouragement, well-wishes, or **sincere congratulations**. It still counts if the rest of the reply is advice or even disagreement ("Sorry you went through that. Still, H-1B isn't the cause").
- **NO.**
  - "Sorry, but…" that only softens a disagreement or correction.
  - "Sorry for my English" or "sorry for the long post".
  - Sarcastic or dismissive "good luck with that attitude".
  - "Glad you asked".
  - "congrats, you played yourself".

#### `advice` (rows 181–200). Informational support
- **Regex.** you should, you need to, I'd / I would recommend/suggest, try to / try applying / try reaching / try looking, have you tried/considered, my advice, focus on, reach out, update your resume, tailor, apply to/for/anyway, network/networking.
- **Fired on:** network(ing) 6, apply to/for 5, you should 4, try to 2, focus on 2, you need to 1.
- **YES.** The reply recommends something the person could do: an imperative tip, "you should…", "I'd recommend…", "focus on…", "what worked for me was networking". Blunt advice counts too.
  - A question that **proposes a concrete action** counts: "Have you tried contract roles?"
- **NO.**
  - **A pure information question**: "What did you apply to?", "Do you need to relocate?". Replies that only ask questions are a known false positive for this rule.
  - A description of what someone else does: "companies focus on profit", "the same rules apply to everyone", "recruiters reach out to me".
  - The replier describing themselves without recommending it: "I try to stay positive".
  - Computer or neural "network".
  - A put-down phrased as advice: "you should be ashamed", "you need to learn to read".

#### `agree` (rows 201–220). Agreement
- **Regex.**
  - The reply's **very first word** (after any punctuation) is: this, exactly, agree(d), so true, same, yep, yup, facts, well said, preach, truth.
  - Or anywhere in the reply: "I (completely/totally/fully) agree", "spot on", "couldn't agree more", "this is (so) true/right".
- **Fired on:** **first word "This" 12**, "I (totally) agree" 3, agreed/agree 2, spot on 1, exactly 1, yup 1.
- **Known problem.** The rule fires on **any reply starting with "This"**, including hostile ones. The stance model read only 30% of those as agreement.
- **YES.** The reply's **main stance** is agreement with the comment it answers: "This.", "This 100%", "Exactly", "Spot on", "I agree, and…". It also covers "Same here, happened to me too", where the replier shares the parent's experience or view.
- **NO.**
  - Starts with "This" but disagrees or attacks: "This is not true", "This is the dumbest take here", "This is why nobody hires you".
  - Starts with "Truth" or "Same" in another sense: "Truth is nobody cares", "Same old story".
  - "I can't say I agree" (contains "I agree").
  - Agreement that is only a lead-in to disagreeing: "Agreed, but you're wrong about…", where the point is the disagreement.

#### `challenge` (rows 221–240). Pushback
- **Regex.** source / source?, citation, not true, wrong, disagree, nonsense, bullshit, cope, delusional, "no it", "that's not", "this is false", "lol no".
- **Fired on:** **wrong 6**, "that's not" 3, cope 2, source 2, and 1 each of bullshit, "no it", delusional, "lol no", nonsense, "not true" and disagree.
- **YES.** The reply pushes back on the comment or person it answers: disputes or corrects a claim, says they are wrong, mocks or dismisses their view ("cope", "delusional", "lol no"), or demands a source sceptically.
- **NO.**
  - "open source", "source code".
  - "no IT experience".
  - "You're not wrong" or "I don't disagree" (these agree).
  - "nothing wrong with that".
  - "what's wrong with this market" (a shared complaint).
  - "how do you cope with the stress".
  - "that's not fair to you" (sympathy).
  - Anger at a company, executives or the market that sides with the person: "these layoffs are bullshit".
- If you cannot tell whether the pushback targets the person or a third party, choose `unsure`.

## 6. Optional second judgement: `blamed_target` (topic versus stance)

This applies only to the 4 blame-topic labels: `mentions_execs`, `mentions_offshore`, `ai_excuse` and `blames_workers` (yellow cells; 80 rows).

> **Does the author actually BLAME that target?**

- Answer **`yes` or `no` on all 20 rows of each of these labels**, even when `label_correct` is `no`; then it is almost always `no`. That way the scorer can compare the **topic rate** (`label_correct`) with the **blame rate** (`blamed_target`) over the same rows.
- Answer **`yes` only when the blame is clear**: stated, or unmistakable in context. Otherwise answer `no`, and if you hesitated, write why in `notes`.
- Quoting someone else's blame, rejecting it, or a neutral mention is `no`.

| label | the target | `yes` when the author… |
|---|---|---|
| `mentions_execs` | executives, shareholders, investors, "corporate greed" | holds them responsible for layoffs, bad hiring or worse conditions ("CEOs cut jobs to pump the stock") |
| `mentions_offshore` | offshoring and outsourcing, H-1B and visa hiring, or the foreign workers | presents them as a cause of job losses, lower pay or a harder market. Write `workers` in notes if the blame is aimed at the foreign workers themselves rather than companies or policy. Provisional reading: only 7 of 70 mentions blamed foreign workers |
| `ai_excuse` | companies using AI as a pretext | asserts that AI is an excuse, cover or pretext for cuts, or that cuts blamed on AI really have other causes (endorses the "AI is the excuse" claim) |
| `blames_workers` | workers or job seekers | holds them (others, or themselves; write `self` in notes) responsible for losing or not getting jobs because of their skill, effort or performance |

Everything else is pre-filled `na`; leave it. The dropdown offers `yes`, `no` and `na`.

## 7. Running the scorer

From the project folder (`Archive/`), run:

```
python3 scripts/score_human_check.py
```

It needs Python 3 with pandas and openpyxl. They are already in the project laptop's Anaconda Python. On another machine, if you see `ModuleNotFoundError`, run `python3 -m pip install pandas openpyxl` once, then rerun.

- **What it reads.**
  - Every `annotations/human_check/check_sheet_coder_*.xlsx`; the matching `.csv` is used if the xlsx is blank or missing.
  - The optional `annotations/human_check/adjudicated.csv`.
  - Each file is validated against `outputs/12_replies/check_sheet.csv`: 240 rows, row_ids 1–240, matching labels and ids, and allowed values only.
  - Blank coder files are skipped. A bad file stops the run with `ERROR: <file>, row_id …, column …` and exit code 2.
- **If nothing is coded yet**, it prints a message, writes nothing, and exits with code 0.
- **What it writes** (to `outputs/18_human_check/`):

| file | contents |
|---|---|
| `precision_by_label.csv` | For each coder, for consensus (rows the coders agree on) and for final (agreed + adjudicated): yes / no / unsure counts, precision = yes/(yes+no), and the Wilson 95% CI. One row per label plus a pooled `ALL` row. `unsure` is excluded from precision and reported separately. `field` = `label_correct` or `blamed_target` (4 labels) |
| `agreement_by_label.csv` | For every pair of coders who share coded rows, per label and overall: number of overlapping rows, percent agreement and Cohen's kappa (on rows both answered yes/no), and the number of rows with an unsure. If kappa is undefined (both coders gave the same answer on every row), kappa is blank and `kappa_note` gives the reason. Agreement is still reported |
| `disagreements.csv` | Rows to adjudicate: `row_id`, `machine_label`, `field`, `kind` (`yes_vs_no` or `involves_unsure`) and each coder's answer. No text: look the row up by `row_id` in your workbook |
| `SUMMARY.md` | Slide-ready tables (below), overall kappa, an auto-filled interpretation sentence per label, and caveats |

## 8. Putting it on a slide

One table, then one sentence.

| label | n | precision % (95% CI) | % agreement | Cohen's κ |
|---|---|---|---|---|
| experience | 20 | e.g. 85.0% (64.0–94.8%) | 95.0% | 0.83 |
| … | | | | |
| none (baseline purity) | 20 | … | … | … |

- **n** is the number of rows with a final yes/no; `unsure` rows and rows still being adjudicated are left out.
- **Precision** is the share of the rule's hits that are correct. For `none`, it is **baseline purity**: the share of "unmarked" comments that really contain none of the seven types.
- **Interval.** The Wilson 95% interval. With n = 20 it is wide: 20/20 still only guarantees about 84% or more, and 10/20 spans 30–70%.
- **Kappa.** Lead with the **overall kappa**; per-label kappa on 20 rows is jumpy. A common reading (Landis & Koch): 0.41–0.60 moderate, 0.61–0.80 substantial, above 0.80 almost perfect. Always show percent agreement next to kappa, because kappa drops when nearly all answers are "yes" (the kappa paradox).
- **Suggested decision rule for the results slides:**
  - precision of 80% or more with κ of 0.6 or more → the label can support a **Finding**;
  - 50–80% → usable with a caveat, because noise pulls every lift toward 1 and real effects are probably larger than measured;
  - below 50% → do not quote counts from that label.
- **For the four blame-topic labels**, add the topic rate next to the blame rate (`SUMMARY.md`, second table). This is the "a topic is not blame" point in numbers.
- **One-sentence template:** "Two coders independently checked 240 rule hits, 20 per label. Agreement was X% (κ = Y). The `experience` rule was right in A% of cases (95% CI B–C%), while `agree` was right in only D%, because it fires on any reply starting with 'This'."
- **Do not** present a pooled precision as a corpus-level rate. The sample has 20 per label, not in proportion to how often the labels occur.

## 9. Optional: the 200-row reading sample (not needed for tomorrow)

**What it is.** `annotations/reading_labels_employment.csv` is a separate, balanced sample of **200 records**:
- 40 each from the layoffs and hiring-conditions groups;
- 30 each from AI-and-work and background;
- 20 each from restructuring, economic policy and career transition.

It covers posts and comments from all three communities. All its code fields are blank: `relevance`, `document_type`, `experiences`, `explanations`, `future_expectations`, `themes`, `emotions`, `response_function` and `notes`. The codebook is `docs/CODING_STARTER.md`.

**Why it is not needed tomorrow.** The 240-row check is what turns our numbers into Findings: it gives the precision and agreement of the labels the results count. The reading sample is **exploratory, qualitative coding**. It deepens interpretation (themes, explanations, emotions), but its frequencies **do not** estimate prevalence, and nothing on tomorrow's slides depends on it.

**How to code it if time allows** (follow `docs/CODING_STARTER.md`):
1. Work in a **copy** (for example `annotations/reading_labels_employment_<name>.csv`); never overwrite the original. Join records by `(kind,id)`, not by row position.
2. Do **relevance first**: `relevant`, `irrelevant` or `uncertain`. A screen match is only a retrieval aid. Code the other fields only for relevant or uncertain rows.
3. Code each dimension independently. Use semicolons for multiple codes, and leave a field blank when the text does not support it.
   - In `explanations`, mark whether the attribution is asserted, tentative or rejected (`ai_tentative` versus `ai_rejected`).
   - Keep quotation separate from the author's own claim.
   - Put a short evidence span in `notes`.
4. Start with a subset across all seven groups. Have a second reader code an overlapping subset (about 40 rows) independently, then discuss the disagreements and date any rule changes.
5. Count codes with `python3 scripts/summarize_annotations.py --input annotations/reading_labels_employment_<name>.csv`. This counts codes; it does not validate them.

## 10. Quick reference

| label | family | YES in one line |
|---|---|---|
| experience | act | a layoff or job loss really happened to the author or their own team |
| mentions_execs | topic | really refers to executives, shareholders, investors, Wall Street or corporate greed (any stance) |
| mentions_offshore | topic | really about offshoring or outsourcing jobs, H-1B or work visas, including the author's own visa (any stance) |
| blames_workers | topic | the trigger describes workers' or job seekers' skill, effort or performance (any stance, including self) |
| ai_excuse | topic | about AI being an excuse or cover for cuts, or whether AI is really the cause (any stance) |
| ai_replaces | claim | the author asserts AI or automation will replace or take jobs |
| doom | claim | the author asserts the tech job market or their job prospects are bad |
| none | baseline | none of the seven comment types appear, in any wording (for type 4, only workers described as lazy, unskilled, unqualified or low performers count, not ordinary skills talk) |
| sympathy | reply act | genuine emotional support or well-wishes for the person |
| advice | reply act | recommends something the person could do |
| agree | reply act | main stance is agreement with the comment answered |
| challenge | reply act | pushes back on the comment or person answered |
