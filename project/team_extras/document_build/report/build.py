import sys
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

IMG = sys.argv[1]
OUT = sys.argv[2]

d = Document()
sec = d.sections[0]
sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)
for s in ("left_margin", "right_margin"):
    setattr(sec, s, Inches(0.9))
sec.top_margin = sec.bottom_margin = Inches(0.85)

st = d.styles["Normal"]
st.font.name = "Calibri"
st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st.paragraph_format.space_after = Pt(5)
st.paragraph_format.line_spacing = 1.1
for lvl, size in ((1, 14), (2, 11.5)):
    h = d.styles[f"Heading {lvl}"]
    h.font.name = "Calibri"
    h.font.size = Pt(size)
    h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    h.element.rPr.rFonts.set(qn("w:asciiTheme"), "") if False else None

fig_no = [0]
tab_no = [0]


def P(text, bold_lead=None, italic=False, size=None, align=None, after=None):
    p = d.add_paragraph()
    if bold_lead:
        r = p.add_run(bold_lead)
        r.bold = True
        if size:
            r.font.size = Pt(size)
    r = p.add_run(text)
    r.italic = italic
    if size:
        r.font.size = Pt(size)
    if align:
        p.alignment = align
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    return p


def B(text, lead=None):
    p = d.add_paragraph(style="List Bullet")
    if lead:
        p.add_run(lead).bold = True
    p.add_run(text)
    p.paragraph_format.space_after = Pt(2)
    return p


def H(text, lvl=1):
    return d.add_heading(text, level=lvl)


def FIG(name, caption, width=6.4):
    fig_no[0] += 1
    p = d.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(f"{IMG}/{name}.png", width=Inches(width))
    c = d.add_paragraph()
    r = c.add_run(f"Figure {fig_no[0]}. ")
    r.bold = True
    r.font.size = Pt(8.5)
    r2 = c.add_run(caption)
    r2.font.size = Pt(8.5)
    r2.italic = True
    c.paragraph_format.space_after = Pt(8)


def shade(cell, hexcol):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), hexcol)
    tcPr.append(sh)


def TABLE(header, rows, widths, caption, size=8.5):
    tab_no[0] += 1
    c = d.add_paragraph()
    r = c.add_run(f"Table {tab_no[0]}. ")
    r.bold = True
    r.font.size = Pt(8.5)
    r2 = c.add_run(caption)
    r2.font.size = Pt(8.5)
    r2.italic = True
    c.paragraph_format.keep_with_next = True
    c.paragraph_format.space_after = Pt(2)
    t = d.add_table(rows=1 + len(rows), cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, row in enumerate([header] + rows):
        for j, val in enumerate(row):
            cell = t.rows[i].cells[j]
            cell.width = Inches(widths[j])
            cell.text = ""
            para = cell.paragraphs[0]
            para.paragraph_format.space_after = Pt(0)
            para.paragraph_format.line_spacing = 1.0
            run = para.add_run(str(val))
            run.font.size = Pt(size)
            if i == 0:
                run.bold = True
                shade(cell, "DCE6F0")
    for j, w in enumerate(widths):
        t.columns[j].width = Inches(w)
    grid = t._tbl.tblGrid
    for j, gc in enumerate(grid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(widths[j] * 1440)))
    tblPr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    if tab_no[0] in (2, 9):
        for ri, row in enumerate(t.rows):
            row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            if ri < len(t.rows) - 1:
                for cell in row.cells:
                    for pp in cell.paragraphs:
                        pp.paragraph_format.keep_with_next = True
    d.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


# ---------------- Title page ----------------
for _ in range(5):
    d.add_paragraph()
P("COMPUTATIONAL SOCIAL MEDIA ANALYSIS (CSE3729)", size=12, align=WD_ALIGN_PARAGRAPH.CENTER)
t = d.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("Solidarity or Blame")
r.bold = True
r.font.size = Pt(28)
r.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
P("How Reddit communities discuss disruption in technology employment", size=15, align=WD_ALIGN_PARAGRAPH.CENTER)
d.add_paragraph()
P("Final Project Report", size=13, align=WD_ALIGN_PARAGRAPH.CENTER)
P("Semester 7, Academic Year 2026-27, BMU", size=11, align=WD_ALIGN_PARAGRAPH.CENTER)
P("Faculty: Dr. Kiran Sharma and Dr. Jakob Baek Kristensen", size=11, align=WD_ALIGN_PARAGRAPH.CENTER)
d.add_paragraph()
P("Team: Vanshit Ahuja, Vaibhav Jain, Tanya, Krish, Dividh Vijay", size=12, align=WD_ALIGN_PARAGRAPH.CENTER)
P("27 November 2026", size=11, align=WD_ALIGN_PARAGRAPH.CENTER)
d.add_paragraph()
P("Status of the evidence: all labels in this report come from transparent keyword rules whose precision has been checked "
  "provisionally in an AI-assisted reading (Claude), not by a person. A human check with two independent coders (240 rows) is prepared but has not been completed. "
  "Results are therefore reported as \"Supported\" or \"Lead\", never as \"Findings\".",
  italic=True, size=9.5, align=WD_ALIGN_PARAGRAPH.CENTER)
