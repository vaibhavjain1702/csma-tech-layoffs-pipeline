import os
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

from pathlib import Path
# project root = four levels up from this file (team_extras/document_build/deck/build.py); override with CSMA_ARCH
ARCH = os.environ.get("CSMA_ARCH", str(Path(__file__).resolve().parents[3]))
OUT = os.environ.get("CSMA_OUT", os.path.join(ARCH, "deliverables/final"))
S = os.path.dirname(os.path.abspath(__file__))
# full-resolution Tableau screenshots the dashboard crops are cut from (shipped next to this script)
TAB = os.environ.get("CSMA_TABCHECK", str(Path(__file__).resolve().parent / "tabcheck"))
GF = os.path.join(ARCH, "gephi/figures")
os.makedirs(OUT, exist_ok=True)

# ---- crop Tableau captures (preview coords x197-1475, y333-818 @1600px; scale 2.1375)
k = 2.1375
box = (round(197 * k), round(333 * k), round(1475 * k), round(818 * k))
crops = {}
for n in ["wb1", "v2p2", "sp3", "sp4"]:
    im = Image.open(os.path.join(TAB, n + ".png")).convert("RGB").crop(box)
    p = os.path.join(S, n + "_crop.png")
    im.save(p)
    crops[n] = p

def small(name):
    im = Image.open(os.path.join(GF, name)).convert("RGB")
    im = im.resize((2560, round(2560 * im.size[1] / im.size[0])), Image.LANCZOS)
    q = os.path.join(S, name)
    im.save(q, optimize=True)
    return q


ACC = RGBColor(0x0B, 0x5C, 0x8A)      # accent (deep blue)
INK = RGBColor(0x1E, 0x23, 0x2B)
GREY = RGBColor(0x5F, 0x67, 0x72)
LIGHT = RGBColor(0xEA, 0xF2, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Calibri"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BL = prs.slide_layouts[6]
SW = 13.333
TOTAL = 16


def tb(slide, x, y, w, h, text="", size=18, bold=False, color=INK, align=PP_ALIGN.LEFT,
       anchor=MSO_ANCHOR.TOP, italic=False):
    s = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = s.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    lines = text if isinstance(text, list) else [text]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = ln
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
        r.font.name = FONT
    return s


def bullets(slide, x, y, w, h, items, size=18, gap=8, color=INK):
    s = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = s.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        if isinstance(it, tuple):
            head, rest = it
        else:
            head, rest = None, it
        r0 = p.add_run()
        r0.text = "■  "
        r0.font.size = Pt(size - 6)
        r0.font.color.rgb = ACC
        r0.font.name = FONT
        if head:
            r = p.add_run()
            r.text = head + " "
            r.font.bold = True
            r.font.size = Pt(size)
            r.font.color.rgb = ACC
            r.font.name = FONT
        r = p.add_run()
        r.text = rest
        r.font.size = Pt(size)
        r.font.color.rgb = color
        r.font.name = FONT
    return s


def rect(slide, x, y, w, h, fill=LIGHT, line=None, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1.25)
    s.shadow.inherit = False
    return s


def new_slide(title, notes, n, kicker=None):
    sl = prs.slides.add_slide(BL)
    sl.background.fill.solid()
    sl.background.fill.fore_color.rgb = WHITE
    rect(sl, 0, 0, 0.18, 7.5, fill=ACC)
    if kicker:
        tb(sl, 0.55, 0.28, 12, 0.35, kicker.upper(), size=12, bold=True, color=ACC)
    tb(sl, 0.55, 0.55, 12.3, 1.0, title, size=27, bold=True, color=INK, anchor=MSO_ANCHOR.TOP)
    ln = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(0.6), Inches(1.55), Inches(12.75), Inches(1.55))
    ln.line.color.rgb = RGBColor(0xD5, 0xDB, 0xE1)
    ln.line.width = Pt(1)
    tb(sl, 0.55, 7.08, 9, 0.3, "Solidarity or Blame  |  CSE3729 Computational Social Media Analysis", size=10, color=GREY)
    tb(sl, 11.9, 7.08, 0.9, 0.3, f"{n} / {TOTAL}", size=10, color=GREY, align=PP_ALIGN.RIGHT)
    sl.notes_slide.notes_text_frame.text = notes
    return sl


def pic(slide, path, x, y, w=None, h=None, border=True):
    im = Image.open(path)
    ar = im.size[0] / im.size[1]
    if w is not None and h is not None:
        if w / h > ar:
            w2 = h * ar; x += (w - w2) / 2; w = w2
        else:
            h2 = w / ar; y += (h - h2) / 2; h = h2
    elif w is not None:
        h = w / ar
    else:
        w = h * ar
    p = slide.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))
    if border:
        p.line.color.rgb = RGBColor(0xD5, 0xDB, 0xE1)
        p.line.width = Pt(0.75)
    return p, (x, y, w, h)


