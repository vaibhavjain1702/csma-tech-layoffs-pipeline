"""Export reproducible author rankings from the existing network node CSV.

Run from the project root: python gephi/scripts/export_author_rankings.py
No SQLite database, Gephi installation, or third-party libraries are needed.
"""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from project import GEPHI, GEPHI_ROOT, ROOT


RANKINGS = {
    'top_received_replies.csv': 'InWeightRetained',
    'top_sent_replies.csv': 'OutWeightRetained',
    'top_distinct_replying_users.csv': 'InDegreeRetained',
    'top_distinct_users_replied_to.csv': 'OutDegreeRetained',
}


def export_rankings(source, destination, top):
    with source.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        required = {'Id', 'Label', *RANKINGS.values()}
        if not required.issubset(fields):
            raise ValueError(f'Missing columns: {sorted(required - set(fields))}')
        if {'Position', 'RankingMetric'} & set(fields):
            raise ValueError('Input contains reserved ranking output columns')
        rows = list(reader)
    if not rows:
        raise ValueError('Node table is empty')
    identifiers = [row['Id'] for row in rows]
    if any(not key for key in identifiers) or len(set(identifiers)) != len(rows):
        raise ValueError('Node IDs must be nonempty and unique')
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ValueError('Malformed CSV row')
        for metric in RANKINGS.values():
            if int(row[metric]) < 0:
                raise ValueError('Retained degree and reply counts must be nonnegative')
    destination.mkdir(parents=True, exist_ok=True)
    try:
        source_label = source.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        source_label = source.name
    manifest = {
        'source': source_label,
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_nodes': len(rows),
        'requested_top': top,
        'scope': 'Nodes supplied in the input CSV; default input is the full retained author network.',
        'tie_rule': 'Metric descending, then Id ascending. Position is row order; tied values are not substantive differences.',
        'metrics': 'Retained columns describe the original export, even if input nodes were later filtered in Gephi.',
        'interpretation': 'Reply attention and response activity, not verified influence, agreement, or total Reddit activity.',
        'outputs': {},
    }
    for filename, metric in RANKINGS.items():
        ordered = sorted(rows, key=lambda row: (-int(row[metric]), row['Id']))
        selected = ordered[:top]
        with (destination / filename).open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['Position', 'RankingMetric', *fields])
            writer.writeheader()
            for position, row in enumerate(selected, 1):
                writer.writerow({'Position': position, 'RankingMetric': metric, **row})
        cutoff = int(selected[-1][metric])
        manifest['outputs'][filename] = {
            'metric': metric,
            'rows': len(selected),
            'cutoff_value': cutoff,
            'nodes_tied_at_cutoff_in_input': sum(int(row[metric]) == cutoff for row in rows),
            'nodes_tied_at_cutoff_included': sum(int(row[metric]) == cutoff for row in selected),
        }
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=GEPHI / 'authors_keyword-comments_direct/nodes.csv')
    parser.add_argument('--output', type=Path, default=GEPHI_ROOT / 'rankings')
    parser.add_argument('--top', type=int, default=20)
    args = parser.parse_args()
    if args.top <= 0:
        parser.error('--top must be positive')
    try:
        manifest = export_rankings(args.input, args.output, args.top)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f'Ranked {manifest["source_nodes"]:,} nodes; wrote four top-{args.top} CSVs to {args.output}')
    print('Ties are ordered by node ID; cutoff ties are documented in manifest.json.')


if __name__ == '__main__':
    main()
