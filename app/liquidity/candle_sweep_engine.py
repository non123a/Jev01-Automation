from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime

from app.liquidity.liquidity_map import ActiveLiquidity
from app.market.bars import CompletedBar


@dataclass(frozen=True)
class ConfirmedSweep:
    event_id: str
    liquidity_id: str
    symbol: str
    timeframe: str
    liquidity_direction: str
    liquidity_price: float
    confirmation_type: str
    sweep_bar_start: datetime
    confirmation_bar_start: datetime
    confirmed_at: datetime
    sweep_extreme: float
    distance_from_level: float
    body_size: float
    average_prior_body: float | None
    body_to_average: float | None


@dataclass(frozen=True)
class PendingSweep:
    level: ActiveLiquidity
    first_bar: CompletedBar
    extreme: float


class CandleSweepEngine:
    """Detect confirmed liquidity sweeps from completed candles."""

    def __init__(
        self,
        lookback: int = 10,
        strength_multiple: float = 1.5,
    ):
        if lookback < 1:
            raise ValueError("lookback must be at least 1")
        if strength_multiple <= 0:
            raise ValueError("strength_multiple must be positive")

        self.lookback = lookback
        self.strength_multiple = strength_multiple

        self.body_history: dict[
            tuple[str, str], deque[float]
        ] = defaultdict(lambda: deque(maxlen=self.lookback))

        self.pending: dict[
            tuple[str, str, str], PendingSweep
        ] = {}

        self.consumed_level_ids: set[str] = set()
        self.counter = 0
        self.last_bar_start: dict[tuple[str, str], datetime] = {}

    @staticmethod
    def _body(bar: CompletedBar) -> float:
        return abs(bar.close - bar.open)

    def update(
        self,
        bar: CompletedBar,
        levels: list[ActiveLiquidity],
    ) -> list[ConfirmedSweep]:
        stream = (bar.symbol, bar.timeframe)
        previous_start = self.last_bar_start.get(stream)

        if previous_start is not None and bar.start <= previous_start:
            raise ValueError(
                "Bars must be supplied in strictly increasing order "
                "for each symbol and timeframe"
            )

        self.last_bar_start[stream] = bar.start
        history = self.body_history[stream]
        events: list[ConfirmedSweep] = []
        handled_pending: set[tuple[str, str, str]] = set()

        matching_levels = {
            (level.symbol, level.timeframe, level.level_id): level
            for level in levels
            if level.active
            and level.symbol == bar.symbol
            and level.timeframe == bar.timeframe
            and level.level_id not in self.consumed_level_ids
            and level.created_at <= bar.start
        }

        # Resolve pending setups. They may survive multiple candles,
        # but only while the original sweep remains valid.
        for key, setup in list(self.pending.items()):
            if key[:2] != stream:
                continue

            handled_pending.add(key)
            level = matching_levels.get(key)

            if level is None:
                del self.pending[key]
                continue

            body = self._body(bar)
            average = (
                sum(history) / self.lookback
                if len(history) == self.lookback
                else None
            )

            if level.direction == "high":
                # Buy-side setup: invalidate if price exceeds the original
                # sweep high or a candle closes back at/above liquidity.
                invalidated = (
                    bar.high > setup.extreme
                    or bar.close >= level.price
                )

                if invalidated:
                    del self.pending[key]
                    continue

                confirmed = (
                    average is not None
                    and average > 0
                    and bar.close < bar.open
                    and bar.close < level.price
                    and body >= self.strength_multiple * average
                )
                extreme = setup.extreme

            elif level.direction == "low":
                # Sell-side setup: invalidate if price breaks the original
                # sweep low or a candle closes at/below liquidity.
                invalidated = (
                    bar.low < setup.extreme
                    or bar.close <= level.price
                )

                if invalidated:
                    del self.pending[key]
                    continue

                confirmed = (
                    average is not None
                    and average > 0
                    and bar.close > bar.open
                    and bar.close > level.price
                    and body >= self.strength_multiple * average
                )
                extreme = setup.extreme

            else:
                del self.pending[key]
                continue

            if not confirmed:
                # Keep waiting while the original setup remains valid.
                continue

            del self.pending[key]
            events.append(
                self._make_event(
                    level=level,
                    sweep_bar=setup.first_bar,
                    confirmation_bar=bar,
                    confirmation_type="delayed",
                    extreme=extreme,
                    body=body,
                    average=average,
                )
            )
            self.consumed_level_ids.add(level.level_id)

        # Look for new sweeps. A level whose pending setup was just
        # resolved cannot be reused by the same candle.
        for key, level in matching_levels.items():
            if key in handled_pending or level.level_id in self.consumed_level_ids:
                continue

            if key in self.pending:
                continue

            if level.direction == "high":
                # Buy-side liquidity: approach from below and sweep above.
                swept_and_rejected = (
                    bar.open < level.price
                    and bar.high > level.price
                    and bar.close < level.price
                )

                if not swept_and_rejected:
                    continue

                if bar.close < bar.open:
                    events.append(
                        self._make_event(
                            level=level,
                            sweep_bar=bar,
                            confirmation_bar=bar,
                            confirmation_type="immediate",
                            extreme=bar.high,
                            body=self._body(bar),
                            average=None,
                        )
                    )
                    self.consumed_level_ids.add(level.level_id)
                else:
                    # Bullish or doji sweep candle: wait exactly one candle.
                    self.pending[key] = PendingSweep(
                        level=level,
                        first_bar=bar,
                        extreme=bar.high,
                    )

            elif level.direction == "low":
                # Sell-side liquidity: approach from above and sweep below.
                swept_and_rejected = (
                    bar.open > level.price
                    and bar.low < level.price
                    and bar.close > level.price
                )

                if not swept_and_rejected:
                    continue

                if bar.close > bar.open:
                    events.append(
                        self._make_event(
                            level=level,
                            sweep_bar=bar,
                            confirmation_bar=bar,
                            confirmation_type="immediate",
                            extreme=bar.low,
                            body=self._body(bar),
                            average=None,
                        )
                    )
                    self.consumed_level_ids.add(level.level_id)
                else:
                    # Bearish or doji sweep candle: wait exactly one candle.
                    self.pending[key] = PendingSweep(
                        level=level,
                        first_bar=bar,
                        extreme=bar.low,
                    )

        # Current candle only enters the baseline for FUTURE candles.
        history.append(self._body(bar))
        return events

    def _make_event(
        self,
        level: ActiveLiquidity,
        sweep_bar: CompletedBar,
        confirmation_bar: CompletedBar,
        confirmation_type: str,
        extreme: float,
        body: float,
        average: float | None,
    ) -> ConfirmedSweep:
        self.counter += 1

        return ConfirmedSweep(
            event_id=f"CANDLE_SWEEP_{self.counter}",
            liquidity_id=level.level_id,
            symbol=level.symbol,
            timeframe=level.timeframe,
            liquidity_direction=level.direction,
            liquidity_price=level.price,
            confirmation_type=confirmation_type,
            sweep_bar_start=sweep_bar.start,
            confirmation_bar_start=confirmation_bar.start,
            confirmed_at=confirmation_bar.end,
            sweep_extreme=extreme,
            distance_from_level=abs(extreme - level.price),
            body_size=body,
            average_prior_body=average,
            body_to_average=(
                body / average if average is not None and average > 0 else None
            ),
        )
