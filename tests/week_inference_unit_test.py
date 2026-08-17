import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from connections.api_client import infer_week


# python3 -m unittest tests.week_inference_unit_test -v
class WeekInferenceUnitTest(unittest.TestCase):
    def test_regular_season_uses_state_week(self):
        self.assertEqual(infer_week({'season_type': 'regular', 'week': 7}), 7)

    def test_postseason_uses_state_week(self):
        self.assertEqual(infer_week({'season_type': 'post', 'week': 16}), 16)

    def test_preseason_defaults_to_one(self):
        # Sleeper counts preseason weeks in the same field; don't trust it
        self.assertEqual(infer_week({'season_type': 'pre', 'week': 2}), 1)

    def test_offseason_defaults_to_one(self):
        self.assertEqual(infer_week({'season_type': 'off', 'week': 0}), 1)

    def test_missing_or_bad_fields_default_to_one(self):
        self.assertEqual(infer_week({}), 1)
        self.assertEqual(infer_week({'season_type': 'regular'}), 1)
        self.assertEqual(infer_week({'season_type': 'regular', 'week': None}), 1)
        self.assertEqual(infer_week({'season_type': 'regular', 'week': 0}), 1)


if __name__ == "__main__":
    unittest.main()
