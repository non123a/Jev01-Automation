from __future__ import annotations

from app.database.db import get_connection


SCHEMA = """
CREATE TABLE IF NOT EXISTS market_ticks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    time_msc INTEGER NOT NULL,
    timestamp TEXT NOT NULL,

    symbol TEXT NOT NULL,

    bid REAL NOT NULL,
    ask REAL NOT NULL,
    last REAL NOT NULL,
    volume REAL NOT NULL,

    spread REAL NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(symbol, time_msc)
);


CREATE INDEX IF NOT EXISTS idx_market_ticks_symbol_time
ON market_ticks(symbol, time_msc);


CREATE TABLE IF NOT EXISTS market_bars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,

    bar_start TEXT NOT NULL,
    bar_end TEXT NOT NULL,

    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,

    tick_count INTEGER NOT NULL,

    min_bid REAL,
    max_bid REAL,
    min_ask REAL,
    max_ask REAL,

    min_spread REAL,
    max_spread REAL,
    avg_spread REAL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(symbol, timeframe, bar_start)
);


CREATE INDEX IF NOT EXISTS idx_market_bars_symbol_time
ON market_bars(symbol, timeframe, bar_start);
"""


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA)
        connection.commit()