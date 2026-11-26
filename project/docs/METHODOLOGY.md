# Methods and interpretation

## Research scope

The project studies technology employment disruption as a process involving layoffs, hiring conditions, AI, restructuring, and economic or policy developments. See [the research design](RESEARCH_DESIGN.md) for the supplied project brief and proposed operationalization. Layoff screens and lexical summaries cover an initial strand. Separate broader screens support candidate review without establishing relevance; records without matching terms may be relevant. The design document distinguishes planned research from implemented pipeline behavior below.

## Profiling and provenance

The collection contains 115,213 posts and 2,859,037 comments in 29,821 JSON batches. Creation timestamps define UTC dates; batch filename numbers are opaque identifiers. The current raw data has no repeated `(kind,id)` records, malformed JSON batches, or folder/creation-month mismatches. Repeated snapshots in future input are deduplicated by greatest known retrieval time, with sorted-file order breaking ties.

A teammate was tasked with collecting layoff-related Reddit content using Arctic Shift, but queries, pagination settings, and cutoff reasons are unknown. Completeness and representativeness are unverified. Posts cover technology/programming into September 2026; career-question posts are absent. Technology comments end June 9, 2025, programming comments December 12, 2025, and career-question comments September 23, 2026. Pooled time trends therefore mix changing community coverage. Compare within communities and identify partial boundary months.

## Preprocessing

Raw files and original body text are preserved. Prepared text decodes HTML entities and normalizes whitespace, preserving punctuation, negation, emojis, case, slang, and URLs. Line-prefixed Markdown quotations are separated into `quoted_text`; `own_text` excludes those lines. This is a simple formatting heuristic, not reliable attribution of every quotation. Deleted/removed bodies have empty prepared text and explicit states; empty link-post bodies are not automatically classified as missing.

Known usernames are normalized to lowercase and mapped to stable 96-bit SHA-256-derived pseudonyms. Unknown/deleted authors have null identifiers and are not merged into one user. Original handles remain in raw files; pseudonymization does not guarantee anonymity. `likely_bot` is an unverified name-based flag and does not remove content. Word counts split on whitespace; character counts use Unicode code points.

## Conversation structure

Record IDs identify posts/comments. `link_id=t3_<post-id>` identifies a structural thread root; `parent_id` points to a post or comment. Roots can exist without downloaded submission content. Depth 1 means a reply to the structural root. Missing intermediate parents, malformed ancestry, or cycles yield unknown depth and a reason; missing root content alone does not invalidate resolved depth.

Sizes, durations, and maximum resolved depth describe collected discussion only. Reported comment counts are retrieval-snapshot metadata and may differ from downloaded counts. Distinct-author counts exclude unknown authors.

## Preliminary analysis

Monthly output groups by community, record type, and UTC month. Engagement output compares direct keyword matches and unmatched records within each community/type. Score quantiles use exact frequency histograms with linear interpolation over non-null scores. Thread statistics describe sizes/depths; reply-quality statistics expose missing parents, unknown authors, unresolved ancestry, and timestamp anomalies. The preprocessing audit checks prepared text and character counts.

Lexical output ranks unigram/bigram document frequencies in keyword-matching documents. It uses titles and `own_text` separately, excludes URLs, lowercases, and applies an English function-word stoplist. Negation and retrieval words remain. Stopwords break bigrams instead of creating artificial adjacency. No stemming or lemmatization is applied. Non-English text is retained, so cross-language comparison would require further preparation. Term frequency is not a validated theme, stance, emotion, or cause.

An optional Matplotlib stage exports five static EDA figures: community-specific monthly coverage, normalized body states, direct layoff-match shares, overlapping broader facet counts, and saved-score bands. Missing coverage months are gaps rather than zeros. Percentage denominators are explicit. Score bins separate negatives, zero, one, and increasing positive bands; source counts are checked against the descriptive totals. PNG/SVG files, supplementary source tables, interpretation notes, and input hashes are retained. No inferential tests are implied by these figures.

## Retrieval and qualitative sample

### Broader employment pilot

`screen_disruption.py` adds versioned screens in a separate sparse `disruption_screen` table, preserving original layoff flags. It scans all retained records, using titles and prepared `own_text` separately, excluding URLs and line-marked body quotations. Contextual facets require an employment anchor in the same field; co-occurrence may span sentences. Negation does not suppress retrieval. Six binary facets cover layoffs, hiring conditions, AI/work change, restructuring, economic/policy, and career transition. Exact patterns, employment anchors, version, fingerprint, and scan count are recorded in manifests. Matching evidence lists original matched terms and their field. These are unvalidated English lexical screens; they can miss indirect or non-English accounts and retrieve unrelated co-occurrences.

