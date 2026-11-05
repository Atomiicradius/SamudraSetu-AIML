"""
Forecast module.

Produces a naive baseline, a statistical (Holt exponential-smoothing) point
forecast, a crude P10/P50/P90 band derived from real holdout-residual spread,
and a probability-of-increase figure computed from historical N-day forward
changes. Nothing here is a hardcoded number — every value is derived from the
scenario's price series.
"""

import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

Z_10_90 = 1.2816  # standard normal quantile for the 10th / 90th percentile
MODEL_NAME = "Holt exponential smoothing (damped trend)"


def get_scenario_series(df: pd.DataFrame, route: str, vessel_class: str, cargo_type: str) -> pd.Series:
    mask = (
        (df["route"] == route)
        & (df["vessel_class"] == vessel_class)
        & (df["cargo_type"] == cargo_type)
    )
    sub = df.loc[mask].sort_values("date")
    return sub.set_index("date")["rate_usd_per_mt"]


def _fit_holt(series: pd.Series):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = ExponentialSmoothing(
            series.values, trend="add", damped_trend=True, seasonal=None
        )
        return model.fit(optimized=True)


def _holdout_residual_std(series: pd.Series, holdout_days: int) -> float:
    """Fit on data up to the holdout window, forecast forward, and measure
    the real error against the actuals we held back. That spread is the
    basis for the P10/P90 band — a crude but genuinely computed estimate."""
    if len(series) <= holdout_days + 30:
        holdout_days = max(5, len(series) // 5)

    train = series.iloc[:-holdout_days]
    actual_holdout = series.iloc[-holdout_days:].values

    fit = _fit_holt(train)
    forecast = fit.forecast(holdout_days)
    residuals = actual_holdout - forecast
    return float(np.std(residuals)), holdout_days


def naive_forecast(series: pd.Series, horizon: int) -> np.ndarray:
    last_value = series.iloc[-1]
    return np.full(horizon, last_value)


def statistical_forecast(series: pd.Series, horizon: int) -> np.ndarray:
    fit = _fit_holt(series)
    return np.asarray(fit.forecast(horizon))


def probability_of_increase(series: pd.Series, horizon: int) -> float:
    """Share of historical horizon-day forward moves that were positive."""
    values = series.values
    n = len(values)
    if n <= horizon:
        return float("nan")
    forward_changes = values[horizon:] - values[:-horizon]
    return float(np.mean(forward_changes > 0))


def holdout_errors(series: pd.Series, holdout_days: int = 60) -> dict:
    """MAE/RMSE for the naive baseline and the statistical forecast over the
    same holdout window used to size the P10/P90 band (same train/test split
    as _holdout_residual_std, computed independently here). Purely a
    diagnostic side-computation -- does not feed into the forecast, the band,
    the risk score, or the backtest, and does not alter any of those."""
    if len(series) <= holdout_days + 30:
        holdout_days = max(5, len(series) // 5)

    train = series.iloc[:-holdout_days]
    actual_holdout = series.iloc[-holdout_days:].values

    stat_fit = _fit_holt(train)
    stat_forecast = np.asarray(stat_fit.forecast(holdout_days))
    naive_holdout = naive_forecast(train, holdout_days)

    def _mae(actual, pred):
        return float(np.mean(np.abs(actual - pred)))

    def _rmse(actual, pred):
        return float(np.sqrt(np.mean((actual - pred) ** 2)))

    return {
        "holdout_days_used": holdout_days,
        "model_name": MODEL_NAME,
        "stat_mae": _mae(actual_holdout, stat_forecast),
        "stat_rmse": _rmse(actual_holdout, stat_forecast),
        "naive_mae": _mae(actual_holdout, naive_holdout),
        "naive_rmse": _rmse(actual_holdout, naive_holdout),
    }


def build_forecast(df: pd.DataFrame, route: str, vessel_class: str, cargo_type: str,
                    horizon: int, holdout_days: int = 60) -> dict:
    series = get_scenario_series(df, route, vessel_class, cargo_type)
    return build_forecast_from_series(series, horizon, holdout_days)


def build_forecast_from_series(series: pd.Series, horizon: int, holdout_days: int = 60) -> dict:
    """Same computation as build_forecast, but operating directly on an
    already-sliced series -- used by the backtest to forecast from data
    available as of a past decision point, with no look-ahead."""
    point = statistical_forecast(series, horizon)
    naive = naive_forecast(series, horizon)
    sigma, holdout_used = _holdout_residual_std(series, holdout_days)

    # sigma reflects the average holdout-horizon error scale; grow it with
    # sqrt(t) for a simple random-walk-style widening uncertainty band
    day_index = np.arange(1, horizon + 1)
    band_width = Z_10_90 * sigma * np.sqrt(day_index)

    p10 = point - band_width
    p90 = point + band_width
    p50 = point

    forecast_dates = pd.date_range(series.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D")

    return {
        "series": series,
        "forecast_dates": forecast_dates,
        "naive": naive,
        "point": point,
        "p10": p10,
        "p50": p50,
        "p90": p90,
        "prob_increase": probability_of_increase(series, horizon),
        "residual_sigma": sigma,
        "holdout_days_used": holdout_used,
        "current_rate": float(series.iloc[-1]),
    }
