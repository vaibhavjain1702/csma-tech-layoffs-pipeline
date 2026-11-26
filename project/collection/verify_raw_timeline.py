#!/usr/bin/env python3
"""Read-only check of the raw collection: when was each file written, and which content dates did it cover?

Usage:  python3 -B verify_raw_timeline.py "/path/to/raw"

The collector names every batch file  <posts|comments>_batch_<epoch-milliseconds>.json  (collector.py:99-100),
so the file name is the moment (UTC) the batch was saved. This script groups the files by
(type, subreddit) and prints file counts, item counts, the first/last save time and the newest
content date (created_utc) seen. Nothing is written or modified. Standard library only.
"""
import collections
import glob
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

NAME = re.compile(r'(posts|comments)_batch_(\d+)\.json$')


def fmt(epoch_seconds):
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')


def read_file(path):
    kind, epoch_ms = NAME.search(os.path.basename(path)).groups()
    with open(path) as handle:
        items = json.load(handle)
    by_sub = collections.Counter(item.get('subreddit') for item in items)
    newest = max((item.get('created_utc', 0) for item in items), default=0)
    return kind, int(epoch_ms) / 1000, dict(by_sub), newest


def main(root):
    files = glob.glob(os.path.join(root, '*', '*_batch_*.json'))
    print('batch files:', len(files))
    with ThreadPoolExecutor(8) as pool:
        rows = list(pool.map(read_file, files))
    groups = {}
    for kind, saved, subs, newest in rows:
        for sub, count in subs.items():
            g = groups.setdefault((kind, sub), dict(files=0, items=0, first=1e18, last=0, newest=0))
            g['files'] += 1
            g['items'] += count
            g['first'] = min(g['first'], saved)
            g['last'] = max(g['last'], saved)
            g['newest'] = max(g['newest'], newest)
    print('%-10s %-18s %7s %10s  %-16s  %-16s  %s' % ('type', 'subreddit', 'files', 'items', 'first saved UTC', 'last saved UTC', 'newest content UTC'))
    for (kind, sub), g in sorted(groups.items()):
        print('%-10s %-18s %7d %10d  %-16s  %-16s  %s' % (kind, sub, g['files'], g['items'], fmt(g['first']), fmt(g['last']), fmt(g['newest'])))
    print('files per type:', dict(collections.Counter(r[0] for r in rows)))
    print_run_structure(files, rows)


def print_run_structure(files, rows):
    """Gaps in save time (the run split) and the number of files holding exactly 100 items."""
    events = sorted((saved, kind, sub) for kind, saved, subs, _ in rows for sub in subs)
    print('files holding exactly 100 items:', sum(1 for r in rows if sum(r[2].values()) == 100), 'of', len(rows))
    print('gaps over 30 minutes between consecutive saves (global, any stream):')
    for (a, _, _), (b, kind, sub) in zip(events, events[1:]):
        if b - a > 1800:
            print('  %s -> %s  (%.1f h), next file is %s/%s' % (fmt(a), fmt(b), (b - a) / 3600, kind, sub))
    per = collections.defaultdict(list)
    for saved, kind, sub in events:
        per[(kind, sub)].append(saved)
    print('gaps over 30 minutes inside one stream:')
    for key, times in sorted(per.items()):
        for i, (a, b) in enumerate(zip(times, times[1:]), start=1):
            if b - a > 1800:
                print('  %s/%s: %s -> %s  (%.1f h); %d files before the gap, %d after' % (
                    key[0], key[1], fmt(a), fmt(b), (b - a) / 3600, i, len(times) - i))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
