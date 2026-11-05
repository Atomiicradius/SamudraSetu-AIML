"""
Backtest module.

Walks backward through the historical series to several past decision
points. At each point the SAME forecast + risk + recommendation rule used
live in the app is re-applied using only the data available before that
point (no look-ahead).

The spot-only baseline is "never charter early -- just pay whatever spot
costs when the cargo actually needs to move" (the realized rate `horizon`
days later). The rule's simulated strategy only differs from that baseline
when it says "Charter Now" (locking a contract today, at a small premium,
instead of waiting); a "Wait/Monitor" call is scored identically to the
baseline by construction. This isolates how much the "Charter Now" calls
were worth.

The resulting "savings vs spot-only" figure is a backtested/simulated
estimate over a handful of historical decision points, not a guarantee --
the UI must always label it that way.
"""

import numpy as np
import pandas as pd

from backend.forecasting import build_forecast_from_series
from backend.recommendation import CONTRACT_PREMIUM, score_decision
from backend.risk import compute_risk


def run_backtest(series: pd.Series, horizon: int, congestion_level: str, availability_level: str,
                  n_decision_points: int = 18, min_history_days: int = 200) -> dict:
    n = len(series)
    latest_index = n - horizon - 1  # need `horizon` real future days after this point to score the outcome
    earliest_index = min_history_days

    if latest_index <= earliest_index:
        return {"points": [], "avg_savings_per_mt": None, "n_points": 0}

    decision_indices = np.linspace(earliest_index, latest_index, n_decision_points, dtype=int)
    decision_indices = sorted(set(decision_indices.tolist()))

    points = []
    for idx in decision_indices:
        history = series.iloc[: idx + 1]
        future_actual = series.iloc[idx + 1: idx + 1 + horizon]
        if len(future_actual) < horizon:
            continue

        fc = build_forecast_from_series(history, horizon)
        risk = compute_risk(history, congestion_level, availability_level)
        decision, _ = score_decision(fc, risk)

        rate_at_decision = float(history.iloc[-1])
        rate_at_horizon_end = float(future_actual.iloc[-1])

        baseline_rate = rate_at_horizon_end  # spot-only: wait, pay spot when cargo actually needs to move

        if decision == "Charter Now":
            strategy_rate = rate_at_decision * (1 + CONTRACT_PREMIUM)  # lock a contract today instead of waiting
        else:
            strategy_rate = rate_at_horizon_end  # Wait/Monitor -> same outcome as the spot-only baseline

        savings_per_mt = baseline_rate - strategy_rate

        points.append({
            "decision_date": history.index[-1],
            "decision": decision,
            "rate_at_decision": rate_at_decision,
            "realized_rate_after_horizon": rate_at_horizon_end,
            "strategy_rate": strategy_rate,
            "baseline_rate": baseline_rate,
            "savings_per_mt": savings_per_mt,
        })

    avg_savings = float(np.mean([p["savings_per_mt"] for p in points])) if points else None

    return {
        "points": points,
        "avg_savings_per_mt": avg_savings,
        "n_points": len(points),
    }
