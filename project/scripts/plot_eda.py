#!/usr/bin/env python3
"""Produce static EDA figures, source tables, and an interpretation note.

Optional dependency: install requirements-eda.txt in an isolated environment.
Core processing and Gephi exports do not depend on this plotting stage.
"""
import csv
import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1]/'.cache/matplotlib'))
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, PercentFormatter
except ImportError:
    raise SystemExit('Plotting requires Matplotlib. Install requirements-eda.txt; see README.md.')

from project import ANALYSIS, ROOT, research_db
from disruption_rules import FACETS

OUT = ANALYSIS / 'figures'
COLORS = {'cscareerquestions': '#137f76', 'programming': '#7062aa', 'technology': '#2878b5'}
LABELS = {'layoffs': 'Layoffs', 'hiring_conditions': 'Hiring conditions',
    'ai_work_change': 'AI / work change', 'corporate_restructuring': 'Corporate restructuring',
    'economic_policy': 'Economic / policy', 'career_transition': 'Career transitions'}


def read_csv(name):
    with (ANALYSIS / name).open(encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


def write_csv(name, columns, rows):
    with (OUT / name).open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle); writer.writerow(columns); writer.writerows(rows)


def save(fig, stem, note):
    fig.text(.06, .025, note, fontsize=9, color='#4e5b68', va='bottom')
    fig.tight_layout(rect=(.025, .105, .99, .96))
    for extension in ('png', 'svg'):
        fig.savefig(OUT / f'{stem}.{extension}', dpi=170, facecolor='white')
    plt.close(fig)
    print(f'Created {stem}.png and .svg', flush=True)
    return {'stem': stem, 'note': note}


def coverage_plot(monthly, coverage):
    months = sorted({row['month'] for row in monthly})
    lookup = {(row['kind'], row['subreddit'], row['month']): int(row['records']) for row in monthly}
    last_dates = {(row['kind'], row['subreddit']): row['last_utc'][:10] for row in coverage}
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    for ax, kind in zip(axes, ('posts', 'comments')):
        communities = sorted({row['subreddit'] for row in monthly if row['kind'] == kind})
        for sub in communities:
            values = [lookup.get((kind, sub, month), float('nan')) for month in months]
            ax.plot(range(len(months)), values, marker='o', markersize=4, linewidth=2,
                color=COLORS[sub], label=f'r/{sub} (last: {last_dates[(kind, sub)]})')
        ax.set_title('Collected ' + kind, loc='left', fontsize=12)
        ax.set_ylabel('Records / UTC month')
        group_max = max(int(row['records']) for row in monthly if row['kind'] == kind)
        ax.set_ylim(0, group_max*1.22)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x:,.0f}'))
        ax.legend(loc='upper right', fontsize=9, frameon=False)
        ax.grid(axis='y', alpha=.18)
    ticks = list(range(0, len(months), 3))
    if len(months)-1 not in ticks: ticks.append(len(months)-1)
    axes[-1].set_xticks(ticks, [months[index] for index in ticks])
    axes[-1].set_xlabel('Creation month (UTC)')
    fig.suptitle('Collection coverage changes across communities', fontsize=16, x=.06, ha='left')
    return save(fig, '01_monthly_coverage',
        'Absent months are gaps, not zeros. Boundary months can be partial. These are collected records, not Reddit-wide activity.')


def aggregate_monthly(monthly):
    result = defaultdict(lambda: defaultdict(int))
    fields = ('records', 'direct_keyword_matches', 'available_bodies', 'empty_bodies', 'removed_bodies', 'deleted_bodies')
    for row in monthly:
        for field in fields: result[(row['subreddit'], row['kind'])][field] += int(row[field])
    for group in result.values():
        if sum(group[state] for state in fields[2:]) != group['records']:
            raise ValueError('Text-state totals do not equal collected record counts')
    return result


def text_plot(groups):
    keys = sorted(groups, key=lambda key: (key[1], key[0]))
    states = [('available_bodies', 'Available', '#137f76'), ('empty_bodies', 'Empty', '#bfd3e0'),
        ('removed_bodies', 'Removed', '#d78a35'), ('deleted_bodies', 'Deleted', '#ad5b72')]
    fig, ax = plt.subplots(figsize=(12, 6))
    left = [0.0] * len(keys)
    source = []
    for field, label, color in states:
        values = [100 * groups[key][field] / groups[key]['records'] for key in keys]
        ax.barh(range(len(keys)), values, left=left, height=.62, color=color, label=label)
        for index, value in enumerate(values):
            source.append((*keys[index], label.lower(), groups[keys[index]][field], groups[keys[index]]['records'], value))
            if value >= 5:
                ax.text(left[index] + value/2, index, f'{value:.1f}%', ha='center', va='center',
                    color='white' if field == 'available_bodies' else '#172f42', fontsize=10)
        left = [a+b for a, b in zip(left, values)]
    ax.set_yticks(range(len(keys)), [f'r/{sub} — {kind}' for sub, kind in keys])
    ax.invert_yaxis(); ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(PercentFormatter(100))
    ax.set_xlabel('Share of collected record bodies')
    ax.set_title('Comment text is mostly available; post bodies require different interpretation', loc='left', fontsize=14)
    ax.legend(ncol=4, frameon=False, loc='upper center', bbox_to_anchor=(.5, -.14))
    write_csv('text_availability.csv', ['subreddit','kind','text_state','records','collected_records','percent'], source)
    return save(fig, '02_text_availability',
        'Body states only; all stored posts have titles. Empty post bodies often reflect link posts. Labels below 5% are omitted.')


