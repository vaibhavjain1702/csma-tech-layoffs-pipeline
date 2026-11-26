# Solidarity or Blame: findings by hypothesis

*19 November 2026. Each result was put through `docs/INTERPRETATION_ROUTINE.md`. Check outputs come from `scripts/check_interpretations.py` (in `outputs/13_interpretation/`) and `scripts/explore_replies.py` (in `outputs/12_replies/`). Label precision checks marked "provisional" were done by Claude and still need a human check.*

## Summary

| | Claim | Label |
|---|---|---|
| H1 | Layoffs are a constant background in cscq and an occasional news topic in r/technology | **Supported** |
| H2 | cscq talks about layoffs as personal experience and its consequences; r/technology frames them as corporate and executive action | **Supported** |
| H3 | Replies follow what a comment *does* (telling your story gets comfort), not whom it blames | **Supported**; becomes a Finding once a human checks the labels |
| also | "AI as an excuse" did **not** grow once AI talk is accounted for. Talk of AI replacing jobs fell. | **Corrects an earlier note** |

---

## H1. Community concentration

1. **In plain words:** in January–June 2025, 2.45% of cscq comments mention layoffs, against 0.20% in r/technology (about 11×).
2. **Expected?** Confirmed.
3. **Rivals:**
   - (a) cscq is where people work through employment.
   - (b) Denominator and threads (R2, R3): r/technology is huge and mostly about other news, so layoff talk is diluted; it may be just as intense inside a few layoff news threads.
   - (c) The label (R1): the screen fits cscq's vocabulary.
4. **Checks** (`13_interpretation/C1_h1_thread_spread.csv`):
   - **Against (b).** Even *inside threads that mention layoffs at all*, the rate is 4.06% in cscq against 0.49% in r/technology (8×).
     - In cscq, **67%** of threads with 50+ comments contain layoff talk; in r/technology, 21%.
     - The 10 busiest threads hold 8.6% of cscq's layoff comments, against 19.8% in r/technology and 40.7% in r/programming.
   - **Against (c).** In the provisional precision check, the layoffs screen is about 95% precise (`09_leads/screen_audit/manual_precision_by_group.csv`).
   - **Not usable as a headline.** The *hiring-conditions* screen is only about 22% precise, so the midterm's 18.7× hiring ratio should not be repeated.
5. **Name:** in cscq layoffs are an ambient topic that runs through ordinary career threads; in r/technology and r/programming they are event-driven and come up in a few news threads.
6. **Claim:** cscq does not just have more layoff talk. Layoffs come up in most of its conversations, while in r/technology they stay inside a small number of news threads.

**Do not claim:** that cscq users are more affected by layoffs, or anything about prevalence outside these collected communities.

## H2. Discourse function

1. **In plain words:** when cscq comments mention layoffs, they talk about *their own* layoff 3× as often as r/technology comments, and r/technology talks about executives and shareholders about 2× as often.
2. **Expected?** Confirmed, and now measured rather than assumed.
3. **Rivals:**
   - (a) The communities have different roles: job seekers vs news readers.
   - (b) Selection (R4): different kinds of people post in each community, so this says something about who posts, not about how they frame layoffs.
   - (c) The label (R1).
4. **Checks.** Several independent measures converge. Jan–Jun 2025 layoff comments (`09_leads/lead2_proximity/first_person_vs_other.csv`):

   | Measure | cscq | r/technology | r/programming |
   |---|---:|---:|---:|
   | Own layoff story (share of layoff comments) | 8.9% | 3.1% | 3.3% |
   | Mentions execs, shareholders or greed (non-personal comments) | 6.5% | 11.8% | 16.1% |
   | Consequence words: rent, savings, insurance, months unemployed | 15.8% | 11.2% | 8.2% |
   | Mentions AI | 11.8% | 18.5% | 41.5% |

   - **Distinctive vocabulary** (`10_language/A`): cscq is about the job search (resume, recruiter, yoe); r/technology about politics (dei, trump, tariffs); r/programming about the craft (code, tools, vibe coding).
   - **Sources linked** (`11_dynamics/H`): cscq links FRED and BLS; r/technology links news sites; r/programming links GitHub and studies.
   - **Reading rival (b).** Rival (b) is not a competing explanation; it is *part of the answer*. Communities differ partly *because* different people go to them. We describe communities, not individuals.
   - **Label check.** The own-layoff-story label was 39/40 correct on layoff comments in the provisional check.
5. **Name:** different **evidence cultures** and community roles. Job seekers give personal accounts and labour statistics; news readers give corporate framing and journalism; programmers talk about the craft and its tools.
6. **Claim:** H2 is supported by four independent measures: own stories, framing words, distinctive vocabulary and linked sources.

