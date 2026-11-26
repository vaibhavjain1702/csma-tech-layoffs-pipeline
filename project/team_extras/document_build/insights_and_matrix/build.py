import os, subprocess
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

import os
from pathlib import Path
# project root = four levels up from this file; override the output folder with CSMA_OUT
OUT = os.environ.get("CSMA_OUT", str(Path(__file__).resolve().parents[3] / "deliverables" / "final"))

def shade(cell,hexcol):
    tcPr=cell._tc.get_or_add_tcPr(); s=OxmlElement('w:shd')
    s.set(qn('w:val'),'clear'); s.set(qn('w:color'),'auto'); s.set(qn('w:fill'),hexcol); tcPr.append(s)

def base(doc,size=10):
    st=doc.styles['Normal']; st.font.name='Calibri'; st.font.size=Pt(size)
    st.element.rPr.rFonts.set(qn('w:eastAsia'),'Calibri')
    st.paragraph_format.space_after=Pt(3)
    for n,sz in (('Heading 1',16),('Heading 2',12)):
        h=doc.styles[n]; h.font.name='Calibri'; h.font.size=Pt(sz); h.font.bold=True
        h.font.color.rgb=RGBColor(0x1F,0x3A,0x5F)
        h.paragraph_format.space_before=Pt(8); h.paragraph_format.space_after=Pt(3)

def runs(p,text):
    # **bold** support
    parts=text.split('**')
    for i,t in enumerate(parts):
        if t:
            r=p.add_run(t); r.bold=(i%2==1)

# ---------------- Insights ----------------
TITLE="Solidarity or Blame: how Reddit communities discuss disruption in technology employment"
SUB="CSE3729 Computational Social Media Analysis, BMU, Semester 7. Final insights, 27 November 2026."
ANSWER=("In r/cscareerquestions, solidarity follows disclosure, not a shared enemy: people who tell what happened to them "
 "get sympathy, while blame topics draw less support and no extra agreement, and who gets blamed comes with the person rather than the community.")
CLAIMS=[
("1. Layoff talk is concentrated in the career community (H1, Supported).",
 ["Share of non-bot comments that mention layoffs, Jan-Jun 2025: **2.45%** in r/cscareerquestions (cscq), **0.20%** in r/technology, **0.32%** in r/programming.",
  "Inside threads that mention layoffs: 4.06% vs 0.49% (cscq vs r/technology). 67% of large cscq threads contain layoff talk, against 21% in r/technology.",
  "Weekly variability (CV) is 0.21 / 0.45 / 0.76 (cscq / r/technology / r/programming): layoffs are ambient in cscq and event-driven in r/technology.",
  "The midterm comparison (Jan-May 2025) gave 2.32% vs 0.20%, 11.36x.",
  "The hiring screen's ratio is unreliable (precision about 22%) and is not quoted."]),
("2. The communities frame disruption differently, and part of the gap follows the person (H2, Supported, then narrowed).",
 ["Own layoff stories: **8.9%** (cscq) vs **3.1%** (r/technology). cscq links labour statistics (FRED, BLS); r/technology links news; r/programming talks craft.",
  "D1: for the same ~152-160 authors who write in both communities, executive mentions are 6.6% vs 5.8% (the gap disappears), while AI talk still differs by +9.4 points. Who gets blamed comes with the person; topics are shaped by the community."]),
("3. Sympathy follows disclosure, not blame (H3, Supported).",
 ["Replies to personal layoff stories contain sympathy in **5.11%** of cases vs **1.82%** for unmarked comments (x2.82). This covers all cscq months, Jan 2025 - Sep 2026: 91,229 reply pairs on 134,749 employment comments. Jan-Jun 2025 alone gives 4.42% vs 1.93% (x2.29).",
  "Advice does not rise for stories; doom draws advice (x1.38). Blame topics (executives, offshoring, AI-as-excuse) draw less sympathy (x0.77-0.81) and no extra agreement (stance model x0.92-1.19). The effect holds within a length band and with thread-clustered confidence intervals.",
  "Network view (cscq reply graph, Jan-Jun 2025; largest connected component 30,976 authors, 162,024 replies): blame-talkers reply to each other 1.69x more than chance (z = 8, within-thread null) with more challenge (7.2% vs 4.5%) but not more agreement, consistent with an antagonistic echo chamber. Position follows activity, not role; the top 1% of users receive 17.8% of replies."]),
]
OTHER=["Newcomers who get any reply come back more often, 50% vs 39% (a lead, not causal).",
 "After the H-1B announcement (19 Sep 2025), offshoring talk rose from about 13% to 43% for one week, then fell below its earlier level: a shock, not a shift.",
 "\"AI as an excuse\" did not grow; that was a denominator effect. Sentiment is not stance: sentiment separates story comments from blame comments only at 0.50, which is chance."]
