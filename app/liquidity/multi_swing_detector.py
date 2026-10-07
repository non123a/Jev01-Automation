from __future__ import annotations

from collections import deque

from app.liquidity.swing import SwingPoint
from app.market.bars import CompletedBar


class MultiTimeframeSwingDetector:

    def __init__(self, strength: int = 2):
        self.strength = strength

        self.bars: dict[str, deque] = {}

        self.counters: dict[str, int] = {}

    def update(
        self,
        bar: CompletedBar,
    ) -> list[SwingPoint]:

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

        center_index = self.strength

        center = values[center_index]

        left = values[:center_index]
        right = values[center_index + 1:]

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

            self.counters[timeframe] += 1

            swings.append(
                SwingPoint(
                    swing_id=(
                        f"{timeframe}_SWING_HIGH_"
                        f"{self.counters[timeframe]}"
                    ),
                    symbol=center.symbol,
                    timestamp=center.start,
                    price=center.high,
                    direction="high",
                    timeframe=timeframe,
                )
            )

        if is_swing_low:

            self.counters[timeframe] += 1

            swings.append(
                SwingPoint(
                    swing_id=(
                        f"{timeframe}_SWING_LOW_"
                        f"{self.counters[timeframe]}"
                    ),
                    symbol=center.symbol,
                    timestamp=center.start,
                    price=center.low,
                    direction="low",
                    timeframe=timeframe,
                )
            )

        return swings