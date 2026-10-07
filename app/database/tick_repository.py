from __future__ import annotations

from app.database.db import get_connection
from app.market.models import MarketTick


def save_tick(tick: MarketTick) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO market_ticks (
                time_msc,
                timestamp,
                symbol,
                bid,
                ask,
                last,
                volume,
                spread
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tick.time_msc,
                tick.timestamp.isoformat(),
                tick.symbol,
                tick.bid,
                tick.ask,
                tick.last,
                tick.volume,
                tick.spread,
            ),
        )

        connection.commit()