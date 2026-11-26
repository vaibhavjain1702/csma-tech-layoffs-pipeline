#!/usr/bin/env python3
"""Summarize manually edited reading-label CSVs; never assign labels automatically."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from project import ANNOTATIONS,OUTPUTS,ensure_dirs

LABELS=('document_type','themes','emotions','response_function','experiences','explanations','future_expectations')


def summarize(records):
    ids=set();progress=Counter();labels=Counter()
    for row in records:
        key=(row.get('kind'),row.get('id'))
        if not all(key):raise ValueError('Every row needs kind and id')
        if key in ids:raise ValueError(f'Duplicate annotated record: {key}')
        ids.add(key)
        relevance=(row.get('relevance') or '').strip().lower()
        if relevance not in ('','relevant','irrelevant','uncertain'):
            raise ValueError(f'Invalid relevance for {key}: {relevance}')
        group=row.get('group','');community=row.get('subreddit','')
        progress[(group,community,relevance or 'unreviewed')]+=1
        for field in LABELS:
            # One count per distinct label per focus record; multiple codes use semicolons.
            for value in {v.strip().lower() for v in (row.get(field) or '').split(';') if v.strip()}:
                labels[(field,value,group,community)]+=1
    return progress,labels


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ANNOTATIONS/'reading_labels_employment.csv')
    args=parser.parse_args();ensure_dirs()
    with args.input.open(newline='',encoding='utf-8-sig') as f:records=list(csv.DictReader(f))
    progress,labels=summarize(records)
    out=OUTPUTS/'07_annotations';out.mkdir(exist_ok=True)
    with (out/'review_progress.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['group','subreddit','relevance','records'])
        for key,count in sorted(progress.items()):writer.writerow((*key,count))
    with (out/'label_counts.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['field','label','group','subreddit','records'])
        for key,count in sorted(labels.items()):writer.writerow((*key,count))
    summary={'input':str(args.input.resolve()),'records':len(records),
        'reviewed':sum(v for k,v in progress.items() if k[2]!='unreviewed'),
        'unreviewed':sum(v for k,v in progress.items() if k[2]=='unreviewed'),
        'method':'Human-provided codes only; semicolon-separated labels; one count per code per record.',
        'interpretation':'This balanced reading sample is exploratory; counts are not population prevalence estimates.'}
    (out/'manifest.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
