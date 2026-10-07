from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CompletedBar:
    symbol: str
    timeframe: str

    start: datetime
    end: datetime

    open: float
    high: float
    low: float
    close: float

    tick_count: int