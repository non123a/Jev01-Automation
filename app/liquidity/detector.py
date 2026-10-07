from __future__ import annotations

from collections import deque

from app.liquidity.models import LiquidityLevel
from app.market.state import MarketState


class LiquidityDetector:

    def __init__(self, max_bars: int = 60):
        self.bars = deque(maxlen=max_bars)
        self.level_counter = 0

    def update(self, state: MarketState) -> list[LiquidityLevel]:

        if state.previous_bar_high is None:
            return []

        if state.current_bar_start is None:
            return []

        self.level_counter += 1

        levels = []

        levels.append(
            LiquidityLevel(
                level_id=f"PREV_BAR_HIGH_{self.level_counter}",
                symbol=state.symbol,
                price=state.previous_bar_high,
                liquidity_type="previous_bar_high",
                created_at=state.timestamp,
                source_timeframe="1M",
            )
        )

        if state.previous_bar_low is not None:

            levels.append(
                LiquidityLevel(
                    level_id=f"PREV_BAR_LOW_{self.level_counter}",
                    symbol=state.symbol,
                    price=state.previous_bar_low,
                    liquidity_type="previous_bar_low",
                    created_at=state.timestamp,
                    source_timeframe="1M",
                )
            )

        return levels