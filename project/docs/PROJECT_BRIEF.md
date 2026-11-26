# Understanding technology employment disruption through Reddit

Project summary — 6 October 2026

## What we are studying and why

This project examines how people discuss and make sense of disruption in technology employment. Layoffs are an important part of this, but the broader picture also includes difficult hiring conditions, artificial intelligence and changing work, corporate restructuring, economic uncertainty, and changing career expectations.

We want to understand how people describe their experiences, explain employment changes, express concern or uncertainty, seek advice, and offer support. We also want to examine how different explanations and expectations are reinforced or challenged through discussion. For example, participants may attribute employment difficulties to AI, corporate decisions, or wider economic conditions. Identifying these explanations and how others respond to them is part of the intended research, rather than a finding already established.

Reddit provides both discussion content and visible reply relationships. This allows us to examine what people say alongside how they interact. Our approach combines descriptive data analysis, network analysis, and later qualitative reading. The eventual goal is to interpret online patterns alongside employment events, labor-market indicators, AI developments, and worker surveys.

## What data we are working with

The supplied collection was downloaded using Arctic Shift by a teammate tasked with collecting layoff-related Reddit content. It contains 115,213 posts and 2,859,037 comments, approximately 2.97 million records altogether, from r/technology, r/programming, and r/cscareerquestions. The files span January 2025 to September 2026.

Our first task was to establish what had actually been collected. The original search settings are unknown, and coverage differs between communities. Technology comments end in June 2025, programming comments in December 2025, and career-question comments in September 2026. Career-question submissions are absent. These differences matter because an apparent change over time could reflect changing data coverage as well as changing discussion.

## How we prepared the data

We audited the original files for their structure, dates, duplicate records, text availability, and missing conversation context. No duplicate post/comment identifiers or JSON parsing errors were found. Around 94.61% of comment bodies are available. Many posts have empty bodies because they are link posts, so their titles remain important analytical text.

We then used Python to prepare consistent text and identifiers while preserving the original data. We decoded HTML characters, normalized whitespace, marked removed or deleted text, and separated line-marked quotations from a participant’s own text where possible. We retained punctuation, negation, slang, and other details that may matter during interpretation. Author names were mapped to stable pseudonyms for the analytical outputs.

We organized the records into a SQLite database and structured tables for posts, comments, threads, and replies. Available parent links were used to reconstruct conversation structure, including reply depth and timing where possible. Missing context remains explicitly marked. This makes the collection easier to search, compare, join, and read without repeatedly processing thousands of raw files.

## What the exploratory analysis showed

We completed an initial exploratory data analysis covering community and monthly coverage, text availability, engagement scores, common words and phrases, thread structure, and reply quality. Five statistical figures accompany the corpus summaries.

The original direct layoff-language screen identified 654 posts and 28,077 comments. Of those comments, 84.90% came from r/cscareerquestions. This suggests that the collected career discussions are an important source of material for the layoff-focused analysis, although uneven coverage prevents treating that percentage as a measure of discussion across Reddit generally.

Engagement scores are strongly skewed: the median score is 1 for both posts and comments, while their means are considerably larger. A small number of highly scored records therefore affect averages substantially. This supports examining distributions and varied examples rather than relying only on average engagement.

To align the work with the broader research purpose, we added keyword-based screens for layoffs, hiring conditions, AI and work, restructuring, economic or policy discussion, and career transitions. These retrieve 177,808 distinct candidate records. Categories overlap, and a keyword match is a retrieval aid rather than proof of relevance, a theme, or a participant’s position. Human reading is needed to assess these candidates.

## How we used network analysis

We prepared two networks: one connecting users through replies and another representing replies within conversations. The author network has been analysed; the conversation network has been exported for later work.

In the author network, each node is a pseudonymous user. A directed edge runs from the person replying to the author of the parent message. Its weight records how many selected replies connect that ordered pair. The replying comments must match the original direct layoff screen; their parent messages do not need to match. Replies with missing parents or unknown authors, self-replies, and invalid cross-thread links were excluded. The network therefore represents retained interactions within a specific subset, rather than all relationships among the collected users.

