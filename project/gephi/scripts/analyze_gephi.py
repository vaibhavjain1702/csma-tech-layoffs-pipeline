"""Analyze the user's Gephi node CSV against the original author network.

Core analysis uses Python's standard library. --plots requires Matplotlib.
Imported centralities are preserved; they are not silently recalculated.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from project import ROOT, GEPHI, GEPHI_ROOT

ALIASES = {
    'scopecommentcount': 'selected_comments', 'outdegreeretained': 'partners_replied_to',
    'indegreeretained': 'replying_partners', 'outweightretained': 'replies_sent',
    'inweightretained': 'replies_received', 'Degree': 'degree', 'Weighted Degree': 'strength',
    'Eccentricity': 'eccentricity', 'closnesscentrality': 'closeness',
    'harmonicclosnesscentrality': 'harmonic_closeness', 'betweenesscentrality': 'betweenness',
    'modularity_class': 'modularity_class', 'clustering': 'clustering',
    'eigencentrality': 'eigenvector', 'Authority': 'authority', 'Hub': 'hub',
    'pageranks': 'pagerank', 'componentnumber': 'weak_component', 'strongcompnum': 'strong_component',
}
RANK_METRICS = ['replies_received', 'replies_sent', 'replying_partners', 'partners_replied_to',
                'pagerank', 'betweenness', 'eigenvector', 'authority', 'hub']
COMPARE = ['replies_received', 'replies_sent', 'pagerank', 'betweenness', 'eigenvector', 'authority', 'hub']
INTEGER_FIELDS = {'selected_comments', 'partners_replied_to', 'replying_partners', 'replies_sent',
                  'replies_received', 'degree', 'strength', 'modularity_class', 'weak_component', 'strong_component'}


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows, fields=None):
    if fields is None:
        fields = list(rows[0])
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def quantile(values, fraction):
    values = sorted(values)
    location = (len(values) - 1) * fraction
    lo, hi = math.floor(location), math.ceil(location)
    return values[lo] + (values[hi] - values[lo]) * (location - lo)


def average_ranks(values):
    ordered = sorted(range(len(values)), key=values.__getitem__)
    result = [0.0] * len(values)
    lo = 0
    while lo < len(ordered):
        hi = lo + 1
        while hi < len(ordered) and values[ordered[hi]] == values[ordered[lo]]:
            hi += 1
        rank = (lo + 1 + hi) / 2
        for index in ordered[lo:hi]:
            result[index] = rank
        lo = hi
    return result


def correlation(a, b):
    am, bm = statistics.mean(a), statistics.mean(b)
    covariance = sum((x - am) * (y - bm) for x, y in zip(a, b))
    divisor = math.sqrt(sum((x - am) ** 2 for x in a) * sum((y - bm) ** 2 for y in b))
    return covariance / divisor if divisor else None


def components(adj, reverse):
    weak, seen = [], set()
    for start in adj:
        if start in seen:
            continue
        group, queue = set(), deque([start])
        seen.add(start)
        while queue:
            node = queue.popleft()
            group.add(node)
            for target in adj[node] + reverse[node]:
                if target not in seen:
                    seen.add(target)
                    queue.append(target)
        weak.append(group)
    order, seen = [], set()
    for start in adj:
        if start in seen:
            continue
        seen.add(start)
        stack = [(start, iter(adj[start]))]
        while stack:
            node, targets = stack[-1]
            target = next(targets, None)
            if target is None:
                order.append(node)
                stack.pop()
            elif target not in seen:
                seen.add(target)
                stack.append((target, iter(adj[target])))
    strong, seen = [], set()
    for start in reversed(order):
        if start in seen:
            continue
        group, stack = set(), [start]
        seen.add(start)
        while stack:
            node = stack.pop()
            group.add(node)
            for target in reverse[node]:
                if target not in seen:
                    seen.add(target)
                    stack.append(target)
        strong.append(group)
    return weak, strong


def imported_partition(rows, field):
    groups = defaultdict(set)
    for row in rows:
        groups[row[field]].add(row['Id'])
    return {frozenset(group) for group in groups.values()}


def modularity_q(edges, nodes, lookup, weighted):
    """Standard undirected modularity at gamma=1 after summing opposite weights."""
    total, internal, strength = 0, Counter(), Counter()
    for edge in edges:
        a, b = edge['Source'], edge['Target']
        if a not in nodes or b not in nodes:
            continue
        weight = int(edge['Weight']) if weighted else 1
        ca, cb = lookup[a]['modularity_class'], lookup[b]['modularity_class']
        total += weight
        strength[ca] += weight
        strength[cb] += weight
        if ca == cb:
            internal[ca] += weight
    return sum(internal[c] / total - (strength[c] / (2 * total)) ** 2 for c in strength)


def plot_outputs(destination, rows, weak_rows, community_rows, correlations, roles):
    cache = ROOT / '.cache' / 'matplotlib'
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR', str(cache))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    figures = destination / 'figures'
    figures.mkdir(exist_ok=True)

    def save(fig, name):
        fig.savefig(figures / f'{name}.png', dpi=170, bbox_inches='tight')
        fig.savefig(figures / f'{name}.svg', bbox_inches='tight')
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    for metric, title, color in [('replies_received', 'Replies received', '#276a91'),
                                  ('replies_sent', 'Replies sent', '#bb652e')]:
        values = sorted((r[metric] for r in rows), reverse=True)
        total, running = sum(values), 0
        x, y = [0], [0]
        for index, value in enumerate(values, 1):
            running += value
            x.append(100 * index / len(values))
            y.append(100 * running / total)
        ax.plot(x, y, color=color, label=title)
    ax.plot([0, 100], [0, 100], '--', color='#999999', label='Equal distribution reference')
    ax.set(xlabel='Users ranked by the measure (% of all users)', ylabel='Cumulative retained replies (%)',
           title='Concentration of reply attention and response activity', xlim=(0, 100), ylim=(0, 102))
    ax.legend(loc='lower right')
    ax.grid(alpha=.15)
    save(fig, 'reply_concentration')

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    sizes = Counter(r['users'] for r in weak_rows)
    names = ['2 users', '3–4 users', '5–9 users', '10–99 users', '100+ users']
    counts = [sum(count for size, count in sizes.items() if lo <= size <= hi)
              for lo, hi in [(2, 2), (3, 4), (5, 9), (10, 99), (100, len(rows))]]
    axes[0].bar(names, counts, color='#276a91')
    axes[0].set_yscale('log')
    axes[0].set(ylabel='Weak components (log scale)', title='Many small components and one large component')
    axes[0].tick_params(axis='x', rotation=30)
    for index, count in enumerate(counts):
        axes[0].text(index, max(count, 1) * 1.15, str(count), ha='center', fontsize=9)
    axes[0].set_ylim(.7, max(counts) * 3)
    largest = community_rows[:10]
    axes[1].barh([str(r['modularity_class']) for r in largest][::-1], [r['users'] for r in largest][::-1], color='#55856c')
    axes[1].set(xlabel='Users', ylabel='Exported group ID', title='Largest groups within the main component')
    fig.tight_layout()
    save(fig, 'components_and_groups')

    matrix = [[correlations[a, b] for b in COMPARE] for a in COMPARE]
    short = ['Received', 'Sent', 'PageRank', 'Betweenness', 'Eigenvector', 'Authority', 'Hub']
    fig, ax = plt.subplots(figsize=(8.4, 6.8))
    im = ax.imshow(matrix, cmap='coolwarm', vmin=-1, vmax=1)
    ax.set_xticks(range(len(short)), short, rotation=40, ha='right')
    ax.set_yticks(range(len(short)), short)
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            ax.text(j, i, f'{value:.2f}', ha='center', va='center', color='white' if abs(value) > .7 else '#222222')
    ax.set_title('Centrality measures capture different interaction roles\nSpearman correlation across all users; ties use average ranks', pad=16)
    fig.colorbar(im, ax=ax, shrink=.8, label='Rank correlation')
    fig.tight_layout()
    save(fig, 'centrality_correlations')

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh([r['role'] for r in roles][::-1], [r['users'] for r in roles][::-1], color=['#55856c', '#bb652e', '#276a91'])
    ax.set(xlabel='Users', title='Observed reply roles in the retained network')
    for index, row in enumerate(roles[::-1]):
        ax.text(row['users'] + 70, index, f'{row["users"]:,} ({row["share_pct"]:.1f}%)', va='center')
    ax.set_xlim(0, max(r['users'] for r in roles) * 1.35)
    fig.tight_layout()
    save(fig, 'reply_roles')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=GEPHI_ROOT / 'input/authors_keyword-comments.csv')
    parser.add_argument('--edges', type=Path, default=GEPHI / 'authors_keyword-comments_direct/edges.csv')
    parser.add_argument('--output', type=Path, default=GEPHI_ROOT / 'analysis')
    parser.add_argument('--plots', action='store_true')
    args = parser.parse_args()
    raw, edges = read_csv(args.input), read_csv(args.edges)
    original = {r['Id']: r for r in read_csv(GEPHI / 'authors_keyword-comments_direct/nodes.csv')}
    if not raw or any(None in r or any(v is None or v == '' for v in r.values()) for r in raw):
        raise ValueError('Empty node table, malformed rows, or missing metric values')
    if len({r['Id'] for r in raw}) != len(raw) or {r['Id'] for r in raw} != set(original):
        raise ValueError('Expected a full-network export with unique original node IDs')
    rows = []
    for source in raw:
        row = {'Id': source['Id'], 'Label': source['Label']}
        for source_key, key in ALIASES.items():
            value = float(source[source_key])
            if not math.isfinite(value) or value < 0:
                raise ValueError(f'Invalid {source_key} for {source["Id"]}')
            if key in INTEGER_FIELDS and value != int(value):
                raise ValueError(f'Noninteger {source_key}')
            row[key] = int(value) if key in INTEGER_FIELDS else value
        rows.append(row)
    lookup = {r['Id']: r for r in rows}
    adj, reverse = {key: [] for key in lookup}, {key: [] for key in lookup}
    in_weight, out_weight = Counter(), Counter()
    pair_lookup = {}
    for edge in edges:
        a, b, weight = edge['Source'], edge['Target'], int(edge['Weight'])
        if a not in lookup or b not in lookup or a == b or (a, b) in pair_lookup or edge['Type'] != 'Directed' or weight < 1:
            raise ValueError('Invalid edge endpoints, type, weight, self-loop, or duplicate pair')
        if not 1 <= int(edge['ThreadCount']) <= weight:
            raise ValueError('Invalid thread count')
        pair_lookup[a, b] = edge
        adj[a].append(b)
        reverse[b].append(a)
        in_weight[b] += weight
        out_weight[a] += weight
    source_pairs = [('scopecommentcount', 'ScopeCommentCount'), ('outdegreeretained', 'OutDegreeRetained'),
                    ('indegreeretained', 'InDegreeRetained'), ('outweightretained', 'OutWeightRetained'),
                    ('inweightretained', 'InWeightRetained')]
    if any(float(r[a]) != float(original[r['Id']][b]) for r in raw for a, b in source_pairs):
        raise ValueError('Imported retained values differ from original node table')
    for row, source in zip(rows, raw):
        key = row['Id']
        expected = {'partners_replied_to': len(adj[key]), 'replying_partners': len(reverse[key]),
                    'replies_sent': out_weight[key], 'replies_received': in_weight[key]}
        if any(row[f] != value for f, value in expected.items()):
            raise ValueError('Node metrics do not match supplied edge topology')
        if row['degree'] != row['replying_partners'] + row['partners_replied_to'] or row['strength'] != row['replies_received'] + row['replies_sent']:
            raise ValueError('Total degree/strength mismatch')
        for a, b in [('indegree', 'replying_partners'), ('outdegree', 'partners_replied_to'),
                     ('weighted indegree', 'replies_received'), ('weighted outdegree', 'replies_sent')]:
            if float(source[a]) != row[b]:
                raise ValueError('Calculated Gephi degrees/weights differ from original retained metrics')
    weak, strong = components(adj, reverse)
    if {frozenset(c) for c in weak} != imported_partition(rows, 'weak_component'):
        raise ValueError('Gephi weak components do not match original edge topology')
    if {frozenset(c) for c in strong} != imported_partition(rows, 'strong_component'):
        raise ValueError('Gephi strong components do not match original edge topology')
    largest = max(weak, key=len)
    n, m, total = len(rows), len(edges), sum(int(e['Weight']) for e in edges)
    for row in rows:
        row['in_largest_weak_component'] = int(row['Id'] in largest)
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / 'nodes_analyzed.csv', rows)
    metric_summary = []
    for metric in ALIASES.values():
        if metric.endswith('component') or metric == 'modularity_class':
            continue
        values = [r[metric] for r in rows]
        metric_summary.append({'metric': metric, 'nodes': n, 'mean': statistics.mean(values),
                               'median': statistics.median(values), 'p90': quantile(values, .9),
                               'p99': quantile(values, .99), 'max': max(values),
                               'zero_nodes': sum(v == 0 for v in values), 'unique_values': len(set(values))})
    write_csv(output / 'metric_summary.csv', metric_summary)
    rankings, top_sets = [], {}
    for metric in RANK_METRICS:
        ordered = sorted(rows, key=lambda r: (-r[metric], r['Id']))[:20]
        top_sets[metric] = {r['Id'] for r in ordered}
        rankings.extend({'ranking_metric': metric, 'position': i, **r} for i, r in enumerate(ordered, 1))
    write_csv(output / 'top20_rankings.csv', rankings)
    rank_vectors = {metric: average_ranks([r[metric] for r in rows]) for metric in COMPARE}
    correlations, comparisons = {}, []
    for a in COMPARE:
        for b in COMPARE:
            correlations[a, b] = correlation(rank_vectors[a], rank_vectors[b])
            comparisons.append({'metric_a': a, 'metric_b': b, 'spearman_rho': correlations[a, b],
                                'shared_top20_users': len(top_sets[a] & top_sets[b]), 'nodes': n})
    write_csv(output / 'centrality_comparisons.csv', comparisons)
    role_counts = Counter('Received only' if r['partners_replied_to'] == 0 else
                          'Sent only' if r['replying_partners'] == 0 else 'Sent and received' for r in rows)
    roles = [{'role': name, 'users': count, 'share_pct': 100 * count / n} for name, count in role_counts.items()]
    write_csv(output / 'reply_roles.csv', roles)
    weak_rows = []
    for group in sorted(weak, key=lambda c: (-len(c), min(c))):
        names = Counter(lookup[key]['modularity_class'] for key in group)
        weak_rows.append({'component_id': lookup[next(iter(group))]['weak_component'], 'users': len(group),
                          'share_pct': 100 * len(group) / n, 'modularity_groups': len(names)})
    write_csv(output / 'weak_components.csv', weak_rows)
    strong_rows = [{'component_id': lookup[next(iter(c))]['strong_component'], 'users': len(c),
                    'share_pct': 100 * len(c) / n} for c in sorted(strong, key=lambda c: (-len(c), min(c)))]
    write_csv(output / 'strong_components.csv', strong_rows)
    groups = defaultdict(list)
    for row in rows:
        groups[row['modularity_class']].append(row)
    group_traffic = defaultdict(Counter)
    matrix = defaultdict(Counter)
    for edge in edges:
        a, b, weight = edge['Source'], edge['Target'], int(edge['Weight'])
        ca, cb = lookup[a]['modularity_class'], lookup[b]['modularity_class']
        if ca == cb:
            group_traffic[ca]['internal_edges'] += 1
            group_traffic[ca]['internal_replies'] += weight
        else:
            group_traffic[ca]['outgoing_between_edges'] += 1
            group_traffic[ca]['outgoing_between_replies'] += weight
            group_traffic[cb]['incoming_between_edges'] += 1
            group_traffic[cb]['incoming_between_replies'] += weight
        if a in largest:
            matrix[ca, cb]['edges'] += 1
            matrix[ca, cb]['replies'] += weight
    community_rows = []
    for label, members in groups.items():
        if len({r['weak_component'] for r in members}) != 1:
            raise ValueError('An exported modularity class spans disconnected weak components')
        biggest = max(members, key=lambda r: (r['replies_received'], r['Id']))
        count = len(members)
        community_rows.append({'modularity_class': label, 'weak_component': members[0]['weak_component'],
                               'in_largest_component': members[0]['in_largest_weak_component'], 'users': count,
                               'share_all_users_pct': 100 * count / n,
                               'share_main_component_pct': 100 * count / len(largest) if members[0]['Id'] in largest else '',
                               **{k: group_traffic[label][k] for k in ['internal_edges', 'internal_replies',
                                  'outgoing_between_edges', 'outgoing_between_replies', 'incoming_between_edges', 'incoming_between_replies']},
                               'mean_clustering': statistics.mean(r['clustering'] for r in members),
                               'most_replied_to_id': biggest['Id'], 'most_replied_to_label': biggest['Label']})
    community_rows.sort(key=lambda r: (-r['users'], r['modularity_class']))
    write_csv(output / 'modularity_groups.csv', community_rows)
    main_groups = [r for r in community_rows if r['in_largest_component']]
    write_csv(output / 'main_component_group_replies.csv',
              [{'source_group': a, 'target_group': b, 'directed_edges': v['edges'], 'retained_replies': v['replies']}
               for (a, b), v in sorted(matrix.items(), key=lambda item: (-item[1]['replies'], item[0]))])
    repeated = [{'Source': e['Source'], 'SourceLabel': lookup[e['Source']]['Label'],
                 'Target': e['Target'], 'TargetLabel': lookup[e['Target']]['Label'],
                 'Weight': int(e['Weight']), 'ThreadCount': int(e['ThreadCount']),
                 'FirstReplyUTC': e['FirstReplyUTC'], 'LastReplyUTC': e['LastReplyUTC'],
                 'ReverseWeight': int(pair_lookup.get((e['Target'], e['Source']), {}).get('Weight', 0))}
                for e in sorted(edges, key=lambda e: (-int(e['ThreadCount']), -int(e['Weight']), e['Source'], e['Target']))
                if int(e['Weight']) > 1]
    write_csv(output / 'repeated_pairs.csv', repeated,
              ['Source', 'SourceLabel', 'Target', 'TargetLabel', 'Weight', 'ThreadCount', 'FirstReplyUTC', 'LastReplyUTC', 'ReverseWeight'])
    concentration = []
    for metric in ['replies_received', 'replies_sent']:
        ordered = sorted((r[metric] for r in rows), reverse=True)
        for title, count in [('top20', 20), ('top1pct', math.ceil(n * .01)), ('top5pct', math.ceil(n * .05))]:
            concentration.append({'metric': metric, 'group': title, 'users': count,
                                  'share_users_pct': 100 * count / n, 'retained_replies': sum(ordered[:count]),
                                  'share_replies_pct': 100 * sum(ordered[:count]) / total})
    write_csv(output / 'reply_concentration.csv', concentration)
    main_edges = [e for e in edges if e['Source'] in largest]
    main_weight = sum(int(e['Weight']) for e in main_edges)
    internal_weight = sum(int(e['Weight']) for e in main_edges
                          if lookup[e['Source']]['modularity_class'] == lookup[e['Target']]['modularity_class'])
    reciprocal_dyads = sum((b, a) in pair_lookup for a, b in pair_lookup) // 2
    closeness_one = [r for r in rows if r['closeness'] == 1]
    sink_neighbors = sum(r['partners_replied_to'] == 1 and not adj[adj[r['Id']][0]] for r in closeness_one)
    authority_total = sum(r['authority'] ** 2 for r in rows)
    summary = {'nodes': n, 'directed_edges': m, 'retained_replies': total, 'directed_density': m / (n * (n - 1)),
               'weak_components': len(weak), 'strong_components': len(strong),
               'largest_weak_component_users': len(largest), 'largest_weak_component_share_pct': 100 * len(largest) / n,
               'largest_strong_component_users': max(map(len, strong)),
               'largest_strong_component_share_pct': 100 * max(map(len, strong)) / n,
               'two_user_weak_components': sum(len(c) == 2 for c in weak),
               'modularity_groups_all': len(groups), 'modularity_groups_main': len(main_groups),
               'other_components_with_multiple_groups': sum(r['modularity_groups'] > 1 for r in weak_rows[1:]),
               'main_component_edges': len(main_edges), 'main_component_replies': main_weight,
               'main_component_internal_group_replies': internal_weight,
               'main_component_internal_group_reply_share_pct': 100 * internal_weight / main_weight,
               'recomputed_undirected_weighted_modularity_gamma1_full': modularity_q(edges, set(lookup), lookup, True),
               'recomputed_undirected_weighted_modularity_gamma1_main': modularity_q(edges, largest, lookup, True),
               'repeated_directed_pairs': len(repeated), 'cross_thread_directed_pairs': sum(int(e['ThreadCount']) > 1 for e in edges),
               'single_reply_pair_share_pct': 100 * sum(int(e['Weight']) == 1 for e in edges) / m,
               'reciprocal_unordered_pairs': reciprocal_dyads,
               'reciprocal_dyad_share_pct': 100 * reciprocal_dyads / (m - reciprocal_dyads),
               'positive_clustering_users': sum(r['clustering'] > 0 for r in rows),
               'closeness_one_users': len(closeness_one), 'closeness_one_single_terminal_neighbor_users': sink_neighbors,
               'positive_betweenness_users': sum(r['betweenness'] > 0 for r in rows),
               'pagerank_export_sum': sum(r['pagerank'] for r in rows),
               'top_authority_squared_norm_share_pct': 100 * max(r['authority'] ** 2 for r in rows) / authority_total,
               'top20_received_betweenness_overlap': len(top_sets['replies_received'] & top_sets['betweenness']),
               'top20_received_pagerank_overlap': len(top_sets['replies_received'] & top_sets['pagerank']),
               'top20_received_sent_overlap': len(top_sets['replies_received'] & top_sets['replies_sent'])}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    settings_path = output / 'run_settings.json'
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {'user_report': 'Not supplied'}
    manifest = {'created_utc': datetime.now(timezone.utc).isoformat(), 'script': 'gephi/scripts/analyze_gephi.py',
                'inputs': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in [args.input, args.edges]},
                'settings': settings, 'validation': {'node_ids_match_original': True, 'retained_values_match_original': True,
                'calculated_degrees_match_edges': True, 'weak_partitions_match_edges': True, 'strong_partitions_match_edges': True,
                'numeric_fields_complete_finite_nonnegative': True},
                'methods': {'quantiles': 'Linear interpolation', 'rank_correlation': 'Pearson correlation of average ranks (Spearman); no p-values',
                'top20': 'Descending metric, then ascending node ID; ties at cutoff can be excluded',
                'modularity_quality': 'Weighted undirected Q at gamma=1 for exported labels; opposite directions summed. No community detection rerun. Not an asserted recovery of the Gephi report.',
                'strong_components': 'Iterative Kosaraju; labels compared as node sets',
                'weak_components': 'Breadth-first traversal ignoring edge direction',
                'export_rounding': 'Gephi centralities are rounded to six decimals; imported values preserved'},
                'plots': args.plots}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    if args.plots:
        plot_outputs(output, rows, weak_rows, main_groups, correlations, roles)
    create_report(output, summary, rows, main_groups, concentration, correlations, roles, args.plots)
    print(json.dumps(summary, indent=2))
    print(f'Analysis written to {output}')


def create_report(output, s, rows, groups, concentration, correlations, roles, plots):
    top = {metric: sorted(rows, key=lambda r: (-r[metric], r['Id']))[0] for metric in RANK_METRICS}
    shares = {(r['metric'], r['group']): r['share_replies_pct'] for r in concentration}
    second_pr = sorted(rows, key=lambda r: (-r['pagerank'], r['Id']))[1]
    settings = json.loads((output / 'run_settings.json').read_text()) if (output / 'run_settings.json').exists() else {}
    probability = settings.get('pagerank_probability_exact')
    epsilon = settings.get('pagerank_epsilon_exact')
    pagerank_settings = (f'The user confirmed PageRank probability **{probability}** and epsilon **{epsilon}**.'
                        if probability is not None and epsilon is not None else
                        'PageRank probability and tolerance were not separately confirmed.')
    text = f'''# Gephi author network: preliminary findings

Python analysis of the user's `authors_keyword-comments.csv`, using the original author-edge export to verify topology. All {s['nodes']:,} node IDs match the original network. Retained and Gephi-calculated degrees/weights agree exactly. Both weak and strong component partitions independently match the edges. Imported centrality values are complete, finite, and nonnegative. The source CSV is preserved.

## 1. Connectedness

The network contains **{s['nodes']:,} users**, **{s['directed_edges']:,} directed user pairs**, and **{s['retained_replies']:,} retained replies**. There are **{s['weak_components']:,} weak components**. The largest includes **{s['largest_weak_component_users']:,} users ({s['largest_weak_component_share_pct']:.1f}%)**; {s['two_user_weak_components']:,} components contain just two users. No isolates are present because the export includes only endpoints of retained edges.

There are **{s['strong_components']:,} strong components**. The largest contains **{s['largest_strong_component_users']:,} users ({s['largest_strong_component_share_pct']:.1f}% of all users)**. Weak connection through a chain of replies is therefore much more widespread than mutual directed reachability. A directed path in this aggregated graph can combine different threads and times; it does not demonstrate a contemporaneous conversation or information diffusion.

See [weak components](weak_components.csv), [strong components](strong_components.csv), and [summary](summary.json).

## 2. Attention and response activity

The top 20 recipients receive **{shares['replies_received', 'top20']:.2f}%** of retained replies. The top 1% of users (rounded up) receive **{shares['replies_received', 'top1pct']:.2f}%**, and the top 5% receive **{shares['replies_received', 'top5pct']:.2f}%**. The top 20 senders contribute **{shares['replies_sent', 'top20']:.2f}%**. These percentages describe the collected network; no external concentration benchmark is assumed.

**{top['replies_received']['Label']}** receives {top['replies_received']['replies_received']:,} replies from {top['replies_received']['replying_partners']:,} distinct users and sends {top['replies_received']['replies_sent']:,} retained replies. **{top['replies_sent']['Label']}** sends {top['replies_sent']['replies_sent']:,} replies to {top['replies_sent']['partners_replied_to']:,} distinct users and receives {top['replies_sent']['replies_received']:,}. This distinguishes an attention recipient from an active responder. Only **{s['top20_received_sent_overlap']} users** appear in both top-20 lists.

| Observed role | Users | Share |
|---|---:|---:|
'''
    text += '\n'.join(f'| {r["role"]} | {r["users"]:,} | {r["share_pct"]:.1f}% |' for r in roles)
    text += f'''

Roles apply only to retained edges. "Received only" does not mean the person never responds on Reddit: their replies may not match keywords or may have been excluded. Replies indicate response attention, which may include disagreement, criticism, or support.

See [concentration](reply_concentration.csv), [roles](reply_roles.csv), and [rankings](top20_rankings.csv). The rankings file contains 20 users per measure, with every analyzed metric. Equal values remain ties even when displayed positions differ.

## 3. Repeated and mutual exchanges

**{s['single_reply_pair_share_pct']:.1f}% of directed pairs represent just one retained reply.** There are {s['repeated_directed_pairs']:,} directed pairs with repeated replies, and only {s['cross_thread_directed_pairs']} directed pairs recur across multiple threads. This export therefore contains mostly one-off directed connections. That finding cannot establish that the users have no ongoing relationships elsewhere.

There are **{s['reciprocal_unordered_pairs']:,} unordered user pairs with replies in both directions**, representing {s['reciprocal_dyad_share_pct']:.2f}% of unordered connected pairs. Reverse edges may occur in different threads or times, so reciprocity here means mutual observed responding rather than a verified dialogue.

See [repeated pairs](repeated_pairs.csv), including reverse weights and thread counts.

## 4. Interpreting modularity groups

The export assigns **{s['modularity_groups_all']:,} modularity classes**, but **{s['modularity_groups_main']} are within the main component**. The other {s['weak_components'] - 1:,} weak components each correspond to one class. Thus the full class count largely reflects fragmentation, rather than thousands of demonstrated thematic communities.

Within the main component, **{s['main_component_internal_group_reply_share_pct']:.1f}% of retained replies connect users in the same exported group** ({s['main_component_internal_group_replies']:,} of {s['main_component_replies']:,}). This is descriptive of a partition optimized using these connections; it is not independent evidence that the groups are meaningful or share narratives.

| Largest main-component group | Users | Share of main component |
|---|---:|---:|
'''
    text += '\n'.join(f'| {r["modularity_class"]} | {r["users"]:,} | {r["share_main_component_pct"]:.2f}% |' for r in groups[:5])
    text += f'''

For an explicit reference calculation, weighted undirected modularity at gamma=1 for the exported labels is {s['recomputed_undirected_weighted_modularity_gamma1_full']:.4f} on the full graph and {s['recomputed_undirected_weighted_modularity_gamma1_main']:.4f} within the main component. This assesses the supplied partition; it does not rerun detection or recover an undocumented Gephi setting. The high full-graph value includes separation of disconnected components. Group labels within the main component were detected in the full graph and have not been optimized separately for the subset.

See [group sizes and traffic](modularity_groups.csv) and [directed group-to-group replies](main_component_group_replies.csv). Group IDs have no intrinsic topic meaning. Gephi's standard Modularity uses an [undirected view](https://github.com/gephi/gephi/blob/master/modules/StatisticsPlugin/src/main/java/org/gephi/statistics/plugin/Modularity.java).

## 5. Centralities capture different roles

The leading betweenness user is **{top['betweenness']['Label']}**, who also sends {top['betweenness']['replies_sent']} replies and receives {top['betweenness']['replies_received']}. Only **{s['top20_received_betweenness_overlap']} users** occur in both the top-20 incoming-reply and betweenness lists. Betweenness identifies positions on modeled shortest paths; it does not prove brokerage, information transmission, or influence. Its exported scale appears unnormalized and is preserved rather than compared with normalized values from other software.

Incoming reply counts and PageRank have a Spearman correlation of **{correlations['replies_received', 'pagerank']:.3f}**, but only **{s['top20_received_pagerank_overlap']} users** overlap between their top-20 lists. For example, the second-highest PageRank belongs to **{second_pr['Label']}**, with {second_pr['replying_partners']} incoming partners and {second_pr['replies_received']} received replies. PageRank weights network position and can elevate users with relatively few incoming connections. It is not a direct popularity count. The exported PageRank values sum to {s['pagerank_export_sum']:.6f}, consistent with rounding of a probability-like vector.

**Closeness is not used to identify influential users here.** {s['closeness_one_users']:,} users have the maximum exported closeness of 1; {s['closeness_one_single_terminal_neighbor_users']:,} of those have one outgoing partner whose own outgoing degree is zero. A perfect score can therefore arise from reaching only one immediate neighbor. Gephi's [distance implementation](https://github.com/gephi/gephi/blob/master/modules/StatisticsPlugin/src/main/java/org/gephi/statistics/plugin/GraphDistance.java) computes directed outgoing distances and averages over reachable nodes. The zero-eccentricity pattern is consistent with directed distance calculations; the setting was not separately recorded.

The top HITS authority accounts for **{s['top_authority_squared_norm_share_pct']:.2f}% of the squared authority-score norm**. This is a numerical concentration measure, not a share of replies or an estimate of authority among workers. HITS and eigenvector rankings are exploratory and depend on topology, algorithm settings, and exported rounding. Only {s['positive_clustering_users']:,} users have a positive exported clustering coefficient; the graph contains little observed local closure, although the exact directed/undirected clustering option is unrecorded.

See [metric distributions](metric_summary.csv) and [rank correlations and top-20 overlaps](centrality_comparisons.csv). Correlations use average ranks for ties and have no inferential p-values. Rounded centralities can introduce ties.

## Settings, scope, and research meaning

The user reports using mostly default settings with edge weights enabled, and mentioned a value of 1 as resolution. {pagerank_settings} The exact association of the resolution value with a dialog is unconfirmed: resolution is a Modularity parameter; PageRank has a separate probability setting. Software version, distance normalization, clustering direction, and randomization are not saved in the CSV. See [reported settings](run_settings.json) and [validation and methods](manifest.json). Analysis describes the exported centralities without silently replacing them. PageRank's confirmed parameters and optional weights correspond to its [implementation](https://github.com/gephi/gephi/blob/master/modules/StatisticsPlugin/src/main/java/org/gephi/statistics/plugin/PageRank.java).

The network includes replies sourced from selected layoff-matching comments, with parent authors as targets. The parent record does not have to match. Unknown authors, missing parents, self-replies, and invalid cross-thread links were excluded. Selective retrieval can remove exchanges and break paths. Collection coverage differs across communities and dates. The original edge export supplies topology; the user supplied a node export, not a newly exported Gephi edge table.

This stage supports claims about observed interaction structure, attention distribution, response activity, and candidate groups/users for later reading. It does not establish support networks, competing narratives, worker status, diffusion, temporal causality, or population-level behavior. Those require conversation content and compatible contextual data. The qualitative pilot remains aside.

## Reproduce

From the project root:

```bash
python gephi/scripts/analyze_gephi.py
```

For the four static figures, use a Python environment with Matplotlib. The existing project plotting environment can run:

```bash
.venv-eda/bin/python gephi/scripts/analyze_gephi.py --plots
```

The original source CSV is unchanged. Output names are stable and regenerated in this folder. Core calculations need only Python's standard library. See [all analyzed nodes](nodes_analyzed.csv) for readable metric names and full/main-component membership.
'''
    if plots:
        text += '''
## Figures

![Reply concentration](figures/reply_concentration.png)

![Components and groups](figures/components_and_groups.png)

![Centrality comparisons](figures/centrality_correlations.png)

![Observed reply roles](figures/reply_roles.png)

Each figure is also supplied as an editable SVG in the figures folder. These plots describe the retained network and exported metrics.
'''
    (output / 'FINDINGS.md').write_text(text, encoding='utf-8')


if __name__ == '__main__':
    main()
