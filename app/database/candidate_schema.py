from __future__ import annotations

from app.database.db import get_connection


SCHEMA = """
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    candidate_time TEXT NOT NULL,
    symbol TEXT NOT NULL,

    -- Market context
    bid REAL NOT NULL,
    ask REAL NOT NULL,
    mid REAL NOT NULL,
    spread REAL NOT NULL,

    session TEXT,
    timeframe_context TEXT,

    -- Liquidity / structure
    liquidity_type TEXT,
    liquidity_price REAL,
    sweep_direction TEXT,
    sweep_price REAL,

    structure_direction TEXT,
    displacement REAL,

    -- Proposed trade
    direction TEXT NOT NULL,
    entry_price REAL NOT NULL,
    stop_price REAL NOT NULL,
    target_price REAL NOT NULL,
    risk_distance REAL NOT NULL,

    -- JEV decision
    jev_decision TEXT NOT NULL,
    jev_version TEXT NOT NULL,
    jev_reason TEXT,

    -- Risk decision
    risk_allowed INTEGER,
    risk_reason TEXT,

    -- Execution
    executed INTEGER NOT NULL DEFAULT 0,
    actual_entry REAL,
    actual_exit REAL,

    -- Outcome
    mfe REAL,
    mae REAL,
    pnl REAL,
    r_multiple REAL,
    outcome TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_candidates_time
ON candidates(candidate_time);

CREATE INDEX IF NOT EXISTS idx_candidates_decision
ON candidates(jev_decision);

CREATE INDEX IF NOT EXISTS idx_candidates_outcome
ON candidates(outcome);
"""


def initialize_candidate_database() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA)
        connection.commit()