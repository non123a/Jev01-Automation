from __future__ import annotations

from collections import deque

from app.liquidity.swing import SwingPoint
from app.market.bars import CompletedBar


class SwingDetector:

    def __init__(self, strength: int = 2):
        self.strength = strength
        self.bars = deque(maxlen=(strength * 2) + 1)
        self.counter = 0

    def update(self, bar: CompletedBar) -> list[SwingPoint]:
        self.bars.append(bar)
        required = (self.strength * 2) + 1

        if len(self.bars) < required:
            return []

        bars = list(self.bars)
        center = bars[self.strength]
        neighbors = bars[:self.strength] + bars[self.strength + 1:]
        confirmed_at = bars[-1].end
        swings = []

        if all(center.high > other.high for other in neighbors):
            self.counter += 1
            swings.append(SwingPoint(
                swing_id=f"SWING_HIGH_{self.counter}",
                symbol=center.symbol,
                timestamp=center.start,
                price=center.high,
                direction="high",
                timeframe=center.timeframe,
                confirmed_at=confirmed_at,
            ))

        if all(center.low < other.low for other in neighbors):
            self.counter += 1
            swings.append(SwingPoint(
                swing_id=f"SWING_LOW_{self.counter}",
                symbol=center.symbol,
                timestamp=center.start,
                price=center.low,
                direction="low",
                timeframe=center.timeframe,
                confirmed_at=confirmed_at,
            ))

        return swings