d.add_page_break()

# ---------------- Abstract ----------------
H("Abstract")
P("We study how three Reddit communities talk about disruption in technology employment: layoffs, hiring conditions, AI and work, "
  "restructuring, economic policy and career change. The corpus has 2,974,250 records (115,213 posts and 2,859,037 comments) from "
  "r/cscareerquestions (cscq), r/technology and r/programming, January 2025 to September 2026, collected with the Arctic Shift API. "
  "Because collection coverage is uneven, cross-community comparisons use the shared window January-June 2025 and trends over time use cscq only. "
  "Layoff talk is far more common in cscq than in r/technology (2.45% vs 0.20% of non-bot comments, January-June 2025) and is ambient rather than "
  "event-driven (weekly coefficient of variation 0.21 vs 0.45). When the same ~160 authors write in both communities, their rate of executive MENTIONS "
  "converges (6.6% vs 5.8%) while AI talk still differs by 9.4 points: who gets blamed travels with the person, topics are shaped by the community. "
  "In cscq replies, a personal layoff story draws sympathy 2.82 times as often as an unmarked comment (5.11% vs 1.82%, 91,229 reply pairs), whereas "
  "blame topics draw less sympathy (x0.77-0.81) and no extra agreement. In the reply network, blame-talkers reply to each other 1.69 times more "
  "than chance (z = 8) with more challenge, consistent with an affective, antagonistic echo chamber, but network communities are not sorted by author type. "
  "Solidarity follows disclosure, not a shared enemy. All labels are keyword rules with provisional precision; a two-coder human check is pending, "
  "so the results are labelled Supported, and none is causal or population-level.")

# ---------------- 1 Introduction ----------------
H("1 Introduction")
P("Technology layoffs, slower hiring, generative AI and offshoring are discussed online by people who are directly affected and by people who follow "
  "the industry as news. Whether such talk builds solidarity (support for the people affected) or turns into blame (anger at executives, foreign workers "
  "or AI) matters for moderators, career services and researchers who read online discussion as a signal of worker sentiment. A career-advice forum and "
  "a general technology forum have different purposes and audiences, so the same event may be framed very differently. The project therefore compares "
  "communities before it draws any conclusion about reactions to disruption.")
P("Research questions.", bold_lead=None)
B(" Where does employment-disruption talk live, and is it ambient or event-driven?", "RQ1.")
B(" How do communities frame it: personal experience, evidence, explanations and targets of blame?", "RQ2.")
B(" How do replies respond to stories, doom and blame, and how is the reply network structured?", "RQ3.")
P("Hypotheses.")
B(" Employment-disruption language differs between r/cscareerquestions and r/technology in the same observation window.", "H1 (community concentration).")
B(" Career discussion contains more worker-centred support and experience narratives; technology discussion has more news and industry framing.", "H2 (discourse function).")
B(" Validated solidarity and blame labels are associated with different reply and engagement patterns.", "H3 (reply structure).")
P("The midterm (6 October 2026) gave preliminary support to H1 only. This final report tests H1-H3, adds three directions (D1-D3) and a network analysis (R4), "
  "and states the robustness and limits of every result (R5).")

