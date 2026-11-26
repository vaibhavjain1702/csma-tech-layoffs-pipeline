#!/usr/bin/env python3
"""Build a portable collaborator ZIP from a deliberate allowlist.

Includes source code and selected review outputs, not raw data, SQLite, heavy
full-corpus exports, runtime environments, caches, or logs. Never sends files.
"""
import argparse
import hashlib
import json
import posixpath
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote
from project import ROOT

PREFIX = 'csma-review'
PACKAGE_NAME = 'package_manifest.json'
LARGE_TABLES = {'posts.csv.gz','comments.csv.gz','threads.csv','reply_edges.csv.gz'}


def selected_files(root):
    paths = [root/'README.md',root/'requirements-eda.txt',root/'gephi/README.md']
    for folder,pattern in [('docs','*.md'),('docs','*.sql'),('scripts','*.py'),('tests','*.py'),
        ('outputs/01_profile','*.csv'),('outputs/01_profile','*.json'),
        ('outputs/02_preprocessing','*.csv'),('outputs/02_preprocessing','*.json'),
        ('outputs/04_analysis','*.csv'),('outputs/04_analysis','*.json'),('outputs/04_analysis','*.md'),
        ('outputs/04_analysis/figures','*.png'),('outputs/04_analysis/figures','*.svg'),
        ('outputs/04_analysis/figures','*.csv'),('outputs/04_analysis/figures','*.json'),('outputs/04_analysis/figures','*.md'),
        ('outputs/05_sample/employment','*.csv'),('outputs/05_sample/employment','*.json'),
        ('outputs/05_sample/employment','*.jsonl'),
        ('gephi/scripts','*.py'),('gephi/tests','*.py')]:
        paths.extend((root/folder).glob(pattern))
    paths.extend((root/'gephi/exports').glob('*/*.csv'))
    paths.extend((root/'gephi/exports').glob('*/manifest.json'))
    paths.append(root/'gephi/input/authors_keyword-comments.csv')
    paths.extend((root/'gephi/rankings').glob('*.csv'))
    paths.append(root/'gephi/rankings/manifest.json')
    for pattern in ('*.csv', '*.json', '*.md', 'figures/*.png', 'figures/*.svg'):
        paths.extend((root/'gephi/analysis').glob(pattern))
    paths.extend((root/'outputs/07_annotations').glob('*.csv'))
    paths.extend((root/'outputs/07_annotations').glob('*.json'))
    for name in ('disruption_candidates.csv.gz','disruption_manifest.json','manifest.json'):
        paths.append(root/'outputs/03_tables'/name)
    paths.extend([root/'annotations/reading_labels_employment.csv',root/'outputs/validation.json'])
    return sorted({path for path in paths if path.is_file()},key=lambda p:p.relative_to(root).as_posix())


def validate_package(path):
    """Check inventory hashes, portable links, required artifacts, and exclusions."""
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:raise ValueError('ZIP CRC check failed')
        names=set(archive.namelist())
        manifest_name=f'{PREFIX}/{PACKAGE_NAME}'
        manifest=json.loads(archive.read(manifest_name))
        expected={f'{PREFIX}/{entry["path"]}' for entry in manifest['files']}|{manifest_name}
        if names!=expected:raise ValueError('ZIP inventory mismatch')
        required=['README.md','docs/RUNNING.md','docs/PROCESS_REPORT.md','gephi/README.md',
            'gephi/input/authors_keyword-comments.csv','gephi/analysis/FINDINGS.md',
            'outputs/04_analysis/figures/EDA_NOTES.md','annotations/reading_labels_employment.csv',
            'outputs/05_sample/employment/reading_packet.jsonl',
            'gephi/exports/authors_keyword-comments_direct/nodes.csv',
            'gephi/exports/authors_keyword-comments_direct/edges.csv',
            'gephi/exports/conversations_keyword-posts_direct/nodes.csv',
            'gephi/exports/conversations_keyword-posts_direct/edges.csv']
        if not all(f'{PREFIX}/{name}' in names for name in required):
            raise ValueError('Missing a core review artifact')
        for entry in manifest['files']:
            relative=Path(entry['path'])
            if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe ZIP path')
            if any(part in ('.cache','.venv-eda','__pycache__','raw','logs') for part in relative.parts):
                raise ValueError('Unexpected private/runtime/intermediate input')
            if entry['path'].startswith('data/processed/') or relative.name in LARGE_TABLES:
                raise ValueError('Unexpected full-corpus data')
            data=archive.read(f'{PREFIX}/{entry["path"]}')
            if len(data)!=entry['bytes'] or hashlib.sha256(data).hexdigest()!=entry['sha256']:
                raise ValueError('ZIP content differs from manifest')
            if relative.suffix=='.md':
                text=data.decode('utf-8')
                for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
                    if target.startswith(('https:','http:','mailto:','#')):continue
                    target=unquote(target.split('#',1)[0].split('?',1)[0])
                    if not target:continue
                    if target.startswith('/') or re.match(r'^[A-Za-z]:',target):
                        raise ValueError(f'Absolute link in {relative}: {target}')
                    resolved=posixpath.normpath(posixpath.join(f'{PREFIX}/{relative.parent.as_posix()}',target))
                    if not resolved.startswith(PREFIX+'/'):raise ValueError('Link escapes package')
                    if resolved not in names and not any(name.startswith(resolved.rstrip('/')+'/') for name in names):
                        raise ValueError(f'Broken review link in {relative}: {target}')
        return {'files':len(manifest['files']),'zip_bytes':Path(path).stat().st_size,
            'crc':'passed','inventory_hashes':'passed','portable_links':'passed','exclusions':'passed'}


def build_package(root, destination):
    files=selected_files(root)
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_name(destination.name+'.tmp')
    manifest={'package':'CSMA collaborator review snapshot','created_utc':datetime.now(timezone.utc).isoformat(),
        'start_here':'README.md','source_script':'scripts/build_share_package.py',
        'purpose':'Review results, inspect methods and source, read/code examples, and import prepared networks into Gephi.',
        'excluded':['raw JSON collection','SQLite working database','full-corpus posts/comments/threads/reply-edge CSVs',
            'local environments','caches','run logs'],
        'reproduction':'Full processing and full-table validation require the original collection/database. Unit tests, supplied-code summaries, and figure-only validation can run with this snapshot.',
        'human_labels':'Snapshot of the current working labels; keep collaborator edits separately and join by kind/id.',
        'files':[]}
    try:
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            for path in files:
                if not path.resolve().is_relative_to(root.resolve()):raise ValueError('Selected file leaves project root')
                data=path.read_bytes();relative=path.relative_to(root).as_posix()
                manifest['files'].append({'path':relative,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
                archive.writestr(f'{PREFIX}/{relative}',data)
            archive.writestr(f'{PREFIX}/{PACKAGE_NAME}',json.dumps(manifest,indent=2)+'\n')
        checks=validate_package(temporary)
        temporary.replace(destination)
        return checks
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'share/csma-review.zip')
    parser.add_argument('--check',type=Path,help='Validate an existing ZIP instead of rebuilding')
    args=parser.parse_args()
    if args.check:
        print(json.dumps(validate_package(args.check),indent=2));return
    checks=build_package(ROOT,args.output.resolve())
    print(f'Created {args.output.resolve()} ({checks["zip_bytes"]/1024**2:.2f} MiB, {checks["files"]} files)')
    print('ZIP contents, hashes, portable document links, and exclusions validated.')


if __name__=='__main__':main()
