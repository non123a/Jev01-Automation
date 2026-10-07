from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketState:
    symbol: str

    timestamp: datetime

    bid: float
    ask: float
    mid: float
    spread: float

    current_bar_start: datetime | None = None

    bar_open: float | None = None
    bar_high: float | None = None
    bar_low: float | None = None
    bar_close: float | None = None

    bar_tick_count: int = 0

    previous_bar_high: float | None = None
    previous_bar_low: float | None = None

    session: str | None = None