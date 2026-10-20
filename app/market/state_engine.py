from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")

from app.market.bars import CompletedBar
from app.market.models import MarketTick
from app.market.state import MarketState


class MarketStateEngine:

    def __init__(self):
        self.state: MarketState | None = None

    @staticmethod
    # def get_session(timestamp: datetime) -> str:
    #     hour = timestamp.astimezone(timezone.utc).hour

    #     if 0 <= hour < 7:
    #         return "ASIA"

    #     if 7 <= hour < 13:
    #         return "LONDON"

    #     if 13 <= hour < 21:
    #         return "NEW_YORK"

    #     return "OFF_SESSION"
    def get_session(timestamp: datetime) -> str:
        if timestamp.tzinfo is None:
            raise ValueError("Session timestamps must be timezone-aware")

        new_york_time = timestamp.astimezone(NEW_YORK)
        hour = new_york_time.hour

        if 0 <= hour < 7:
            return "ASIA"

        if 7 <= hour < 13:
            return "LONDON"

        if 13 <= hour < 21:
            return "NEW_YORK"

        return "OFF_SESSION"
    @staticmethod
    def minute_start(timestamp: datetime) -> datetime:
        return timestamp.replace(
            second=0,
            microsecond=0,
        )

    def update(
        self,
        tick: MarketTick,
    ) -> tuple[MarketState, CompletedBar | None]:

        bar_start = self.minute_start(tick.timestamp)

        # First tick ever seen.
        if self.state is None:

            self.state = MarketState(
                symbol=tick.symbol,
                timestamp=tick.timestamp,

                bid=tick.bid,
                ask=tick.ask,
                mid=tick.mid,
                spread=tick.spread,

                current_bar_start=bar_start,

                bar_open=tick.mid,
                bar_high=tick.mid,
                bar_low=tick.mid,
                bar_close=tick.mid,

                bar_tick_count=1,

                session=self.get_session(tick.timestamp),
            )

            return self.state, None

        self.state.timestamp = tick.timestamp
        self.state.bid = tick.bid
        self.state.ask = tick.ask
        self.state.mid = tick.mid
        self.state.spread = tick.spread
        self.state.session = self.get_session(tick.timestamp)

        # Still inside the current minute.
        if bar_start == self.state.current_bar_start:

            self.state.bar_high = max(
                self.state.bar_high,
                tick.mid,
            )

            self.state.bar_low = min(
                self.state.bar_low,
                tick.mid,
            )

            self.state.bar_close = tick.mid
            self.state.bar_tick_count += 1

            return self.state, None

        # The previous minute is now complete.
        completed_bar = CompletedBar(
            symbol=self.state.symbol,
            timeframe="1M",

            start=self.state.current_bar_start,
            end=bar_start,

            open=self.state.bar_open,
            high=self.state.bar_high,
            low=self.state.bar_low,
            close=self.state.bar_close,

            tick_count=self.state.bar_tick_count,
        )

        # Start the new minute.
        self.state.current_bar_start = bar_start

        self.state.bar_open = tick.mid
        self.state.bar_high = tick.mid
        self.state.bar_low = tick.mid
        self.state.bar_close = tick.mid

        self.state.bar_tick_count = 1

        self.state.previous_bar_high = completed_bar.high
        self.state.previous_bar_low = completed_bar.low

        return self.state, completed_bar