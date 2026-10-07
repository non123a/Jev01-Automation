from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.liquidity.swing import SwingPoint


@dataclass(frozen=True)
class ActiveLiquidity:
    level_id: str
    symbol: str

    price: float
    direction: str

    timeframe: str
    created_at: datetime

    active: bool = True


class LiquidityMap:

    def __init__(self):
        self.levels: dict[str, ActiveLiquidity] = {}

    def add_swing(self, swing: SwingPoint) -> None:

        level = ActiveLiquidity(
            level_id=swing.swing_id,
            symbol=swing.symbol,
            price=swing.price,
            direction=swing.direction,
            timeframe=swing.timeframe,
            created_at=swing.timestamp,
        )

        self.levels[level.level_id] = level

    def active_levels(self) -> list[ActiveLiquidity]:
        return [
            level
            for level in self.levels.values()
            if level.active
        ]

    def levels_by_timeframe(
        self,
        timeframe: str,
    ) -> list[ActiveLiquidity]:

        return [
            level
            for level in self.active_levels()
            if level.timeframe == timeframe
        ]

    def nearest_levels(
        self,
        price: float,
        tolerance: float,
    ) -> list[ActiveLiquidity]:

        return [
            level
            for level in self.active_levels()
            if abs(level.price - price) <= tolerance
        ]

    def mark_swept(
        self,
        level_id: str,
    ) -> None:

        level = self.levels.get(level_id)

        if level is None:
            return

        self.levels[level_id] = ActiveLiquidity(
            level_id=level.level_id,
            symbol=level.symbol,
            price=level.price,
            direction=level.direction,
            timeframe=level.timeframe,
            created_at=level.created_at,
            active=False,
        )