def layoff_plot(groups):
    keys = sorted(groups, key=lambda key: (key[1], key[0]))
    percentages = [100*groups[key]['direct_keyword_matches']/groups[key]['records'] for key in keys]
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.barh(range(len(keys)), percentages, color=[COLORS[key[0]] for key in keys], height=.6)
    for index, key in enumerate(keys):
        ax.text(percentages[index]+.035, index,
            f'{percentages[index]:.2f}%  (n={groups[key]["direct_keyword_matches"]:,})', va='center', fontsize=10)
    ax.set_yticks(range(len(keys)), [f'r/{sub} — {kind}' for sub, kind in keys])
    ax.invert_yaxis(); ax.set_xlim(0, max(percentages)*1.48)
    ax.xaxis.set_major_formatter(PercentFormatter(100))
    ax.set_xlabel('Direct keyword matches / all collected records in group')
    ax.set_title('Explicit layoff language varies within the collected corpus', loc='left', fontsize=14)
    ax.grid(axis='x', alpha=.15); ax.set_axisbelow(True)
    return save(fig, '03_direct_layoff_shares',
        'Original direct layoff screen; not validated relevance. Communities cover different periods. Percentages are corpus descriptions.')


def facet_plot(rows):
    totals = {facet: sum(int(row[facet]) for row in rows) for facet in FACETS}
    order = sorted(FACETS, key=lambda facet: (-totals[facet], facet))
    fig, ax = plt.subplots(figsize=(12, 6))
    left = [0] * len(order)
    for sub in sorted(COLORS):
        values = [sum(int(row[facet]) for row in rows if row['subreddit'] == sub) for facet in order]
        ax.barh(range(len(order)), values, left=left, color=COLORS[sub], height=.65, label='r/'+sub)
        left = [a+b for a, b in zip(left, values)]
    for index, facet in enumerate(order):
        ax.text(totals[facet]+1200, index, f'{totals[facet]:,}', va='center', fontsize=10)
    ax.set_yticks(range(len(order)), [LABELS[facet] for facet in order])
    ax.invert_yaxis(); ax.set_xlim(0, max(totals.values())*1.22)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x:,.0f}'))
    ax.set_xlabel('Candidate records across collected posts and comments')
    ax.set_title('Broader employment screens retrieve candidates beyond layoffs', loc='left', fontsize=14)
    ax.legend(frameon=False, loc='lower right', fontsize=9)
    ax.grid(axis='x', alpha=.15); ax.set_axisbelow(True)
    candidate_total = sum(int(row['candidate_records']) for row in rows)
    return save(fig, '04_broader_candidates',
        f'{candidate_total:,} distinct candidates. Facets overlap; do not add bars. Lexical screens remain unvalidated and do not identify themes or causes.')


