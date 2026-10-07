from __future__ import annotations

import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "jev01.sqlite3"


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30,
    )

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute("PRAGMA foreign_keys=ON;")
    connection.execute("PRAGMA synchronous=NORMAL;")

    return connection