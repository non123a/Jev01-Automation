from __future__ import annotations

from collections import deque

from app.liquidity.swing import SwingPoint
from app.market.bars import CompletedBar


class SwingDetector:

    def __init__(self, strength: int = 2):
        self.strength = strength
        self.bars = deque(
            maxlen=(strength * 2) + 1
        )
        self.counter = 0

    def update(
        self,
        bar: CompletedBar,
    ) -> list[SwingPoint]:

        self.bars.append(bar)

        required = (self.strength * 2) + 1

        if len(self.bars) < required:
            return []

        bars = list(self.bars)

        center_index = self.strength
        center = bars[center_index]

        left = bars[:center_index]
        right = bars[center_index + 1:]

        swings = []

        is_swing_high = all(
            center.high > other.high
            for other in left + right
        )

        is_swing_low = all(
            center.low < other.low
            for other in left + right
        )

        if is_swing_high:

            self.counter += 1

            swings.append(
                SwingPoint(
                    swing_id=f"SWING_HIGH_{self.counter}",
                    symbol=center.symbol,
                    timestamp=center.start,
                    price=center.high,
                    direction="high",
                    timeframe=center.timeframe,
                )
            )

        if is_swing_low:

            self.counter += 1

            swings.append(
                SwingPoint(
                    swing_id=f"SWING_LOW_{self.counter}",
                    symbol=center.symbol,
                    timestamp=center.start,
                    price=center.low,
                    direction="low",
                    timeframe=center.timeframe,
                )
            )

        return swings