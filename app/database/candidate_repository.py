from __future__ import annotations

from app.database.db import get_connection


def save_candidate(candidate: dict) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO candidates (
                candidate_time,
                symbol,

                bid,
                ask,
                mid,
                spread,

                session,
                timeframe_context,

                liquidity_type,
                liquidity_price,
                sweep_direction,
                sweep_price,

                structure_direction,
                displacement,

                direction,
                entry_price,
                stop_price,
                target_price,
                risk_distance,

                jev_decision,
                jev_version,
                jev_reason,

                risk_allowed,
                risk_reason,

                executed,
                actual_entry,
                actual_exit,

                mfe,
                mae,
                pnl,
                r_multiple,
                outcome
            )
            VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?
            )
            """,
            (
                candidate["candidate_time"],
                candidate["symbol"],

                candidate["bid"],
                candidate["ask"],
                candidate["mid"],
                candidate["spread"],

                candidate.get("session"),
                candidate.get("timeframe_context"),

                candidate.get("liquidity_type"),
                candidate.get("liquidity_price"),
                candidate.get("sweep_direction"),
                candidate.get("sweep_price"),

                candidate.get("structure_direction"),
                candidate.get("displacement"),

                candidate["direction"],
                candidate["entry_price"],
                candidate["stop_price"],
                candidate["target_price"],
                candidate["risk_distance"],

                candidate["jev_decision"],
                candidate["jev_version"],
                candidate.get("jev_reason"),

                candidate.get("risk_allowed"),
                candidate.get("risk_reason"),

                candidate.get("executed", 0),
                candidate.get("actual_entry"),
                candidate.get("actual_exit"),

                candidate.get("mfe"),
                candidate.get("mae"),
                candidate.get("pnl"),
                candidate.get("r_multiple"),
                candidate.get("outcome"),
            ),
        )

        connection.commit()

        return int(cursor.lastrowid)