# ---------------- 2 Literature ----------------
H("2 Literature review")
P("The midterm reviewed fifteen studies. Table 1 condenses them and states what this project takes from each. Three substantive studies frame the question: "
  "Bose (2026) found an attention gap in AI-layoff discourse on X that did not replicate on Reddit; Ton (2025) found displacement fear and adaptation side by side "
  "in profession subreddits; Yin, Wong and Reddy (2025) showed that Reddit users seek different kinds of support and can receive mismatched replies. "
  "Labour-economics work (Acemoglu and Restrepo, 2020; Eloundou et al., 2024; Brynjolfsson et al., 2025) warns that exposure, productivity and job loss are different things, "
  "so AI talk must not be read as evidence of displacement. Methods work supports a staged, transparent design: lexicons such as VADER measure sentiment, not the target of "
  "support or blame (Hutto and Gilbert, 2014); contextual models (Devlin et al., 2019; Reimers and Gurevych, 2019) and topic models (Blei et al., 2003; Grootendorst, 2022) "
  "need validated labels. Network studies (Notarmuzi et al., 2022; Kristensen et al., 2023) caution that an edge records contact, not agreement. Reagle (2022) shows that "
  "quoted Reddit text can be traced back to users.")
lit = [
    ["Bose, AI layoff discourse", "2026", "763 X posts; 647 Reddit posts", "Capital-side posts amplified on X, not on Reddit", "Control platform/community context; audit keywords"],
    ["Yin, Wong and Reddy, Reddit support", "2025", "Interviews, 16 Reddit users", "Users seek several support types; replies can mismatch", "Code response function (emotional vs informational support)"],
    ["Ton, AI as a threat", "2025", "72 profession subreddits, 2009-2024", "Threat, adaptation and productivity narratives coexist", "Compare communities; separate narratives"],
    ["Naing and Udomwong, ChatGPT opinions", "2024", "202,905 Reddit comments", "Job-market concern among mixed views", "Topic and sentiment as baselines only"],
    ["Brynjolfsson et al., Generative AI at work", "2025", "5,179 support agents, one firm", "Productivity up about 14% on average", "Keep opportunity narratives in the frame"],
    ["Eloundou et al., GPTs are GPTs", "2024", "O*NET tasks, human and GPT-4 ratings", "80% of workers have >=10% task exposure", "Separate AI/work facet; exposure is not job loss"],
    ["Acemoglu and Restrepo, Robots and jobs", "2020", "US local labour markets, 1990-2007", "Robot exposure reduced jobs and wages", "Separate automation from other explanations"],
    ["Hutto and Gilbert, VADER", "2014", "Human-rated social-media text", "Interpretable sentiment baseline", "Test sentiment vs stance (Section 5.6)"],
    ["Devlin et al., BERT", "2019", "BooksCorpus, Wikipedia, 11 tasks", "Context improves NLP tasks", "Fine-tune only after a validated codebook"],
    ["Reimers and Gurevych, Sentence-BERT", "2019", "Similarity / inference datasets", "Efficient semantic comparison", "Sampling and theme exploration"],
    ["Blei et al., LDA", "2003", "Benchmark corpora", "Documents as topic mixtures", "Interpretable topic baseline"],
    ["Grootendorst, BERTopic", "2022", "Benchmark corpora", "Coherent embedding-based topics", "Stability check against LDA"],
    ["Notarmuzi et al., propagation", "2022", "~1 billion events, 3 platforms", "Shared cascade scaling", "Separate reach from meaning"],
    ["Kristensen et al., partisan boundaries", "2023", "30 million posts, 8 platforms", "Boundaries persisted; heterophily rose slightly", "Edges are contact, not agreement"],
    ["Reagle, disguising Reddit sources", "2022", "22 studies; 10 author interviews", "Quoted Reddit text often traceable", "No usernames or record-level quotes"],
]
TABLE(["Study", "Year", "Data", "Main result", "What this project adopts"], lit, [1.55, 0.4, 1.4, 1.6, 1.55],
      "Literature reviewed (condensed from the midterm Table 1). Year = publication year.", size=8)
P("Gap and novelty. ", bold_lead=None)
d.paragraphs[-1].runs[0].bold = True
d.paragraphs[-1].add_run(
    "No study we reviewed compares career and technology communities on Reddit in a shared time window and joins the framing of "
    "disruption to how replies respond to it. This project adds (i) a shared-window, non-bot denominator comparison across three communities; "
    "(ii) a same-author test (D1) that separates what a person brings from what a community shapes; (iii) a reply-level test of which kinds of "
    "disclosure draw emotional vs informational support, following Yin et al. (2025); and (iv) a reply network profiled by author type and analysed "
    "in both Gephi and networkx, read as contact rather than agreement (Kristensen et al., 2023). Its open limit is the human validation of labels, "
    "which is prepared (240 rows, two coders) but not yet done.")

