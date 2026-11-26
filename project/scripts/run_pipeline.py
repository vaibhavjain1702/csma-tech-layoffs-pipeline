#!/usr/bin/env python3
"""Run the staged CSMA data-science workflow; uses the current Python interpreter."""
import argparse
import json
import subprocess
import sys
from datetime import datetime,timezone
from project import ROOT,DB_PATH,PROFILE,OUTPUTS,CACHE,ensure_dirs

STAGES=['profile','preprocess','screen','tables','analysis','plots','sample','gephi','annotations']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stages',nargs='+',choices=STAGES,default=[stage for stage in STAGES if stage not in ('plots','annotations')])
    args=parser.parse_args();ensure_dirs();logs=CACHE/'logs';logs.mkdir(parents=True,exist_ok=True)
    data_stages={'preprocess','screen','tables','analysis','plots','sample','gephi'}
    if not DB_PATH.exists() and (data_stages.intersection(args.stages) or 'profile' in args.stages):
        if 'profile' not in args.stages or not any((ROOT/'raw').glob('*/*.json')):
            parser.error('These stages need the working database or original raw JSON batches. The review ZIP omits them. Place the collection in raw/YYYY-MM/ and run the full pipeline to rebuild; see docs/RUNNING.md.')
    commands={
        'profile':[['profile_data.py']],
        'preprocess':[['preprocess_data.py']],
        'screen':[['screen_disruption.py']],
        'tables':[['export_tables.py']],
        'analysis':[['summarize_data.py'],['preliminary_analysis.py']],
        'plots':[['plot_eda.py']],
        'sample':[['sample_data.py']],
        'gephi':[['export_gephi.py','--network','authors','--scope','keyword-comments','--match','direct'],
                 ['export_gephi.py','--network','conversations','--scope','keyword-posts','--match','direct']],
        'annotations':[['summarize_annotations.py']]
    }
    results=[]
    for stage in STAGES:
        if stage not in args.stages:continue
        if stage=='profile' and DB_PATH.exists() and (PROFILE/'profile.json').exists():
            print('profile: existing index and profile reused',flush=True)
            results.append({'stage':stage,'status':'reused'});continue
        for index,command in enumerate(commands[stage],1):
            log=logs/f'{stage}_{index}.log'
            print(f'{stage}: running {" ".join(command)}; log: {log.relative_to(ROOT)}',flush=True)
            with log.open('w') as output:
                directory=ROOT/'gephi'/'scripts' if stage=='gephi' else ROOT/'scripts'
                run=subprocess.run([sys.executable,str(directory/command[0]),*command[1:]],cwd=ROOT,stdout=output,stderr=subprocess.STDOUT)
            if run.returncode:
                print(log.read_text()[-7000:],file=sys.stderr)
                raise SystemExit(run.returncode)
        results.append({'stage':stage,'status':'completed'})
        print(f'{stage}: complete',flush=True)
    (OUTPUTS/'pipeline_run.json').write_text(json.dumps({'completed_utc':datetime.now(timezone.utc).isoformat(),'stages':results},indent=2))


if __name__=='__main__':main()