def stat(slide, x, y, w, h, big, small, bigsize=26, smallsize=13):
    rect(slide, x, y, w, h, fill=LIGHT)
    rect(slide, x, y, 0.07, h, fill=ACC)
    tb(slide, x + 0.2, y + 0.06, w - 0.3, 0.55, big, size=bigsize, bold=True, color=ACC)
    tb(slide, x + 0.2, y + 0.06 + bigsize / 72 * 1.25, w - 0.3, h - 0.6, small, size=smallsize, color=INK)


# ---------------- 1 Title
sl = prs.slides.add_slide(BL)
sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
rect(sl, 0, 0, SW, 0.22, fill=ACC)
tb(sl, 0.8, 0.9, 11.5, 0.4, "CSE3729 COMPUTATIONAL SOCIAL MEDIA ANALYSIS  |  FINAL PRESENTATION", size=14, bold=True, color=ACC)
tb(sl, 0.8, 1.45, 11.8, 1.0, "Solidarity or Blame", size=48, bold=True, color=INK)
tb(sl, 0.8, 2.4, 11.8, 1.0, "How Reddit communities discuss disruption in technology employment", size=28, color=INK)
tb(sl, 0.8, 3.35, 11.8, 0.5, "r/cscareerquestions, r/technology and r/programming, Jan 2025 - Sep 2026", size=18, color=GREY)
team = [
    ("Vanshit Ahuja", "framing, hypotheses, statistics, literature, report and slides, QA"),
    ("Vaibhav Jain", "Reddit data collection (Arctic Shift), provenance, coverage checks"),
    ("Tanya", "cleaning, thread linkage, descriptive analysis, community comparison, figures"),
    ("Krish", "lexical and stance baselines, reading sample, coding framework, NLP evaluation"),
    ("Dividh Vijay", "Gephi and network work, reply-structure part of H3"),
]
rect(sl, 0.8, 4.15, 11.7, 2.25, fill=LIGHT)
y = 4.27
for nm, role in team:
    tb(sl, 1.0, y, 2.4, 0.38, nm, size=15, bold=True, color=ACC)
    tb(sl, 3.4, y, 9.0, 0.38, role, size=15, color=INK)
    y += 0.41
tb(sl, 0.8, 6.6, 11.8, 0.4, "Faculty: Dr. Kiran Sharma and Dr. Jakob Baek Kristensen  |  BMU, Semester 7  |  November 2026", size=14, color=GREY)
sl.notes_slide.notes_text_frame.text = (
    "Introduce the team and the topic. One sentence: we studied how three Reddit communities talk about layoffs and "
    "other disruption in tech jobs, and whether replies look like solidarity or blame. Roles as documented in the project "
    "reference: Vanshit framing and statistics; Vaibhav data collection; Tanya cleaning and descriptive analysis; Krish NLP "
    "baselines and coding framework; Dividh Gephi and network work and the reply-structure part of H3.")

# ---------------- 2 Problem and RQ
sl = new_slide("When tech jobs are disrupted, do Reddit communities answer with solidarity or with blame?",
    "Motivation: layoffs and AI talk are discussed online every day, but we rarely know whether a community supports the "
    "person or argues about who is at fault. Prior work: Bose (2026) found an amplification gap on X that did not replicate "
    "on Reddit; Ton (2025) found both displacement worry and adaptation in profession subreddits; Yin, Wong and Reddy (2025) "
    "found that support seekers can receive mismatched replies. Our gap: a controlled comparison of communities joined to "
    "support, blame and reply structure.", 2, kicker="Problem and research question")
bullets(sl, 0.6, 1.85, 6.3, 4.8, [
    ("Problem:", "layoffs, hiring freezes and AI are widely discussed online, but we rarely know whether replies support people or assign fault."),
    ("Prior work:", "amplification gaps on X (Bose, 2026); worry and adaptation side by side (Ton, 2025); mismatched support replies (Yin, Wong and Reddy, 2025)."),
    ("Gap:", "no controlled community comparison joined to support, blame and reply structure."),
    ("Warning from network studies:", "a reply records contact, not agreement (Kristensen et al., 2023)."),
], size=18, gap=12)
rect(sl, 7.3, 1.95, 5.45, 4.5, fill=LIGHT)
rect(sl, 7.3, 1.95, 5.45, 0.08, fill=ACC)
tb(sl, 7.55, 2.2, 5.0, 0.4, "RESEARCH QUESTION", size=13, bold=True, color=ACC)
tb(sl, 7.55, 2.7, 5.0, 3.6,
   "How do r/cscareerquestions, r/technology and r/programming discuss disruption in technology employment, "
   "and do personal stories and blame draw different replies?", size=22, bold=True, color=INK)

