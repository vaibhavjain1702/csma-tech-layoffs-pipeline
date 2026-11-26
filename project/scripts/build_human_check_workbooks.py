"""Build the coder workbooks (xlsx + csv twins) for the 240-row human label check.

Builder (kept in the project for reproducibility). Reads A/outputs/12_replies/check_sheet.csv (never modified), the
full own_text of the 240 ids from data/processed/reddit.sqlite opened read-only +
immutable (cached in fulltext.json), and the real regexes from scripts/explore_replies.py.
Writes A/annotations/human_check/check_sheet_coder_{A,B,C,D}.{xlsx,csv}.

Usage (from the project root): python3 -B scripts/build_human_check_workbooks.py . [<fulltext.json>] [--force]
Refuses to overwrite coder files that already contain answers unless --force is given.
"""
import csv, json, re, sys, sqlite3
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

FORCE = '--force' in sys.argv
ARGS = [a for a in sys.argv[1:] if a != '--force']
A = Path(ARGS[0] if ARGS else '.').resolve()
FULL = Path(ARGS[1]) if len(ARGS) > 1 else None
sys.path.insert(0, str(A / 'scripts'))
from explore_replies import PARENT, REPLY  # the real rules  # noqa: E402

BLAME = ('mentions_execs', 'mentions_offshore', 'ai_excuse', 'blames_workers')
COLS = ['row_id', 'unit', 'machine_label', 'label_meaning', 'text', 'label_correct', 'blamed_target', 'notes', 'id']

# One-line rules (same wording as docs/HUMAN_CHECK_GUIDE.md section 5).
MEANING = {
    'experience': "ACT. YES = the author says a layoff/job loss really happened to them or their own team (even one line inside a question). NO = hypothetical, feared or 'almost', denied ('I was never laid off'), pay/budget cut, 'let me go ahead', someone else's layoff, author did the laying off.",
    'mentions_execs': "TOPIC (stance does not matter). YES = the word really refers to company leadership or capital: executives, CEOs, C-suite, shareholders, investors, Wall Street, stock price/buybacks, corporate greed. NO = other sense: 'executive order', 'greedy algorithm', the author's own personal investing.",
    'mentions_offshore': "TOPIC (stance does not matter). YES = really about offshoring/outsourcing jobs, H-1B or work visas (including the author's own visa). NO = Visa the company, tourist/travel visa, 'outsourcing' to AI or of non-job tasks.",
    'blames_workers': "TOPIC (stance does not matter). YES = lazy / low performer / skill issue / not good enough / unqualified / underperform describes workers' or job seekers' skill, effort or performance (also self-talk, or rejecting that blame). NO = about code, tools, AI, products, pay or stocks ('lazy loading', 'AI is not good enough'), or aimed at employers/recruiters/execs.",
    'ai_excuse': "TOPIC (stance does not matter). YES = the text deals with AI being an excuse, cover or pretext for layoffs/hiring cuts, or disputes that AI is the real cause of job cuts. NO = 'excuse', 'cover for', 'scapegoat' etc. not about AI and jobs ('no excuse', 'excuse me', 'H-1Bs are a scapegoat').",
    'ai_replaces': "CLAIM. YES = the author asserts AI/automation will replace, eliminate or take jobs/workers (even only some), or that people who don't adapt to AI will be left behind. NO = 'it will take [time]' where 'it' is not AI, doubt/denial ('I don't think AI will replace'), a question, someone else's view, a joke, jobs gone for non-AI reasons.",
    'doom': "CLAIM. YES = the author asserts the tech job market or job prospects are bad, from 'rough' to 'cooked' (own prospects count). NO = cooking, housing/stock market, 'denial' of a claim/visa/service, 'not lying' about something else, disputing doom, quoting it to reject it.",
    'none': "BASELINE. YES = the text contains NONE of the 7 comment types in any wording: own job loss; execs/upper management/shareholders/greed; offshoring/H-1B/work visas; workers described as lazy/unskilled/unqualified/low performers (ordinary skills talk does not count); AI as excuse; AI will replace jobs; bad-market claim. NO = at least one is present (write which in notes).",
    'sympathy': "REPLY ACT. YES = genuine emotional support for the person: sympathy, comfort, encouragement, well-wishes or sincere congratulations (even next to advice or disagreement). NO = 'sorry, but…' that only softens a disagreement, 'sorry for my English', sarcastic 'good luck with that', 'glad you asked'.",
    'advice': "REPLY ACT. YES = recommends something the person could do (imperative tip, 'you should', 'I'd recommend', 'have you tried X?' that proposes X, 'what worked for me was…'). NO = a pure information question, a description ('companies focus on profit', 'the rules apply to everyone', 'I try to…'), computer/neural 'network', a put-down ('you should be ashamed').",
    'agree': "REPLY ACT. YES = the reply's main stance is agreement with the comment it answers ('This.', 'Exactly', 'Spot on', 'Same here, happened to me too'). NO = starts with 'This…'/'Truth…' but disagrees or attacks ('This is not true', 'This is the dumbest take'), 'I can't say I agree', or agreement that is only a lead-in to disagreeing.",
    'challenge': "REPLY ACT. YES = pushes back on the comment or person it answers: disputes, corrects, mocks, calls it cope/delusional, demands a source sceptically. NO = 'open source', 'no IT experience', 'you're not wrong', 'I don't disagree', 'nothing wrong with that', coping with stress, 'that's not fair to you', anger at a company/market that sides with the person.",
}
BLAME_Q = {
    'mentions_execs': "Does the author hold executives / shareholders / investors / 'corporate greed' responsible for layoffs, bad hiring or worse conditions?",
    'mentions_offshore': "Does the author present offshoring/outsourcing or H-1B/visa hiring (the practice, the policy or the foreign workers) as a cause of job losses, lower pay or a harder market? Write 'workers' in notes if the blame is aimed at the foreign workers themselves.",
    'ai_excuse': "Does the author themselves assert that AI is an excuse/cover/pretext for cuts, or that cuts blamed on AI really have other causes (i.e. endorse the 'AI is the excuse' claim)?",
    'blames_workers': "Does the author hold workers or job seekers (others, or themselves: write 'self' in notes) responsible for losing or not getting jobs because of their skill, effort or performance?",
}

