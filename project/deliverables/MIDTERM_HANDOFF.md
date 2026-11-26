# CSMA Mid-term handoff

The mid-term target is Phase 2: data collection, preprocessing, preliminary analysis, comparison, and an initial inference.

## Present these files

- `CSMA_Midterm_Report_Solidarity_or_Blame.pdf` for the hard copy.
- `CSMA_Midterm_Report_Solidarity_or_Blame.docx` for edits.
- `CSMA_Midterm_Presentation_Solidarity_or_Blame.pptx` for the 15-minute presentation.

Before printing, add or confirm each member's enrollment number. The supplied synopsis lists names and roles but does not include enrollment numbers.

The presentation contains 15 slides. Slides 3-6 cover the 15-study literature review. Slides 8-9 explain the methodology and validation plan. Keep the delivery compact and use the speaker notes in the PPTX.

## Suggested 15-minute speaking order

1. Vanshit: title, research question, hypotheses, research gap, and current conclusion.
2. Krish: literature review, NLP method choices, and exploratory stance baseline.
3. Vaibhav: data collection, provenance, and corpus coverage.
4. Tanya: preprocessing, methodology, controlled comparison, and figures.
5. Dividh: Gephi exports, graph definitions, and limits of network interpretation.
6. Vanshit: contributions, next phase, and questions.

## Headline result

In the shared January-May 2025 window, layoff-language matches occurred in 2.32% of collected r/cscareerquestions comments and 0.20% of collected r/technology comments, an 11.36x rate ratio. Hiring-condition language was 8.50% versus 0.45%, an 18.69x ratio. These are corpus descriptions, not prevalence estimates for all workers.

## How to explain the comparison

The denominator is every collected comment in the community and shared window. Facets overlap. The screen is a reproducible retrieval aid, not a validated stance label. The two-proportion test is descriptive support for the size of the difference under an independence assumption; it does not remove sampling bias or repeated-author effects.

## Hypothesis status

- H1, community concentration: preliminary support.
- H2, discourse function: not yet tested; human coding is required.
- H3, reply structure: not yet tested; validated stance labels must be joined to the networks.

Call the current study a within-Reddit, cross-community pilot. Do not claim that X or LinkedIn have been analysed.

## What remains after the mid-term

1. Human-code the 200-record reading sample and an overlapping subset for agreement.
2. Evaluate VADER and a transformer stance classifier against those labels.
3. Run topic modelling and interpret Gephi graphs after joining validated labels.
4. Add sourced external events and labor indicators for triangulation.

The final package passed the archive validator and all 15 unit tests after the literature, methodology, and contribution revision.

## Contribution statements

- Vanshit Ahuja: archive QA, research reframing, shared-window comparison, hypotheses, statistical interpretation, literature review, report and PPT revision, privacy checks, testing, repository cleanup, and public release.
- Vaibhav Jain: Reddit data collection, raw batches, provenance, and coverage checks.
- Dividh Vijay: all Gephi and network work, including node and edge exports, direction, weights, scope, and validation.
- Tanya: data cleaning, thread linkage, quality checks, descriptive analysis, community comparison, and figures.
- Krish: lexical and stance baselines, reading sample, coding framework, and NLP evaluation plan.