# ---------------- 3 Hypotheses
sl = new_slide("We tested three hypotheses: where the talk lives, how it is framed, and how people reply",
    "H1 asks where disruption talk concentrates. H2 asks how communities frame it: experience versus news. H3 asks whether "
    "stories and blame draw different replies. Status words matter: we say Supported, not Findings, because our labels are "
    "keyword rules whose precision is provisional (AI-assisted check, not yet human-validated). H2 was supported and then narrowed by the same-author check D1.",
    3, kicker="Hypotheses")
rows = [
    ("H1", "Community concentration", "Disruption language differs between r/cscareerquestions and r/technology in the same window.", "Supported"),
    ("H2", "Discourse function", "Career talk has more personal experience; technology talk has more news and industry framing.", "Supported, then narrowed"),
    ("H3", "Reply structure", "Personal stories and blame are associated with different reply patterns.", "Supported"),
]
y = 1.9
for h, name, txt, st in rows:
    rect(sl, 0.6, y, 12.15, 1.4, fill=LIGHT)
    rect(sl, 0.6, y, 1.1, 1.4, fill=ACC)
    tb(sl, 0.6, y, 1.1, 1.4, h, size=30, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    tb(sl, 1.95, y + 0.15, 7.3, 0.4, name, size=19, bold=True, color=ACC)
    tb(sl, 1.95, y + 0.58, 7.6, 0.8, txt, size=16, color=INK)
    tb(sl, 9.7, y, 2.9, 1.4, st, size=19, bold=True, color=INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    y += 1.6
tb(sl, 0.6, 6.7, 12.1, 0.35, "\"Supported\", not \"Findings\": labels are keyword rules with provisional precision; the human check is pending.",
   size=13, italic=True, color=GREY)

# ---------------- 4 Data
sl = new_slide("We collected 2.97 million Reddit records, with uneven coverage that we report openly",
    "Collection used the Arctic Shift API: full subreddit pulls, with keyword screens applied afterwards, run on 23-24 Sep 2026. "
    "Only 3 of 7 configured subreddits were collected. End dates differ because the collector stops silently on API errors, "
    "or the run was interrupted (collection/PROVENANCE.md). So cross-community comparisons use the shared window Jan-Jun 2025, "
    "and trends over time use r/cscareerquestions only. Posts for cscq are absent.", 4, kicker="Data and coverage")
hdr = ["Subreddit", "Comments", "Posts", "Coverage"]
data = [
    ["r/cscareerquestions", "962,337", "0", "1 Jan 2025 - 23 Sep 2026"],
    ["r/technology", "1,657,900", "76,782", "comments to 9 Jun 2025"],
    ["r/programming", "238,800", "38,431", "comments to 12 Dec 2025"],
    ["Total", "2,859,037", "115,213", "2,974,250 records"],
]
shp = sl.shapes.add_table(5, 4, Inches(0.6), Inches(1.9), Inches(7.4), Inches(2.6))
t = shp.table
widths = [2.3, 1.5, 1.1, 2.5]
for i, wv in enumerate(widths):
    t.columns[i].width = Inches(wv)
for r in range(5):
    for c in range(4):
        cell = t.cell(r, c)
        cell.text = hdr[c] if r == 0 else data[r - 1][c]
        para = cell.text_frame.paragraphs[0]
        para.alignment = PP_ALIGN.RIGHT if c in (1, 2) else PP_ALIGN.LEFT
        f = para.runs[0].font
        f.size = Pt(15); f.name = FONT
        f.bold = (r == 0 or r == 4)
        f.color.rgb = WHITE if r == 0 else INK
        cell.fill.solid()
        cell.fill.fore_color.rgb = ACC if r == 0 else (LIGHT if r % 2 == 0 else WHITE)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
bullets(sl, 8.35, 1.9, 4.5, 4.9, [
    ("Source:", "Arctic Shift API, full pulls, run 23-24 Sep 2026."),
    ("Gap:", "3 of 7 planned subreddits; end dates differ (collection artefact)."),
    ("Fair comparison:", "shared window Jan-Jun 2025."),
    ("Trends:", "r/cscareerquestions only."),
], size=17, gap=12)
stat(sl, 0.6, 4.85, 3.55, 1.6, "94.61%", "of comment text usable")
stat(sl, 4.45, 4.85, 3.55, 1.6, "177,808", "candidates from six employment keyword screens")

# ---------------- 5 Pipeline
sl = new_slide("Our pipeline runs from raw collection to a validity check at every stage",
    "Walk the boxes left to right. Collection: Arctic Shift. Cleaning: usable text, thread linkage, bot denominator. Screens and "
    "markers: six employment keyword screens plus markers for personal experience, doom, blame topics, and reply types such as "
    "sympathy and advice. Comparisons: shared window, community denominators. Replies: reply pairs, stories versus unmarked "
    "comments. Network: cscq reply graph and Gephi. Validity: provisional precision, robustness and a human check that is prepared but pending.",
    5, kicker="Method")
steps = [
    ("Collection", "Arctic Shift API, 3 subreddits"),
    ("Cleaning", "usable text, threads, bot filter"),
    ("Screens and markers", "6 keyword screens; story, doom, blame"),
    ("Comparisons", "shared window Jan-Jun 2025"),
    ("Replies", "reply pairs: sympathy, advice"),
    ("Network", "reply graph, Gephi, Louvain"),
    ("Validity", "precision, robustness, human check"),
]
n = len(steps)
bw, gapw = 1.55, 0.2
x0 = (SW - (n * bw + (n - 1) * gapw)) / 2
for i, (a, b) in enumerate(steps):
    x = x0 + i * (bw + gapw)
    fill = ACC if i in (0, 6) else LIGHT
    rect(sl, x, 2.6, bw, 1.5, fill=fill, line=ACC, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    tb(sl, x, 2.6, bw, 1.5, a, size=16, bold=True, color=WHITE if i in (0, 6) else ACC,
       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    tb(sl, x, 4.25, bw, 1.0, b, size=13, color=INK, align=PP_ALIGN.CENTER)
    if i < n - 1:
        ar = sl.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + bw + 0.02), Inches(3.22), Inches(gapw - 0.04), Inches(0.26))
        ar.fill.solid(); ar.fill.fore_color.rgb = ACC; ar.line.fill.background()
tb(sl, 0.6, 5.6, 12.1, 0.9,
   "Each result is checked against the bot denominator, shared window, thread clustering, length bands, label noise, "
   "activity thresholds and megathread removal.", size=16, color=GREY, align=PP_ALIGN.CENTER)

# ---------------- 6 R1
sl = new_slide("R1: Layoff talk is ambient in r/cscareerquestions but event-driven in r/technology",
    "Dashboard 1 from our Tableau workbook. Layoff share of comments, Jan-Jun 2025, with a non-bot denominator: 2.45% in cscq, "
    "0.20% in r/technology, 0.32% in r/programming. Inside threads that mention layoffs it is 4.06% versus 0.49%. 67% of large cscq "
    "threads contain layoff talk versus 21%. Weekly variability (coefficient of variation) is 0.21 / 0.45 / 0.76, so cscq is steady "
    "and the others spike with events. The midterm figure was 2.32% vs 0.20% (11.36x). We do not quote the hiring screen's ratio "
    "because its precision is only about 22%.", 6, kicker="Result 1  |  H1 supported")
pic(sl, crops["wb1"], 0.6, 1.75, w=12.1, h=3.75)
stat(sl, 0.6, 5.65, 3.9, 1.3, "2.45% vs 0.20%", "layoff share of non-bot comments, cscq vs r/technology (Jan-Jun 2025)", bigsize=22)
stat(sl, 4.7, 5.65, 3.9, 1.3, "67% vs 21%", "of large threads contain layoff talk", bigsize=22)
stat(sl, 8.8, 5.65, 3.9, 1.3, "CV 0.21 / 0.45 / 0.76", "weekly variability: steady in cscq, spiky elsewhere", bigsize=22)

# ---------------- 7 R2
sl = new_slide("R2: Communities frame disruption differently, but who gets blamed travels with the person",
    "Dashboard 2. cscq has more own layoff stories, 8.9% versus 3.1%. Evidence cultures differ: cscq links labour statistics such "
    "as FRED and BLS, r/technology links news, r/programming talks about craft. D1 narrows H2: for the same roughly 152-160 authors "
    "who post in both communities, executive mentions are 6.6% versus 5.8%, so the gap disappears, while AI talk still differs by "
    "9.4 points. Who gets blamed comes with the person; topics are shaped by the community. D1 panel: 152-author variant (career-transition-only comments excluded): 6.1% vs 6.0%. The tile quotes the 160-author D1.", 7, kicker="Result 2  |  H2 supported, then narrowed")
pic(sl, crops["v2p2"], 0.6, 1.75, w=12.1, h=3.25)
tb(sl, 0.6, 5.05, 12.1, 0.5, "D1 panel: 152-author variant (career-transition-only comments excluded): 6.1% vs 6.0%. The tile quotes the 160-author D1.", size=13, color=GREY, align=PP_ALIGN.CENTER)
stat(sl, 0.6, 5.65, 3.9, 1.3, "8.9% vs 3.1%", "own layoff stories, cscq vs r/technology", bigsize=22)
stat(sl, 4.7, 5.65, 3.9, 1.3, "Stats vs news vs craft", "cscq links FRED/BLS; r/technology links news; r/programming talks craft", bigsize=20, smallsize=12)
stat(sl, 8.8, 5.65, 3.9, 1.3, "Same authors: 6.6% vs 5.8%", "executive mentions converge; AI talk still differs (+9.4 pts)", bigsize=20, smallsize=12)

# ---------------- 8 R3
sl = new_slide("R3: Personal layoff stories draw sympathy 2.8 times as often; blame topics draw less",
    "Replies to first-person layoff stories are sympathetic in 5.11% of cases versus 1.82% for unmarked comments, x2.82. This uses "
    "all cscq months, Jan 2025 - Sep 2026: 91,229 reply pairs on 134,749 employment comments. Jan-Jun 2025 alone gives 4.42% vs 1.93%, "
    "x2.29. Stories do not draw more advice; doom draws advice (x1.38). Blame topics (executives, offshoring, AI as an excuse) draw "
    "less sympathy (x0.77-0.81) and no extra agreement (stance model x0.92-1.19). Holds within a length band and with thread-clustered "
    "CIs. Concept: emotional versus informational support; solidarity follows disclosure, not a shared enemy. The image is the Gephi "
    "type network (edge weight = lift). CAUTION: its 'agree' edges are a marker artefact, because the agree marker over-fires on replies "
    "starting with 'This'. Do not read them as agreement.", 8, kicker="Result 3  |  H3 supported")
stat(sl, 0.6, 1.85, 4.9, 1.35, "x2.82", "sympathy for own layoff stories: 5.11% vs 1.82% of replies (cscq, 91,229 reply pairs)", bigsize=30, smallsize=13)
bullets(sl, 0.6, 3.45, 4.95, 3.5, [
    "Jan-Jun 2025 only: 4.42% vs 1.93% (x2.29).",
    "Stories do not draw more advice; doom draws advice (x1.38).",
    "Blame topics draw less sympathy (x0.77-0.81) and no extra agreement.",
    "Holds within length bands and with thread-clustered CIs.",
    "Solidarity follows disclosure, not a shared enemy.",
], size=16, gap=7)
pic(sl, small("type_network_lift_slide.png"), 5.8, 1.8, w=6.95, h=4.4)
tb(sl, 5.8, 6.28, 6.95, 0.75, "Edges into 'agree reply' are a marker artefact (the rule over-fires on replies starting with 'This'); the stance model shows no extra agreement (x0.92-1.19).", size=12, color=GREY)

# ---------------- 9 R4
sl = new_slide("R4: In the reply network, blame-talkers reply to each other and challenge more, with no extra agreement",
    "cscq reply graph, Jan-Jun 2025; largest connected component of 30,976 authors and 162,024 replies. N1: network position follows "
    "activity, not author role. N2: story-sharers receive 1.6-1.9x more sympathy (a lead). N3: blame-talkers reply to each other 1.69 "
    "times more than chance (z = 8, within-thread null); challenge is up (7.2% vs 4.5%), agreement is not. Consistent with an "
    "affective, antagonistic echo chamber. N4: Louvain Q = 0.43, but the 59 communities are not sorted by type (NMI about 0.005). "
    "N5: k-means finds no helper cluster (ARI 0.14). The Gephi image shows the profiled subgraph (10,778 authors with enough comments, coloured by rule-based author type); layout positions have no meaning. Attention is concentrated: top 1% of users receive 17.8% of replies, and 97% "
    "of pairs exchange only one reply.", 9, kicker="Result 4  |  Reply network")
bullets(sl, 0.6, 1.85, 4.95, 5.0, [
    ("Scope:", "cscq, Jan-Jun 2025; largest connected component 30,976 authors, 162,024 replies"),
    ("Blame-talkers:", "reply to each other 1.69x chance (z = 8); challenge 7.2% vs 4.5%, agreement not up."),
    ("Stories:", "sharers receive 1.6-1.9x more sympathy (lead)."),
    ("No sorting:", "Q = 0.43, groups not sorted by type (NMI ~0.005); no helper cluster (ARI 0.14)."),
    ("Attention:", "top 1% receive 17.8% of replies; 97% of pairs exchange one reply."),
], size=15, gap=8)
pic(sl, small("r4_author_types_slide.png"), 5.8, 1.8, w=6.95, h=5.1)

# ---------------- 10 Gephi structure
sl = new_slide("Gephi: the layoff reply network breaks into many small, tight conversation groups (Q = 0.813)",
    "Gephi Toolkit 0.11.4, run headless; projects open in Gephi Desktop 0.11.3. October export of the layoff-keyword author reply "
    "network: 14,507 users, 15,427 directed pairs, summed weight 15,977. 2,199 weak components; the largest has 9,330 users (64.31%); "
    "1,771 are two-user pairs. Modularity at resolution 1.0, weighted: Q = 0.813, 66 groups, the largest 361 users (3.87%). 83.0% of "
    "retained replies stay inside a group. For the R4 profiled subgraph (10,778 nodes, 91,657 edges) Q is only 0.2723 with 81 classes, "
    "and the type mix inside the big classes stays close to the overall mix. Also built: a 12-node type network and a 13,866-node "
    "conversation network (660 weak components, largest 2,190).", 10, kicker="Network structure in Gephi")
pic(sl, small("largest_component_communities_slide.png"), 0.6, 1.8, w=7.6, h=5.15)
stat(sl, 8.5, 1.85, 4.25, 1.2, "Q = 0.813", "66 groups; largest 361 users (3.87%)", bigsize=26)
bullets(sl, 8.5, 3.25, 4.3, 3.7, [
    "14,507 users, 15,427 reply pairs.",
    "Largest component: 9,330 users (64.31%); 1,771 two-user components.",
    "83.0% of retained replies stay within a group.",
    "Profiled core is weaker: Q = 0.2723, 81 classes, type mix close to overall.",
], size=15, gap=8)

# ---------------- 11 Tableau 3 & 4
sl = new_slide("Two more Tableau dashboards show who replies to whom and how far to trust the numbers",
    "The Tableau workbook CSMA_Solidarity_or_Blame.twbx has 11 worksheets, 4 dashboards and 1 story. It was opened and checked in "
    "Tableau Desktop 2026.3; all four story points render and match the expected values. Dashboard 3, Who replies to whom, shows the "
    "reply-network results. Dashboard 4, Can we trust the numbers, shows provisional precision and the robustness checks. The 'agree' column is a marker artefact: the rule fires on replies starting with 'This'. The stance model shows no extra agreement for blame topics (x0.92-1.19).",
    11, kicker="Tableau")
pic(sl, crops["sp3"], 0.6, 1.72, w=8.4, h=2.0)
tb(sl, 0.6, 3.76, 8.4, 0.7, "The 'agree' column is a marker artefact: the rule fires on replies starting with 'This'. The stance model shows no extra agreement for blame topics (x0.92-1.19).", size=13, color=GREY)
pic(sl, crops["sp4"], 0.6, 4.55, w=8.4, h=2.45)
tb(sl, 9.25, 1.9, 3.6, 0.7, "Dashboard 3: Who replies to whom", size=17, bold=True, color=ACC)
tb(sl, 9.25, 2.6, 3.6, 1.7, "Which replies follow which comments (stories draw sympathy x2.8), blame-talker mixing (1.7x) and the network core by author type.", size=14)
tb(sl, 9.25, 4.6, 3.6, 0.7, "Dashboard 4: Can we trust the numbers", size=17, bold=True, color=ACC)
tb(sl, 9.25, 5.3, 3.6, 1.7, "Coverage by community, provisional precision per screen (AI-assisted check) and robustness of the blame-talker lift.", size=14)

# ---------------- 12 Validity
sl = new_slide("Can you trust the numbers? Results survive every robustness check, but labels need a human check",
    "Precision is provisional: samples were checked with AI assistance (Claude), not yet by people. Layoffs 95%, restructuring 75%, economic policy 70%, AI/work 26.7%, hiring "
    "22.5%, career transition 15%. That is why we lean on the layoff screen and do not quote the hiring ratio. Marker checks: the "
    "experience marker is 39 of 40 on layoff comments, about 11 of 20 overall; only 7 of 30 'AI replaces' hits endorse the idea; only "
    "7 of 70 offshoring mentions blame foreign workers; the agree marker over-fires. Robustness: every result holds under the bot "
    "denominator, shared window, thread clustering, length bands, label-noise simulation, activity thresholds and megathread removal "
    "(R5 table, outputs/16_tableau/r5_robustness_long.csv). Next step: a human check with two independent coders on 240 rows is "
    "prepared (docs/HUMAN_CHECK_GUIDE.md) but pending. Polarisation is not measurable yet.", 12, kicker="Validity")
prec = [("Screen", "Precision"), ("Layoffs", "95%"), ("Restructuring", "75%"), ("Economic policy", "70%"),
        ("AI / work", "26.7%"), ("Hiring", "22.5%"), ("Career transition", "15%")]
shp = sl.shapes.add_table(len(prec), 2, Inches(0.6), Inches(1.85), Inches(4.6), Inches(3.9))
t = shp.table
t.columns[0].width = Inches(3.0); t.columns[1].width = Inches(1.6)
for r, (a, b) in enumerate(prec):
    for c, v in enumerate((a, b)):
        cell = t.cell(r, c); cell.text = v
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT if c == 1 else PP_ALIGN.LEFT
        f = p.runs[0].font; f.size = Pt(16); f.name = FONT; f.bold = (r == 0 or r == 1)
        f.color.rgb = WHITE if r == 0 else INK
        cell.fill.solid(); cell.fill.fore_color.rgb = ACC if r == 0 else (LIGHT if r % 2 == 0 else WHITE)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
tb(sl, 0.6, 5.85, 4.6, 0.9, "Provisional precision (AI-assisted check). Strong for layoffs; weak screens are not quoted.", size=13, italic=True, color=GREY)
bullets(sl, 5.6, 1.85, 7.2, 3.3, [
    ("Robust:", "bot denominator, shared window, thread clusters, length bands, label noise, activity thresholds, megathreads."),
    ("Markers:", "experience 39/40 on layoff comments; only 7/70 offshoring mentions blame foreign workers."),
    ("Limits:", "the agree marker over-fires; polarisation is not measurable yet."),
], size=16, gap=10)
rect(sl, 5.6, 5.05, 7.15, 1.75, fill=LIGHT)
rect(sl, 5.6, 5.05, 0.07, 1.75, fill=ACC)
tb(sl, 5.85, 5.15, 6.8, 0.4, "NEXT STEP: HUMAN CHECK (PENDING)", size=13, bold=True, color=ACC)
tb(sl, 5.85, 5.55, 6.8, 1.2, "Two independent coders, 240 rows, guide prepared. Until it is done, results stay \"Supported\", not \"Findings\".", size=16, color=INK)

# ---------------- 13 Applications
sl = new_slide("The results suggest practical uses for moderators and analysts, which we have not yet tested",
    "These are suggestions that follow from the results; we have not tested any of them with moderators or community members, and "
    "the results are associations in three subreddits. Even with x2.8 sympathy, about 95% of replies to stories are not sympathetic, "
    "so many stories go unanswered with care.", 13, kicker="Applications")
apps = [
    ("Route stories to support", "First-person layoff stories draw sympathy (x2.8), yet ~95% of replies to them are not sympathetic."),
    ("Answer worry with information", "Doom draws advice (x1.4): practical information helps."),
    ("Measure blame with stance", "Topic counts and sentiment mistake topic for blame (sentiment separates at 0.50, chance)."),
    ("Support continuously", "In career communities layoffs are ambient, not only news-driven."),
    ("Watch blame threads", "Blame draws less support; blame-talkers reply to each other 1.7x with more challenge."),
]
y = 1.85
for i, (h, d) in enumerate(apps):
    rect(sl, 0.6, y, 0.55, 0.8, fill=ACC)
    tb(sl, 0.6, y, 0.55, 0.8, str(i + 1), size=20, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    rect(sl, 1.15, y, 11.6, 0.8, fill=LIGHT)
    tb(sl, 1.35, y, 3.9, 0.8, h, size=17, bold=True, color=ACC, anchor=MSO_ANCHOR.MIDDLE)
    tb(sl, 5.25, y, 7.4, 0.8, d, size=15, color=INK, anchor=MSO_ANCHOR.MIDDLE)
    y += 0.98

# ---------------- 14 Conclusion
sl = new_slide("Three claims: layoffs are ambient, blame travels with people, and solidarity follows disclosure",
    "Claim 1 (H1): in the career community layoffs are a constant background topic; in r/technology they spike with news. Claim 2 "
    "(H2 narrowed): communities shape topics and evidence, but for the same authors in both places, who gets blamed stays with the "
    "person. Claim 3 (H3): telling your own story draws sympathy; blame topics draw less support and no extra agreement, and in the "
    "network blame-talkers cluster and challenge each other. All three are Supported, pending the human label check; three subreddits, "
    "comments only, Jan 2025 - Sep 2026, no causal claims.", 14, kicker="Conclusion")
claims = [
    ("1", "Layoffs are ambient", "2.45% of cscq comments vs 0.20% in r/technology; steady weekly rate (CV 0.21)."),
    ("2", "Blame travels with people", "Same authors: executive mentions 6.6% vs 5.8%; topics still differ by community."),
    ("3", "Solidarity follows disclosure", "Own stories draw sympathy x2.82; blame draws less support and no extra agreement."),
]
for i, (nn, h, d) in enumerate(claims):
    x = 0.6 + i * 4.1
    rect(sl, x, 1.9, 3.9, 4.3, fill=LIGHT)
    rect(sl, x, 1.9, 3.9, 0.1, fill=ACC)
    tb(sl, x + 0.25, 2.15, 1.0, 0.8, nn, size=40, bold=True, color=ACC)
    tb(sl, x + 0.25, 3.05, 3.45, 1.0, h, size=21, bold=True, color=INK)
    tb(sl, x + 0.25, 4.1, 3.45, 2.0, d, size=16, color=INK)
tb(sl, 0.6, 6.4, 12.1, 0.5, "Supported, not yet Findings: three subreddits, comments only, Jan 2025 - Sep 2026; associations, not causes.",
   size=14, italic=True, color=GREY, align=PP_ALIGN.CENTER)

# ---------------- 15 Limitations & future
sl = new_slide("Limits are clear, and the next steps follow directly from them",
    "Limitations: keyword labels with provisional, AI-assisted precision; weak screens for hiring, AI/work and career transition; "
    "only 3 of 7 subreddits with uneven end dates, and no cscq posts; associations only, no causal or population claims; the agree "
    "marker over-fires and polarisation is not measurable yet. Leads that need follow-up: D2 newcomers who get any reply come back "
    "more often, 50% vs 39% (a lead, not causal); D3 after the H-1B announcement on 19 Sep 2025 offshoring talk went from about 13% "
    "to 43% for one week and then fell below its earlier level, a shock not a shift; 'AI as an excuse' did not grow (a denominator "
    "effect). Future work: finish the two-coder human check, train a stance classifier on validated labels. The team decided not "
    "to collect more data, so claims stay limited to the collected corpus.", 15, kicker="Limitations and future work")
tb(sl, 0.6, 1.8, 6.0, 0.45, "Limitations", size=20, bold=True, color=ACC)
bullets(sl, 0.6, 2.35, 5.9, 4.5, [
    "Keyword labels; precision provisional (AI-assisted check).",
    "Weak screens: hiring, AI/work, career transition.",
    "3 of 7 subreddits; uneven end dates; no cscq posts.",
    "Associations only: no causal or population claims.",
    "Agree marker over-fires; polarisation not measurable.",
], size=17, gap=10)
tb(sl, 6.9, 1.8, 6.0, 0.45, "Future work", size=20, bold=True, color=ACC)
bullets(sl, 6.9, 2.35, 5.9, 4.5, [
    "Finish the two-coder human check (240 rows).",
    "Train a stance model on validated labels.",
    "Coverage limit stated up front (team decided not to collect more data).",
    "Follow leads: newcomers who get a reply return more (50% vs 39%).",
    "H-1B shock: offshoring talk 13% to 43% for one week, then fell below its earlier level (a shock, not a shift).",
], size=17, gap=10)

# ---------------- 16 Thanks
sl = prs.slides.add_slide(BL)
sl.background.fill.solid(); sl.background.fill.fore_color.rgb = WHITE
rect(sl, 0, 0, SW, 0.22, fill=ACC)
tb(sl, 0.8, 1.3, 11.8, 1.0, "Thank you. Questions?", size=48, bold=True, color=INK)
tb(sl, 0.8, 2.4, 11.8, 0.6, "Solidarity follows disclosure, not a shared enemy.", size=24, color=ACC)
tb(sl, 0.8, 3.3, 11.8, 0.5, "Vanshit Ahuja  |  Vaibhav Jain  |  Tanya  |  Krish  |  Dividh Vijay", size=18, color=INK)
tb(sl, 0.8, 4.2, 11.8, 0.4, "SELECTED REFERENCES", size=12, bold=True, color=ACC)
tb(sl, 0.8, 4.55, 11.8, 2.4, [
    "Bose, J. (2026). Attention asymmetry in AI layoff discourse on X. arXiv:2605.29367.",
    "Hutto, C. J., & Gilbert, E. (2014). VADER. ICWSM, 8(1), 216-225.",
    "Kristensen, J. B., Henriksen, F. M., & Mayerhoffer, E. (2023). Did COVID-19 blur partisan boundaries? Social Media + Society, 9(3).",
    "Reagle, J. (2022). Disguising Reddit sources and the efficacy of ethical research. Ethics and Information Technology, 24, 41.",
    "Ton, N. T. D. (2025). AI as a threat? Evidence from Reddit. APSA Preprints.",
    "Yin, J. Y., Wong, N., & Reddy, M. C. (2025). Support-seeking on Reddit during stressful times. Proc. ACM HCI.",
], size=12, color=GREY)
tb(sl, 0.8, 6.95, 11.8, 0.35, "Full reference list in the final report. Data, code and Gephi/Tableau files are in the project archive.", size=11, italic=True, color=GREY)
sl.notes_slide.notes_text_frame.text = (
    "Close with the one-line takeaway: solidarity follows disclosure, not a shared enemy. Invite questions. Likely questions: why "
    "not causal (associations in three subreddits); why 'Supported' (labels provisional until the two-coder check); why the hiring "
    "ratio is not quoted (precision about 22%); why agree edges are not trusted (marker over-fires on replies starting with 'This').")

out = os.path.join(OUT, "CSMA_Final_Presentation_Solidarity_or_Blame.pptx")
prs.save(out)
print(out, len(prs.slides))
