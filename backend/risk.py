"""
Risk module.

Combines a real, computed forecast-volatility figure (coefficient of
variation over a recent window of the actual series) with two illustrative,
UI-adjustable factors -- port congestion and vessel availability -- that are
NOT fetched from any live source. The combined Low/Medium/High score always
comes with its contributing factors, never a bare label.
"""

import numpy as np
import pandas as pd

CONGESTION_LEVELS = ["Low", "Medium", "High"]
AVAILABILITY_LEVELS = ["Low", "Medium", "High"]  # vessel availability -- Low availability raises risk

_LEVEL_SCORE = {"Low": 0, "Medium": 1, "High": 2}
# for availability, risk rises as availability falls, so invert the mapping
_AVAILABILITY_RISK_SCORE = {"Low": 2, "Medium": 1, "High": 0}


def compute_volatility(series: pd.Series, window: int = 30) -> float:
    """Coefficient of variation (std / mean) of the recent window of the
    actual rate series -- a real, computed measure of recent price spread."""
    recent = series.iloc[-window:]
    mean = recent.mean()
    if mean == 0:
        return 0.0
    return float(recent.std() / mean)


def _volatility_score(cv: float) -> int:
    if cv < 0.03:
        return 0
    if cv < 0.07:
        return 1
    return 2


def compute_risk(series: pd.Series, congestion_level: str, availability_level: str,
                  window: int = 30) -> dict:
    cv = compute_volatility(series, window)
    vol_score = _volatility_score(cv)
    congestion_score = _LEVEL_SCORE[congestion_level]
    availability_score = _AVAILABILITY_RISK_SCORE[availability_level]

    total = vol_score + congestion_score + availability_score  # 0-6

    if total <= 1:
        level = "Low"
    elif total <= 3:
        level = "Medium"
    else:
        level = "High"

    return {
        "level": level,
        "total_score": total,
        "max_score": 6,
        "factors": [
            {"name": "Forecast volatility (CoV, recent window)", "value": f"{cv:.1%}", "score": vol_score, "max": 2},
            {"name": "Port congestion (illustrative, user-set)", "value": congestion_level, "score": congestion_score, "max": 2},
            {"name": "Vessel availability (illustrative, user-set)", "value": availability_level, "score": availability_score, "max": 2},
        ],
    }