GREY = PatternFill('solid', fgColor='D9D9D9'); YELLOW = PatternFill('solid', fgColor='FFF2CC')
HEAD = PatternFill('solid', fgColor='1F3864'); BLUE = PatternFill('solid', fgColor='DDEBF7')
THIN = Side(style='thin', color='BFBFBF'); BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical='top')


def clean(s):
    return ILLEGAL_CHARACTERS_RE.sub('', s or '')


def load_full(rows):
    if FULL and FULL.exists():
        return json.loads(FULL.read_text())
    db = A / 'data/processed/reddit.sqlite'
    c = sqlite3.connect(f'file:{db}?mode=ro&immutable=1', uri=True)
    ids = [r['id'] for r in rows]
    return dict(c.execute("select id, own_text from features where kind='comments' and id in (%s)" % ','.join('?' * len(ids)), ids).fetchall())


def build_rows():
    rows = list(csv.DictReader((A / 'outputs/12_replies/check_sheet.csv').open(encoding='utf-8')))
    assert len(rows) == 240, len(rows)
    full = load_full(rows)
    out, hidden = [], []
    for i, r in enumerate(rows, 1):
        lab, text = r['machine_label'], r['text']
        cell = text
        if lab != 'none':
            rx = PARENT.get(lab) or REPLY.get(lab)
            ft = full.get(r['id']) or ''
            m = rx.search(ft)
            assert m, (i, lab)  # every label reproduces on the full text (checked)
            fired = ' '.join(m.group(0).split())
            if rx.search(text):
                cell = f"{text}\n[rule fired on: «{fired}»]"
            else:
                lo, hi = max(0, m.start() - 220), min(len(ft), m.end() + 220)
                ctx = ' '.join(ft[lo:hi].split())
                cell = (f"{text}\n[TEXT CUT AT {len(text)} CHARACTERS. The rule fired further on, on «{fired}». "
                        f"Excerpt from the full comment:] {'…' if lo > 0 else ''}{ctx}{'…' if hi < len(ft) else ''}")
                hidden.append(i)
        else:
            assert not any(x.search(full.get(r['id']) or '') for x in PARENT.values()), i
        out.append({'row_id': i, 'unit': r['unit'], 'machine_label': lab, 'label_meaning': MEANING[lab],
                    'text': clean(cell), 'label_correct': '', 'blamed_target': '' if lab in BLAME else 'na',
                    'notes': '', 'id': r['id']})
    return out, hidden


