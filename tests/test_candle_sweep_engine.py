import unittest
from datetime import datetime, timedelta

from app.liquidity.candle_sweep_engine import CandleSweepEngine
from app.liquidity.liquidity_map import ActiveLiquidity
from app.market.bars import CompletedBar


BASE = datetime(2026, 10, 1, 9, 0, 0)


def bar(
    minute,
    open_price,
    high,
    low,
    close,
    timeframe="1M",
    symbol="XAUUSD",
):
    start = BASE + timedelta(minutes=minute)
    return CompletedBar(
        symbol=symbol,
        timeframe=timeframe,
        start=start,
        end=start + timedelta(minutes=1),
        open=open_price,
        high=high,
        low=low,
        close=close,
        tick_count=10,
    )


def level(
    price=2000.0,
    direction="high",
    created_minute=-10,
    timeframe="1M",
    symbol="XAUUSD",
    level_id="L1",
):
    return ActiveLiquidity(
        level_id=level_id,
        symbol=symbol,
        price=price,
        direction=direction,
        timeframe=timeframe,
        created_at=BASE + timedelta(minutes=created_minute),
        active=True,
    )


def warm_history(engine, timeframe="1M"):
    for minute in range(10):
        engine.update(
            bar(
                minute, 1990, 1992, 1989, 1992,
                timeframe=timeframe,
            ),
            [],
        )


