import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from connections.db import get_test_connection
from models.roster import get_rosters
from logic.stats_module import TeamMetricsModule


# python3 -m unittest tests.team_metrics_unit_test -v
class TeamMetricsUnitTest(unittest.TestCase):
    def setUp(self):
        self.db = get_test_connection()

    def tearDown(self):
        self.db.close()

    def test_effective_wins_and_losses_calculates_correctly(self):
        # roster_id, wins, losses
        expected_effective_wins_and_losses = [
            (1, 26, 29),
            (2, 36, 19),
            (3, 27, 28),
            (4, 32, 23),
            (5, 31, 24),
            (6, 15, 40),
            (7, 38, 17),
            (8, 15, 40),
            (9, 21, 34),
            (10, 41, 14),
            (11, 20, 35),
            (12, 28, 27),
        ]
        rosters = get_rosters(self.db)
        self.assertTrue(len(rosters) > 0)
        for roster in rosters:
            metrics = TeamMetricsModule(self.db, roster.roster_id)
            expected_wins, expected_losses = next(
                (wins, losses) for (_id, wins, losses) in expected_effective_wins_and_losses if _id == roster.roster_id
            )
            [actual_wins, actual_losses] = metrics.effective_wins_and_losses(5)
            self.assertEqual(expected_wins, actual_wins)
            self.assertEqual(expected_losses, actual_losses)

    def test_win_percentage(self):
        # roster_id, percentage
        expected_win_percentage = [
            (1, .47),
            (2, .65),
            (3, .49),
            (4, .58),
            (5, .56),
            (6, .27),
            (7, .69),
            (8, .27),
            (9, .38),
            (10, .75),
            (11, .36),
            (12, .51),
        ]
        rosters = get_rosters(self.db)
        self.assertTrue(len(rosters) > 0)
        for roster in rosters:
            metrics = TeamMetricsModule(self.db, roster.roster_id)
            expected_percentage = next(
                (percentage) for (_id, percentage) in expected_win_percentage if _id == roster.roster_id
            )
            actual_percentage = round(metrics.win_percentage(5), 2)
            self.assertEqual(expected_percentage, actual_percentage)

    def test_point_diff(self):
        # roster_id, point_diff normalized to 1
        expected_point_diff = [
            (1, .50),
            (2, .01),
            (3, .23),
            (4, .66),
            (5, .15),
            (6, -.31),
            (7, .17),
            (8, -.87),
            (9, -.48),
            (10, .43),
            (11, -.51),
            (12, .05),
        ]
        rosters = get_rosters(self.db)
        self.assertTrue(len(rosters) > 0)
        for roster in rosters:
            metrics = TeamMetricsModule(self.db, roster.roster_id)
            expected_diff = next(
                (diff) for (_id, diff) in expected_point_diff if _id == roster.roster_id
            )
            actual_diff = round(metrics.point_diff(), 2)
            self.assertEqual(expected_diff, actual_diff)

    def test_point_for(self):
        # roster_id, poitns for normalized to 1
        expected_point_for = [
            (1, .87),
            (2, .93),
            (3, .88),
            (4, .94),
            (5, .95),
            (6, .80),
            (7, .93),
            (8, .74),
            (9, .80),
            (10, 1),
            (11, .77),
            (12, .88),
        ]
        rosters = get_rosters(self.db)
        self.assertTrue(len(rosters) > 0)
        for roster in rosters:
            metrics = TeamMetricsModule(self.db, roster.roster_id)
            expected_pf = next(
                (pf) for (_id, pf) in expected_point_for if _id == roster.roster_id
            )
            actual_pf = round(metrics.points_for_normalized(), 2)
            self.assertEqual(expected_pf, actual_pf)



if __name__ == "__main__":
    unittest.main()
