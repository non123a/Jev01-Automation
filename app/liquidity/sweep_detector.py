from __future__ import annotations

from app.liquidity.liquidity_map import LiquidityMap
from app.liquidity.sweep import SweepEvent
from app.market.models import MarketTick


class SweepDetector:

    def __init__(
        self,
        tolerance: float = 0.001,
    ):
        self.tolerance = tolerance
        self.counter = 0

    def update(
        self,
        tick: MarketTick,
        liquidity_map: LiquidityMap,
    ) -> list[SweepEvent]:

        events = []

        for level in liquidity_map.active_levels():

            sweep_price = None
            sweep_direction = None

            # High liquidity:
            # price must trade ABOVE the known high.
            if level.direction == "high":

                if tick.ask > level.price + self.tolerance:

                    sweep_price = tick.ask
                    sweep_direction = "above"

            # Low liquidity:
            # price must trade BELOW the known low.
            elif level.direction == "low":

                if tick.bid < level.price - self.tolerance:

                    sweep_price = tick.bid
                    sweep_direction = "below"

            if sweep_price is None:
                continue

            self.counter += 1

            event = SweepEvent(
                sweep_id=f"SWEEP_{self.counter}",
                liquidity_id=level.level_id,
                symbol=level.symbol,
                timestamp=tick.timestamp,
                liquidity_price=level.price,
                sweep_price=sweep_price,
                liquidity_direction=level.direction,
                sweep_direction=sweep_direction,
                liquidity_timeframe=level.timeframe,
                liquidity_created_at=level.created_at,
                distance_from_level=abs(
                    sweep_price - level.price
                ),
            )

            events.append(event)

            # A liquidity level is consumed once swept.
            liquidity_map.mark_swept(
                level.level_id
            )

        return events