The network was imported into Gephi to calculate structural measures. We then analysed the exported metrics in Python, checked them against the original edge data, and produced ranked-user tables, group summaries, concentration statistics, and four statistical figures. This makes the network analysis useful beyond its visual layout.

The author network contains 14,507 users, 15,427 directed user pairs, and 15,977 retained replies. Its largest connected component contains 9,330 users, or 64.3% of the network, when arrow direction is ignored. Many other components are small, separate exchanges.

Response attention is unevenly distributed: the top 1% of users receive 17.81% of retained replies. Most directed pairs, 97.1%, represent only one retained reply. Within the largest component, the exported modularity partition identifies 55 structural groups. These results give us candidates for closer examination: prominent recipients, active responders, users occupying connecting positions, and groups whose discussion content can be compared.

These measures require interpretation. Incoming replies may reflect support, disagreement, or criticism. PageRank describes recursive network position, while betweenness describes positions on shortest paths. Neither establishes real-world influence or demonstrated information transmission. Similarly, a detected group is not automatically a shared narrative or identity group. Reading its conversations is necessary to explain its meaning.

## Further observations and what they suggest

### The collection supports several kinds of discussion

Only 0.57% of collected posts and 0.98% of comments match the original direct layoff-language screen. This shows why the collection should be explored before being treated as a fully relevant layoff dataset. Keyword absence does not prove irrelevance: a participant may discuss job insecurity or hiring difficulties without using the word “layoff.” Conversely, a match may be incidental or unrelated to technology employment.

Within the collected comments, direct layoff-language shares differ: 2.48% in r/cscareerquestions, 0.35% in r/programming, and 0.21% in r/technology. These observed differences make community-specific comparisons worth pursuing. They do not yet establish differences in worker experiences, because coverage, selection, and discussion context also differ.

The stored posts largely provide link-based discussion material, while career-question comments offer a separate source of potentially experience-oriented material. A useful later distinction is between personal accounts, discussion of news or company announcements, advice, and general speculation. We have prepared the data to examine these differences, but have not yet assigned those interpretations through coding.

### Conversation context is a major analytical resource and limitation

Around 65.96% of comments connect to a stored submission. In contrast, 99.33% of comment-to-comment replies have their immediate parent comment available. We can therefore often inspect a local exchange even when its opening post is missing. Immediate context and complete conversation context should be treated separately.

Only 929 directly matching comments connect to directly matching stored posts. This demonstrates that selecting matching posts and selecting matching comments yield quite different material. Reading only discussions beneath matching posts would miss much of the explicitly matching language in this collection. Looking only at isolated matching comments would also lose responses and surrounding interpretation. The reading packets help recover the available context for selected examples.

### The broader project has material beyond explicit layoffs

The broader retrieval screens identify the following overlapping candidate pools:

| Candidate facet | Matching records |
|---|---:|
| Hiring conditions | 90,004 |
| AI and work change | 58,658 |
| Layoffs | 28,326 |
| Economic or policy discussion | 18,792 |
| Career transitions | 14,315 |
| Corporate restructuring | 11,396 |

These counts should not be added because the same record can match several facets. The broader layoff screen also differs from the original direct screen in its rules and prepared text fields. The results suggest substantial material for investigating hiring and AI-related employment discussion alongside layoffs. They do not establish which concern dominates participants’ thinking: category breadth and wording affect retrieval counts, and relevance remains unvalidated.

### Receiving attention and contributing responses are distinct roles

Within the retained author network, 5,099 users receive replies without sending a retained reply, 6,022 send without receiving, and 3,386 do both. These correspond to approximately 35.1%, 41.5%, and 23.3% of users. Only nine users appear in both the top-20 recipient and top-20 sender lists.

For example, one pseudonymous user receives 300 replies from 296 distinct users while sending one retained reply. Another sends 89 replies and receives 89, and has the highest exported betweenness score. These provide contrasting cases for reading: a prominent recipient and a participant who combines responding with a connecting position. We cannot tell from the numbers whether either user is supportive, controversial, knowledgeable, or discussing their own employment experience.

