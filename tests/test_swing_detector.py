import unittest
from datetime import datetime, timedelta

from app.liquidity.swing_detector import SwingDetector
from app.liquidity.multi_swing_detector import MultiTimeframeSwingDetector
from app.liquidity.liquidity_map import LiquidityMap
from app.market.bars import CompletedBar


BASE = datetime(2026, 10, 1, 9, 0, 0)


def make_bar(minute, high, low, timeframe="1M"):
    start = BASE + timedelta(minutes=minute)
    return CompletedBar(
        symbol="XAUUSD",
        timeframe=timeframe,
        start=start,
        end=start + timedelta(minutes=1),
        open=(high + low) / 2,
        high=high,
        low=low,
        close=(high + low) / 2,
        tick_count=10,
    )


def swing_bars(timeframe="1M"):
    # The center bar at minute 2 is a swing high, but not a swing low.
    values = [
        (10, 2),
        (11, 4),
        (15, 3),
        (12, 4),
        (13, 5),
    ]
    return [
        make_bar(i, high, low, timeframe)
        for i, (high, low) in enumerate(values)
    ]


class SwingDetectorTests(unittest.TestCase):

    def test_swing_waits_for_two_right_side_bars(self):
        detector = SwingDetector(strength=2)
        bars = swing_bars()

        for completed_bar in bars[:4]:
            self.assertEqual(detector.update(completed_bar), [])

        swings = detector.update(bars[4])

        self.assertEqual(len(swings), 1)
        self.assertEqual(swings[0].direction, "high")

    def test_swing_timestamp_and_confirmation_time_are_distinct(self):
        detector = SwingDetector(strength=2)
        bars = swing_bars()

        swings = []
        for completed_bar in bars:
            swings.extend(detector.update(completed_bar))

        swing = next(item for item in swings if item.direction == "high")

        self.assertEqual(swing.timestamp, bars[2].start)
        self.assertEqual(swing.confirmed_at, bars[4].end)
        self.assertGreater(swing.confirmed_at, swing.timestamp)

    def test_multi_timeframe_detector_preserves_timeframe_and_timing(self):
        detector = MultiTimeframeSwingDetector(strength=2)
        bars = swing_bars("5M")

        for completed_bar in bars[:4]:
            self.assertEqual(detector.update(completed_bar), [])

        swings = detector.update(bars[4])
        swing = next(item for item in swings if item.direction == "high")

        self.assertEqual(swing.timeframe, "5M")
        self.assertEqual(swing.timestamp, bars[2].start)
        self.assertEqual(swing.confirmed_at, bars[4].end)

    def test_liquidity_map_uses_confirmation_time(self):
        detector = SwingDetector(strength=2)
        bars = swing_bars()

        swings = []
        for completed_bar in bars:
            swings.extend(detector.update(completed_bar))

        swing = next(item for item in swings if item.direction == "high")

        liquidity_map = LiquidityMap()
        liquidity_map.add_swing(swing)

        level = liquidity_map.levels[swing.swing_id]

        self.assertEqual(level.created_at, swing.confirmed_at)
        self.assertEqual(level.price, swing.price)
        self.assertEqual(level.direction, swing.direction)
        self.assertEqual(level.timeframe, swing.timeframe)

    def test_swing_ids_are_unique_across_timeframes(self):
        detector = MultiTimeframeSwingDetector(strength=2)

        generated_swings = []

        for timeframe in ("1M", "5M"):
            for bar in swing_bars(timeframe):
                generated_swings.extend(detector.update(bar))

        swing_ids = [swing.swing_id for swing in generated_swings]

        self.assertEqual(len(swing_ids), len(set(swing_ids)))

if __name__ == "__main__":
    unittest.main()
