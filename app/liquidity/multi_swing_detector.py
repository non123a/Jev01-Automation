from __future__ import annotations

from collections import deque

from app.liquidity.swing import SwingPoint
from app.market.bars import CompletedBar


class MultiTimeframeSwingDetector:

    def __init__(self, strength: int = 2):
        self.strength = strength
        self.bars: dict[str, deque] = {}
        self.counters: dict[str, int] = {}

    def update(self, bar: CompletedBar) -> list[SwingPoint]:
        timeframe = bar.timeframe

        if timeframe not in self.bars:
            self.bars[timeframe] = deque(
                maxlen=(self.strength * 2) + 1
            )
            self.counters[timeframe] = 0

        bars = self.bars[timeframe]
        bars.append(bar)
        required = (self.strength * 2) + 1

        if len(bars) < required:
            return []

        values = list(bars)
        center = values[self.strength]
        neighbors = values[:self.strength] + values[self.strength + 1:]
        confirmed_at = values[-1].end
        swings = []

        if all(center.high > other.high for other in neighbors):
            self.counters[timeframe] += 1
            swings.append(SwingPoint(
                swing_id=(
                    f"{timeframe}_SWING_HIGH_"
                    f"{self.counters[timeframe]}"
                ),
                symbol=center.symbol,
                timestamp=center.start,
                price=center.high,
                direction="high",
                timeframe=timeframe,
                confirmed_at=confirmed_at,
            ))

        if all(center.low < other.low for other in neighbors):
            self.counters[timeframe] += 1
            swings.append(SwingPoint(
                swing_id=(
                    f"{timeframe}_SWING_LOW_"
                    f"{self.counters[timeframe]}"
                ),
                symbol=center.symbol,
                timestamp=center.start,
                price=center.low,
                direction="low",
                timeframe=timeframe,
                confirmed_at=confirmed_at,
            ))

        return swings
