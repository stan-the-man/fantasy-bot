import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from connections.db import get_test_connection
from models.roster import get_rosters
from logic.stats_module import MatchMetricsModule


# python3 -m unittest tests.matchmetrics_unit_test -v
class MatchMetricsUnitTest(unittest.TestCase):
    def setUp(self):
        self.db = get_test_connection()

    def tearDown(self):
        self.db.close()

    def test_highest_score(self):
        metrics = MatchMetricsModule(self.db, 1)
        [team, score] = metrics.highest_scorer()
        self.assertEqual(team, 'beelicious ')
        self.assertEqual(score, 138.06)

    def test_lowest_score(self):
        metrics = MatchMetricsModule(self.db, 1)
        [team, score] = metrics.lowest_scorer()
        self.assertEqual(team, 'McLovin')
        self.assertEqual(score, 75.62)

    def test_closest_scores(self):
        metrics = MatchMetricsModule(self.db, 1)
        [(teamA, scoreA), (teamB, scoreB)] = metrics.closest_score()
        self.assertEqual(teamA, 'I Love my McBride Moore')
        self.assertEqual(scoreA, 82.22)
        self.assertEqual(teamB, 'Bundlerooski of Hate')
        self.assertEqual(scoreB, 80.9)


if __name__ == "__main__":
    unittest.main()