The top 20 recipients account for 7.32% of retained replies, while the top 20 senders contribute 4.89%. This describes how response attention and response activity are distributed. It also suggests that a qualitative sample should include ordinary participants alongside prominent users, so that highly visible conversations do not become the only evidence considered.

### Structural connection is more common than mutual exchange

There are 2,199 weak components, including 1,771 two-user components. The largest strongly connected component contains 1,210 users, or 8.3% of all users. Unlike weak connectivity, strong connectivity requires directed paths in both directions. A large weak component therefore does not mean that all its participants engage in mutually reachable exchanges.

There are 859 unordered user pairs with retained replies in both directions, representing 5.90% of connected unordered pairs. Only 18 directed pairs recur across multiple threads. These findings describe sparse repeated and mutual responding in this selected network. They cannot establish the absence of relationships elsewhere, because keyword selection and exclusions remove some exchanges. Nor do paths establish information diffusion: an aggregate path can combine replies from unrelated threads and times.

### Detected groups need content-based interpretation

The full export contains 2,253 modularity classes, but only 55 occur within the main connected component. Each of the other 2,198 weak components corresponds to one class. Much of the full class count therefore reflects disconnected exchanges rather than thousands of substantive communities.

Within the main component, 82.8% of retained replies connect users assigned to the same group. This describes the detected partition, whose algorithm seeks dense internal connections; it is not an independent validation of meaningful social groups. The largest group contains 412 users, or 4.42% of the main component. Reading across several groups could test whether differences correspond to discussion topics, particular threads, community participation, or recurring interpretations.

### Network rankings should be used together

Received-reply counts and PageRank have a strong rank correlation of 0.935, but their top-20 lists overlap on only 16 users. The second-highest PageRank user receives just two retained replies. This illustrates how recursive network position can differ from the volume of attention received.

Betweenness and received-reply rankings overlap on nine of their top 20 users, offering another set of contrasting cases. Closeness needs particular care here: 4,110 users have an exported score of 1, and 3,566 of those reach just one immediate outgoing neighbor with no outgoing connections of its own. A maximum score can therefore describe very limited reach. Selecting one metric as a universal measure of importance would obscure these differences.

## What these results contribute to the research

The main contribution so far is an evidence-based way to move from a large collection toward focused questions and readable cases. Coverage analysis tells us which periods and communities can be compared. Text and context audits tell us which records can support interpretation. Retrieval screens identify candidate material. Network analysis identifies different participation roles and structural groups to examine alongside that material.

For the preliminary evaluation, we can demonstrate a complete path from raw Reddit files to structured records, descriptive results, importable networks, and analysed Gephi metrics. Five corpus figures and four network-statistics figures make those results presentable. The tables preserve the numerical evidence behind the figures, while scripts and validation checks support reproduction. These nine figures are analytical plots; the manually arranged Gephi network image is a separate illustration.

The substantive questions now become more focused: What kinds of contributions attract responses? Do active responders provide advice or contest explanations? Do structural groups contain different accounts of employment disruption? How do ordinary participants’ experiences compare with highly visible discussions? These are motivated by the completed analysis and remain questions for qualitative investigation.

## Where the project stands

We have completed data preparation, corpus exploration, network construction, and preliminary author-network analysis. We now have reproducible Python scripts, structured data, statistical summaries, figures, Gephi-compatible exports, and documented processing decisions.

We also prepared a varied 200-record reading sample with available conversation context and a coding framework for relevance, experiences, explanations, expectations, emotions, and response functions. Human coding has not yet been completed, and the separate qualitative pilot is currently set aside. Consequently, we have not yet established substantive narrative or support-related findings.

The next stage is to connect the structural results to the actual discussion content: read selected conversations, assess relevance, refine qualitative categories, and compare examples from different network positions and groups. Later comparisons over time or against external events must account for the collection’s uneven coverage. Our current results establish a practical foundation for that work and demonstrate what the data can support at the preliminary stage.