# ---------------- 3 Data ----------------
H("3 Data and collection")
P("Source and provenance. Posts and comments were downloaded through the Arctic Shift API (endpoints posts/search and comments/search) on 23-24 September 2026. "
  "The collector took full subreddit pulls with no search term; keyword screening was applied afterwards. Seven subreddits were configured, but only three were "
  "collected (r/cscareerquestions, r/technology, r/programming). The uneven end dates are a collection-run artefact: the collector stops silently on API errors, "
  "or the run was interrupted (collection/PROVENANCE.md). Raw JSON is kept unchanged in 29,821 batch files.")
TABLE(["Community", "Comments (count)", "Comment coverage", "Posts (count)"], [
    ["r/cscareerquestions", "962,337", "1 Jan 2025 - 23 Sep 2026", "0"],
    ["r/technology", "1,657,900", "to 9 Jun 2025", "76,782"],
    ["r/programming", "238,800", "to 12 Dec 2025", "38,431"],
    ["Total", "2,859,037", "", "115,213"],
], [1.7, 1.4, 2.0, 1.2], "Collected corpus by community (counts of records). 2,974,250 records in total.")
P("Consequences for design. Because coverage differs, every cross-community comparison uses the shared window January-June 2025, and every trend over "
  "time uses cscq only. 94.61% of comment text is usable (the rest is removed or deleted). Six employment screens retrieve 177,808 candidate records.")
FIG("f_cov", "Collected posts (top) and comments (bottom) per month by community. Absent months are gaps, not zeros: r/technology comments stop in June 2025 "
    "and r/programming comments in December 2025, and cscq has comments only. Source: outputs/04_analysis/figures/01_monthly_coverage.png.", 5.2)
P("Ethics. The data are public Reddit content collected through a public archive. We report aggregates only, publish no usernames, use pseudonymous author keys "
  "for structural analysis, and do not infer occupation, location or employment status of any user (Reagle, 2022). Results describe public online discussion "
  "in three communities, not technology workers in general.")

# ---------------- 4 Methods ----------------
H("4 Methods")
H("4.1 Preprocessing", 2)
P("Whitespace and HTML entities were normalised, line-prefixed quotations and URLs were separated from each comment's own text, removed/deleted states were kept "
  "explicit, and threads and immediate reply edges were reconstructed. Known bot accounts are excluded from denominators (the \"non-bot denominator\").")
H("4.2 Screens and markers", 2)
P("Six versioned keyword screens retrieve employment-disruption candidates: layoffs, hiring conditions, AI and work, restructuring, economic policy and career "
  "transition. Inside employment comments, marker rules tag functions and topics: own layoff story (experience), doom, advice, sympathy, agreement, challenge, "
  "and blame topics (mentions of executives, offshoring, AI as an excuse, blaming workers). A stance model is used as a second view of agreement. "
  "These are keyword rules, not validated classifiers; their provisional precision is in Section 6.")
H("4.3 Interpretation routine", 2)
P("Every number passes through the project's interpretation routine (docs/INTERPRETATION_ROUTINE.md): state the claim, list the boring explanations "
  "(denominator, coverage, bots, thread size, text length, label noise), test their predictions, and look for an independent measure. A result is a Lead "
  "(one number, no checks), Supported (survives the boring explanations plus one independent measure) or a Finding (convergence across three or more "
  "measures and human-checked labels). Because the human check is pending, nothing in this report is a Finding.")
H("4.4 Statistics", 2)
P("Shares use community-window denominators. Lift is the rate of a reply type after a marked comment divided by its rate after unmarked comments. "
  "Confidence intervals use a thread-clustered bootstrap (threads are resampled, because replies in one thread are not independent). Weekly variability is the "
  "coefficient of variation (CV) of weekly shares. Network mixing is compared with a within-thread null (reply targets shuffled inside threads).")
H("4.5 Network analysis", 2)
P("The cscq reply graph (January-June 2025) has directed edges from the replying author to the parent author, weighted by reply count. networkx computes "
  "components, centrality, Louvain communities, mixing by author type and k-means profiles. Gephi (Gephi Toolkit 0.11.4, run headless; projects open in Gephi "
  "Desktop 0.11.3) computes weighted modularity (resolution 1.0) and ForceAtlas2 layouts for four networks: the October author network (built from selected "
  "layoff-matching comments), the R4 profiled subgraph, the 12-node type network and the conversation network.")
H("4.6 Tableau", 2)
P("A packaged workbook (tableau/CSMA_Solidarity_or_Blame.twbx) holds 11 worksheets, 4 dashboards (Where disruption talk lives; How communities frame it; "
  "Who replies to whom; Can we trust the numbers) and 1 story. It was opened in Tableau Desktop 2026.3 and all four story points match the expected values "
  "(tableau/EXPECTED_VALUES.md). Figures 2, 3 and 8 are crops of these dashboards.")