**Update, 19 Nov (`14_directions/D1`).** Rival (b) was tested directly.
- 160 authors post employment comments in both communities.
- **Within the same people, the gap in mentioning executives disappears** (6.6% vs 5.8%). The AI gap remains (+9.4 points).
- **Narrowed claim:** the communities differ in *who* frames layoffs as executive action, but the *topic* mix, such as AI, is shaped by the community.

**Do not claim:** that r/technology users are not workers, or that the framing *causes* anything.

## H3. Solidarity and blame get different replies

1. **In plain words:** in cscq, when someone shares their own layoff, the replies comfort them 2.8× more often than usual (5.1% vs 1.8%) and push back 0.6× as often.
2. **Expected?** The comfort part was expected. **The surprise:** the direction of blame barely matters. Comments about executives, offshoring and "AI is the excuse" all get the same pattern:
   - slightly more agreement (×1.05–1.3);
   - much less advice and sympathy (×0.6–0.8).
3. **Rivals:**
   - (a) A community norm: personal disclosure is read as a request for support.
   - (b) Layoff stories are really requests for help, so sympathy just comes with the answers.
   - (c) Length (R6).
   - (d) Thread clustering (R3).
4. **Checks** (`12_replies/`):
   - **Against (b).** If stories were mainly requests, advice replies would rise too. They don't (×0.96).
   - **Against (c).** The effect holds for comments of 30–150 words (×2.7).
   - **Against (d).** The confidence interval resamples whole threads: 3.9–6.4% vs 1.8%.
   - **Votes agree.** Own-story comments are the least often downvoted (1.5% vs 4.2%). Upvoted cscq comments use experience vocabulary (`10_language/C`).
   - **Different people.** Among authors with 5 or more employment comments, 2,392 mention offshoring but never share a layoff, and 306 share a layoff but never mention offshoring. The offshoring group mostly replies to itself.
   - **Label correction (R1).** "Blame sideways" turned out to be ~95% *mentions* of offshoring or visas, not blame.
     - In the provisional coding of 70 offshoring comments, only 7 frame foreign workers as the problem. 21 blame employers or the system, and 9 push back *against* blaming immigrants.
     - The upvoted half is mostly employer blame (16/35).
5. **Examples:**
   - "*Can confirm, I got laid off 1 week before my daughter was born…*" → "*Sorry to hear. That's terrible.*"
   - In response to doom: "*Don't listen to this fool lol…*"
6. **Name:** **emotional vs informational support.**
   - Personal accounts draw emotional support.
   - Doom ("the market is cooked") draws informational support, at 1.4× advice.
   - Explanations of any direction draw debate instead of support.
7. **Claim:** in cscq, solidarity is tied to *disclosure*, not to a shared enemy. The title's answer: comments that **blame** start debates, and **solidarity** goes to people who say what happened to them.

**Network part (yours):** `12_replies/gephi/type_nodes.csv` and `type_edges.csv` give an 11-node "kind of comment → kind of reply" graph with lift as the edge weight. Use it as one slide.

**Do not claim:** that the comments *cause* the replies, or that the rule-based labels are stance detection.

---

## Also found: one earlier note corrected

**AI as an excuse** (`10_language/LANGUAGE_NOTES.md` said it "more than doubled").
- **Rival R2:** AI talk overall doubled (20% → 38% of cscq employment comments from 2025-H1 to 2026-H1).
- **Check** (`13_interpretation/C3_ai_excuse_vs_ai_talk.csv`): per 1,000 AI comments, "AI is the excuse" is flat (18.0 → 19.3) and falls to 12.2 in 2026-H2. **The boring explanation wins.**
- Talk of AI *replacing* jobs per 1,000 AI comments fell from 35.2 to 22.3. This marker catches rejections as well as endorsements (provisional: 7/30 endorse).
- **Rewritten claim:** AI became a much bigger part of cscq's employment talk, but as a *working condition* (tools, review, slop; `10_language/B`), not as a growing story about replacement or excuses.

**Other leads, not yet run through the routine:**
- The H-1B shock in September 2025. The existing community talked, not newcomers (`11_dynamics/F`).
- The 2026 turn to conditions inside the job: PIPs, PTO, mandates (`11_dynamics/E`).
- Early arrival matters 10× more than style for votes (`11_dynamics/G`).

## What is needed before the final report

1. **Human check sheet** (`12_replies/check_sheet.csv`, 240 rows: 160 comments + 80 replies, yes/no). It is the only step that can move H3 from Supported to Finding. Two coders give the agreement number the midterm promised.
2. **Remove the 18.7× hiring figure** from headlines, because that screen is only about 22% precise. Use the layoffs figure.
3. **Tell Krish** before presenting H3, because stance labels are his part.