The candidate CSV is keyed by `(kind,id)` and contains only matches. Absence means no rule matched under that complete screen, not irrelevance. Monthly output includes all community/type/month strata, including zero matches. Percentages use all collected records, so text availability and incomplete community coverage affect interpretation. Facets overlap; summing them double-counts records.

The default broader reading sample has quotas of 40 layoffs, 40 hiring conditions, 30 AI/work change, 20 restructuring, 20 economic/policy, 20 career transitions, and 30 nonmatching background records. Eligible frames overlap; fixed group order and global record deduplication assign one sampling group while retaining all flags. It balances community × UTC quarter × kind × score band, with the bands below and deterministic hash ordering. At most one focus record per thread is chosen within a group. This is exploratory diversity sampling, not a probability sample for prevalence or retrieval-error estimates.

Broader samples and context packets are in `05_sample/employment/`; their working labels are `annotations/reading_labels_employment.csv`. New blank coding columns capture experiences, explanations, and future expectations. Definitions in the coding starter are pilot prompts, not a validated codebook. No qualitative interpretation is assigned by screening.

### Original layoff pilot

This earlier pilot is retained as an optional reproducible method, not as a second current result set. Its generated files and byte-identical unused annotation template were removed on 5 October 2026. `sample_data.py --focus layoffs` regenerates them. SQLite membership metadata is retained for existing sample-scoped network queries.

Direct matching covers variants of layoff(s), laid off, laying off, and lay off. Broad matching adds redundancy, furlough, downsizing, job cuts, workforce reductions, and reduction in force. Broad matching can pick up unrelated programming uses of “redundancy”; quotations can trigger either screen. Unmatched records can still be relevant.

The 200-record sample includes 70 broad-matching posts, 90 broad-matching comments with available bodies, 20 unmatched posts, and 20 unmatched comments with available bodies. It balances community × UTC quarter × score band by round-robin selection with deterministic hash priority. Post bands are <=1, 2–713, and >713; comment bands are <=1, 2–15, and >15. At most one record per thread is chosen within each group; separate groups can share threads. This supports varied reading, not unbiased prevalence estimation.

The manifest records the seed and eligibility/selection strata. The JSONL packet includes full focus text, available submission content, up to 30 ancestors, and up to 40 direct replies, with missing/truncated context marked. Working annotations are separate from generated samples and preserved on reruns. Develop category definitions from reading, record ambiguous cases, and revisit earlier labels when definitions change. Use an independently coded overlapping subset to investigate reader disagreements before quantitative interpretation. The annotation script only counts supplied labels.

## Networks for Gephi

Author edges connect replying author → parent author. Weight counts selected observed replies. Parent records need not themselves match keywords. Unknown authors, absent parent content, different-thread parents, and self-replies are excluded. Only endpoints of retained pairs become nodes. Minimum-pair-weight filtering is explicit. `ScopeCommentCount` describes selected source comments before filtering; degree/strength columns describe retained pairs.

Conversation edges connect replying comment → immediate parent with weight 1. Missing records become nodes with `Present=0`. Structural roots and immediate parent nodes are included; keyword-comment scope is not a complete conversation tree. No missing edges are invented.

Date filters apply to comment creation: inclusive start, exclusive end, in UTC. Parent context may predate that interval. Filtered exports retain only threads with selected comments; unfiltered keyword-post exports also retain matching posts with no collected replies. All exports check unique IDs, valid positive weights, and endpoint completeness.

These networks measure observed responses, not friendship, agreement, support, or causal influence. Missing submissions particularly affect career-question top-level replies. Changing collection coverage also affects graph comparisons over time. Export manifests record scope and overlapping exclusion counts.

## Reproducibility

The pipeline uses the current Python interpreter and standard library. Existing profile/preparation stages are reused; large tables stream to CSV. Per-stage logs in `.cache/logs/` and a run manifest record execution. Raw files remain authoritative and are referenced by `source_file`. Changing the source collection requires deliberately rebuilding the profile and derived preparation stages. Annotation working files are kept outside generated-output replacement. Rebuildable caches and obsolete logs are disposable; current manifests, quality audits, and output tables retain useful provenance.