class CandleSweepEngineTests(unittest.TestCase):

    def test_condition_a_buy_side_immediate_bearish(self):
        engine = CandleSweepEngine()
        events = engine.update(
            bar(10, 1999, 2005, 1995, 1997),
            [level()],
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].confirmation_type, "immediate")
        self.assertEqual(events[0].liquidity_direction, "high")

    def test_condition_a_sell_side_immediate_bullish(self):
        engine = CandleSweepEngine()
        events = engine.update(
            bar(10, 2002, 2005, 1995, 2004),
            [level(direction="low")],
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].confirmation_type, "immediate")
        self.assertEqual(events[0].liquidity_direction, "low")

    def test_wrong_side_open_rejected_for_buy_side(self):
        engine = CandleSweepEngine()
        events = engine.update(
            bar(10, 2002, 2005, 1995, 1997),
            [level()],
        )

        self.assertEqual(events, [])
        self.assertEqual(engine.pending, {})

    def test_wrong_side_open_rejected_for_sell_side(self):
        engine = CandleSweepEngine()
        events = engine.update(
            bar(10, 1998, 2005, 1995, 2003),
            [level(direction="low")],
        )

        self.assertEqual(events, [])
        self.assertEqual(engine.pending, {})

    def test_condition_b_buy_side_requires_strong_next_bearish(self):
        engine = CandleSweepEngine()
        target = level()

        warm_history(engine)
        first = engine.update(
            bar(10, 1995, 2004, 1992, 1998),
            [target],
        )
        self.assertEqual(first, [])
        self.assertEqual(len(engine.pending), 1)

        second = engine.update(
            bar(11, 1999, 2001, 1994, 1995),
            [target],
        )

        self.assertEqual(len(second), 1)
        self.assertEqual(second[0].confirmation_type, "delayed")
        self.assertAlmostEqual(second[0].average_prior_body, 2.1)

    def test_condition_b_sell_side_requires_strong_next_bullish(self):
        engine = CandleSweepEngine()
        target = level(price=1980, direction="low")

        warm_history(engine)
        first = engine.update(
            bar(10, 1985, 1988, 1976, 1982),
            [target],
        )
        self.assertEqual(first, [])
        self.assertEqual(len(engine.pending), 1)

        second = engine.update(
            bar(11, 1982, 1987, 1980, 1986),
            [target],
        )

        self.assertEqual(len(second), 1)
        self.assertEqual(second[0].confirmation_type, "delayed")

    def test_weak_confirmation_keeps_setup_pending(self):
        engine = CandleSweepEngine()
        target = level()

        warm_history(engine)
        engine.update(
            bar(10, 1995, 2004, 1992, 1998),
            [target],
        )

        events = engine.update(
            bar(11, 1998, 1999, 1994, 1995.5),
            [target],
        )

        self.assertEqual(events, [])
        self.assertEqual(len(engine.pending), 1)

    def test_later_strong_candle_can_confirm_valid_setup(self):
        engine = CandleSweepEngine()
        target = level()

        warm_history(engine)
        engine.update(
            bar(10, 1995, 2004, 1992, 1998),
            [target],
        )

        # Weak candle: setup stays pending.
        events = engine.update(
            bar(11, 1998, 1999, 1994, 1995.5),
            [target],
        )
        self.assertEqual(events, [])
        self.assertEqual(len(engine.pending), 1)

        # Later strong bearish candle: confirms while staying below
        # the original sweep high (2004) and liquidity level (2000).
        events = engine.update(
            bar(12, 1999, 2001, 1993, 1994),
            [target],
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].confirmation_type, "delayed")
        self.assertEqual(events[0].sweep_extreme, 2004)
        self.assertEqual(engine.pending, {})

    def test_buy_setup_invalidated_above_original_sweep_high(self):
        engine = CandleSweepEngine()
        target = level()

        warm_history(engine)
        engine.update(
            bar(10, 1995, 2004, 1992, 1998),
            [target],
        )
        self.assertEqual(len(engine.pending), 1)

        # High exceeds the original sweep high of 2004.
        events = engine.update(
            bar(11, 1998, 2004.1, 1994, 1995),
            [target],
        )

        self.assertEqual(events, [])
        self.assertEqual(engine.pending, {})

    def test_sell_setup_invalidated_below_original_sweep_low(self):
        engine = CandleSweepEngine()
        target = level(price=1980, direction="low")

        warm_history(engine)
        engine.update(
            bar(10, 1985, 1988, 1976, 1982),
            [target],
        )
        self.assertEqual(len(engine.pending), 1)

        # Low breaks the original sweep low of 1976.
        events = engine.update(
            bar(11, 1982, 1987, 1975.9, 1986),
            [target],
        )

        self.assertEqual(events, [])
        self.assertEqual(engine.pending, {})

    def test_level_created_after_bar_started_is_not_used(self):
        engine = CandleSweepEngine()
        future_level = level(created_minute=11)

        events = engine.update(
            bar(10, 1999, 2005, 1995, 1997),
            [future_level],
        )

        self.assertEqual(events, [])

    def test_other_timeframe_level_is_ignored(self):
        engine = CandleSweepEngine()

        events = engine.update(
            bar(10, 1999, 2005, 1995, 1997, timeframe="1M"),
            [level(timeframe="5M")],
        )

        self.assertEqual(events, [])

    def test_level_cannot_confirm_twice(self):
        engine = CandleSweepEngine()
        target = level()

        first = engine.update(
            bar(10, 1999, 2005, 1995, 1997),
            [target],
        )
        second = engine.update(
            bar(11, 1999, 2006, 1994, 1996),
            [target],
        )

        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])

    def test_wrong_side_buy_setup_cannot_enter_condition_b(self):
        engine = CandleSweepEngine()

        events = engine.update(
            bar(10, 2002, 2005, 1995, 1999),
            [level()],
        )

        self.assertEqual(events, [])
        self.assertEqual(engine.pending, {})

    def test_equal_open_level_is_not_a_valid_approach(self):
        engine = CandleSweepEngine()

        buy_events = engine.update(
            bar(10, 2000, 2005, 1995, 1997),
            [level()],
        )
        sell_events = engine.update(
            bar(
                11, 2000, 2005, 1995, 2003,
            ),
            [level(direction="low", level_id="L2")],
        )

        self.assertEqual(buy_events, [])
        self.assertEqual(sell_events, [])

    def test_bars_must_be_in_increasing_order(self):
        engine = CandleSweepEngine()
        engine.update(bar(10, 1999, 2001, 1998, 2000), [])

        with self.assertRaises(ValueError):
            engine.update(bar(10, 1999, 2001, 1998, 2000), [])


if __name__ == "__main__":
    unittest.main()
