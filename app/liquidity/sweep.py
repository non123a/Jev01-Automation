from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SweepEvent:
    sweep_id: str
    liquidity_id: str
    symbol: str

    timestamp: datetime

    liquidity_price: float
    sweep_price: float

    liquidity_direction: str
    sweep_direction: str

    liquidity_timeframe: str
    liquidity_created_at: datetime

    distance_from_level: float