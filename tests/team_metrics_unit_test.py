import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

from connections.db import get_test_connection
from models.roster import get_rosters
from models.weekly_player_performance import WeeklyPlayerPerformance
from logic.team_metrics import TeamMetricsModule
from logic.player_metrics import PlayerMetricsModule

load_dotenv()


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

    def test_roster_management_score_keeps_max_value_on_position_collision(self):
        # roster 1, week 1: 3 starter WRs (WR1/WR2/FLEX collision), 3 bench RBs
        # and 3 bench WRs (RB1/RB2/FLEX and WR1/WR2/FLEX collisions, with both
        # overflow groups competing for the single bench FLEX slot)
        season = os.environ['SEASON']
        performance_points = {
            # starters
            '11539': 5.0,   # K
            '11635': 12.0,  # WR -> WR1
            '12518': 9.0,   # TE
            '2216': 8.0,    # WR -> WR2 (bumped to FLEX by 9493)
            '3198': 15.0,   # RB -> RB1
            '4892': 20.0,   # QB
            '8205': 10.0,   # RB -> RB2
            '9493': 18.0,   # WR -> collides with WR2 (8.0), wins, bumps 2216's 8.0 to FLEX
            'SF': 6.0,      # DEF -> DST
            # bench
            '10219': 3.0,   # RB -> RB1
            '11626': 4.0,   # WR -> WR1
            '1479': 22.0,   # WR -> WR2
            '3163': 7.0,    # QB
            '4018': 11.0,   # RB -> RB2
            '7049': 2.0,    # WR -> collides with WR2 (22.0), loses, sent to FLEX
            '7528': 25.0,   # RB -> collides with RB2 (11.0), wins, bumps 11.0 to FLEX
        }
        for player_id, points in performance_points.items():
            WeeklyPlayerPerformance(
                player_id=player_id, week=1, season=season, stats={'pts_half_ppr': points}
            ).save(self.db)

        try:
            metrics = PlayerMetricsModule(self.db, 1)
            self.assertEqual(4.7, metrics.roster_management_score())
        finally:
            for player_id in performance_points:
                self.db.execute(
                    "DELETE FROM weekly_player_performances WHERE player_id = ? AND week = 1 AND season = ?",
                    (player_id, season),
                )
            self.db.commit()


if __name__ == "__main__":
    unittest.main()
