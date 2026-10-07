from __future__ import annotations

from datetime import datetime, timezone
import time

import MetaTrader5 as mt5

from app.config import Settings
from app.market.bars import CompletedBar
from app.market.models import MarketTick
from app.mt5.connection import MT5Connection


MT5_TIMEFRAMES = {
    "1M": mt5.TIMEFRAME_M1,
    "5M": mt5.TIMEFRAME_M5,
    "15M": mt5.TIMEFRAME_M15,
    "1H": mt5.TIMEFRAME_H1,
}


class MT5ExnessProvider:

    def __init__(
        self,
        settings: Settings,
        connection: MT5Connection,
    ):
        self.settings = settings
        self.connection = connection

    def get_tick(self) -> MarketTick:

        raw = mt5.symbol_info_tick(
            self.settings.mt5_symbol
        )

        if raw is None:
            raise RuntimeError(
                f"Unable to retrieve tick for "
                f"{self.settings.mt5_symbol}: "
                f"{mt5.last_error()}"
            )

        timestamp_ms = int(raw.time_msc)

        return MarketTick(
            timestamp=datetime.fromtimestamp(
                timestamp_ms / 1000.0,
                tz=timezone.utc,
            ),
            symbol=self.settings.mt5_symbol,
            bid=float(raw.bid),
            ask=float(raw.ask),
            last=float(raw.last),
            volume=float(raw.volume),
            time_msc=timestamp_ms,
        )

    def get_historical_bars(
        self,
        timeframe: str,
        count: int = 100,
    ) -> list[CompletedBar]:

        if timeframe not in MT5_TIMEFRAMES:
            raise ValueError(
                f"Unsupported timeframe: {timeframe}"
            )

        rates = mt5.copy_rates_from_pos(
            self.settings.mt5_symbol,
            MT5_TIMEFRAMES[timeframe],
            1,  # start at previous completed candle
            count,
        )

        if rates is None:
            raise RuntimeError(
                f"Unable to retrieve historical "
                f"{timeframe} bars: {mt5.last_error()}"
            )

        bars = []

        for row in rates:

            start = datetime.fromtimestamp(
                int(row["time"]),
                tz=timezone.utc,
            )

            if timeframe == "1M":
                minutes = 1
            elif timeframe == "5M":
                minutes = 5
            elif timeframe == "15M":
                minutes = 15
            elif timeframe == "1H":
                minutes = 60
            else:
                raise ValueError(
                    f"Unsupported timeframe: {timeframe}"
                )

            end = start.timestamp() + (
                minutes * 60
            )

            bars.append(
                CompletedBar(
                    symbol=self.settings.mt5_symbol,
                    timeframe=timeframe,
                    start=start,
                    end=datetime.fromtimestamp(
                        end,
                        tz=timezone.utc,
                    ),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    tick_count=int(
                        row["tick_volume"]
                    ),
                )
            )

        bars.sort(
            key=lambda bar: bar.start
        )

        return bars

    def stream(
        self,
        interval_seconds: float = 0.1,
    ):

        last_time_msc = None

        while True:

            tick = self.get_tick()

            if tick.time_msc != last_time_msc:

                last_time_msc = tick.time_msc

                yield tick

            time.sleep(interval_seconds)