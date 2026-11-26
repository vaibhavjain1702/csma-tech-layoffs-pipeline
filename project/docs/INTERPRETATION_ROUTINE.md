# From a number to a finding: the interpretation routine

*Written 19 November 2026. Use it every time an analysis produces a number, before starting the next analysis.*

Producing numbers and plots is the easy part. This routine is the step in between: it turns a number into a claim about people, then tests that claim against other numbers. Running it on one result usually takes 20–40 minutes. It also tells you what to compute next.

The routine applied to this project is in `docs/PROJECT_REFERENCE_2.md` (layers 4–7). The earlier write-up by hypothesis is archived at `outputs/archive/FINDINGS_BY_HYPOTHESIS.md`.

```
 number ──► 1 SAY IT ──► 2 EXPECTED? ──► 3 RIVALS ──► 4 CHECK ──► 5 READ ──► 6 NAME IT ──► claim
              ▲                                         │            │
              └───────── a rival wins: rewrite step 1 ──┴────────────┘
```

---

## Step 1. Say it as what people did

Rewrite the number as one plain sentence about people. Do not use the variable name.

- Bad: "experience → sympathy lift = 2.8"
- Good: "When someone in cscq says they were laid off, strangers comfort them about 3× more than usual."

**Done when** someone who has never seen the data understands the sentence. If you can't write it, you don't know yet what the number measures, so go back and check what the label really captures.

## Step 2. Compare it with what you expected

Write down what you expected before you looked. Then put the result in one of three groups:
- **Confirmed:** fine, but it adds little.
- **Surprising:** this is where findings come from.
- **No difference:** this counts as a result too, when you expected one.

If you had no expectation, ask what a hypothesis (H1–H3) predicts.

## Step 3. List the rival explanations

Ask why people would behave this way, and write 2–3 different answers. One is your preferred story. **At least one should be a boring explanation.** Social media data has a standard list of boring explanations, so go through it every time:

| # | Boring explanation | How it fools you | Typical check |
|---|---|---|---|
| R1 | **The label doesn't measure what its name says** | A keyword rule matches the topic, not the stance. "Visa" is not blame. | Read 20 random matches and count the hits |
| R2 | **The denominator moved** | "X doubled", but all of the topic doubled | Divide by the parent topic, not by all comments |
| R3 | **A few threads or users drive it** | One megathread or one spammer makes a month | Count distinct threads and authors; check the share in the top 10 |
| R4 | **Coverage differs** | One community has no data for that period | Use the shared window (Jan–Jun 2025) for comparisons between communities |
| R5 | **Timing and position** | Early comments get the votes, whatever they say | Use within-thread percentiles and control for early arrival |
| R6 | **Length** | Long comments match more keywords and get more replies | Repeat the check within a word-count band |
| R7 | **Bots and promotion** | Repeated commercial posts | Check distinct authors and domains |
| R8 | **An outside event** | A news event, not a change in the community | Look at daily counts and match them to a dated event |

## Step 4. Check: each rival predicts a different number

This is the step that connects results to each other. For every explanation, ask what **other** number would look different if it were true, and compute it.

- If the boring explanation's prediction holds, it wins. Rewrite step 1 (see C3 in the findings file, where this happened).
- If your story's predictions hold across **independent measures** (replies, votes, vocabulary, sources, people), you have **convergence**. Convergence is what turns a lead into a finding.

## Step 5. Read 5–10 real examples

Read single comments or comment–reply pairs, not whole threads. The question is narrow: does the text look like the story? Keep one or two quotes for the write-up. If the examples don't fit, go back to step 3.

## Step 6. Name it

Ask what idea in the literature this is an instance of. A name links your result to existing work and tells the reader why it matters. Concepts that fit this project:

- **Emotional vs informational support** (online support communities). One reply comforts, the other gives information.
- **Community norms enforced through votes.** What a community upvotes shows what it values (Goyal et al.).
- **Attribution and blame.** People blame the system, the employer, or other workers.
- **Evidence cultures and information ecosystems.** What counts as proof in a community: data, studies, or news.
- **Event shock vs gradual drift** in community language (Zhang et al. 2017).
- **Core vs periphery adoption** of new vocabulary (Danescu-Niculescu-Mizil et al. 2013).

## Write the claim

> In **[community]**, when people **[do X]**, others **[respond Y]** (**[N]×** more than usual). This suggests **[meaning, step 6 name]**, because **[independent result]** points the same way. An alternative is **[rival]**, but **[check]** argues against it. Example: "*[quote]*".

Then give the claim one of three labels:

| Label | Means | Allowed wording |
|---|---|---|
| **Lead** | One number, no checks yet | "we observed…; this may indicate…" |
| **Supported** | It survived the boring explanations, plus one independent measure | "the evidence suggests…" |
| **Finding** | Convergence across 3 or more independent measures, examples fit, labels have been checked by a human | "we find…" |

Nothing in this project counts as a **Finding** until a human has checked the labels. All precision checks so far were done by Claude and are marked `claude-provisional`.

---

## Checklist (copy it under any result)

```
[ ] 1 Sentence about people:
[ ] 2 Expected?  confirmed / surprising / no difference
[ ] 3 Rivals:  my story = ... ; boring = R_ ... ; other = ...
[ ] 4 Checks run (file):            outcome:
[ ] 5 Examples read: n=    fit? y/n   quote:
[ ] 6 Concept:
[ ] Claim + label (lead / supported / finding)
```