CAN=["Describe, for three subreddits and comments only, how often and how employment disruption is discussed and how replies respond, in the collected corpus (2,974,250 records; 115,213 posts, 2,859,037 comments).",
 "State that the results are Supported by the keyword-rule labels and are robust to the bot denominator, shared window, thread clustering, length bands, label-noise simulation, activity thresholds and megathread removal.",
 "Compare communities only in the shared window (Jan-Jun 2025); describe time trends in cscq only."]
CANNOT=["No causal claims and no population claims: three subreddits, comments only, Jan 2025 - Sep 2026. Not representative of technology workers; not cross-platform.",
 "Coverage is uneven (cscq to 23 Sep 2026 with 0 posts; r/technology comments to 9 Jun 2025; r/programming to 12 Dec 2025). This is a collection-run artefact (see collection/PROVENANCE.md), so prevalence and complete coverage cannot be claimed.",
 "We do not claim that blame topics draw agreement: the agree marker over-fires on replies that start with \"This\". We claim only less support and no extra agreement.",
 "Polarisation is not measurable now. Topic is not stance; the AI/work, hiring and career-transition screens are weak (see below)."]
VALID=["**The human label check has not been completed.** The labels are keyword rules, and their precision is provisional (an AI-assisted check by Claude, not yet human-validated). A human check with two independent coders is prepared (docs/HUMAN_CHECK_GUIDE.md, 240 rows) but pending. Until it is done, results are \"Supported\", not \"Findings\", and no inter-coder agreement is reported.",
 "Provisional precision (AI-assisted check): layoffs screen 95%; restructuring 75%; economic policy 70%; AI/work 26.7%; hiring 22.5%; career transition 15%. Experience marker 39/40 on layoff comments (about 11/20 overall); ai_replaces only 7/30 endorse; offshore only 7/70 blame foreign workers; the agree marker over-fires."]
NEXT=["Run the human check (240 rows, two coders working alone), then score it with scripts/score_human_check.py. Only then upgrade labels from \"Supported\" to \"Findings\" or revise them.",
 "Join validated stance labels to the reply networks to test the reply-structure part of H3 with human labels.",
 "Replace or retire the weak screens (hiring, AI/work, career transition); date the second offshoring spike (mid-Dec 2025).",
 "Add topic modelling and external labour indicators only if a hypothesis needs them. The team decided not to collect more data."]

def write_md():
    L=[f"# {TITLE}",f"*{SUB}*","","## Answer in one sentence","",ANSWER,"","## Three core claims",""]
    for h,bs in CLAIMS:
        L.append(f"**{h}**"); L+= [f"- {b}" for b in bs]; L.append("")
    L.append("**Other results.**"); L+=[f"- {b}" for b in OTHER]
    L+=["","## What we can claim",""]+[f"- {b}" for b in CAN]
    L+=["","## What we cannot claim",""]+[f"- {b}" for b in CANNOT]
    L+=["","## Validity status",""]+[f"- {b}" for b in VALID]
    L+=["","## Next steps",""]+[f"{i}. {b}" for i,b in enumerate(NEXT,1)]
    open(f"{OUT}/CSMA_Final_Insights.md","w").write("\n".join(L)+"\n")

def write_ins_docx():
    d=Document(); base(d,9.5)
    s=d.sections[0]; s.page_width=Cm(21); s.page_height=Cm(29.7)
    s.left_margin=s.right_margin=Cm(1.7); s.top_margin=Cm(1.4); s.bottom_margin=Cm(1.3)
    d.add_heading(TITLE,1)
    p=d.add_paragraph(); r=p.add_run(SUB); r.italic=True
    d.add_heading("Answer in one sentence",2)
    p=d.add_paragraph(); runs(p,"**"+ANSWER+"**")
    d.add_heading("Three core claims",2)
    for h,bs in CLAIMS:
        p=d.add_paragraph(); p.paragraph_format.space_after=Pt(1); runs(p,"**"+h+"**")
        for b in bs:
            q=d.add_paragraph(style='List Bullet'); q.paragraph_format.space_after=Pt(1); runs(q,b)
    p=d.add_paragraph(); p.paragraph_format.space_after=Pt(1); runs(p,"**Other results.**")
    for b in OTHER:
        q=d.add_paragraph(style='List Bullet'); q.paragraph_format.space_after=Pt(1); runs(q,b)
    for head,items,sty in (("What we can claim",CAN,'List Bullet'),("What we cannot claim",CANNOT,'List Bullet'),("Validity status",VALID,'List Bullet'),("Next steps",NEXT,'List Number')):
        d.add_heading(head,2)
        for b in items:
            q=d.add_paragraph(style=sty); q.paragraph_format.space_after=Pt(1); runs(q,b)
    d.save(f"{OUT}/CSMA_Final_Insights.docx")

