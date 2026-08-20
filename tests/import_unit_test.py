import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from connections.db import get_connection
from models import matchup, roster, user
from models.matchup import import_matchups, count_matchups_for_week, get_matchup, get_top_scoring_matchup
from models.roster import import_rosters, get_roster, get_rosters
from models.user import import_users, get_user

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


# Fixtures are real Sleeper API responses for the test league (display names
# scrubbed to match the anonymized fantasy_bot_test.db).
# python3 -m unittest tests.import_unit_test -v
class ImportUnitTest(unittest.TestCase):
    def setUp(self):
        self.db = get_connection(":memory:")

    def tearDown(self):
        self.db.close()

    def test_import_users(self):
        users = import_users(self.db, load_fixture("users.json"))
        self.assertEqual(len(users), 13)
        santa = get_user(self.db, "1266116820645990400")
        self.assertEqual(santa.display_name, "fWTmhISjXI")
        self.assertEqual(santa.team_name(), "Santa")
        self.assertTrue(get_user(self.db, "995165913596878848").is_owner)
        self.assertFalse(santa.is_owner)

    def test_import_users_handles_null_is_owner(self):
        # regression: Sleeper sends is_owner: null for non-commissioners in
        # some leagues, which used to crash the sqlite insert with int(None)
        users_json = load_fixture("users.json")
        for u in users_json:
            u["is_owner"] = None
        import_users(self.db, users_json)
        self.assertFalse(get_user(self.db, "1266116820645990400").is_owner)

    def test_import_rosters(self):
        import_rosters(self.db, load_fixture("rosters.json"))
        self.assertEqual(len(get_rosters(self.db)), 12)
        r1 = get_roster(self.db, 1)
        self.assertEqual(r1.owner_id, "1266116820645990400")
        self.assertEqual(r1.settings["fpts"], 1469)
        self.assertEqual(r1.settings["wins"], 7)
        self.assertIsInstance(r1.players, list)
        self.assertTrue(all(isinstance(p, str) for p in r1.players))

    def test_import_matchups(self):
        import_matchups(self.db, load_fixture("matchups_1.json"), 1)
        self.assertEqual(count_matchups_for_week(self.db, 1), 12)
        top = get_top_scoring_matchup(self.db, 1)
        self.assertEqual(top.roster_id, 5)
        self.assertEqual(top.points, 138.06)
        m = get_matchup(self.db, 5, 1)
        self.assertEqual(len(m.starters), 9)

    def test_reimport_is_idempotent(self):
        rosters_json = load_fixture("rosters.json")
        import_rosters(self.db, rosters_json)
        import_rosters(self.db, rosters_json)
        self.assertEqual(len(get_rosters(self.db)), 12)


if __name__ == "__main__":
    unittest.main()
