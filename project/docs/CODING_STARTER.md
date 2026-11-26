# Coding starter for the employment-disruption pilot

These prompts support an initial reading pass. They are not a validated codebook. Refine definitions using actual examples, retain ambiguous cases, and record disagreements before interpreting code counts.

Use `annotations/reading_labels_employment.csv` and the context packet in `outputs/05_sample/employment/`. The original layoff sample can be regenerated separately with `sample_data.py --focus layoffs` if needed. All human-code fields start blank. Use semicolons for multiple codes and `(kind,id)` as the record key.

## Relevance first

- `relevant`: the focus text, interpreted with available context, concerns employment, hiring, careers, or changing work in technology, or explicitly connects a disruption factor to these issues.
- `irrelevant`: sufficient context exists and the text does not concern that scope. General AI discussion, unrelated technical redundancy, or a generic economic comment is insufficient by itself.
- `uncertain`: the connection is ambiguous or missing context prevents a decision.

A facet flag is evidence for retrieval only. A nonmatching background record can be relevant. Brief replies can be relevant through their relationship to the parent; note when the judgment depends on context. Do not infer participants' occupation or location from the subreddit.

## Independent dimensions

| CSV field | Reading question | Possible provisional codes or notes |
|---|---|---|
| `document_type` | What kind of contribution is this? | First-person account, secondhand report, news discussion, question, interpretation, response; distinguish self-report from verified biography |
| `experiences` | What employment experience is actually described? | Job loss, job search, hiring/interview, workplace change, career transition; do not infer an experience from a generic claim |
| `explanations` | What explanation does the author assert, propose, or reject? | AI, corporate strategy, economic conditions, policy, other; qualify attribution as asserted, tentative, or rejected in notes, e.g. `ai_tentative` versus `ai_rejected` |
| `future_expectations` | What does the author anticipate about technology employment? | Recovery, continued difficulty, displacement, changing tasks, opportunity, uncertainty; retain mixed expectations |
| `themes` | What broader recurring issue is being discussed? | Develop through reading rather than copying screen facets into this field |
| `emotions` | What affect is expressed, toward what, and with what evidence? | Concern, anger, hope, resignation, mixed; leave blank when unsupported; sentiment is only one dimension |
| `response_function` | What does the contribution do relative to its parent or audience? | Seek/provide advice, empathy, resource sharing, clarification, endorsement, challenge, dismissal; multiple functions may coexist |
| `notes` | What evidence, ambiguity, or context supports this interpretation? | Short evidence span, target of a claim/response, missing context, qualifications, and counterinterpretations |

Separate the author's explanation from independently established causes. Separate quotation from the author's own claim. An employment concern does not automatically mean the author was laid off; a reply does not automatically signal agreement.

## First pass

Read a manageable subset across all seven sampling groups, including background records and cases with missing roots. Use the available title, body, ancestors, and replies to interpret the focus record; note truncated context. Record inclusion/exclusion examples and refine a dated codebook before scaling up. Have another reader independently code an overlapping subset where feasible, then examine disagreements.

The balanced 200-record sample supports exploration. Its code frequencies do not estimate prevalence in the corpus or among technology workers. When definitions change, revisit earlier labels. Working copies are never overwritten by sampling; join them by record key, not row position, if generated samples change.

Summarize supplied labels with:

```bash
python scripts/summarize_annotations.py
```

This counts human codes; it neither validates definitions nor assigns interpretations.
