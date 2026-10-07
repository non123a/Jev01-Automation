from __future__ import annotations

from datetime import datetime, timedelta

from app.market.bars import CompletedBar
from app.market.models import MarketTick


TIMEFRAME_MINUTES = {
    "1M": 1,
    "5M": 5,
    "15M": 15,
    "1H": 60,
}


class MultiTimeframeBarBuilder:

    def __init__(self):
        self.current_bars: dict[str, dict] = {}

    @staticmethod
    def _bar_start(
        timestamp: datetime,
        minutes: int,
    ) -> datetime:

        timestamp = timestamp.replace(
            second=0,
            microsecond=0,
        )

        total_minutes = (
            timestamp.hour * 60
            + timestamp.minute
        )

        aligned_minutes = (
            total_minutes // minutes
        ) * minutes

        return timestamp.replace(
            hour=aligned_minutes // 60,
            minute=aligned_minutes % 60,
        )

    def update(
        self,
        tick: MarketTick,
    ) -> list[CompletedBar]:

        completed = []

        for timeframe, minutes in TIMEFRAME_MINUTES.items():

            start = self._bar_start(
                tick.timestamp,
                minutes,
            )

            current = self.current_bars.get(
                timeframe
            )

            if current is None:

                self.current_bars[timeframe] = {
                    "start": start,
                    "open": tick.mid,
                    "high": tick.mid,
                    "low": tick.mid,
                    "close": tick.mid,
                    "tick_count": 1,
                }

                continue

            if start == current["start"]:

                current["high"] = max(
                    current["high"],
                    tick.mid,
                )

                current["low"] = min(
                    current["low"],
                    tick.mid,
                )

                current["close"] = tick.mid
                current["tick_count"] += 1

                continue

            completed.append(
                CompletedBar(
                    symbol=tick.symbol,
                    timeframe=timeframe,
                    start=current["start"],
                    end=start,
                    open=current["open"],
                    high=current["high"],
                    low=current["low"],
                    close=current["close"],
                    tick_count=current["tick_count"],
                )
            )

            self.current_bars[timeframe] = {
                "start": start,
                "open": tick.mid,
                "high": tick.mid,
                "low": tick.mid,
                "close": tick.mid,
                "tick_count": 1,
            }

        return completed