# ---------------- 5 Results ----------------
H("5 Results")
H("5.1 R1: where disruption talk lives (H1, Supported)", 2)
TABLE(["Measure (Jan-Jun 2025)", "cscq", "r/technology", "r/programming"], [
    ["Layoff share of non-bot comments (%)", "2.45", "0.20", "0.32"],
    ["Layoff share inside threads that mention layoffs (%)", "4.06", "0.49", "-"],
    ["Large threads containing layoff talk (%)", "67", "21", "-"],
    ["Weekly variability of layoff share (CV, unitless)", "0.21", "0.45", "0.76"],
], [3.0, 1.0, 1.1, 1.1], "R1 measures. Shares in percent of comments or threads; CV = standard deviation / mean of weekly shares. \"-\" = not reported.")
P("Layoff talk is far more concentrated in cscq, and the gap holds inside layoff threads and in threads of every size. Its low weekly variability shows that layoffs "
  "are ambient in cscq and event-driven in r/technology. The midterm's January-May window gave 2.32% vs 0.20% (11.36x). The hiring screen's large ratio is not "
  "quoted because that screen's precision is only about 22%.")
FIG("f_d1", "Tableau dashboard 1, \"Where disruption talk lives\". Left: weekly layoff share by community, January-June 2025, and collected records per week "
    "(coverage). Right: share of threads with layoff talk by thread size. Keyword markers; labels not yet human-checked.")
H("5.2 R2: how communities frame it (H2, Supported, then narrowed)", 2)
P("Own layoff stories are 8.9% of layoff comments in cscq vs 3.1% in r/technology. Evidence cultures differ: cscq links labour statistics (FRED, BLS), "
  "r/technology links news, r/programming talks about craft. H2 was then narrowed by D1, a same-author test: among the ~152-160 authors who write in both "
  "cscq and r/technology, executive mentions are 6.6% vs 5.8% (the community gap disappears), while AI talk still differs by +9.4 points. "
  "Who gets blamed comes with the person; which topics are discussed is shaped by the community.")
FIG("f_d2", "Tableau dashboard 2, \"How communities frame it\". Left: topic-marker rates per community (employment comments, January-June 2025). Right: the same-author D1 panel. "
    "The D1 panel shows a dashboard variant (152 authors, career-transition-only comments excluded: executive mentions 6.1% vs 6.0%); the text quotes the 160-author version.")
H("5.3 R3: how replies respond (H3, Supported)", 2)
TABLE(["Comment type", "Reply outcome", "Rate or lift", "Scope"], [
    ["Personal layoff story", "Sympathy reply (%)", "5.11 vs 1.82 unmarked (x2.82)", "cscq, Jan 2025-Sep 2026, 91,229 reply pairs"],
    ["Personal layoff story", "Sympathy reply (%)", "4.42 vs 1.93 (x2.29)", "cscq, Jan-Jun 2025"],
    ["Personal layoff story", "Advice reply", "no rise", "cscq"],
    ["Doom", "Advice reply (lift)", "x1.38", "cscq"],
    ["Blame topics (executives, offshoring, AI-as-excuse)", "Sympathy reply (lift)", "x0.77-0.81", "cscq"],
    ["Blame topics", "Agreement (stance model lift)", "x0.92-1.19 (no extra agreement)", "cscq"],
], [1.8, 1.4, 1.6, 1.7], "R3 reply outcomes on 134,749 cscq employment comments. Lift = rate after the comment type / rate after unmarked comments.")
P("A personal layoff story draws sympathy nearly three times as often as an unmarked comment, but not more advice; doom draws advice. Blame topics draw less "
  "sympathy and no extra agreement. The effect holds within a text-length band and with thread-clustered confidence intervals. In the terms of Yin et al. (2025), "
  "disclosure draws emotional support and worry draws informational support. Solidarity follows disclosure, not a shared enemy. Even so, about 95% of replies "
  "to stories are not sympathetic.")
FIG("f_mix", "Left: who replies to whom in the cscq reply network (lift vs random mixing; blame-talker to blame-talker = 1.69). Middle and right: sympathy and "
    "challenge share of each replier-parent cell relative to the overall share. Author types are rule-based. Source: outputs/15_network/fig_mixing_lift.png.")
