# Research design: technology employment disruption

This document records the supplied project scope and a proposed analytical plan. The pipeline described in the README and methodology is implemented; the research questions, coding dimensions, and extensions here are proposals to develop through reading and validation. A modest steering pass now adds six versioned employment screens, candidate/monthly exports, and a separate broader reading sample with blank coding fields. These support the pilot below; broader relevance and qualitative constructs remain unvalidated.

## Project brief supplied by the researcher

> This project examines how ongoing disruption in technology employment is reflected, interpreted, and socially negotiated across online communities. Rather than treating layoffs as isolated events or reducing online discussion to sentiment, the study views technology employment disruption as a broader process shaped by layoffs, changing hiring conditions, rapid advances in artificial intelligence, corporate restructuring, and wider economic and policy developments. Using social-media data, the project investigates how people report their experiences, explain the causes of employment change, express uncertainty and concern, seek or provide support, and construct competing narratives about the future of technology work. It also considers the social structure of these discussions by examining interactions between users, community formation, information diffusion, and the amplification or contestation of different narratives. These online patterns will be interpreted alongside external contextual data such as major employment events, AI developments, labor-market indicators, and worker surveys. The overall aim is to understand not only what people are saying about disruption in the technology labor market, but how collective interpretations and responses emerge, spread, and evolve over time, and whether these digital traces provide meaningful insight into changing worker experiences and perceptions of technology employment.

## Proposed research questions

1. What employment experiences and changes do participants describe, and how do these accounts vary across communities and observed periods?
2. How do participants explain disruption, assign responsibility, and imagine the future of technology work? Which explanations coexist or compete?
3. How do replies provide support, seek clarification, endorse claims, challenge them, or negotiate uncertainty?
4. How are participation and responses structured, and how do particular narratives receive attention or become contested within discussions?
5. How do these patterns vary alongside documented employment, AI, economic, and policy developments, and where do they align with or diverge from labor indicators and worker surveys?

These questions concern collected discourse. Participants' worker status, location, occupation, and personal circumstances cannot be assumed from their community or username.

## Units and analysis dimensions

| Dimension | Unit and proposed evidence | Initial analysis | Current support or gap |
|---|---|---|---|
| Experiences | A post/comment reporting job loss, search difficulties, hiring, career transition, or workplace change; distinguish first-person accounts from secondhand reporting | Compare coded experiences within communities and periods; inspect counterexamples | Full text and contextual reading packets exist; experience labels need development |
| Explanations and futures | A claim attributing change to AI, employer strategy, economic conditions, policy, or other causes; future expectations and proposed responses | Examine recurring explanations, responsibility, alternatives, and evidence used | Lexical candidates exist; words alone do not identify narratives or causal claims |
| Uncertainty and affect | Explicit expressions of uncertainty, concern, hope, anger, resignation, or mixed reactions | Read affect together with its target and situation | Human annotation fields exist; no emotion or sentiment labels have been inferred |
| Social responses | A reply and the claim or experience it addresses | Code advice, empathy, resource sharing, clarification, endorsement, challenge, and dismissal | Parent links and available ancestors exist; response functions require contextual coding |
| Interaction structure | Replying users, parent users, threads, and participation over time | Gephi exploration of response patterns, concentration, reciprocity, and groups | Directed weighted reply CSVs exist; missing parents/authors affect observability |
| Narrative attention and contestation | Coded narrative occurrences and the replies they receive | Count distinct participants, threads, follow-up responses, and endorsement/challenge separately | Requires narrative labels joined to reply edges; Reddit score is snapshot metadata |
| Change and external context | Community-specific periods and dated, sourced contextual records | Align discourse patterns with events and indicators using compatible time and geographic units | Coverage summaries exist; external contextual records have not been assembled |

Code multiple dimensions independently. A report of job loss may contain an explanation, a fearful future expectation, and a request for advice. Retain mixed and ambiguous cases rather than forcing one overall sentiment.

## Corpus scope and relevance

The available corpus contains 115,213 posts and 2,859,037 comments, including substantial content outside explicit layoff mentions. Collection settings remain unknown. It is neither an established census of these communities nor a validated sample of technology workers.

Direct layoff terms currently identify 654 posts and 28,077 comments. These are retrieval counts, not the size of the research-relevant population. A broader scope should consider hiring freezes, recruitment and job searching, work displacement or changing tasks, restructuring, career transitions, and economic/policy explanations when connected to technology employment. A general discussion of AI or a programming use of “redundancy” is not sufficient by itself.

Before extending quantitative claims:

1. Pilot the relevance definition on matching and nonmatching records, reading available thread context.
2. Record inclusion/exclusion examples, uncertain cases, and whether employment context is stated or inferred from surrounding discussion.
3. Develop separate retrieval rules for the main disruption dimensions. Keep versioned flags and matched evidence, preserving the current layoff flags.
4. Inspect false positives among retrieved records and potential misses among nonmatches, stratified by community and time. Use a probability-based audit sample if estimating error rates; the existing balanced reading sample supports exploration only.
5. Report relevance decisions separately from text availability and missing context. An absent root can make a comment uncertain without making it irrelevant.

Technology comments stop on June 9, 2025; programming comments stop on December 12, 2025; career-question comments extend to September 23, 2026, with no collected submissions from that community. Pooled trends and network changes therefore confound discussion change with collection coverage. Begin with within-community comparisons and shared observed windows; mark partial months and retain missing-context indicators. Normalizing by collected record counts describes the collected corpus, not community-wide activity.

## Qualitative development and structured outputs

Start with the existing 200-record reading sample and its context packet, then purposively read cases the pilot reveals as missing. Draft definitions for experiences, causal explanations, future expectations, uncertainty, and response functions. Treat the table above as sensitizing questions, not established findings or a final codebook. Read both supportive and contradictory cases.

The current working CSV, `annotations/reading_labels_employment.csv`, contains `relevance`, `document_type`, `themes`, `emotions`, `response_function`, and `notes`, plus blank `experiences`, `explanations`, and `future_expectations` columns; see [the coding starter](CODING_STARTER.md). The original layoff template was unused and removed during cleanup; it can be regenerated separately if needed. Before expanding coding, define a versioned codebook and consider a separate long-form annotation table with one row per coded dimension or claim:

| Proposed field | Purpose |
|---|---|
| `kind`, `id`, `thread_id` | Join to records and conversations |
| `annotation_id`, `coder_id`, `codebook_version` | Identify coding decisions and their provenance |
| `dimension`, `code` | Distinguish experience, explanation, expectation, affect, and response |
| `evidence_text`, `target_kind`, `target_id` | Locate supporting text and, for a response, the addressed record when identifiable |
| `certainty`, `notes` | Preserve ambiguity and contextual interpretation |

These fields are proposed, not yet generated. Use an independently coded overlap to examine disagreements, refine definitions, and revisit earlier decisions. Quantified code frequencies require an appropriate sampling design and clearly stated denominators. Later automated classification or topic discovery should be evaluated against human-reviewed examples; it should not substitute for defining the constructs.

## Networks, narratives, and diffusion

Existing author graphs encode replying author → parent author, weighted by observed replies. Existing conversation graphs encode comment → immediate parent. A graph cluster is an interaction grouping to interpret with its text and scope; it does not by itself establish a shared identity, stance, or narrative. A reply does not necessarily endorse its target.

Join narrative and response labels to records and edges before studying who endorses or contests which claims. Compare participation and attention within explicitly defined windows, reporting omitted unknown-author and missing-parent links. Distinguish repeated contributions by one author from engagement by additional authors.

The current graphs establish observed response sequences. Studying diffusion would additionally require operational evidence of transmission, such as explicit cross-references, shared source URLs, crossposts, or traceable reuse with timing. Shared vocabulary and temporal order alone do not demonstrate that a person saw or adopted another person's interpretation. Do not describe reply degree or Reddit score as causal influence or exposure.

## External context and triangulation

Build sourced contextual tables separately from Reddit participants' claims. Proposed outputs are an event register and an indicator table:

- Event register: `event_id`, event date or interval, date precision, event type, organization, geography, sector, description, source URL, source publication date, and retrieval date. Separate an announcement date from any effective date.
- Indicator table: source, measure, period, geography, population/sector definition, value, unit, adjustment/revision information, and retrieval date. For surveys, retain fieldwork dates, question wording, sample population, weighting, and the published denominator where available.

Choose contextual sources and observation windows in advance of interpreting apparent peaks. Align periods and definitions, and document mismatches: a technology firm's layoffs, technology occupations across industries, and total employment measure different populations. Country-specific indicators cannot be assigned to geographically unidentified commenters.

Use contextual data to interpret convergences, divergences, and plausible explanations. Event-aligned patterns are descriptive associations unless a separate design supports causal inference. Claims about digital traces as labor-market indicators would require additional validation against suitable external series; the current collection cannot establish representativeness or predictive value.

## Order of work

1. Use the completed profiling, preprocessing, structured exports, and descriptive outputs to establish what is observable.
2. Pilot broad relevance and qualitative definitions, documenting examples and coverage limitations.
3. Extend retrieval and contextual sampling through reproducible Python scripts, with versioned rules and audit outputs.
4. Analyze validated dimensions by community and period; connect narrative and response annotations to Gephi graphs.
5. Assemble external context and triangulate interpretations, preserving disagreement and uncertainty.

Each extension should produce inspectable tables, a script or explicit coding procedure, and a manifest describing scope and choices. No UI is required.
