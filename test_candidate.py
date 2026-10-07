from app.database.candidate_repository import save_candidate


candidate = {
    "candidate_time": "2026-10-06T08:30:00+00:00",
    "symbol": "XAUUSD",

    "bid": 4145.000,
    "ask": 4145.040,
    "mid": 4145.020,
    "spread": 0.040,

    "session": "NY",
    "timeframe_context": "1H/15M/5M",

    "liquidity_type": "previous_day_low",
    "liquidity_price": 4144.500,
    "sweep_direction": "sell_side",
    "sweep_price": 4144.300,

    "structure_direction": "bullish",
    "displacement": 1.20,

    "direction": "long",
    "entry_price": 4145.020,
    "stop_price": 4143.820,
    "target_price": 4148.620,
    "risk_distance": 1.20,

    "jev_decision": "TAKE",
    "jev_version": "JEV-v0.1",
    "jev_reason": "Synthetic test candidate",

    "risk_allowed": 1,
    "risk_reason": "Synthetic test",

    "executed": 0,
    "actual_entry": None,
    "actual_exit": None,

    "mfe": None,
    "mae": None,
    "pnl": None,
    "r_multiple": None,
    "outcome": None,
}


candidate_id = save_candidate(candidate)

print("=" * 60)
print("CANDIDATE SAVE TEST")
print("=" * 60)
print(f"Candidate ID: {candidate_id}")
print("Saved successfully.")