H("5.4 R4: the reply network (Supported unless marked Lead)", 2)
P("The cscq reply graph for January-June 2025 has a largest connected component of 30,976 authors and 162,024 replies.")
B(" Network position follows activity, not role: differences between author types shrink once activity is held equal.", "N1.")
B(" Story-sharers receive 1.6-1.9x more sympathy (Lead).", "N2.")
B(" Blame-talkers reply to each other 1.69x more than chance (z = 8, within-thread null). Challenge is higher (7.2% vs 4.5%); agreement is not. "
  "This is consistent with an affective, antagonistic echo chamber.", "N3.")
B(" Louvain modularity Q = 0.43; the 59 communities are not sorted by author type (NMI about 0.005).", "N4.")
B(" k-means on behaviour profiles finds no separate helper cluster (ARI 0.14).", "N5.")
P("Attention is concentrated: the top 1% of users receive 17.8% of replies, and 97% of pairs exchange a single reply. Gephi gives a consistent picture on two further "
  "networks (Table 5): the October author network is highly modular (Q = 0.813, 83.0% of retained replies stay within a group), whereas the profiled R4 core is "
  "only modestly modular (Q = 0.2723) and its large classes keep a type mix close to the overall one.")
TABLE(["Gephi network", "Nodes (count)", "Edges (count)", "Structure"], [
    ["October author network", "14,507", "15,427 (weight 15,977)", "2,199 weak components; largest 9,330 users (64.31%); 1,771 two-user components; Q = 0.813, 66 groups, largest 361 (3.87%)"],
    ["R4 profiled subgraph", "10,778", "91,657", "Q = 0.2723, 81 classes; type mix close to overall in big classes"],
    ["Type network", "12", "32", "Edge weight = lift"],
    ["Conversation network", "13,866", "13,206", "660 weak components; largest 2,190"],
], [1.5, 0.9, 1.3, 2.8], "Gephi networks (Gephi Toolkit 0.11.4, weighted modularity, resolution 1.0).")
FIG("f_types", "Gephi: cscq reply network, January-June 2025, 10,778 profiled authors and 91,657 directed pairs. Colour = rule-based author type; size = PageRank; "
    "ForceAtlas2 layout. Typed authors are not in separate regions (N1, N4). Positions have no geographic or temporal meaning.", 5.6)
FIG("f_comm", "Gephi: largest weak component of the October layoff-related author reply network (9,330 users, 12,360 directed pairs). Colour = modularity group "
    "(weighted, resolution 1.0; 66 groups, Q = 0.813); size = replies received.", 5.6)
H("5.5 Directions D1-D3", 2)
B(" Same authors, two communities: executive mentions 6.6% vs 5.8%, AI talk +9.4 points (Section 5.2). Supported.", "D1.")
B(" Newcomers who receive any reply come back more often: 50% vs 39%. This is a Lead, not a causal effect; no figure is included.", "D2.")
B(" After the H-1B announcement on 19 September 2025, offshoring talk in cscq went from about 13% to 43% for one week, then fell below its earlier level. "
  "A shock, not a shift.", "D3.")
FIG("f_h1b", "D3: daily H-1B mentions per 1,000 cscq comments, August-October 2025 (the 19 September proclamation is the spike). This plots mentions per 1,000 "
    "comments; the 13% to 43% offshoring share quoted in the text is a separate weekly measure. Source: outputs/09_leads/figures/lead4_daily_h1b.png.", 5.6)
H("5.6 Other results", 2)
B(" \"AI as an excuse\" did not grow over time; the apparent rise was a denominator effect.", "No AI-excuse trend.")
B(" Sentiment separates story comments from blame comments only at 0.50, which is chance. Sentiment tools cannot measure blame.", "Sentiment is not stance.")
B(" Polarisation cannot be measured with the current labels.", "Polarisation.")

# ---------------- 6 Validity ----------------
H("6 Validity and limitations")
TABLE(["Screen or marker", "Provisional precision (%, AI-assisted check)"], [
    ["Layoffs screen", "95"], ["Restructuring", "75"], ["Economic policy", "70"], ["AI / work", "26.7"], ["Hiring", "22.5"], ["Career transition", "15"],
    ["Experience marker on layoff comments", "39 of 40 (about 11 of 20 overall)"],
    ["ai_replaces endorses replacement", "7 of 30"], ["Offshore blames foreign workers", "7 of 70"], ["Agree marker", "over-fires (replies starting with \"This\")"],
], [3.2, 2.6], "Provisional precision from a single reader (20-40 rows per screen; up to 70 per marker). Not a human-validated estimate.")
P("Robustness (R5). Every result above is robust to the bot denominator, the shared window, thread clustering, text-length bands, a label-noise simulation, "
  "activity thresholds and megathread removal (outputs/16_tableau/r5_robustness_long.csv). The blame-talker mixing lift, for example, stays above 1 in every variant (Figure 8).")
