"""Check graph partition and rank-statistic methods on small known examples."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'gephi' / 'scripts'))
from analyze_gephi import average_ranks, components, correlation, modularity_q


class GephiAnalysisMethods(unittest.TestCase):
    def test_weak_and_strong_partitions_are_distinct(self):
        # A/B/C cycle, an outgoing tail D, and independent E/F pair.
        adj = {'A': ['B'], 'B': ['C'], 'C': ['A', 'D'], 'D': [], 'E': ['F'], 'F': []}
        reverse = {n: [] for n in adj}
        for n, targets in adj.items():
            for target in targets:
                reverse[target].append(n)
        weak, strong = components(adj, reverse)
        self.assertEqual({frozenset(c) for c in weak}, {frozenset('ABCD'), frozenset('EF')})
        self.assertEqual({frozenset(c) for c in strong},
                         {frozenset('ABC'), frozenset('D'), frozenset('E'), frozenset('F')})

    def test_tied_rank_correlation(self):
        ranks = average_ranks([9, 3, 3, 6])
        self.assertEqual(ranks, [4, 1.5, 1.5, 3])
        self.assertAlmostEqual(correlation(ranks, ranks), 1)
        self.assertAlmostEqual(correlation(ranks, average_ranks([-9, -3, -3, -6])), -1)
        self.assertIsNone(correlation([1, 1], [1, 2]))

    def test_modularity_separated_groups_and_subset(self):
        lookup = {n: {'modularity_class': c} for n, c in [('A', 0), ('B', 0), ('C', 1), ('D', 1)]}
        edges = [{'Source': 'A', 'Target': 'B', 'Weight': '3'},
                 {'Source': 'B', 'Target': 'A', 'Weight': '1'},
                 {'Source': 'C', 'Target': 'D', 'Weight': '4'}]
        self.assertAlmostEqual(modularity_q(edges, set(lookup), lookup, True), .5)
        self.assertAlmostEqual(modularity_q(edges, {'A', 'B'}, lookup, True), 0)
        # Without weights, group edge shares are 2/3 and 1/3: Q = 4/9.
        self.assertAlmostEqual(modularity_q(edges, set(lookup), lookup, False), 4 / 9)


if __name__ == '__main__':
    unittest.main()