def split_note(coder):
    part = 'rows 1–120 (labels experience … ai_replaces)' if coder in 'AB' else 'rows 121–240 (labels doom … challenge)'
    return (f"Your file: coder {coder}. With 2 coders, coders A and B each code ALL 240 rows. "
            f"With 4 coders, you (coder {coder}) code {part} only and leave the other rows blank.")


def instructions(ws, coder):
    ws.title = 'Instructions'
    lines = [
        ('Human label check: coder ' + coder, True),
        ('Full guide: docs/HUMAN_CHECK_GUIDE.md. Work ALONE: do not discuss rows with anyone until every coder has finished.', False),
        (split_note(coder), False),
        ('THE ONE QUESTION per row: does the machine label correctly describe this text, using the rule for that label? Judge only the label in column machine_label.', True),
        ('label_correct: yes = the rule is right for this text; no = it is a false hit; unsure = you truly cannot decide (text cut off, unreadable sarcasm, reply that only makes sense with the unseen parent). Keep unsure under ~10% and write why in notes.', False),
        ('blamed_target (only the 4 blame-topic labels mentions_execs, mentions_offshore, ai_excuse, blames_workers; their cells are yellow, all others grey): yes/no on EVERY one of those rows, even when label_correct is no (then it is almost always no). Answer yes only when the blame is clear. All other rows are pre-filled "na": leave them.', False),
        ('TOPIC labels (mentions_execs, mentions_offshore, ai_excuse, blames_workers): YES whenever the word is used in its employment sense, whatever the stance: quoting, denying or defending still counts as the topic. Stance goes in blamed_target.', False),
        ('ACT / CLAIM labels (experience, ai_replaces, doom and the 4 reply labels): YES only if the author actually does or asserts it. Negation, quoting someone else, hypotheticals, questions and sarcasm are NO.', False),
        ('Replies are shown without their parent comment: judge from the reply\'s own words. The text was cut at 500 characters (comments) or 400 (replies); where the rule fired in the hidden part, an excerpt is added in [brackets]. «rule fired on» shows the words the rule matched.', False),
    ]
    r = 1
    for text, bold in lines:
        c = ws.cell(row=r, column=1, value=text); c.font = Font(bold=bold, size=13 if r == 1 else 11); c.alignment = WRAP
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
        ws.row_dimensions[r].height = 18 if r == 1 else 15 * max(2, len(text) // 150 + 1)
        r += 1
    r += 1
    for j, h in enumerate(['label', 'rows', 'YES / NO rule', 'blamed_target question (4 labels only)'], 1):
        c = ws.cell(row=r, column=j, value=h); c.font = Font(bold=True, color='FFFFFF'); c.fill = HEAD; c.alignment = WRAP; c.border = BOX
    order = list(MEANING)
    for k, lab in enumerate(order):
        r += 1
        lo = 20 * k + 1
        vals = [lab, f'{lo}–{lo + 19}', MEANING[lab], BLAME_Q.get(lab, 'na (pre-filled)')]
        for j, v in enumerate(vals, 1):
            c = ws.cell(row=r, column=j, value=v); c.alignment = WRAP; c.border = BOX
            if lab in BLAME: c.fill = BLUE
        ws.row_dimensions[r].height = 15 * max(len(MEANING[lab]) // 70 + 1, len(vals[3]) // 45 + 1) + 4
    for col, w in zip('ABCD', (18, 9, 85, 50)):
        ws.column_dimensions[col].width = w
    ws.page_setup.orientation = 'landscape'; ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0; ws.sheet_properties.pageSetUpPr.fitToPage = True


def coding(ws, rows):
    ws.title = 'Coding'
    widths = {'row_id': 7, 'unit': 8, 'machine_label': 16, 'label_meaning': 42, 'text': 90,
              'label_correct': 13, 'blamed_target': 13, 'notes': 28, 'id': 10}
    for j, h in enumerate(COLS, 1):
        c = ws.cell(row=1, column=j, value=h); c.font = Font(bold=True, color='FFFFFF'); c.fill = HEAD
        c.alignment = Alignment(wrap_text=True, vertical='center'); c.border = BOX
        ws.column_dimensions[c.column_letter].width = widths[h]
    for i, row in enumerate(rows, 2):
        for j, h in enumerate(COLS, 1):
            c = ws.cell(row=i, column=j, value=row[h])
            if isinstance(row[h], str) and row[h][:1] in ('=', '+', '-', '@'):
                c.data_type = 's'  # never let Reddit text become a formula
            c.alignment = WRAP; c.border = BOX
        ws.cell(row=i, column=6).fill = YELLOW
        bt = ws.cell(row=i, column=7)
        if row['machine_label'] in BLAME:
            bt.fill = YELLOW
        else:
            bt.fill = GREY; bt.font = Font(color='808080')
        ws.cell(row=i, column=4).font = Font(size=9, color='404040')
        lines = sum(len(p) // 82 + 1 for p in row['text'].split('\n'))
        mlines = len(row['label_meaning']) // 40 + 1
        ws.row_dimensions[i].height = min(409, max(lines * 15, mlines * 12) + 6)
    n = len(rows) + 1
    dv1 = DataValidation(type='list', formula1='"yes,no,unsure"', allow_blank=True, showErrorMessage=True,
                         errorTitle='Use the dropdown', error='Allowed: yes, no, unsure (or leave blank).',
                         showInputMessage=True, promptTitle='label_correct', prompt='Is the machine label right for this text? yes / no / unsure')
    dv2 = DataValidation(type='list', formula1='"yes,no,na"', allow_blank=True, showErrorMessage=True,
                         errorTitle='Use the dropdown', error='Allowed: yes, no, na.',
                         showInputMessage=True, promptTitle='blamed_target', prompt='Only for mentions_execs, mentions_offshore, ai_excuse, blames_workers: does the author actually BLAME that target? Else na.')
    ws.add_data_validation(dv1); ws.add_data_validation(dv2)
    dv1.add(f'F2:F{n}'); dv2.add(f'G2:G{n}')
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = f'A1:I{n}'
    ws.print_title_rows = '1:1'
    ws.page_setup.orientation = 'landscape'; ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0; ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_options.gridLines = True
    ws.page_margins.left = ws.page_margins.right = 0.3; ws.page_margins.top = ws.page_margins.bottom = 0.5
    ws.oddFooter.center.text = 'Page &P of &N'; ws.oddHeader.center.text = '&F'


def _already_coded(outdir):
    """True if any existing coder CSV/XLSX already holds an answer (protects real coding work)."""
    for p in sorted(outdir.glob('check_sheet_coder_*.csv')):
        with p.open(newline='', encoding='utf-8-sig', errors='replace') as f:
            for r in csv.DictReader(f):
                if (r.get('label_correct') or '').strip() or (r.get('notes') or '').strip():
                    return p
    try:
        from openpyxl import load_workbook
        for p in sorted(outdir.glob('check_sheet_coder_*.xlsx')):
            ws = load_workbook(p, read_only=True)['Coding']
            hdr = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
            i = hdr.index('label_correct') if 'label_correct' in hdr else None
            if i is not None and any((row[i] or '') for row in ws.iter_rows(min_row=2, values_only=True)):
                return p
    except Exception:
        pass
    return None


def main():
    rows, hidden = build_rows()
    outdir = A / 'annotations/human_check'; outdir.mkdir(parents=True, exist_ok=True)
    hit = _already_coded(outdir)
    if hit and not FORCE:
        sys.exit(f'Refusing to overwrite: {hit.name} already contains coding. Re-run with --force only if you really want blank sheets.')
    for coder in 'ABCD':
        wb = Workbook(); instructions(wb.active, coder); coding(wb.create_sheet('Coding'), rows)
        wb.save(outdir / f'check_sheet_coder_{coder}.xlsx')
        with (outdir / f'check_sheet_coder_{coder}.csv').open('w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
    print(f'wrote 4 xlsx + 4 csv to {outdir}; rows with hidden trigger given an excerpt: {len(hidden)} -> {hidden}')


if __name__ == '__main__':
    main()
