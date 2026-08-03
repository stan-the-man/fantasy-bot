import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db import get_test_connection
from models.roster import get_rosters
from stats_module import TeamMetricsModule


# python3 -m unittest tests.team_metrics_unit_test -v
class TeamMetricsUnitTest(unittest.TestCase):
    # eventually we will rename the current DB as the test db
    def setUp(self):
        self.db = get_test_connection()

    def tearDown(self):
        self.db.close()

    def test_effective_wins_and_losses_calculates_correctly(self):
        # roster_id, wins, losses
        expected_effective_wins_and_losses = [
            # Santa
            (1, 26, 29),
            # Dane
            (2, 36, 19),
            # Jimmy
            (3, 27, 28),
            # Odie
            (4, 32, 23),
            # Budi
            (5, 31, 24),
            # Mclovin
            (6, 15, 40),
            # Tintin
            (7, 38, 17),
            # Jams
            (8, 15, 40),
            # PE
            (9, 21, 34),
            # Henry
            (10, 41, 14),
            # Xavier
            (11, 20, 35),
            # Maeby
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
        # roster_id, wins, losses
        expected_win_percentage = [
            # Santa
            (1, .47),
            # Dane
            (2, .65),
            # Jimmy
            (3, .49),
            # Odie
            (4, .58),
            # Budi
            (5, .56),
            # Mclovin
            (6, .27),
            # Tintin
            (7, .69),
            # Jams
            (8, .27),
            # PE
            (9, .38),
            # Henry
            (10, .75),
            # Xavier
            (11, .36),
            # Maeby
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
        # roster_id, wins, losses
        expected_point_diff = [
            # Santa
            (1, .50),
            # Dane
            (2, .01),
            # Jimmy
            (3, .23),
            # Odie
            (4, .66),
            # Budi
            (5, .15),
            # Mclovin
            (6, -.31),
            # Tintin
            (7, .17),
            # Jams
            (8, -.87),
            # PE
            (9, -.48),
            # Henry
            (10, .43),
            # Xavier
            (11, -.51),
            # Maeby
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
        # roster_id, wins, losses
        expected_point_for = [
            # Santa
            (1, .87),
            # Dane
            (2, .93),
            # Jimmy
            (3, .88),
            # Odie
            (4, .94),
            # Budi
            (5, .95),
            # Mclovin
            (6, .80),
            # Tintin
            (7, .93),
            # Jams
            (8, .74),
            # PE
            (9, .80),
            # Henry
            (10, 1),
            # Xavier
            (11, .77),
            # Maeby
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
