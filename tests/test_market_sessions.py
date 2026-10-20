
import unittest
from datetime import datetime, timezone

from app.market.state_engine import MarketStateEngine


class MarketSessionTests(unittest.TestCase):
    def test_session_boundaries_use_new_york_time(self):
        cases = [
            ("2026-10-19T03:00:00-04:00", "ASIA"),
            ("2026-10-19T06:59:00-04:00", "ASIA"),
            ("2026-10-19T07:00:00-04:00", "LONDON"),
            ("2026-10-19T12:59:00-04:00", "LONDON"),
            ("2026-10-19T13:00:00-04:00", "NEW_YORK"),
            ("2026-10-19T20:59:00-04:00", "NEW_YORK"),
            ("2026-10-19T21:00:00-04:00", "OFF_SESSION"),
        ]

        for value, expected in cases:
            with self.subTest(value=value):
                timestamp = datetime.fromisoformat(value)
                self.assertEqual(
                    MarketStateEngine.get_session(timestamp),
                    expected,
                )

    def test_same_instant_has_same_session_in_utc_and_new_york(self):
        utc_timestamp = datetime(
            2026, 10, 19, 17, 0, tzinfo=timezone.utc
        )
        new_york_timestamp = datetime.fromisoformat(
            "2026-10-19T13:00:00-04:00"
        )

        self.assertEqual(
            MarketStateEngine.get_session(utc_timestamp),
            MarketStateEngine.get_session(new_york_timestamp),
        )

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            MarketStateEngine.get_session(datetime(2026, 10, 19, 13, 0))


if __name__ == "__main__":
    unittest.main()
