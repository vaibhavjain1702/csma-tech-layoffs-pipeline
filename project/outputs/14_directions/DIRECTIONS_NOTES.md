# Four directions, run through the routine

*19 November 2026. Script: `scripts/explore_directions.py`. All labels are rule-based markers, and they are leads until a human checks them.*

| | Question | Answer | Label |
|---|---|---|---|
| D1 | Does framing follow the person or the community? | **Blame follows the person; AI talk follows the community** | Supported (n=160) |
| D2 | Do people who get sympathy come back more? | **No. Getting *any* reply matters; sympathy does not add anything** | Lead |
| D3 | Was the H-1B announcement a shock or a lasting shift? | **One-week shock with no lasting change in volume or framing** | Supported |
| D4 | Are story-sharers newcomers and blamers regulars? | **Barely. They have the same tenure.** | No difference (a result) |

---

## D1. Same person, two communities (tests rival R4 for H2)

1. **Say it.** Across all authors, r/technology comments mention executives or shareholders more than twice as often as cscq comments (7.8% vs 3.3%). We looked at the 160 authors who wrote at least 2 employment comments in each community during Jan–Jun 2025. They mention executives about equally often in both: 6.6% vs 5.8%, a difference of +0.8 points (CI −1.7 to 3.2).
2. **Expected?** Surprising. H2 assumed that r/technology *frames* layoffs as executive action.
3. **Rivals.** One story is that the community shapes how a person talks. The rival is selection (R4): r/technology simply has more of the people who talk about executives.
4. **Check.** Within the same people, the executive gap disappears, and the offshoring and consequence gaps disappear too. **The AI gap does not**: the same people mention AI 9.4 points more in r/technology (CI 2.7 to 15.3).
5. **Name.** *Composition vs context effects.* Who blames whom is part of a person's own view, and they bring it into every community. What people talk about (AI) depends on the community and its threads.
6. **Caveats.**
   - The 160 cross-posters are unusual. They mention executives and offshoring more than average *in both* communities, so they are the politically engaged people.
   - The sample is small.
   - **Claim:** the H2 difference in blame framing is mostly about *who posts in each community*, not about the community changing how people talk.

## D2. Does comfort keep people? (consequence of H3)

1. **Say it.** We followed 1,170 cscq authors after their first story about their own layoff:
   - 36 got a sympathy reply, and 56% of them commented again within 90 days;
   - 439 got replies but no sympathy, and 77% came back;
   - 695 got no reply, and 69% came back.
2. **Expected?** We expected sympathy to keep people. The direction is the opposite, but n=36 is tiny.
3. **Rivals.**
   - (a) The sympathy marker catches "good luck" and "sorry". These are often goodbyes to people in acute distress, who then leave.
   - (b) Leaving may be a good outcome, for example because the person found a job.
   - (c) Prior activity (R5-like).
4. **Check.** Results are split by activity in the previous 90 days:
   - **Newcomers** (0 prior comments): 50% return if they got any reply, against 39% with no reply.
   - **Regulars** (6+ prior comments): about 93–95% return whatever happens.
5. **Name.** *Response and newcomer retention.* Getting a reply makes newcomers more likely to come back (Arguello et al. 2006, "Talk to me").
6. **Claim (lead):** for newcomers, getting answered matters more than being comforted. Sympathy is too rare for this marker to say anything about it. **Do not claim** that sympathy drives people away.

## D3. The H-1B announcement of 19 September 2025 (rival R8, event shock)

1. **Say it.** In the week of the announcement, 43% of cscq employment comments mentioned offshoring, H-1B or visas, against about 13% in the 8 weeks before. The next week it was 13.5%. Weeks 3–12 were *below* the earlier level, at 5–9%.
2. **Expected?** Partly. A spike was expected, but its fast drop, to below the earlier level, was not.
3. **Rivals.**
   - (a) A lasting shift toward blaming foreign workers.
   - (b) A news-cycle shock that changes the amount of talk but not its content.
4. **Check.** Among offshoring comments, the share with an ethnic reference was 16% in the spike week, against about 20% before. The share mentioning executives was 4% in both periods. **The amount of talk changed; its framing did not** (rough markers, R1).
5. **Name.** *Event shock vs gradual drift* (Zhang et al. 2017). The talk was a burst, not a turning point.
6. **To check:** a second spike in week 13 (mid-December 2025, 24%). Find out which event it matches.
7. **Examples** (`examples.txt`). Both sides argue inside the same threads: "*We need to … stop letting in so many H1B*" and "*…I think you missed the white supremac[y]…*".

## D4. Core vs periphery (network)

- Authors who share their own layoff have slightly more newcomers (18% with no comments in the previous 180 days, against 13% overall) and slightly fewer regulars (21% against 26%).
- Doom comments come from the most established authors (28% regulars).
- Median prior activity is 9–14 comments for every kind of comment.
- **Meaning.** Story-sharers and blamers are *different people* (see the findings, H3), but not different *tenure groups*. The split is about which side people take, not core vs periphery.
- **For Gephi:** colour author nodes by "experience vs offshore" rather than by activity. The activity split is flat.

---

## How the directions connect

- D1 and D4 point the same way. The people who blame are a recognisable *type* of person:
  - they bring their framing into every community (D1);
  - they are distinct from the people who share stories (H3 author roles);
  - they are not just newcomers or just regulars (D4).
- D2 and D3 are both about **attention vs content**:
  - a reply keeps a newcomer whatever it says;
  - a policy event moves the volume of talk, not its framing.

**One sentence for the report:** *Each community shapes what is discussed and how much; who gets blamed comes with the person.*