FIG("f_d4", "Tableau dashboard 4, \"Can we trust the numbers\": coverage by community, provisional precision per screen (AI-assisted check, n = 20-40 per screen) and "
    "the R5 robustness check for the blame-talker mixing lift across label noise, megathread removal and activity thresholds.")
P("Limitations.")
B(" The labels are keyword rules with provisional precision from an AI-assisted check (Claude), not yet human-validated. A human check with two independent coders is prepared (docs/HUMAN_CHECK_GUIDE.md, "
  "240 rows) but pending. Until it is done, no result is a Finding, and the weak screens (AI/work, hiring, career transition) are not used for headline claims.", "Labels.")
B(" Three of seven configured subreddits, comments only for cscq, uneven end dates. Results describe these communities in January 2025-September 2026.", "Coverage.")
B(" All results are associations. Nothing here shows that a story causes sympathy or that a reply causes a newcomer to return.", "No causal or population claims.")
B(" The agree marker over-fires, so agreement claims rest on the stance model, and we make no claim that blame draws agreement.", "Agreement.")

# ---------------- 7 Applications ----------------
H("7 Applications and use cases")
P("These follow from the results but have not been tested with moderators or community members.")
TABLE(["Use case", "Result it rests on"], [
    ["Route first-person layoff stories to people trained to reply with care; about 95% of replies to stories are not sympathetic.", "R3: stories draw sympathy x2.82"],
    ["Answer worry with information: a helpful reply to doom is practical advice, not only reassurance.", "R3: doom draws advice x1.38"],
    ["Measure blame with stance, not with topic keywords or sentiment scores.", "7 of 70 offshore mentions blame workers; sentiment separates stories from blame at 0.50"],
    ["Offer continuous support in career communities, not only after news events.", "R1: layoff talk is ambient in cscq (CV 0.21)"],
    ["Watch where blame threads turn into arguments if a community wants to stay supportive.", "R3 less sympathy for blame; N3 blame-talkers cluster with more challenge"],
], [3.9, 2.6], "Applications suggested by the results (not evaluated).")

# ---------------- 8 Conclusion ----------------
H("8 Conclusion and future work")
P("Across three Reddit communities, employment disruption is ambient talk in the career community and event-driven news in the general technology community (H1). "
  "Communities shape topics, while the targets of blame travel with the person (H2, narrowed by D1). In replies, solidarity follows personal disclosure rather "
  "than a shared enemy: stories draw sympathy, doom draws advice, and blame draws less support, no extra agreement and, in the network, a cluster of "
  "blame-talkers who challenge each other (H3, R4). These results are Supported, robust to seven checks, and bounded by keyword labels whose human validation "
  "is still pending.")
P("Future work: (1) complete the two-coder human check and report precision per label; (2) re-run R1-R4 on validated labels and fine-tune a stance model only after "
  "that; (3) the team decided not to collect more data, so every claim is limited to the collected corpus; a future study would need complete r/technology and r/programming coverage and the four missing subreddits; (4) test D2 with a design that can separate "
  "cause from selection; (5) measure polarisation once stance labels are validated.")

# ---------------- Contributions ----------------
H("Contribution of each team member")
TABLE(["Member", "Documented role (docs/PROJECT_REFERENCE.md section 4; deliverables/MIDTERM_HANDOFF.md)"], [
    ["Vanshit Ahuja", "Research framing, hypotheses, shared-window comparison, statistics, literature review, report and slides, QA"],
    ["Vaibhav Jain", "Reddit data collection (Arctic Shift), provenance, coverage checks"],
    ["Tanya", "Data cleaning, thread linkage, descriptive analysis, community comparison, figures"],
    ["Krish", "Lexical and stance baselines, reading sample, coding framework, NLP evaluation"],
    ["Dividh Vijay", "All Gephi and network work (exports, edge direction, weights, scope, validation) and the reply-structure part of H3"],
], [1.4, 5.1], "Team roles as recorded in the project documents.")

