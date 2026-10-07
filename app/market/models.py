from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MarketTick:
    timestamp: datetime
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    time_msc: int

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2.0

    @property
    def spread(self) -> float:
        return self.ask - self.bid