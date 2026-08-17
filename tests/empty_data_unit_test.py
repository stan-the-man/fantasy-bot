import os
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from connections.db import get_connection
from models import matchup, roster, user
from models.matchup import Matchup, get_matchup, count_matchups_for_week
from models.roster import Roster
from models.user import User
from logic.stats_module import TeamMetricsModule, MatchMetricsModule
from main import show_rankings, show_paper_metrics


def make_empty_db():
    db = get_connection(":memory:")
    db.execute(matchup.CREATE_TABLE_SQL)
    db.execute(roster.CREATE_TABLE_SQL)
    db.execute(user.CREATE_TABLE_SQL)
    return db


def capture_output(command, client, db):
    out = StringIO()
    with redirect_stdout(out):
        command(client, db, None)
    return out.getvalue()


# python3 -m unittest tests.empty_data_unit_test -v
class EmptyDbTest(unittest.TestCase):
    def setUp(self):
        self.db = make_empty_db()
        self.client = SimpleNamespace(week=1)

    def tearDown(self):
        self.db.close()

    def test_get_matchup_returns_none(self):
        self.assertIsNone(get_matchup(self.db, 1, 1))

    def test_count_matchups_for_week_is_zero(self):
        self.assertEqual(count_matchups_for_week(self.db, 1), 0)

    def test_match_metrics_return_none(self):
        metrics = MatchMetricsModule(self.db, 1)
        self.assertIsNone(metrics.highest_scorer())
        self.assertIsNone(metrics.lowest_scorer())
        self.assertIsNone(metrics.closest_score())

    def test_show_rankings_prompts_setup_when_no_rosters(self):
        output = capture_output(show_rankings, self.client, self.db)
        self.assertIn("No rosters imported yet", output)

    def test_show_paper_metrics_prints_no_data_message(self):
        output = capture_output(show_paper_metrics, self.client, self.db)
        self.assertIn("No matchup data for week 1 yet", output)


class PartialDataTest(unittest.TestCase):
    """Rosters imported and matchup rows present, but no games scored yet
    (the state between Sleeper publishing the schedule and week 1 kickoff)."""

    def setUp(self):
        self.db = make_empty_db()
        self.client = SimpleNamespace(week=1)
        User(user_id="u1", username="user1", display_name="Team One", avatar=None).save(self.db)
        User(user_id="u2", username="user2", display_name="Team Two", avatar=None).save(self.db)
        Roster(roster_id=1, league_id="L", owner_id="u1",
               settings={"fpts": 0, "fpts_against": 0}).save(self.db)
        Roster(roster_id=2, league_id="L", owner_id="u2",
               settings={"fpts": 0, "fpts_against": 0}).save(self.db)
        Matchup(roster_id=1, week=1, matchup_id=1, points=0.0).save(self.db)
        Matchup(roster_id=2, week=1, matchup_id=1, points=0.0).save(self.db)

    def tearDown(self):
        self.db.close()

    def test_show_rankings_guards_zero_fpts(self):
        output = capture_output(show_rankings, self.client, self.db)
        self.assertIn("No scored games for week 1 yet", output)

    def test_missing_week_contributes_nothing_to_record(self):
        metrics = TeamMetricsModule(self.db, 1)
        self.assertEqual(metrics.effective_wins_and_losses_for_week(3), (0, 0))


if __name__ == "__main__":
    unittest.main()