# ---------------- References ----------------
H("References")
refs = [
    "Acemoglu, D., & Restrepo, P. (2020). Robots and jobs: Evidence from US labor markets. Journal of Political Economy, 128(6), 2188-2244.",
    "Blei, D. M., Ng, A. Y., & Jordan, M. I. (2003). Latent Dirichlet allocation. Journal of Machine Learning Research, 3, 993-1022.",
    "Bose, J. (2026). Attention asymmetry in AI layoff discourse on X: A computational analysis of capital vs labour amplification. arXiv:2605.29367.",
    "Brynjolfsson, E., Li, D., & Raymond, L. R. (2025). Generative AI at work. Quarterly Journal of Economics, 140(2), 889-942.",
    "Devlin, J., Chang, M.-W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers for language understanding. NAACL-HLT.",
    "Eloundou, T., Manning, S., Mishkin, P., & Rock, D. (2024). GPTs are GPTs: Labor market impact potential of LLMs. Science, 384(6702), 1306-1308.",
    "Grootendorst, M. (2022). BERTopic: Neural topic modeling with a class-based TF-IDF procedure. arXiv:2203.05794.",
    "Hutto, C. J., & Gilbert, E. (2014). VADER: A parsimonious rule-based model for sentiment analysis of social media text. ICWSM, 8(1), 216-225.",
    "Kristensen, J. B., Henriksen, F. M., & Mayerhöffer, E. (2023). Did COVID-19 blur partisan boundaries? Social Media + Society, 9(3).",
    "Naing, S. Z. S., & Udomwong, P. (2024). Public opinions on ChatGPT: An analysis of Reddit discussions by using sentiment analysis, topic modeling, and SWOT analysis. Data Intelligence, 6(2), 349-380.",
    "Notarmuzi, D., Castellano, C., Flammini, A., Mazzilli, D., & Radicchi, F. (2022). Universality, criticality and complexity of information propagation in social media. Nature Communications, 13, 1308.",
    "Reagle, J. (2022). Disguising Reddit sources and the efficacy of ethical research. Ethics and Information Technology, 24, 41.",
    "Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. EMNLP-IJCNLP.",
    "Ton, N. T. D. (2025). AI as a threat? Evidence from Reddit. APSA Preprints.",
    "Yin, J. Y., Wong, N., & Reddy, M. C. (2025). Understanding user experience of support-seeking on Reddit during stressful times. Proceedings of the ACM on Human-Computer Interaction.",
]
for i, r_ in enumerate(refs, 1):
    p = P(f"{i}. {r_}", size=9, after=2)

# ---------------- Appendix ----------------
H("Appendix A: Reproducibility")
TABLE(["Folder", "Contents"], [
    ["collection/", "Arctic Shift collector and PROVENANCE.md (what was collected, when, and why coverage is uneven)"],
    ["scripts/", "Pipeline: profile, preprocess, screen, tables, analysis, sample, Gephi export, explore_* analyses"],
    ["outputs/", "Numbered outputs: 04_analysis (EDA), 09_leads, 11_dynamics, 12_replies (H3), 14_directions (D1-D3), 15_network (R4), 16_tableau (extracts, R5), 17_sentiment_stance"],
    ["gephi/", "Exports, Gephi projects, analysis_notes.md, slide-ready figures"],
    ["tableau/", "CSMA_Solidarity_or_Blame.twbx, its generator and EXPECTED_VALUES.md"],
    ["docs/", "PROJECT_REFERENCE.md, INTERPRETATION_ROUTINE.md, HUMAN_CHECK_GUIDE.md, RUNNING.md"],
    ["annotations/human_check/", "Coder templates for the pending two-coder check (240 rows)"],
], [1.7, 4.8], "Folder map of the project archive.")
P("Environment. Python 3.12; packages are pinned in requirements.txt (numpy 1.26.4, pandas 2.2.3, networkx 3.3, scipy 1.13.1, scikit-learn 1.5.1, "
  "matplotlib 3.9.2, vaderSentiment 3.3.2; optional torch and transformers for the text models). Install with: python3 -m venv venv, activate it, then "
  "pip install -r requirements.txt.")
P("Commands (docs/RUNNING.md). From the project root: python scripts/run_pipeline.py runs the pipeline; python scripts/run_pipeline.py --stages analysis gephi "
  "runs selected stages; python scripts/run_pipeline.py --stages screen sample rebuilds the screens and reading sample. The review ZIP omits raw JSON and the working "
  "database, so a full rebuild needs the original collection in raw/YYYY-MM/; results, Gephi CSVs and unit tests can be used without it.")

d.save(OUT)
print("saved", OUT)