# ---------------- Matrix ----------------
COLS=["Data collection","Cleaning and processing","Analysis and statistics","NLP and labels","Network / Gephi","Visualisation / Tableau","Literature and report","Presentation","QA and reproducibility"]
M={
"Vanshit Ahuja":{2:"Shared-window comparison; hypotheses; statistical interpretation",6:"Literature review; report revision",7:"Slides revision; midterm: title, question, hypotheses, contributions, next phase",8:"Archive QA; privacy checks; testing; repository cleanup; public release"},
"Vaibhav Jain":{0:"Reddit data collection (Arctic Shift); raw batches; provenance; coverage checks",7:"Midterm: data collection, provenance, coverage"},
"Tanya":{1:"Data cleaning; thread linkage; missing and deleted text states; quality checks",2:"Descriptive analysis; community comparison",5:"Figures (midterm)",7:"Midterm: preprocessing, methodology, controlled comparison, figures"},
"Krish":{3:"Lexical and stance baselines; reading sample; coding framework; NLP evaluation plan",7:"Presentation preparation (midterm); midterm: literature review, NLP choices, stance baseline"},
"Dividh Vijay":{3:"Assigned (docs/PROJECT_REFERENCE.md task 1): 240-row human check with one teammate, pending",2:"Reply-structure part of H3 (owner)",4:"Documented role (midterm): Gephi and network work: node and edge exports, direction, weights, scope, validation",7:"Midterm: Gephi exports, graph definitions, limits of network interpretation"},
}
DRAFT_NOTES=[
"Cells are filled only from the documented roles (docs/PROJECT_REFERENCE.md section 4) and the midterm contribution statements (deliverables/MIDTERM_HANDOFF.md and midterm report section 8). A blank cell means nothing is documented there, not that no work was done.",
"Tableau workbook authorship is not documented in the archive; that column holds only Tanya's documented figure work. The team should fill in any final-phase contributions it knows of.",
"Per the git history of the public repository lazinWolf/csma-layoff-sentiment, its 3 commits (25-26 Nov 2026) are authored by 'dividh'. A commit shows who uploaded the files, not who wrote each piece of work.",
"The October midterm repository was committed by 'vanshitahujaa' (5 Oct 2026).",
"Final-phase deliverables of 26 Nov (Gephi projects and slide figures via Gephi Toolkit, the Tableau workbook, collection provenance, the human-check kit, the docs refresh, the final report and slides) were produced in the final build session with Claude Code on the project laptop; the team should record who directed them.",
"The final-phase work (hypothesis tests H1-H3, directions, Gephi, Tableau) is not attributed to named members in the archive beyond the roles above; to be confirmed by the team.",
]
def write_matrix():
    d=Document(); base(d,8)
    s=d.sections[0]; s.orientation=WD_ORIENT.LANDSCAPE; s.page_width=Cm(29.7); s.page_height=Cm(21)
    s.left_margin=s.right_margin=Cm(1.2); s.top_margin=Cm(1.2); s.bottom_margin=Cm(1.1)
    h=d.add_heading("Contribution Matrix",1)
    p=d.add_paragraph(); r=p.add_run("DRAFT, for the team to confirm before submission"); r.bold=True; r.font.size=Pt(13); r.font.color.rgb=RGBColor(0xB0,0x1E,0x1E)
    p=d.add_paragraph("CSE3729 Computational Social Media Analysis. Project: Solidarity or Blame: how Reddit communities discuss disruption in technology employment.")
    t=d.add_table(rows=1,cols=len(COLS)+2); t.style='Table Grid'
    hdr=["Member"]+COLS+["Confirmed by team (initials)"]
    for i,x in enumerate(hdr):
        c=t.rows[0].cells[i]; c.text=""; rr=c.paragraphs[0].add_run(x); rr.bold=True; rr.font.size=Pt(7.5); shade(c,"D9E2F3")
    for name,cells in M.items():
        row=t.add_row().cells
        row[0].text=""; rr=row[0].paragraphs[0].add_run(name); rr.bold=True; rr.font.size=Pt(8)
        for j in range(len(COLS)):
            row[j+1].text=""
            if j in cells:
                rr=row[j+1].paragraphs[0].add_run(cells[j]); rr.font.size=Pt(7)
        row[-1].text=""
    widths=[2.2]+[2.6]*9+[2.2]
    for r_ in t.rows:
        for i,w in enumerate(widths): r_.cells[i].width=Cm(w)
    d.add_paragraph()
    d.add_heading("Notes",2)
    for n in DRAFT_NOTES:
        q=d.add_paragraph(style='List Bullet'); q.paragraph_format.space_after=Pt(1); q.add_run(n).font.size=Pt(8.5)
    d.save(f"{OUT}/CSMA_Contribution_Matrix_DRAFT.docx")

write_md(); write_ins_docx(); write_matrix()
for f in ("CSMA_Final_Insights.docx","CSMA_Contribution_Matrix_DRAFT.docx"):
    subprocess.run(["/Applications/LibreOffice.app/Contents/MacOS/soffice","--headless","--convert-to","pdf","--outdir",OUT,f"{OUT}/{f}"],check=True,capture_output=True)
print("done")
