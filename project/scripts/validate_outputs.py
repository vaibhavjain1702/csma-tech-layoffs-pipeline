#!/usr/bin/env python3
"""Validate exported table row counts, sampling, preparation checks, and Gephi CSVs."""
import argparse
import csv
import gzip
import json
import sys
import hashlib
import struct
import xml.etree.ElementTree as ET
from collections import defaultdict
from project import ROOT,OUTPUTS,TABLES,SAMPLE,GEPHI,PREPROCESS,research_db
sys.path.insert(0,str(ROOT/'gephi'/'scripts'))
from disruption_rules import FACETS,FINGERPRINT,VERSION
from export_gephi import validate_files


def validate_figures():
    directory=OUTPUTS/'04_analysis'/'figures'
    manifest=json.loads((directory/'manifest.json').read_text())
    checks={'source_hashes':'passed','figures':{},'source_tables':{}}
    for source in manifest['sources']:
        path=directory.parent/source['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=source['sha256']:
            raise ValueError(f'Stale figure input: {path}; rerun plot_eda.py')
    for figure in manifest['figures']:
        stem=figure['stem'];png=(directory/(stem+'.png')).read_bytes()
        if png[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError(f'Invalid PNG: {stem}')
        width,height=struct.unpack('>II',png[16:24])
        if width<1 or height<1:raise ValueError('Invalid image dimensions')
        if not ET.parse(directory/(stem+'.svg')).getroot().tag.endswith('svg'):
            raise ValueError(f'Invalid SVG: {stem}')
        checks['figures'][stem]={'png_dimensions':[width,height],'svg_parsed':True}
    stats=json.loads((directory.parent/'descriptive_stats.json').read_text())
    groups=defaultdict(list)
    with (directory/'score_bands.csv').open(newline='') as f:
        for row in csv.DictReader(f):groups[row['kind']].append(row)
    for kind,rows in groups.items():
        n=stats['scores'][kind]['known_scores']
        if sum(int(row['records']) for row in rows)!=n:raise ValueError('Score band frequencies do not sum to score count')
        for row in rows:
            if int(row['known_scores'])!=n or abs(float(row['percent'])-100*int(row['records'])/n)>1e-8:
                raise ValueError('Score-band denominator/percentage mismatch')
    checks['source_tables']['score_bands.csv']='passed'
    groups=defaultdict(list)
    with (directory/'text_availability.csv').open(newline='') as f:
        for row in csv.DictReader(f):groups[(row['subreddit'],row['kind'])].append(row)
    for rows in groups.values():
        n=int(rows[0]['collected_records'])
        if sum(int(row['records']) for row in rows)!=n:raise ValueError('Text states do not sum to collected count')
        for row in rows:
            if int(row['collected_records'])!=n or abs(float(row['percent'])-100*int(row['records'])/n)>1e-8:
                raise ValueError('Text-state denominator/percentage mismatch')
    checks['source_tables']['text_availability.csv']='passed'
    (directory/'validation.json').write_text(json.dumps(checks,indent=2))
    return checks


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick',action='store_true',help='Check CSV headers without fully parsing large tables')
    parser.add_argument('--figures-only',action='store_true',help='Validate optional EDA artifacts without reparsing unchanged large tables')
    args=parser.parse_args();checks={}
    if args.figures_only:
        validate_figures();print('All EDA figure checks passed',flush=True);return
    if not (TABLES/'manifest.json').exists():
        parser.error('Full validation requires the full-project table exports. The review ZIP omits them; use --figures-only for supplied EDA artifacts.')
    manifest=json.loads((TABLES/'manifest.json').read_text())
    missing=[table['file'] for table in manifest['tables'] if not (TABLES/table['file']).exists()]
    if missing:
        parser.error('Full-corpus tables are absent: '+', '.join(missing)+'. The review ZIP omits them; use --figures-only or restore/rebuild the full data.')
    tables=list(manifest['tables'])
    disruption_manifest=TABLES/'disruption_manifest.json'
    if disruption_manifest.exists():
        screening=json.loads(disruption_manifest.read_text())
        if screening['rule_fingerprint']!=FINGERPRINT:raise ValueError('Stale disruption screening rules')
        tables.append({'file':screening['file'],'columns':screening['columns'],'rows':screening['candidate_records']})
        with research_db() as db:
            build=db.execute('SELECT fingerprint,records_scanned FROM screening_builds WHERE version=?',(VERSION,)).fetchone()
            if not build or build[0]!=FINGERPRINT or build[1]!=db.execute('SELECT count(*) FROM records').fetchone()[0]:
                raise ValueError('Incomplete or stale disruption screen')
            if db.execute('SELECT count(*) FROM disruption_screen').fetchone()[0]!=screening['candidate_records']:
                raise ValueError('Disruption candidate count mismatch')
            invalid=' OR '.join(f'{f} NOT IN (0,1)' for f in FACETS)
            empty=' AND '.join(f'{f}=0' for f in FACETS)
            if db.execute(f'SELECT count(*) FROM disruption_screen WHERE ({invalid}) OR ({empty})').fetchone()[0]:
                raise ValueError('Invalid candidate flags')
    for table in tables:
        path=TABLES/table['file']
        opener=gzip.open(path,'rt',encoding='utf-8',newline='') if path.suffix=='.gz' else path.open(newline='',encoding='utf-8')
        with opener as f:
            reader=csv.reader(f);header=next(reader)
            if header!=table['columns']:raise ValueError(f'Incorrect columns: {path}')
            count=0
            if not args.quick:
                for row in reader:
                    if len(row)!=len(header):raise ValueError(f'Incorrect field count: {path}')
                    count+=1
                if count!=table['rows']:raise ValueError(f'Incorrect row count: {path}')
        checks[table['file']]={'rows':table['rows'],'fully_parsed':not args.quick}
        print('Validated',path.name,flush=True)
    for sample_path in sorted(SAMPLE.rglob('reading_sample.json')):
        selected=json.loads(sample_path.read_text())
        if len(selected)!=200 or len({(r['kind'],r['id']) for r in selected})!=200:
            raise ValueError('Reading sample must contain 200 unique focus records')
        packet=[json.loads(line) for line in (sample_path.parent/'reading_packet.jsonl').open()]
        if [(r['record']['kind'],r['record']['id']) for r in packet]!=[(r['kind'],r['id']) for r in selected]:
            raise ValueError('Packet/sample mismatch')
        sample_manifest=json.loads((sample_path.parent/'sample_manifest.json').read_text())
        if sample_manifest.get('focus')=='employment':
            if sample_manifest['rule_fingerprint']!=FINGERPRINT:raise ValueError('Stale employment sample')
            for row in selected:
                evidence=json.loads(row['screen_evidence_json'])
                if set(evidence)!={facet for facet in FACETS if row[facet]}:raise ValueError('Sample evidence/flag mismatch')
                if row['group']=='background' and evidence:raise ValueError('Matching record in background group')
                if row['group']!='background' and row['group'] not in evidence:raise ValueError('Sampling group flag absent')
        checks[str(sample_path.parent.relative_to(OUTPUTS))]={'records':len(selected),'unique_records':len(selected)}
    with (PREPROCESS/'audit.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            if int(row['unavailable_bodies_with_clean_text']) or int(row['inconsistent_character_counts']):
                raise ValueError('Preprocessing audit failed')
    checks['preprocessing_audit']='passed'
    for path in sorted(GEPHI.glob('*/manifest.json')):
        expected=json.loads(path.read_text());actual=validate_files(path.parent)
        if actual['unique_nodes']!=expected['nodes'] or actual['unique_edges']!=expected['edges']:
            raise ValueError('Gephi manifest count mismatch')
        checks[str(path.parent.relative_to(ROOT))]=actual
    if (OUTPUTS/'04_analysis'/'figures'/'manifest.json').exists():
        checks['eda_figures']=validate_figures()
    (OUTPUTS/'validation.json').write_text(json.dumps(checks,indent=2))
    print('All output checks passed',flush=True)


if __name__=='__main__':main()
