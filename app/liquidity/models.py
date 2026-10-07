from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LiquidityLevel:
    level_id: str
    symbol: str

    price: float

    liquidity_type: str

    created_at: datetime

    source_timeframe: str

    active: bool = True