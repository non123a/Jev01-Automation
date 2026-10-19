from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SwingPoint:
    swing_id: str
    symbol: str
    timestamp: datetime
    price: float
    direction: str
    timeframe: str
    confirmed_at: datetime