def score_plot(stats):
    labels = ['Negative', 'Zero', '1', '2–5', '6–20', '21–100', '101–1,000', '>1,000']
    frequencies = defaultdict(dict)
    with research_db() as db:
        for row in db.execute('''SELECT kind,CASE WHEN score<0 THEN 0 WHEN score=0 THEN 1
            WHEN score=1 THEN 2 WHEN score<=5 THEN 3 WHEN score<=20 THEN 4
            WHEN score<=100 THEN 5 WHEN score<=1000 THEN 6 ELSE 7 END AS bin,count(*)
            FROM records WHERE score IS NOT NULL GROUP BY kind,bin'''):
            frequencies[row[0]][row[1]] = row[2]
    source = []
    fig, ax = plt.subplots(figsize=(12, 6))
    for offset, kind, color in [(-.19, 'posts', '#2878b5'), (.19, 'comments', '#137f76')]:
        total = sum(frequencies[kind].values())
        if total != stats['scores'][kind]['known_scores']: raise ValueError('Score counts do not match descriptive statistics')
        percentages = [100*frequencies[kind].get(index,0)/total for index in range(len(labels))]
        ax.bar([index+offset for index in range(len(labels))], percentages, width=.36, color=color,
            label=f'{kind.title()} (n={total:,})')
        for index, label in enumerate(labels): source.append((kind,index,label,frequencies[kind].get(index,0),total,percentages[index]))
    ax.set_xticks(range(len(labels)), labels)
    ax.yaxis.set_major_formatter(PercentFormatter(100))
    ax.set_ylabel('Share of records with a saved score'); ax.set_xlabel('Saved Reddit score band')
    ax.set_title('Most engagement scores are low; a small upper tail raises the mean', loc='left', fontsize=14)
    ax.legend(frameon=False); ax.grid(axis='y', alpha=.15); ax.set_axisbelow(True)
    write_csv('score_bands.csv',['kind','band_order','score_band','records','known_scores','percent'],source)
    return save(fig, '05_score_distribution',
        f'Median scores: posts {stats["scores"]["posts"]["median"]:g}, comments {stats["scores"]["comments"]["median"]:g}. Means: {stats["scores"]["posts"]["mean_score"]} and {stats["scores"]["comments"]["mean_score"]}. Scores are retrieval snapshots, not exposure or agreement.')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11, 'axes.spines.top':False,
        'axes.spines.right':False, 'axes.titlepad':14, 'axes.labelcolor':'#233d50', 'text.color':'#233d50',
        'xtick.color':'#4e5b68', 'ytick.color':'#4e5b68', 'svg.fonttype':'none'})
    monthly = read_csv('monthly_summary.csv'); coverage = read_csv('coverage.csv')
    facets = read_csv('disruption_summary.csv')
    stats = json.loads((ANALYSIS/'descriptive_stats.json').read_text())
    groups = aggregate_monthly(monthly)
    figures = [coverage_plot(monthly,coverage), text_plot(groups), layoff_plot(groups),
        facet_plot(facets), score_plot(stats)]
    sources = ['monthly_summary.csv','coverage.csv','disruption_summary.csv','descriptive_stats.json']
    manifest = {'generated_utc':datetime.now(timezone.utc).isoformat(), 'script':'scripts/plot_eda.py',
        'python':sys.version.split()[0], 'matplotlib':matplotlib.__version__,
        'sources':[{'file':name,'sha256':hashlib.sha256((ANALYSIS/name).read_bytes()).hexdigest()} for name in sources],
        'database_source':'Score-band counts queried from records in data/processed/reddit.sqlite; exported to score_bands.csv.',
        'figures':figures, 'formats':['png','svg'], 'interpretation':'Descriptive EDA only; no significance tests, causal claims, validated themes, or Gephi analysis.'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    lines = ['# EDA figures and preliminary insights', '', 'Five static figures complement the existing descriptive tables. PNG files are ready for presentation; SVG files support vector export. This is descriptive EDA, with no inferential significance tests or qualitative labels.', '']
    last_dates = {(row['kind'],row['subreddit']):row['last_utc'][:10] for row in coverage}
    available_comments = sum(row['available_bodies'] for (sub,kind),row in groups.items() if kind=='comments')
    n_comments = sum(row['records'] for (sub,kind),row in groups.items() if kind=='comments')
    direct_comments = sum(row['direct_keyword_matches'] for (sub,kind),row in groups.items() if kind=='comments')
    career_matches = groups[('cscareerquestions','comments')]['direct_keyword_matches']
    candidate_total = sum(int(row['candidate_records']) for row in facets)
    findings = [
        ('01_monthly_coverage', 'Coverage constrains time comparisons', f'Technology comments stop on {last_dates[("comments","technology")]} and programming comments on {last_dates[("comments","programming")]}; career-question comments extend to {last_dates[("comments","cscareerquestions")]}. Pooled time patterns can reflect collection changes. Missing months are not plotted as zero activity.'),
        ('02_text_availability', 'Body availability differs between record types', f'{100*available_comments/n_comments:.2f}% of comment bodies are available. Many post bodies are empty while their titles remain present; these require title/link-aware analysis rather than blanket removal.'),
        ('03_direct_layoff_shares', 'Explicit layoff language is concentrated in career comments', f'Career-question comments contain {career_matches:,} of the {direct_comments:,} directly matching comments ({100*career_matches/direct_comments:.2f}%). This is a finding about collected language, not worker prevalence or actual layoffs; community coverage and missing roots matter.'),
        ('04_broader_candidates', 'The broader project scope has a substantial candidate pool', f'The six screens retrieve {candidate_total:,} distinct candidates. Compare overlapping facet counts to identify material for review, not confirmed narratives or causes.'),
        ('05_score_distribution', 'Means alone poorly describe saved engagement', f'Post median/mean scores are {stats["scores"]["posts"]["median"]:g}/{stats["scores"]["posts"]["mean_score"]}; comment median/mean scores are {stats["scores"]["comments"]["median"]:g}/{stats["scores"]["comments"]["mean_score"]}. Inspect score distributions and varied engagement levels rather than relying only on popular examples.')]
    for stem, title, finding in findings:
        lines += ['## '+title, '', finding, '', f'![{title}]({stem}.png)', '', f'[Vector figure]({stem}.svg)', '']
    lines += ['## Reproduce', '', 'Run from the project root after preparing the optional plotting environment:', '', '```bash', '.venv-eda/bin/python scripts/plot_eda.py', '```', '', 'See [the running guide](../../../docs/RUNNING.md) for optional environment setup. Gephi graph visualization and interpretation and human qualitative coding remain pending.']
    (OUT/'EDA_NOTES.md').write_text('\n'.join(lines)+'\n')
    print('Five figures, two source tables, manifest, and EDA_NOTES.md generated.', flush=True)


if __name__ == '__main__': main()
